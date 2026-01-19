import traceback
import cv2
from ultralytics import YOLO
import threading
from typing import Dict, List, Any, Optional
import time
import numpy as np
import base64
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from typing import Protocol, runtime_checkable
import logging

# from util import camera_mgr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CameraType(Enum):
    """相机类型枚举"""
    WEBCAM = "webcam"       # 本地USB摄像头
    RTSP = "rtsp"           # RTSP网络摄像头
    HTTP = "http"           # HTTP/MJPEG流
    GIGE = "gige"           # GigE工业相机
    FILE = "file"           # 视频文件
    DUMMY = "dummy"         # 虚拟相机（用于测试）

@dataclass
class CameraConfig:
    """相机配置数据类"""
    camera_id: str
    camera_type: CameraType
    source: str = "0"  # 对于webcam是设备ID，对于RTSP是URL等
    width: int = 640
    height: int = 480
    fps: int = 30
    auto_start: bool = False
    extra_params: Dict[str, Any] = field(default_factory=dict)

# 定义回调接口协议
@runtime_checkable
class CameraProcessCallback(Protocol):
    def on_frame_process_result(self, result:Dict, annoted_frame:cv2.typing.MatLike | None) -> None: ...

@runtime_checkable
class CameraProcess(Protocol):
    _owner_camera = None


    def get_owner_camera(self):
        return self._owner_camera
    
    def is_owner_camera_debug(self)->bool:
        if(self._owner_camera is None):
            return False
        return self._owner_camera.is_debug_frame()
    
    def get_camera_process_name()->str: ...
    def is_camera_process_async(self) -> bool: ...
    def set_camera_process_callback(self, callback: CameraProcessCallback) -> None: ...
    def on_camera_frame(self,frame:cv2.typing.MatLike,config: Optional[Dict] = None) -> tuple[Dict, cv2.typing.MatLike | None]: ...
    def on_camera_error(self, error) -> None: ...
    def set_camera_debug(self, debug: bool=False) -> None: ...
    def get_camera_process_result(self)-> tuple[Dict|None,cv2.typing.MatLike|None]: ...


