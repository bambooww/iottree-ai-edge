from flask import Blueprint
from flask import Flask, request, jsonify, render_template, Response
import time
from datetime import datetime
import numpy as np
import base64
import json
import cv2
#from . import gesture_service_asyn
from util import camera_mgr
import atexit

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


admin = Blueprint('admin', __name__, url_prefix='/admin')

# ==================== 网页路由 ====================

# 标记是否已初始化
_initialized = False


@admin.record_once
def on_load(setup_state):
    """蓝图被加载到应用时调用（一次）"""
    global _initialized
    if not _initialized:
        # 进入上下文管理器
        #gesture_ser.__enter__()
        _initialized = True
        
        # 注册清理函数
        def cleanup():
            if _initialized:
                #gesture_ser.__exit__(None, None, None)
                pass
        
@admin.teardown_app_request
def teardown_request(exception=None):
    """每个请求结束时调用"""
    if exception:
        print(f"请求异常: {exception}")



@admin.route('/')
def index():
    """主页面 - 显示摄像头监控界面"""
    available_cameras = camera_mgr.list_camera_loc() #camera.get_available_cameras()
    cams = []
    for c in available_cameras:
        cams.append({
            "camera_id": c.get_camera_id(),
            "camera_title": c.get_camera_title()
        })
        return render_template('index.html',cameras=cams)

@admin.route('/list_cameras',methods=['GET',"POST"])
def list_cameras():
    try:
        result={"success": True}
        available_cameras = camera_mgr.list_camera_all() #camera.get_available_cameras()
        cams = []
        for c in available_cameras:
            cams.append(c.to_config_dict())
        result["cameras"]=cams
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


# @admin.route('/get_camera_result', methods=['GET'])
# def get_video_result2():
#     try:
#         camera_id = request.args.get('camera_id', "loc_0", type=str)
#         camera = camera_mgr.get_camera(camera_id)
#         if(camera is None):
#             return "摄像头不存在", 404
#         result = camera.get_camera_result(camera_id)
#         return jsonify(result)
        
#     except Exception as e:
#         return jsonify({
#             'error': str(e),
#             'success': False
#         }), 500

@admin.route('/set_camera', methods=['POST'])
def set_camera_ip():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '未提供配置数据', 'success': False}), 400

        camera_mgr.set_camera(data)
        return jsonify({
            'success': True,
            'message': 'set camera ok',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.info(f"err: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@admin.route('/syn_camera_ips', methods=['POST'])
def syn_camera_ips():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'no post config data', 'success': False}), 400

        camera_mgr.syn_camera_ips(data)
        return jsonify({
            'success': True,
            'message': 'syn cameras ok',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.info(f"err: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@admin.route('/del_camera', methods=['POST'])
def del_camera(camera_id:str):
    try:
        camera_id = request.args.get('camera_id', "", type=str)
        if(camera_id=="" or not camera_id.startswith("ip_")):
            return "not valid camera id", 400
        camera = camera_mgr.get_camera(camera_id)
        if(camera is None):
            return "not exist", 404
        ret,_ = camera_mgr.del_camera(camera_id)
        if(ret==False):
            return "del camera err", 500
        return jsonify({
            'success': True,
            'message': 'set camera ok',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.info(f"err: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@admin.route('/camera/detail')
def camera_show():
    """生成摄像头视频流（MJPEG格式）"""
    camera_id = request.args.get('camera_id', None, type=str)
    if(camera_id is None):
        return "未提供摄像头ID", 400
    camera = camera_mgr.get_camera(camera_id)
    if(camera is None):
        return "摄像头不存在", 404
    
    return render_template('camera.html',camera_id=camera_id,camera_title=camera.get_camera_title())


@admin.route('/camera/frames')
def camera_frames():
    """生成摄像头视频流（MJPEG格式）"""
    camera_id = request.args.get('camera_id', None, type=str)
    if(camera_id is None):
        return "未提供摄像头ID", 400
    camera = camera_mgr.get_camera(camera_id)
    if(camera is None):
        return "摄像头不存在", 404
    
    def generate():
        while True:
            frame = camera.get_camera_frame()
            # print(f" fff= {frame is not None}")
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # 如果没有帧，等待一下
                time.sleep(0.033)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@admin.route('/camera/process', methods=['GET','POST'])
def camera_process():
    try:
        camera_id = request.args.get('camera_id', None, type=str)
        if(camera_id is None):
            return "未提供摄像头ID", 400
        camera = camera_mgr.get_camera(camera_id)
        if(camera is None):
            return "摄像头不存在", 404
    
        if(request.method=='POST'):
            # change process
            process_n = request.args.get("process",None,type=str)
            if(process_n is None):
                return "no process input", 400
            proc = camera_mgr.get_process_by_name(process_n)
            if(proc is None):
                return f"no process found with name={process_n}", 400
            camera.set_process(proc)
            return jsonify({
                "success":True
                })
        else:
            # get process
            proc = camera.get_process()
            proc_n = ""
            if(proc is not None):
                proc_n = proc.get_camera_process_name()

            return jsonify({
                'success': True,
                "process":proc_n
            })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@admin.route('/camera/start', methods=['GET'])
def start_camera():
    try:
        camera_id = request.args.get('camera_id', None, type=str)
        if(camera_id is None):
            return "未提供摄像头ID", 400
        camera = camera_mgr.get_camera(camera_id)
        if(camera is None):
            return "摄像头不存在", 404
        
        proc = camera_mgr.get_process_by_name("gesture")
        camera.set_process(proc)
        success = camera.start_camera()
        
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

@admin.route('/camera/stop', methods=['GET'])
def stop_video_detection():
    try:
        camera_id = request.args.get('camera_id', None, type=str)
        if(camera_id is None):
            return "未提供摄像头ID", 400
        camera = camera_mgr.get_camera(camera_id)
        if(camera is None):
            return "摄像头不存在", 404
        
        success = camera.stop_camera()
        
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

@admin.route('/camera/result', methods=['GET'])
def get_video_result():
    try:
        camera_id = request.args.get('camera_id', None, type=str)
        if(camera_id is None):
            return "未提供摄像头ID", 400
        camera = camera_mgr.get_camera(camera_id)
        if(camera is None):
            return "摄像头不存在", 404
        result = camera.get_camera_result()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@admin.route('/camera/status', methods=['GET'])
def stream_status():
    camera_id = request.args.get('camera_id', None, type=str)
    if(camera_id is None):
        return "未提供摄像头ID", 400
    camera = camera_mgr.get_camera(camera_id)
    if(camera is None):
        return "摄像头不存在", 404
    frame = camera.get_camera_frame()
    return jsonify({
        'success': True,
        'camera_id': camera_id,
        'has_frame': frame is not None,
        'is_running': camera.is_camera_running(),
        'debug_frame':camera.is_debug_frame()
    })