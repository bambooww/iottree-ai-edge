import cv2
from ultralytics import YOLO
import threading
from typing import Dict, List, Any, Optional
import time
import numpy as np
import base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from util_log import logger

class YOLOService:
    def __init__(self, model_path: str = '_models/yolov8n.pt'):
        """
        初始化YOLO服务 yolov8n-pose.pt yolov8n.pt
        """
        self.model = YOLO(model_path)
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
        
        # YOLOv8 COCO数据集类别映射
        self.class_names = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
            'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
            'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
            'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
            'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
            'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
            'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
            'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
            'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
            'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]
        
        # 颜色映射（为不同类别分配不同颜色）
        self.colors = self.generate_colors(len(self.class_names))
        
        # 自定义类别映射
        self.custom_categories = {
            'people': [0],
            'vehicles': [1, 2, 3, 4, 5, 6, 7],
            'animals': [14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
            'hand': []
        }

        
            
    
    def on_camera_frame(self, frame:cv2.typing.MatLike,config: Optional[Dict] = None) -> tuple[Dict, cv2.typing.MatLike | None]:
        """处理摄像头帧的回调函数"""
        # 处理classes参数 - 必须确保是整数列表或None
        current_config = self.config.copy()
        if config:
            for key in config:
                if key in current_config:
                    current_config[key] = config[key]

        class_param = current_config['classes']

        # 确保classes参数类型正确
        if class_param is not None:
            if isinstance(class_param, list):
                # 如果是空列表，设为None
                if len(class_param) == 0:
                    class_param = None
                # 检查列表元素类型
                elif all(isinstance(x, int) for x in class_param):
                    # 已经是整数列表，保持不变
                    pass
                elif all(isinstance(x, str) for x in class_param):
                    # 字符串列表，转换为整数ID
                    class_param = self.get_category_ids(class_param)
                else:
                    # 混合类型或不合法类型，设为None
                    class_param = None
            else:
                # 不是列表，设为None
                class_param = None

        # 执行检测
        results = self.model(
            frame,
            conf=current_config['confidence'],
            iou=current_config['iou'],
            classes=class_param,
            max_det=current_config['max_det'],
            imgsz=current_config['imgsz']
        )
        
        # 解析结果
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    detection = {
                        'class_id': int(box.cls[0]),
                        'class_name': self.class_names[int(box.cls[0])],
                        'confidence': float(box.conf[0]),
                        'bbox': box.xyxy[0].tolist(),
                        'center': [
                            float((box.xyxy[0][0] + box.xyxy[0][2]) / 2),
                            float((box.xyxy[0][1] + box.xyxy[0][3]) / 2)
                        ]
                    }
                    detections.append(detection)
        
        # 绘制检测框
        annotated_frame = frame.copy()
        if detections and current_config.get('show_labels', True):
            annotated_frame = self.draw_detections(annotated_frame, detections)
        
        
        
        # 返回结果和处理之后的结果帧
        return ({
            'success': True,
            'detections': detections,
            'detection_count': len(detections),
            'frame_size': {'width': frame.shape[1], 'height': frame.shape[0]},
            'timestamp': datetime.now().isoformat(),
        },annotated_frame)
        
    
    def generate_colors(self, n: int) -> List[tuple]:
        """为不同类别生成不同的颜色"""
        import colorsys
        colors = []
        for i in range(n):
            hue = i / n
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            colors.append(tuple(int(c * 255) for c in rgb))
        return colors
    
    def update_config(self, config: Dict):
        """更新配置参数"""
        valid_keys = ['confidence', 'iou', 'classes', 'max_det', 'imgsz', 'verbose', 
                     'show_labels', 'show_conf', 'line_width']
        for key in valid_keys:
            if key in config:
                self.config[key] = config[key]
        logger.info(f"配置已更新: {self.config}")
    
    def get_category_ids(self, category_names: List[str]) -> List[int]:
        """根据类别名称获取对应的类别ID"""
        ids = []
        for category in category_names:
            if category in self.custom_categories:
                ids.extend(self.custom_categories[category])
            else:
                if category in self.class_names:
                    ids.append(self.class_names.index(category))
        return list(set(ids)) if ids else None
    
    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """在图像上绘制检测框"""
        img_height, img_width = image.shape[:2]
        
        for detection in detections:
            bbox = detection['bbox']
            class_id = detection['class_id']
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # 转换坐标
            x1, y1, x2, y2 = map(int, bbox)
            
            # 确保坐标在图像范围内
            x1 = max(0, min(x1, img_width - 1))
            y1 = max(0, min(y1, img_height - 1))
            x2 = max(0, min(x2, img_width - 1))
            y2 = max(0, min(y2, img_height - 1))
            
            # 获取颜色
            color = self.colors[class_id % len(self.colors)]
            
            # 绘制边界框
            cv2.rectangle(image, (x1, y1), (x2, y2), color, self.config['line_width'])
            
            # 绘制标签背景
            label = f"{class_name}"
            if self.config['show_conf']:
                label += f" {confidence:.2f}"
            
            (label_width, label_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            
            # 标签背景
            cv2.rectangle(
                image, 
                (x1, y1 - label_height - 10), 
                (x1 + label_width, y1), 
                color, 
                -1
            )
            
            # 标签文本
            cv2.putText(
                image, 
                label, 
                (x1, y1 - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (255, 255, 255), 
                1
            )
        
        return image
    
    
    def detect_image(self, image_data: bytes, config: Optional[Dict] = None) -> Dict:
        """检测图片"""
        try:
            current_config = self.config.copy()
            if config:
                for key in config:
                    if key in current_config:
                        current_config[key] = config[key]
            
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {"error": "无法解码图片", "success": False}
            
            # 获取类别ID
            class_ids = current_config['classes']
            if isinstance(class_ids, list) and all(isinstance(x, str) for x in class_ids):
                class_ids = self.get_category_ids(class_ids)
            
            # 执行检测
            results = self.model(
                img,
                conf=current_config['confidence'],
                iou=current_config['iou'],
                classes=class_ids,
                max_det=current_config['max_det'],
                imgsz=current_config['imgsz'],
                verbose=current_config['verbose']
            )
            
            # 解析结果
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        detection = {
                            'class_id': int(box.cls[0]),
                            'class_name': self.class_names[int(box.cls[0])],
                            'confidence': float(box.conf[0]),
                            'bbox': box.xyxy[0].tolist(),
                            'center': [
                                float((box.xyxy[0][0] + box.xyxy[0][2]) / 2),
                                float((box.xyxy[0][1] + box.xyxy[0][3]) / 2)
                            ]
                        }
                        detections.append(detection)
            
            # 绘制检测框
            annotated_image = img.copy()
            if detections and current_config.get('show_labels', True):
                annotated_image = self.draw_detections(annotated_image, detections)
            
            # 编码为base64用于网页显示
            _, buffer = cv2.imencode('.jpg', annotated_image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'success': True,
                'image_size': {'width': img.shape[1], 'height': img.shape[0]},
                'detections': detections,
                'detection_count': len(detections),
                'annotated_image_base64': f"data:image/jpeg;base64,{image_base64}",
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"图片检测错误: {str(e)}")
            return {"error": str(e), "success": False}
    
    