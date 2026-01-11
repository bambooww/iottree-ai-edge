import cv2
from ultralytics import YOLO
import threading
from typing import Dict, List, Any, Optional
import time
import numpy as np
import base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from typing import Protocol, runtime_checkable

# 定义回调接口协议
@runtime_checkable
class CameraProcessCallback(Protocol):
    def on_frame_process_result(self, result:Dict, annoted_frame:cv2.typing.MatLike | None) -> None: ...
    
@runtime_checkable
class CameraProcess(Protocol):
    def is_camera_process_async(self) -> bool: ...
    def set_camera_process_callback(self, callback: CameraProcessCallback) -> None: ...
    def on_camera_frame(self,frame:cv2.typing.MatLike,config: Optional[Dict] = None) -> tuple[Dict, cv2.typing.MatLike | None]: ...
    def on_camera_error(self, error) -> None: ...

class Camera:
    def __init__(self):
        """
        初始化Camera服务
        """
        self.active_cameras: Dict[int, Dict] = {}
        self.camera_results: Dict[int, Dict] = {}
        self.camera_frames: Dict[int, bytes] = {}  # 存储最新的摄像头帧（JPEG格式）
        self.config = {
            'confidence': 0.25,
            'iou': 0.45,
            'classes': None,
            'max_det': 300,
            'imgsz': 640,
            'verbose': False,
            'show_labels': True,
            'show_conf': True,
            'line_width': 2
        }

    def encode_image_to_jpeg(self, image: np.ndarray) -> bytes:
        """将OpenCV图像编码为JPEG字节流"""
        success, encoded_image = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if success:
            return encoded_image.tobytes()
        return None
    
    def on_frame_process_result(self, result:Dict, ret_frm:cv2.typing.MatLike | None) -> None:
        """处理摄像头帧处理结果回调"""
        # 存储帧用于视频流
        if(ret_frm is not None):
            frame_bytes = self.encode_image_to_jpeg(ret_frm)
            if frame_bytes:
                self.camera_frames[self.current_camear_id] = frame_bytes
        self.camera_results[self.current_camear_id] = result
        
        
    def start_camera_stream(self, camera_id: int,process:CameraProcess, config: Optional[Dict] = None) -> bool:
        """启动摄像头视频流检测"""
        if camera_id in self.active_cameras:
            logger.info(f"摄像头 {camera_id} 已在运行")
            return False
        
        self.current_camear_id = camera_id
        if(process.is_camera_process_async and process.is_camera_process_async()):
            process.set_camera_process_callback(self)

        def camera_loop():
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                self.camera_results[camera_id] = {"error": f"无法打开摄像头 {camera_id}", "success": False}
                return
            
            # 设置摄像头参数（可选）
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            logger.info(f"摄像头 {camera_id} 开始运行")
            
            while camera_id in self.active_cameras:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                try:
                    if(process.is_camera_process_async()):
                        # 异步处理不在此处实现
                        process.on_camera_frame(frame) # wait for callback
                    else:
                        result,ret_frm = process.on_camera_frame(frame)
                        # 存储帧用于视频流
                        if(ret_frm is not None):
                            frame_bytes = self.encode_image_to_jpeg(ret_frm)
                            if frame_bytes:
                                self.camera_frames[camera_id] = frame_bytes
                        self.camera_results[camera_id] = result
                except Exception as e:
                    logger.error(f"摄像头 {camera_id} 检测错误: {str(e)}")
                    time.sleep(0.1)
            
            # 清理
            cap.release()
            if camera_id in self.camera_frames:
                del self.camera_frames[camera_id]
            if camera_id in self.camera_results:
                del self.camera_results[camera_id]
            logger.info(f"摄像头 {camera_id} 已停止")
        
        # 启动摄像头线程
        thread = threading.Thread(target=camera_loop, daemon=True)
        self.active_cameras[camera_id] = {
            'thread': thread,
            'config': config or {},
            'start_time': datetime.now()
        }
        thread.start()
        
        # 等待摄像头初始化
        time.sleep(1)
        return True
    
    def stop_camera_stream(self, camera_id: int) -> bool:
        """停止摄像头视频流检测"""
        if camera_id in self.active_cameras:
            del self.active_cameras[camera_id]
            time.sleep(0.5)  # 等待线程结束
            return True
        return False
    
    def get_camera_frame(self, camera_id: int) -> Optional[bytes]:
        """获取摄像头最新帧（JPEG格式）"""
        return self.camera_frames.get(camera_id)
    
    def get_camera_result(self, camera_id: int) -> Dict:
        """获取摄像头最新检测结果"""
        return self.camera_results.get(camera_id, {"error": "摄像头未运行或未找到结果", "success": False})
    
    def get_available_cameras(self) -> List[int]:
        """获取可用的摄像头列表"""
        available = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available
    
    def get_running_cameras(self) -> List[int]:
        """获取正在运行的摄像头列表"""
        return list(self.active_cameras.keys())