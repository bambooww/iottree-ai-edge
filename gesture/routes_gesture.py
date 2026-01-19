from flask import Blueprint
from flask import Flask, request, jsonify, render_template, Response
import time
from datetime import datetime
import numpy as np
import base64
import json
import cv2
from . import gesture_service_asyn
from util import camera_mgr
import atexit

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("加载手势识别路由...")
gest = Blueprint('gesture', __name__, url_prefix='/gesture')

# 初始化服务
logger.info("初始化手势识别服务...")
gesture_ser = gesture_service_asyn.GestureServiceAsyn(draw_result_image=True)

#logger.info("初始化摄像头服务...")
#camera = CameraLoc()

# ==================== 网页路由 ====================

# 标记是否已初始化
_initialized = False

@gest.record_once
def on_load(setup_state):
    """蓝图被加载到应用时调用（一次）"""
    global _initialized
    if not _initialized:
        # 进入上下文管理器
        gesture_ser.__enter__()
        _initialized = True
        
        # 注册清理函数
        def cleanup():
            if _initialized:
                gesture_ser.__exit__(None, None, None)
        
        # 方法1：使用 atexit
        #atexit.register(cleanup)
        
        # 方法2：存储到应用上下文
        # app = setup_state.app
        # app.auth_resource = gesture_ser
        # app.auth_cleanup = cleanup

@gest.teardown_app_request
def teardown_request(exception=None):
    """每个请求结束时调用"""
    if exception:
        print(f"请求异常: {exception}")

@gest.route('/')
def index():
    """主页面 - 显示摄像头监控界面"""
    available_cameras = camera_mgr.list_camera_loc() #camera.get_available_cameras()
    cams = []
    for c in available_cameras:
        cams.append({
            "camera_id": c.get_camera_id(),
            "camera_title": c.get_camera_title()
        })
    return render_template('index_gesture.html',
                            cameras=cams)

@gest.route('/video_feed/<str:camera_id>')
def video_feed(camera_id):
    """生成摄像头视频流（MJPEG格式）"""
    camera = camera_mgr.get_camera(camera_id)
    if(camera is None):
        return "摄像头不存在", 404
    
    def generate():
        while True:
            frame = camera.get_camera_frame(camera_id)
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # 如果没有帧，等待一下
                time.sleep(0.033)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@gest.route('/video_feed_single/<str:camera_id>')
def video_feed_single(camera_id):
    """获取单张摄像头帧（用于AJAX请求）"""
    camera = camera_mgr.get_camera(camera_id)
    if(camera is None):
        return "摄像头不存在", 404
    
    frame = camera.get_camera_frame(camera_id)
    if frame:
        return Response(frame, mimetype='image/jpeg')
    else:
        # 返回空白图像
        blank_image = np.zeros((480, 640, 3), dtype=np.uint8)
        blank_image.fill(50)  # 灰色背景
        _, buffer = cv2.imencode('.jpg', blank_image)
        return Response(buffer.tobytes(), mimetype='image/jpeg')

# ==================== API路由 ====================

# @gest.route('/api/health', methods=['GET'])
# def health_check():
#     return jsonify({
#         'status': 'healthy',
#         'service': 'yolo-detection-api',
#         'timestamp': datetime.now().isoformat(),
#         'running_cameras': camera.get_running_cameras()
#     })

@gest.route('/api/detect/image', methods=['POST'])
def detect_image():
    try:
        config = {}
        if request.form:
            config_json = request.form.get('config', '{}')
            try:
                config = json.loads(config_json)
            except:
                pass
        
        image_data = None
        
        if 'image' in request.files:
            file = request.files['image']
            image_data = file.read()
        elif request.is_json:
            data = request.get_json()
            if 'image_base64' in data:
                base64_str = data['image_base64']
                if 'base64,' in base64_str:
                    base64_str = base64_str.split('base64,')[1]
                image_data = base64.b64decode(base64_str)
            if 'config' in data:
                config.update(data['config'])
        
        if image_data is None:
            return jsonify({
                'error': '未提供图片数据',
                'success': False
            }), 400
        
        result = gesture_ser.recognize_gesture(image_data, config)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API错误: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@gest.route('/api/detect/video/start', methods=['POST'])
