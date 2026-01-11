from flask import Blueprint
from flask import Flask, request, jsonify, render_template, Response
import time
from datetime import datetime
import numpy as np
import base64
import json
import cv2
from util_log import logger
from . import yolo_service
from camera import Camera

yolo = Blueprint('yolo', __name__, url_prefix='/yolo')

# 初始化YOLO服务
yolo_service = yolo_service.YOLOService('_models/yolov8n.pt')
camera = Camera()
# ==================== 网页路由 ====================

@yolo.route('/')
def index():
    """主页面 - 显示摄像头监控界面"""
    available_cameras = camera.get_available_cameras()
    running_cameras = camera.get_running_cameras()
    return render_template('index_yolo.html', 
                          available_cameras=available_cameras,
                          running_cameras=running_cameras)

@yolo.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    """生成摄像头视频流（MJPEG格式）"""
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

@yolo.route('/video_feed_single/<int:camera_id>')
def video_feed_single(camera_id):
    """获取单张摄像头帧（用于AJAX请求）"""
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

@yolo.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'yolo-detection-api',
        'timestamp': datetime.now().isoformat(),
        'running_cameras': yolo_service.get_running_cameras()
    })

@yolo.route('/api/detect/image', methods=['POST'])
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
        
        result = yolo_service.detect_image(image_data, config)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API错误: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@yolo.route('/api/detect/video/start', methods=['POST'])
def start_video_detection():
    try:
        data = request.get_json() or {}
        camera_id = data.get('camera_id', 0)
        config = data.get('config', {})
        
        available_cameras = camera.get_available_cameras()
        if camera_id not in available_cameras:
            return jsonify({
                'error': f'摄像头 {camera_id} 不可用',
                'available_cameras': available_cameras,
                'success': False
            }), 400
        
        success = camera.start_camera_stream(camera_id,yolo_service, config)
        
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

@yolo.route('/api/detect/video/stop', methods=['POST'])
def stop_video_detection():
    try:
        data = request.get_json() or {}
        camera_id = data.get('camera_id', 0)
        
        success = camera.stop_camera_stream(camera_id)
        
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

@yolo.route('/api/detect/video/result', methods=['GET'])
def get_video_result():
    try:
        camera_id = request.args.get('camera_id', 0, type=int)
        result = camera.get_camera_result(camera_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@yolo.route('/api/config/update', methods=['POST'])
def update_config():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '未提供配置数据', 'success': False}), 400
        
        yolo_service.update_config(data)
        
        return jsonify({
            'success': True,
            'message': '配置更新成功',
            'current_config': yolo_service.config,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@yolo.route('/api/config/current', methods=['GET'])
def get_current_config():
    return jsonify({
        'success': True,
        'config': yolo_service.config,
        'class_names': yolo_service.class_names,
        'custom_categories': yolo_service.custom_categories
    })

@yolo.route('/api/cameras/available', methods=['GET'])
def get_available_cameras():
    available = camera.get_available_cameras()
    return jsonify({
        'success': True,
        'available_cameras': available,
        'count': len(available)
    })

@yolo.route('/api/cameras/running', methods=['GET'])
def get_running_cameras():
    running = camera.get_running_cameras()
    return jsonify({
        'success': True,
        'running_cameras': running,
        'count': len(running)
    })

@yolo.route('/api/categories/list', methods=['GET'])
def list_categories():
    return jsonify({
        'success': True,
        'all_classes': yolo_service.class_names,
        'custom_categories': yolo_service.custom_categories,
        'total_classes': len(yolo_service.class_names)
    })

@yolo.route('/api/stream/status', methods=['GET'])
def stream_status():
    camera_id = request.args.get('camera_id', 0, type=int)
    frame = camera.get_camera_frame(camera_id)
    return jsonify({
        'success': True,
        'camera_id': camera_id,
        'has_frame': frame is not None,
        'is_running': camera_id in camera.active_cameras
    })