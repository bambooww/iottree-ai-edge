from abc import abstractmethod
import typing
import cv2
from ultralytics import YOLO
import threading
from typing import Dict, List, Any, Optional
import time
import numpy as np
import base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from util.camera import Camera,CameraProcessCallback, CameraProcess

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_loc_inner_camera_ids() -> List[int]:
    """获取可用的摄像头列表"""
    available = []
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available

class CameraLoc(Camera):

    _inner_camera_id:int = 0
    _cap:cv2.VideoCapture = None

    def __init__(self,inner_camera_id: int,config: Optional[Dict] = None):
        """
        初始化Camera服务
        """
        Camera.__init__(self, camera_id="loc_"+str(inner_camera_id), config=config)
        self._inner_camera_id = inner_camera_id
        # self.active_cameras: Dict[int, Dict] = {}
        # self.camera_results: Dict[int, Dict] = {}
        # self.camera_frames: Dict[int, bytes] = {}  # 存储最新的摄像头帧（JPEG格式）
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

        if(config is not None):
            self.config.update(config)
    
    #@typing.override
    def get_camera_tp(self) -> str:
        return "loc"

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
        self._cap = cv2.VideoCapture(self._inner_camera_id)
        if not self._cap.isOpened():
            self._camera_result = {"error": f"无法打开摄像头 {self._inner_camera_id}", "success": False}
            return False
        
        # 设置摄像头参数（可选）
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config["cap_width"] if "cap_width" in self.config else 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config["cap_height"] if "cap_height" in self.config else 480)
        self._cap.set(cv2.CAP_PROP_FPS, self.config["cap_fps"] if "cap_fps" in self.config else 30)
        return True
    
    #@typing.override
    def _on_get_frame_camera_run(self) -> tuple[Dict, cv2.typing.MatLike]:
        return self._cap.read()
    
    #@typing.override
    def _on_after_camera_run(self) -> bool:
        self._cap.release()
    