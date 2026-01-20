import cv2
from ultralytics import YOLO
import threading
from typing import Dict, List, Any, Optional
import time
import numpy as np
import base64
import json
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from gesture.gesture_process import GestureProcess
from util.camera_ip import CameraIP
from util.camera_loc import CameraLoc
from util import camera_loc
from util.camera import CameraProcessCallback,CameraProcess, Camera,CameraType, CameraConfig


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraManager:
    """相机管理器，统一管理多种类型的相机"""

    _loc_cameras:List[CameraLoc] = None
    _ip_cameras:List[CameraIP] = None

    _name2process:{str,CameraProcess} = {}

    
    def __init__(self,config_file: str = "./_data/cameras.json"):
        #self._camera_instances: Dict[str, Camera] = {}  # camera_id -> Camera实例
        self._lock = threading.RLock()
        self._config_file = Path(config_file)
        
    
    def get_process_by_name(self, name:str) -> Optional[CameraProcess]:
        """根据名称获取处理实例"""
        # with self._lock:
            # if name in self._name2process:
            #     return self._name2process[name]
            
        if(name == "gesture"):
            process = GestureProcess()
            #self._name2process[name] = process
            return process
        return None
        
    def list_camera_loc(self) -> List[CameraLoc]:
        """列出本地可用摄像头ID列表"""
        with self._lock:
            if self._loc_cameras is not None:
                return self._loc_cameras
        
            loc_ids = camera_loc.list_loc_inner_camera_ids()
            self._loc_cameras = []
            for cam_id in loc_ids:
                self._loc_cameras.append(camera_loc.CameraLoc(cam_id))
            return self._loc_cameras
    
    def list_camera_ip(self) -> List[CameraIP]:
        with self._lock:
            if(self._ip_cameras is not None):
                return self._ip_cameras
            
            self._ip_cameras = self._load_ip_cameras()
            return self._ip_cameras
    
    def _load_ip_cameras(self) -> List[CameraIP]:
        """加载IP摄像头配置"""
        try:
            if not self._config_file.exists():
                logger.warning(f"配置文件不存在: {self._config_file}")
                return []
            
            with open(self._config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            ret = []
            for cam_data in data.get("ip_cameras", []):
                try:
                    cid = cam_data.get("camera_id", "")
                    if(cid==""):
                        cid = cam_data.get("id", "")

                    if(cid is None or cid == "" or not cid.startswith("ip_")):
                        continue

                    title = cam_data.get("title", "")
                    if(title==""):
                        title = cam_data.get("t", "")

                    ret.append(CameraIP(camera_id=cid, title=title, config=cam_data))
                except Exception as e:
                    logger.error(f"加载摄像头配置失败: {e}")
                    continue

            logger.info(f"加载了 {len(ret)} 个摄像头配置")
            return ret
        
        except json.JSONDecodeError:
            logger.error(f"配置文件格式错误: {self._config_file}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")

    def _save_ip_cameras(self) -> None:
        """保存IP摄像头配置"""
        try:
            # 准备保存的数据
            ip_cams = []
            save_data = {
                "updated_at": datetime.now().isoformat(),
                "ip_cameras": ip_cams
            }
            
            for cmd_ip in self.list_camera_ip():
                # 更新修改时间
                dd = cmd_ip.to_config_dict()
                ip_cams.append(dd)
            
            # 创建目录（如果不存在）
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已保存到: {self._config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def list_camera_all(self) -> List[Camera]:
        """列出本地可用摄像头ID列表"""
        ret= []
        
        loc_cams = self.list_camera_loc()
        for c in loc_cams:
            ret.append(c)
        
        ip_cams = self.list_camera_ip()
        for c in ip_cams:
            ret.append(c)
            
        return ret

    def get_camera(self, camera_id: str) -> Optional[Camera]:
        if(camera_id.startswith("loc_")):
            ccs = self.list_camera_loc()
            for cc in ccs:
                if(cc.get_camera_id() == camera_id):
                    return cc
        elif(camera_id.startswith("ip_")):
            ccs = self.list_camera_ip()
            for cc in ccs:
                if(cc.get_camera_id() == camera_id):
                    return cc
        return None
    
    def _create_camera_instance(self, config: Dict) -> tuple[bool, Camera|str]:
        """根据配置创建相机实例"""
        camera_id = config['id']
        if(camera_id is None or camera_id == "" or not camera_id.startswith("ip_")):
            logger.error("camera_id is invalid")
            return False,"camera_id is invalid"
        title = config.get("title", "")
        if(title is None or title == ""):
            title = config.get("t", "")
        if(title is None or title == ""):
            return False,"no title"
        
        cam = CameraIP(camera_id=camera_id,title=title, config=config)
        return True,cam

    def set_camera(self, config: Dict) -> tuple[bool, str]:
        """创建相机实例"""
        with self._lock:
            try:
                camera_id = config['id']
                if(camera_id is None or camera_id == "" or not camera_id.startswith("ip_")):
                    logger.error("camera_id is invalid")
                    return False,""
                title = config.get("title", "")
                if(title is None or title == ""):
                    title = config.get("t", "")

                if(title is None or title == ""):
                    return False,"no title"
                
                cam = self.get_camera(camera_id)
                if(cam is None):
                    cam = CameraIP(camera_id=camera_id,title=title, config=config)
                    self.list_camera_ip().append(cam)
                else:
                    cam.set_camera_basic(title=title, config=config)
                self._save_ip_cameras()
            except Exception as e:
                logger.error(f"创建相机失败: {e}")
                return False,f"create camera err: {e}"
    
    def syn_camera_ips(self, camera_configs: List[Dict]) -> tuple[bool, str]:
        """同步IP相机配置列表"""
        with self._lock:
            try:
                """check existing cameras,and stop them all"""
                olds = self.list_camera_ip()
                for c in olds:
                    c.stop_camera()
                
                new_cams = []
                for config in camera_configs:
                    ret,cam = self._create_camera_instance(config)
                    if(ret==False):
                        continue
                    
                    new_cams.append(cam)
                
                # 更新摄像头列表
                self._ip_cameras = new_cams
                self._save_ip_cameras()
                return True,""
            except Exception as e:
                logger.error(f"同步相机配置失败: {e}")
                return False,f"sync camera err: {e}"
    
    def del_camera(self, camera_id: str) -> tuple[bool, str]:
        """删除相机实例"""
        with self._lock:
            try:
                if(not camera_id.startswith("ip_")):
                    logger.error("only ip camera can be deleted")
                    return False,"only ip camera can be deleted"
                
                cam_list = self.list_camera_ip()
                for i,cam in enumerate(cam_list):
                    if(cam.get_camera_id() == camera_id):
                        cam.stop_camera()
                        del cam_list[i]
                        self._save_ip_cameras()
                        return True,""
                
                logger.error(f"相机 {camera_id} 不存在")
                return False,"camera not exist"
            except Exception as e:
                logger.error(f"删除相机失败: {e}")
                return False,f"delete camera err: {e}"
    # def start_camera(self, camera_id: str, 
    #                 process: Optional[CameraProcess] = None) -> bool:
    #     """启动相机"""
    #     with self._lock:
    #         if camera_id not in self._camera_instances:
    #             logger.error(f"相机 {camera_id} 不存在")
    #             return False
            
    #         camera = self._camera_instances[camera_id]
    #         config = self._camera_configs[camera_id]
            
    #         # 如果没有提供处理函数，使用默认的
    #         if process is None:
    #             process = self._default_process
            
    #         # 准备配置参数
    #         camera_config = {
    #             'source': config.source,
    #             'width': config.width,
    #             'height': config.height,
    #             'fps': config.fps,
    #             **config.extra_params
    #         }
            
    #         return camera.start_camera(camera_id, process, camera_config)
    
    # def stop_camera(self, camera_id: str) -> bool:
    #     """停止相机"""
    #     with self._lock:
    #         if camera_id not in self._camera_instances:
    #             logger.error(f"相机 {camera_id} 不存在")
    #             return False
            
    #         camera = self._camera_instances[camera_id]
    #         return camera.stop_camera(camera_id)
    
    # def get_camera(self, camera_id: str) -> Optional[Camera]:
    #     """获取相机实例"""
    #     with self._lock:
    #         return self._camera_instances.get(camera_id)
    
    # def get_camera_info(self, camera_id: str) -> Dict[str, Any]:
    #     """获取相机信息"""
    #     with self._lock:
    #         if camera_id not in self._camera_instances:
    #             return {}
            
    #         camera = self._camera_instances[camera_id]
    #         config = self._camera_configs.get(camera_id, CameraConfig(
    #             camera_id=camera_id, camera_type=CameraType.WEBCAM))
            
    #         info = camera.get_info(camera_id)
    #         info.update({
    #             'config': config.__dict__,
    #             'registered_ids': camera.get_all_camera_ids()
    #         })
            
    #         return info
    
    # def get_all_cameras(self) -> List[str]:
    #     """获取所有相机ID"""
    #     with self._lock:
    #         return list(self._camera_instances.keys())
    
    # def remove_camera(self, camera_id: str) -> bool:
    #     """移除相机"""
    #     with self._lock:
    #         if camera_id not in self._camera_instances:
    #             return True
            
    #         # 先停止相机
    #         camera = self._camera_instances[camera_id]
    #         camera.stop_camera(camera_id)
            
    #         # 移除实例
    #         del self._camera_instances[camera_id]
    #         if camera_id in self._camera_configs:
    #             del self._camera_configs[camera_id]
            
    #         logger.info(f"相机 {camera_id} 已移除")
    #         return True
    
    # def cleanup(self) -> None:
    #     """清理所有相机"""
    #     with self._lock:
    #         camera_ids = list(self._camera_instances.keys())
    #         for camera_id in camera_ids:
    #             self.remove_camera(camera_id)
    
    # def _default_process(self, frame: Any) -> None:
    #     """默认处理函数"""
    #     logger.debug(f"收到帧，形状: {frame.shape if hasattr(frame, 'shape') else '未知'}")

