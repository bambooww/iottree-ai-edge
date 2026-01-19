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

util = Blueprint('util', __name__, url_prefix='/util')


# ==================== 网页路由 ====================

# 标记是否已初始化
_initialized = False

@util.record_once
def on_load(setup_state):
    """蓝图被加载到应用时调用（一次）"""
    global _initialized
    if not _initialized:
        # 进入上下文管理器
        # gesture_ser.__enter__()
        _initialized = True
        
        # 注册清理函数
        def cleanup():
            if _initialized:
                #gesture_ser.__exit__(None, None, None)
                pass
        
        # 方法1：使用 atexit
        #atexit.register(cleanup)
        
        # 方法2：存储到应用上下文
        # app = setup_state.app
        # app.auth_resource = gesture_ser
        # app.auth_cleanup = cleanup

@util.teardown_app_request
def teardown_request(exception=None):
    """每个请求结束时调用"""
    if exception:
        print(f"请求异常: {exception}")

@util.route('/')
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



@util.route('/camera_reco?camera_id=<camera_id>&process=<process>', methods=['GET'])
def camera_reco(camera_id, process = "gesture"):
    camera = camera_mgr.get_camera(camera_id)
    if(camera is None):
        return "camera not found", 404
    pro = camera_mgr.get_process(process)
    if(pro is None):
        return "process not found", 404
    
    frame = camera.get_camera_frame(camera_id)
    return jsonify({
        'success': True,
        'camera_id': camera_id,
        'has_frame': frame is not None,
        'is_running': camera_id in camera.active_cameras
    })

@util.route('/api/detect/video/start', methods=['POST'])
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

@util.route('/api/detect/video/stop', methods=['POST'])
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

@util.route('/api/detect/video/result', methods=['GET'])
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

@util.route('/api/stream/status', methods=['GET'])
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