def start_video_detection():
    try:
        data = request.get_json() or {}
        camera_id = data.get('camera_id', "loc_0")
        camera = camera_mgr.get_camera(camera_id)
        if(camera is None):
            return "摄像头不存在", 404
    
        config = data.get('config', {})
        
        available_cameras = camera.get_available_cameras()
        if camera_id not in available_cameras:
            return jsonify({
                'error': f'摄像头 {camera_id} 不可用',
                'available_cameras': available_cameras,
                'success': False
            }), 400
        
        success = camera.start_camera(camera_id,gesture_ser, config)
        
        return jsonify({
            'success': success,
            'camera_id': camera_id,
            'message': '摄像头检测已启动' if success else '摄像头已在运行或启动失败',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@gest.route('/api/detect/video/stop', methods=['POST'])
def stop_video_detection():
    try:
        data = request.get_json() or {}
        camera_id = data.get('camera_id', "loc_0")
        camera = camera_mgr.get_camera(camera_id)
        if(camera is None):
            return "摄像头不存在", 404
        
        success = camera.stop_camera(camera_id)
        
        return jsonify({
            'success': success,
            'camera_id': camera_id,
            'message': '摄像头检测已停止' if success else '摄像头未在运行'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@gest.route('/api/detect/video/result', methods=['GET'])
def get_video_result():
    try:
        camera_id = request.args.get('camera_id', "loc_0", type=str)
        camera = camera_mgr.get_camera(camera_id)
        if(camera is None):
            return "摄像头不存在", 404
        result = camera.get_camera_result(camera_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

# @gest.route('/api/config/update', methods=['POST'])
# def update_config():
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'error': '未提供配置数据', 'success': False}), 400
        
#         yolo_service.update_config(data)
        
#         return jsonify({
#             'success': True,
#             'message': '配置更新成功',
#             'current_config': yolo_service.config,
#             'timestamp': datetime.now().isoformat()
#         })
        
#     except Exception as e:
#         return jsonify({
#             'error': str(e),
#             'success': False
#         }), 500

# @gest.route('/api/config/current', methods=['GET'])
# def get_current_config():
#     return jsonify({
#         'success': True,
#         'config': yolo_service.config,
#         'class_names': yolo_service.class_names,
#         'custom_categories': yolo_service.custom_categories
#     })

# @gest.route('/api/cameras/available', methods=['GET'])
# def get_available_cameras():
#     available = camera.get_available_cameras()
#     return jsonify({
#         'success': True,
#         'available_cameras': available,
#         'count': len(available)
#     })

# @gest.route('/api/cameras/running', methods=['GET'])
# def get_running_cameras():
#     running = camera.get_running_cameras()
#     return jsonify({
#         'success': True,
#         'running_cameras': running,
#         'count': len(running)
#     })

# @gest.route('/api/categories/list', methods=['GET'])
# def list_categories():
#     return jsonify({
#         'success': True,
#         'all_classes': yolo_service.class_names,
#         'custom_categories': yolo_service.custom_categories,
#         'total_classes': len(yolo_service.class_names)
#     })

@gest.route('/api/stream/status', methods=['GET'])
def stream_status():
    camera_id = request.args.get('camera_id', None, type=str)
    if(camera_id is None):
        return "未提供摄像头ID", 400
    camera = camera_mgr.get_camera(camera_id)
    if(camera is None):
        return "摄像头不存在", 404
    frame = camera.get_camera_frame(camera_id)
    return jsonify({
        'success': True,
        'camera_id': camera_id,
        'has_frame': frame is not None,
        'is_running': camera_id in camera.active_cameras
    })