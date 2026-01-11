import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

class GestureService:
    """手势识别模块"""
    mp.tasks = python

# 1. 初始化识别器
model_path = 'gesture_recognizer.task'  # 你下载的模型文件路径
base_options = mp.tasks.BaseOptions(model_asset_path=model_path)

BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Load the input image from an image file.
mp_image = mp.Image.create_from_file('./thumbs_up.jpg')

IMAGE_FILENAMES = ['thumbs_down.jpg', 'victory.jpg', 'thumbs_up.jpg', 'pointing_up.jpg']
image_paths =['thumbs_down.jpg', 'victory.jpg', 'thumbs_up.jpg', 'pointing_up.jpg']
# Load the input image from a numpy array.
# mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=numpy_image)

# Create a gesture recognizer instance with the image mode:
options = GestureRecognizerOptions(
    base_options,
    running_mode=VisionRunningMode.IMAGE)

# 2. 创建识别器
with GestureRecognizer.create_from_options(options) as recognizer:

    # 3. 读取并处理图像
    
    for image_path in image_paths:
        # 使用OpenCV读取图片
        image_cv2 = cv2.imread(image_path)
        if image_cv2 is None:
            print(f"无法读取图片: {image_path}")
            continue
        
        # 将OpenCV的BGR格式转换为RGB格式，并创建MediaPipe图像对象
        image_rgb = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        # 4. 进行识别
        recognition_result = recognizer.recognize(mp_image)
        
        # 5. 判断与展示结果
        annotated_image = image_cv2.copy()
        
        # 判断是否有检测到手
        if recognition_result.hand_landmarks:
            print(f"\n在 {image_path} 中检测到 {len(recognition_result.hand_landmarks)} 只手")
            
            # 遍历每一只检测到的手
            for hand_idx in range(len(recognition_result.hand_landmarks)):
                # 获取该手的手势分类结果（如果启用了分类器）
                if recognition_result.handedness:
                    handedness_info = recognition_result.handedness[hand_idx][0]
                    hand_label = handedness_info.category_name  # 'Left' 或 'Right'
                    #thum_lb = hand_landmarks[hand_idx]
                    confidence = handedness_info.score
                    category_name = recognition_result.gestures[hand_idx][0].category_name
                    score = recognition_result.gestures[hand_idx][0].score
                    print(f"  第{hand_idx+1}只手: {hand_label}, 置信度: {confidence:.2f}, 手势: {category_name} ({score:.2f})")
                
                # 绘制手部关键点
                hand_landmarks = recognition_result.hand_landmarks[hand_idx]
                for landmark in hand_landmarks:
                    # 将归一化坐标转换为图像像素坐标
                    x = int(landmark.x * image_cv2.shape[1])
                    y = int(landmark.y * image_cv2.shape[0])
                    cv2.circle(annotated_image, (x, y), 5, (0, 255, 0), -1)
                
                # --- 在这里添加你的自定义手势判断逻辑 ---
                # 示例：判断是否是“食指伸出”的指向手势
                # 获取指尖（INDEX_FINGER_TIP，索引为8）和其下方关节的Y坐标
                fingertip_y = hand_landmarks[8].y
                joint_below_y = hand_landmarks[6].y
                if fingertip_y < joint_below_y:  # 指尖在关节上方，说明手指伸直
                    # 可以根据其他手指是否弯曲进一步精确判断
                    cv2.putText(annotated_image, "Pointing", (50, 50+hand_idx*30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                # --- 自定义逻辑结束 ---
        else:
            print(f"\n在 {image_path} 中未检测到手部")
            cv2.putText(annotated_image, "No Hand Detected", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # 6. 展示结果图片
        cv2.imshow('Gesture Recognition Result', annotated_image)
        cv2.waitKey(0)  # 等待按键后显示下一张

    cv2.destroyAllWindows()
    # recognizer.close()  # 关闭识别器释放资源