class Camera(ABC):

    _camera_id: str
    _camera_config: Optional[Dict] = None

    _process:CameraProcess = None

    _camera_frame:bytes = None
    _camera_result:Dict = None

    _lock:threading.RLock = threading.RLock()

    _period_start_time:float = 0.0
    _period_seconds:float = 5.0
    _period_triggered:bool = False

    _thread:threading.Thread = None

    _debug_frame:bool= False

    def __init__(self,camera_id: str,config: Optional[Dict] = None):
        self._camera_id = camera_id
        self._camera_config = config
        if(self._camera_config is None):
            self._camera_config = {}
        self._debug_frame = self._camera_config.get("debug_frame",False)
    
    def get_camera_id(self) -> str:
        return self._camera_id
    
    def get_camera_title(self) -> str:
        return f"Camera-{self._camera_id}"

    @abstractmethod
    def get_camera_tp(self) -> str:
        raise NotImplementedError

    def get_camera_config(self) -> Optional[Dict]:
        return self._camera_config
    
    @abstractmethod
    def _on_before_camera_run(self) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    def _on_get_frame_camera_run(self) -> tuple[Dict, cv2.typing.MatLike]:
        raise NotImplementedError
    
    @abstractmethod
    def _on_after_camera_run(self) -> bool:
        raise NotImplementedError

    def set_debug_frame(self,b:bool)->None:
        self._debug_frame = b
    
    def is_debug_frame(self)->bool:
        return self._debug_frame
    
    def on_process_callback(self,result,ret_frm):
        if(ret_frm is not None and self._debug_frame):
            frame_bytes = self.encode_image_to_jpeg(ret_frm)
            if frame_bytes:
                self._camera_frame = frame_bytes
        self._camera_result = result
        
    def start_camera(self) -> bool:
        """启动摄像头视频流检测"""
        
        with threading.RLock():

            if(self._thread is not None and self._thread.is_alive()):
                logger.info(f"Camera {self.get_camera_title()} {self.get_camera_id()} is in running")
                return False
            

            # if self.camera_id in self.active_cameras:
            #     logger.info(f"摄像头 {self.camera_id} 已在运行")
            #     return False

            # self.current_camear_id = self.camera_id
            if(self._process is not None):
                if(self._process.is_camera_process_async and self._process.is_camera_process_async()):
                    self._process.set_camera_process_callback(self)
                    if(self._camera_config is not None):
                        self._process.set_camera_debug(self._camera_config.get("debug", False))

            def camera_loop():
                
                if not self._on_before_camera_run():
                    return
                
                logger.info(f"摄像头 {self._camera_id} 开始运行")
                
                try:
                    while self._thread is not None:
                        ret, frame = self._on_get_frame_camera_run()
                        if not ret:
                            time.sleep(0.1)
                            continue
                        
                        
                        if(self._process is None):
                            if(self._debug_frame):
                                frame_bytes = self.encode_image_to_jpeg(frame)
                                self._camera_frame = frame_bytes
                            continue

                        try:
                            if(self._process.is_camera_process_async()):
                                # 异步处理不在此处实现
                                self._process.on_camera_frame(frame) # wait for callback
                            else:
                                result,ret_frm = self._process.on_camera_frame(frame)
                                # 存储帧用于视频流
                                self.on_process_callback(result,ret_frm)
                        except Exception as e:
                            logger.error(f"摄像头 {self._camera_id} 检测错误: {str(e)}")
                            traceback.print_exc()
                            time.sleep(0.1)
                
                    # 清理
                    self._on_after_camera_run()

                    logger.info(f"摄像头 {self._camera_id} 已停止")
                finally:
                    self._thread = None

            # 启动摄像头线程
            self._thread = threading.Thread(target=camera_loop, daemon=True)
            # self.active_cameras[self.camera_id] = {
            #     'thread': thread,
            #     'config': self.config or {},
            #     'start_time': datetime.now()
            # }
            self._thread.start()
            
            # 等待摄像头初始化
            time.sleep(1)
            return True
    
    def stop_camera(self) -> bool:
        """停止摄像头视频流检测"""
        with threading.RLock():
            # if camera_id in self.active_cameras:
            #     del self.active_cameras[self.camera_id]
            #     time.sleep(0.5)  # 等待线程结束
            #     return True
            if self._thread is not None and self._thread.is_alive():
                del self._thread
                time.sleep(0.5)  # 等待线程结束
                self._thread = None
                return True
            return False
    
    def is_camera_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
    

    def get_camera_frame(self) -> bytes|None:
        """获取摄像头最新帧（JPEG格式）"""
        return self._camera_frame #camera_frames.get(camera_id)
    
    def get_camera_result(self) -> Dict|None:
        """获取摄像头最新检测结果"""
        return self._camera_result
    
    def get_camera_status(self)->Dict:
        return {
            "running":self.is_camera_running(),
            "debug_frame":self._debug_frame
        }
    
    def to_config_dict(self) -> Dict:
        """将摄像头信息转换为配置字典"""
        return {
            "id": self._camera_id,
            "t": self.get_camera_title(),
            "tp": self.get_camera_tp()
        }

    def close(self):
        """释放资源"""
        self.stop_camera(self)
    
    def encode_image_to_jpeg(self, image: np.ndarray) -> bytes:
        """将OpenCV图像编码为JPEG字节流"""
        success, encoded_image = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if success:
            return encoded_image.tobytes()
        return None
    
    def get_process(self) -> CameraProcess:
        """获取摄像头处理器"""
        return self._process
    
    def set_process(self, process:CameraProcess) -> None:
        """设置摄像头处理器"""
        with self._lock:
            self._process = process
            if process is not None:
                process._owner_camera = self

    # def set_process_by_name(self, process:str) -> bool:
    #     """设置摄像头处理器"""
    #     with self._lock:
    #         if(process is None or process==""):
    #             self._process = None
    #             return True
            
    #         proc = camera_mgr.get_process_by_name(process)
    #         if(proc is None):
    #             return False
    #         self._process = proc
    #         return True

    def trigger_process_period_ret(self,period_seconds:float=5.0) -> tuple[bool,Dict|None,cv2.typing.MatLike|None]:
        """触发摄像头处理器处理结果回调"""
        
        with self._lock:
            if(self._process is None):
                return False,None,None
        
            if self.is_camera_running():
                self._period_start_time = time.time()
                self._period_triggered = True
                return True,self._process.get_camera_process_result()
            
            self.start_camera()
            self._period_start_time = time.time()
            self._period_triggered = True
            return True,self._process.get_camera_process_result()
