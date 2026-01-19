import threading
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

from util.camera import Camera, CameraProcess,CameraProcessCallback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

class GestureProcess(CameraProcess):
    _process_result:Dict|None
    _process_annoted_frame:cv2.typing.MatLike | None
    _recognizer = None

    _lock:threading.RLock = threading.RLock()

    def __init__(self, model_path: str = '_models/gesture_recognizer.task'):
        self.model_path = model_path
        self.base_options = BaseOptions(model_asset_path=model_path)
        

        # Load the input image from an image file.
        #mp_image = mp.Image.create_from_file('./thumbs_up.jpg')

        # IMAGE_FILENAMES = ['thumbs_down.jpg', 'victory.jpg', 'thumbs_up.jpg', 'pointing_up.jpg']
        # image_paths =['thumbs_down.jpg', 'victory.jpg', 'thumbs_up.jpg', 'pointing_up.jpg']
        # Load the input image from a numpy array.
        # mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=numpy_image)

        # Create a gesture recognizer instance with the image mode:
        
        
    def __enter__(self):
        self.get_or_create_recognizer()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        logger.info("关闭手势识别器实例...")
        if self._recognizer:
            self._recognizer.close()
            self._recognizer = None
    
    def get_or_create_recognizer(self):
        with self._lock:
            if(self._recognizer is not None):
                return self._recognizer
            
            self.options = GestureRecognizerOptions(
                self.base_options,
                num_hands=2,
                running_mode=VisionRunningMode.LIVE_STREAM,
                result_callback=self.result_callback)  # VIDEO LIVE_STREAM
            logger.info("手势识别服务初始化完成。")

            logger.info("创建手势识别器实例...")
            self._recognizer = GestureRecognizer.create_from_options(self.options)
            return self._recognizer
        
    def get_camera_process_name(self)->str:
        return "gesture"

    def result_callback(self, recognition_result, output_image, timestamp_ms):
        """处理视频流回调结果"""
         # 判断与展示结果
        annotated_image = None
        if self.is_owner_camera_debug():
            annotated_image = annotated_image = self.current_frame.copy()
        
        # 判断是否有检测到手
        res = None
        if recognition_result.hand_landmarks:
            # print(f"\n在摄像头帧中检测到 {len(recognition_result.hand_landmarks)} 只手")
            
            # 遍历每一只检测到的手
            res = {}
            for hand_idx in range(len(recognition_result.hand_landmarks)):
                if recognition_result.handedness:
                    handedness_info = recognition_result.handedness[hand_idx][0]
                    hand_label = handedness_info.category_name  # 'Left' 或 'Right'
                    #thum_lb = hand_landmarks[hand_idx]
                    confidence = handedness_info.score
                    category_name = recognition_result.gestures[hand_idx][0].category_name
                    score = recognition_result.gestures[hand_idx][0].score
                    # print(f"  第{hand_idx+1}只手: {hand_label}, 置信度: {confidence:.2f}, 手势: {category_name} ({score:.2f})")
                    res[hand_idx] = {
                        'hand_idx': hand_idx,
                        'hand_label': hand_label,
                        'confidence': confidence,
                        'hand_category': category_name,
                        'category_score': score
                    }
                
                if(annotated_image is not None):
                    # 绘制手部关键点
                    hand_landmarks = recognition_result.hand_landmarks[hand_idx]
                    for landmark in hand_landmarks:
                        # 将归一化坐标转换为图像像素坐标
                        x = int(landmark.x * self.current_frame.shape[1])
                        y = int(landmark.y * self.current_frame.shape[0])
                        cv2.circle(annotated_image, (x, y), 5, (0, 255, 0), -1)
        
        if(res is not None):
            self._process_result={
                'success': True,
                'hand_count': len(recognition_result.hand_landmarks),
                'timestamp': datetime.now().isoformat(),
                'results': res
            }
            self._process_annoted_frame = annotated_image
            if(self.process_callback is not None):
                self.process_callback.on_frame_process_result(self._process_result, annotated_image)
            # if(self._owner_camera is not None):
            #     self._owner_camera.on_process_callback(self._process_result, annotated_image)

    def is_camera_process_async(self) -> bool:
        return True
    
    def get_camera_process_result(self)-> tuple[Dict|None,cv2.typing.MatLike|None]:
        return self._process_result,self._process_annoted_frame

    def set_camera_process_callback(self, callback: CameraProcessCallback) -> None:
        self.process_callback = callback

    def set_camera_debug(self, debug: bool=False) -> None:
        # self.draw_result_image = debug
        pass
    
    def on_camera_frame(self, frame:cv2.typing.MatLike,config: Optional[Dict] = None) -> tuple[Dict, cv2.typing.MatLike | None]:
        """处理摄像头帧回调"""
        # 将OpenCV的BGR格式转换为RGB格式，并创建MediaPipe图像对象
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        self.current_frame = frame
        # 进行识别
        self.get_or_create_recognizer().recognize_async(mp_image,int(datetime.now().timestamp() * 1000))
        