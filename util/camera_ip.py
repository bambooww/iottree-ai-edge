# rtsp_worker.py
import av
import cv2
import threading
import logging
import time
from typing import Callable, Optional,Dict

from util.camera import Camera, CameraProcess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraIP(Camera):
    url:str = ""
    title:str = ""

    _container:Optional[av.container.InputContainer] = None

    def __init__(self,camera_id: str,title:str,config: Optional[Dict] = None):
        Camera.__init__(self, camera_id=camera_id, config=config)

        self.set_camera_basic(title=title, config=config)
        # self.read_timeout = read_timeout
        # self.retry_interval = retry_interval
        # self.max_retry = max_retry
        # self.on_frame = on_frame or self._default_callback
        # self.on_error = on_error or self._default_callback

        # self._thread: Optional[threading.Thread] = None
        # self._running = False
        # self._container: Optional[av.Container] = None

    def get_camera_title(self) -> str:
        return self.title

    def get_camera_tp(self) -> str:
        return "ip"
    
    def to_config_dict(self) -> Dict:
        ret = super().to_config_dict()
        ret["u"] = self.url
        return ret
    
    def set_camera_basic(self,title:str,config: Optional[Dict] = None):
        self.title = title
        if(config is not None):
            self._camera_config.update(config)
        
        self.url = self._camera_config.get("url", "")
        if(self.url ==""):
            self.url = self._camera_config.get("u", "")
        self.title = title
        self.connect_timeout = self._camera_config.get("connect_timeout", 3.0)
        self.read_timeout = self._camera_config.get("read_timeout", 3.0)
        self.retry_interval = self._camera_config.get("retry_interval", 5.0)

    #@typing.override
    def on_frame_process_result(self, result:Dict, ret_frm:cv2.typing.MatLike | None) -> None:
        """处理摄像头帧处理结果回调"""
        # 存储帧用于视频流
        if(ret_frm is not None):
            frame_bytes = self.encode_image_to_jpeg(ret_frm)
            if frame_bytes:
                self._camera_frame = frame_bytes
        self._camera_result = result
    
    #@typing.override
    def _on_before_camera_run(self) -> bool:
        return True

    def _on_get_frame_camera_run(self) -> tuple[Dict, cv2.typing.MatLike]:
        return self._cam_conn_and_read()
    
    #@typing.override
    def _on_after_camera_run(self) -> bool:
        if(self._container is not None):
            self._container.close()
            self._container = None
        return True
    
 

    def _open_container(self) -> Optional[av.container.InputContainer]:
        try:
            container = av.open(
                self.url,
                options={
                    "timeout": str(int(self.connect_timeout * 1_000_000)),
                    "tcp_timeout": str(int(self.connect_timeout * 1_000_000)),
                    "stimeout": str(int(self.connect_timeout * 1_000_000)),
                },
                timeout=self.connect_timeout
            )
            logging.info("容器已打开")
            return container
        except av.error.ExitError as e:
            logging.warning("打开容器失败：%s", e)
            # self.on_error(e)
            return None


    def _cam_conn_and_read(self):
        """connect and read frame"""
        # ---------- 1. 连接 ----------
        if self._container is None:
            logging.info("正在连接 %s ...", self.url)
            self._container = self._open_container()
            if self._container is None:
                return False,None
            
        # ---------- 2. 读取帧 ----------
        start = time.time()
        try:
            img = self._read_frame(self._container)
            return img is not None, img
        except Exception as e:
            logging.warning("流异常：%s", e)
            self._container.close()
            self._container = None
            return False,None

    def _read_frame(self,container):
        """带超时的帧读取"""
        start = time.time()
        for packet in container.demux(video=0):   # 只取视频流
            for frame in packet.decode():
                return frame.to_ndarray(format='bgr24')  # 返回 BGR numpy 数组
            if time.time() - start > self.read_timeout:
                logging.warning("帧读取超时（>%s`s）", self.read_timeout)
                return None
        return None
            
