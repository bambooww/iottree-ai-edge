import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

class GestureService:
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
        self.options = GestureRecognizerOptions(
            self.base_options,
            running_mode=VisionRunningMode.IMAGE
            )  # VIDEO LIVE_STREAM
        logger.info("手势识别服务初始化完成。")
        
    def __enter__(self):
        logger.info("创建手势识别器实例...")
        self.recognizer = GestureRecognizer.create_from_options(self.options)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        logger.info("关闭手势识别器实例...")
        if self.recognizer:
            self.recognizer.close()
            self.recognizer = None

    def recognize_gesture(self, image_path: str):
        # 使用OpenCV读取图片
        image_cv2 = cv2.imread(image_path)
        if image_cv2 is None:
            print(f"无法读取图片: {image_path}")
            return None
        
        # 将OpenCV的BGR格式转换为RGB格式，并创建MediaPipe图像对象
        image_rgb = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        # 进行识别
        recognition_result = self.recognizer.recognize(mp_image)
        
        # 判断与展示结果
        annotated_image = image_cv2.copy()
        
        # 判断是否有检测到手
        if recognition_result.hand_landmarks:
            print(f"\n在 {image_path} 中检测到 {len(recognition_result.hand_landmarks)} 只手")
            
            # 遍历每一只检测到的手
            for hand_idx in range(len(recognition_result.hand_landmarks)):
                pass  # 这里可以添加对每只手的处理逻辑
        
        return recognition_result, annotated_image
    
    def on_camera_frame(self, frame:cv2.typing.MatLike,config: Optional[Dict] = None) -> tuple[Dict, cv2.typing.MatLike | None]:
        """处理摄像头帧回调"""
        # 将OpenCV的BGR格式转换为RGB格式，并创建MediaPipe图像对象
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        # 进行识别
        recognition_result = self.recognizer.recognize(mp_image)
        
        # 判断与展示结果
        annotated_image = frame.copy()
        
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
                # 绘制手部关键点
                hand_landmarks = recognition_result.hand_landmarks[hand_idx]
                for landmark in hand_landmarks:
                    # 将归一化坐标转换为图像像素坐标
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    cv2.circle(annotated_image, (x, y), 5, (0, 255, 0), -1)
        
        if(res is not None):
            return ({
                'success': True,
                'hand_count': len(recognition_result.hand_landmarks),
                'timestamp': datetime.now().isoformat(),
                'results': res
            }, annotated_image)
        else:
            return ({
            'success': False,
            'error': '未检测到手部'
            }, annotated_image)