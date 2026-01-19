import json
import os
import uuid
import hashlib
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraStatus(Enum):
    """摄像头状态枚举"""
    ACTIVE = "active"      # 活跃可用
    INACTIVE = "inactive"  # 未激活
    ERROR = "error"       # 错误状态
    OFFLINE = "offline"   # 离线

class CameraType(Enum):
    """摄像头类型枚举"""
    WEBCAM = "webcam"      # USB摄像头
    RTSP = "rtsp"          # RTSP网络摄像头
    HTTP = "http"          # HTTP流
    ONVIF = "onvif"        # ONVIF协议
    GIGE = "gige"          # GigE工业相机
    FILE = "file"          # 视频文件
    DUMMY = "dummy"        # 虚拟相机

@dataclass
class CameraConfig:
    """摄像头配置数据类"""
    # 基本信息
    camera_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "未命名摄像头"
    camera_type: CameraType = CameraType.WEBCAM
    
    # 连接信息
    source: str = "0"  # 对于webcam是设备索引，对于RTSP是URL
    protocol: str = "http"  # 协议类型: http, https, rtsp, rtsp-tcp, etc.
    host: str = ""     # 主机地址
    port: int = 0      # 端口
    path: str = ""     # 路径
    username: str = "" # 用户名
    password: str = "" # 密码
    
    # 视频参数
    width: int = 640
    height: int = 480
    fps: int = 30
    codec: str = "h264"  # 编码格式
    bitrate: int = 2000  # 比特率 kbps
    
    # 控制参数
    auto_start: bool = False
    auto_reconnect: bool = True
    reconnect_interval: int = 5  # 重连间隔(秒)
    
    # 区域设置
    timezone: str = "Asia/Shanghai"
    location: str = ""  # 位置描述
    coordinates: Dict[str, float] = field(default_factory=dict)  # GPS坐标
    
    # 高级设置
    roi: Optional[Dict[str, int]] = None  # 感兴趣区域 {x, y, width, height}
    flip: str = "none"  # 翻转: none, horizontal, vertical, both
    rotate: int = 0     # 旋转角度: 0, 90, 180, 270
    
    # 识别参数
    enable_ai: bool = False
    ai_model: str = ""  # AI模型路径
    ai_confidence: float = 0.5  # AI置信度阈值
    
    # 状态信息
    status: CameraStatus = CameraStatus.INACTIVE
    last_seen: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    description: str = ""
    custom_data: Dict[str, Any] = field(default_factory=dict)

class CameraConfigManager:
    """摄像头配置管理器"""
    
    def __init__(self, config_file: str = "cameras.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.cameras: Dict[str, CameraConfig] = {}
        self._load_config()
    
    def _generate_unique_id(self, name: str, source: str) -> str:
        """生成唯一的摄像头ID"""
        # 使用名称和源的哈希值生成ID
        hash_input = f"{name}_{source}_{datetime.now().timestamp()}"
        hash_obj = hashlib.md5(hash_input.encode())
        return f"cam_{hash_obj.hexdigest()[:8]}"
    
    def _validate_config(self, config_dict: Dict) -> bool:
        """验证配置数据"""
        required_fields = ["name", "camera_type", "source"]
        
        for field in required_fields:
            if field not in config_dict or not config_dict[field]:
                logger.error(f"缺少必需字段: {field}")
                return False
        
        # 验证摄像头类型
        try:
            camera_type = CameraType(config_dict.get("camera_type"))
        except ValueError:
            logger.error(f"无效的摄像头类型: {config_dict.get('camera_type')}")
            return False
        
        return True
    
    def _load_config(self) -> None:
        """从文件加载配置"""
        try:
            if not self.config_file.exists():
                logger.warning(f"配置文件不存在: {self.config_file}")
                # 创建默认配置示例
                self._create_default_configs()
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.cameras.clear()
            
            for cam_data in data.get("cameras", []):
                try:
                    # 转换枚举类型
                    if "camera_type" in cam_data:
                        cam_data["camera_type"] = CameraType(cam_data["camera_type"])
                    if "status" in cam_data:
                        cam_data["status"] = CameraStatus(cam_data["status"])
                    
                    # 创建配置对象
                    config = CameraConfig(**cam_data)
                    self.cameras[config.camera_id] = config
                    
                except Exception as e:
                    logger.error(f"加载摄像头配置失败: {e}")
                    continue
            
            logger.info(f"加载了 {len(self.cameras)} 个摄像头配置")
            
        except json.JSONDecodeError:
            logger.error(f"配置文件格式错误: {self.config_file}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
    
    def _save_config(self) -> bool:
        """保存配置到文件"""
        try:
            # 准备保存的数据
            save_data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "cameras": []
            }
            
            for config in self.cameras.values():
                # 更新修改时间
                config.updated_at = datetime.now().isoformat()
                
                # 转换为字典
                config_dict = asdict(config)
                
                # 处理枚举类型
                config_dict["camera_type"] = config.camera_type.value
                config_dict["status"] = config.status.value
                
                save_data["cameras"].append(config_dict)
            
            # 创建目录（如果不存在）
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已保存到: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def _create_default_configs(self) -> None:
        """创建默认配置示例"""
        default_configs = [
            CameraConfig(
                camera_id=self._generate_unique_id("主摄像头", "0"),
                name="主摄像头",
                camera_type=CameraType.WEBCAM,
                source="0",
                width=1920,
                height=1080,
                fps=30,
                location="会议室",
                description="会议室主摄像头"
            ),
            CameraConfig(
                camera_id=self._generate_unique_id("备用摄像头", "1"),
                name="备用摄像头",
                camera_type=CameraType.WEBCAM,
                source="1",
                width=1280,
                height=720,
                fps=25,
                location="走廊",
                description="走廊监控"
            ),
            CameraConfig(
                camera_id=self._generate_unique_id("网络摄像头", "rtsp://admin:123456@192.168.1.100:554/stream1"),
                name="网络摄像头",
                camera_type=CameraType.RTSP,
                source="rtsp://admin:123456@192.168.1.100:554/stream1",
                protocol="rtsp",
                host="192.168.1.100",
                port=554,
                username="admin",
                password="123456",
                location="大门"
            )
        ]
        
        for config in default_configs:
            self.cameras[config.camera_id] = config
        
        self._save_config()
    
    def add_camera(self, config_data: Dict[str, Any]) -> Optional[str]:
        """
        添加新摄像头
        
        Args:
            config_data: 摄像头配置数据
            
        Returns:
            成功返回camera_id，失败返回None
        """
        try:
            # 验证配置
            if not self._validate_config(config_data):
                return None
            
            # 生成唯一ID（如果未提供）
            if "camera_id" not in config_data or not config_data["camera_id"]:
                name = config_data.get("name", "未命名摄像头")
                source = config_data.get("source", "")
                config_data["camera_id"] = self._generate_unique_id(name, source)
            
            # 转换枚举类型
            if "camera_type" in config_data:
                config_data["camera_type"] = CameraType(config_data["camera_type"])
            
            # 创建配置对象
            config = CameraConfig(**config_data)
            
            # 检查是否已存在相同ID
            if config.camera_id in self.cameras:
                logger.warning(f"摄像头ID已存在: {config.camera_id}")
                return None
            
            # 添加到列表
            self.cameras[config.camera_id] = config
            
            # 保存配置
            if self._save_config():
                logger.info(f"摄像头添加成功: {config.name} (ID: {config.camera_id})")
                return config.camera_id
            
            return None
            
        except Exception as e:
            logger.error(f"添加摄像头失败: {e}")
            return None
    
    def update_camera(self, camera_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新摄像头配置
        
        Args:
            camera_id: 摄像头ID
            update_data: 要更新的数据
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            if camera_id not in self.cameras:
                logger.error(f"摄像头不存在: {camera_id}")
                return False
            
            # 获取现有配置
            config = self.cameras[camera_id]
            
            # 处理枚举类型
            if "camera_type" in update_data:
                update_data["camera_type"] = CameraType(update_data["camera_type"])
            if "status" in update_data:
                update_data["status"] = CameraStatus(update_data["status"])
            
            # 更新配置
            for key, value in update_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            # 更新修改时间
            config.updated_at = datetime.now().isoformat()
            
            # 保存配置
            if self._save_config():
                logger.info(f"摄像头配置已更新: {config.name} (ID: {camera_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新摄像头配置失败: {e}")
            return False
    
    def delete_camera(self, camera_id: str) -> bool:
        """
        删除摄像头
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            if camera_id not in self.cameras:
                logger.error(f"摄像头不存在: {camera_id}")
                return False
            
            camera_name = self.cameras[camera_id].name
            del self.cameras[camera_id]
            
            if self._save_config():
                logger.info(f"摄像头已删除: {camera_name} (ID: {camera_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除摄像头失败: {e}")
            return False
    
    def get_camera(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        获取摄像头配置
        
        Args:
            camera_id: 摄像头ID
            
        Returns:
            摄像头配置字典，不存在返回None
        """
        try:
            if camera_id not in self.cameras:
                return None
            
            config = self.cameras[camera_id]
            config_dict = asdict(config)
            
            # 处理枚举类型
            config_dict["camera_type"] = config.camera_type.value
            config_dict["status"] = config.status.value
            
            return config_dict
            
        except Exception as e:
            logger.error(f"获取摄像头配置失败: {e}")
            return None
    
    def get_camera_by_source(self, source: str) -> Optional[Dict[str, Any]]:
        """
        根据源地址查找摄像头
        
        Args:
            source: 摄像头源地址
            
        Returns:
            摄像头配置字典，不存在返回None
        """
        try:
            for config in self.cameras.values():
                if config.source == source:
                    config_dict = asdict(config)
                    config_dict["camera_type"] = config.camera_type.value
                    config_dict["status"] = config.status.value
                    return config_dict
            
            return None
            
        except Exception as e:
            logger.error(f"根据源地址查找摄像头失败: {e}")
            return None
    
    def get_all_cameras(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        获取所有摄像头配置
        
        Args:
            filters: 过滤条件
            
        Returns:
            摄像头配置列表
        """
        try:
            result = []
            
            for config in self.cameras.values():
                config_dict = asdict(config)
                config_dict["camera_type"] = config.camera_type.value
                config_dict["status"] = config.status.value
                
                # 应用过滤条件
                if filters:
                    match = True
                    for key, value in filters.items():
                        if key not in config_dict or config_dict[key] != value:
                            match = False
                            break
                    
                    if not match:
                        continue
                
                result.append(config_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"获取所有摄像头配置失败: {e}")
            return []
    
    def get_frontend_camera_list(self) -> List[Dict[str, Any]]:
        """
        获取前端可用的摄像头列表（简化版）
        
        Returns:
            前端摄像头列表
        """
        try:
            camera_list = []
            
            for config in self.cameras.values():
                camera_info = {
                    "id": config.camera_id,
                    "name": config.name,
                    "type": config.camera_type.value,
                    "source": config.source,
                    "status": config.status.value,
                    "width": config.width,
                    "height": config.height,
                    "fps": config.fps,
                    "location": config.location,
                    "description": config.description,
                    "last_seen": config.last_seen,
                    "tags": config.tags
                }
                camera_list.append(camera_info)
            
            return camera_list
            
        except Exception as e:
            logger.error(f"获取前端摄像头列表失败: {e}")
            return []
    
    def update_camera_status(self, camera_id: str, status: CameraStatus, 
                           last_seen: Optional[str] = None) -> bool:
        """
        更新摄像头状态
        
        Args:
            camera_id: 摄像头ID
            status: 新状态
            last_seen: 最后活动时间
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            if camera_id not in self.cameras:
                return False
            
            config = self.cameras[camera_id]
            config.status = status
            
            if last_seen:
                config.last_seen = last_seen
            else:
                config.last_seen = datetime.now().isoformat()
            
            config.updated_at = datetime.now().isoformat()
            
            # 自动保存
            self._save_config()
            
            logger.debug(f"摄像头状态更新: {config.name} -> {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"更新摄像头状态失败: {e}")
            return False
    
    def search_cameras(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索摄像头
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的摄像头列表
        """
        try:
            results = []
            keyword_lower = keyword.lower()
            
            for config in self.cameras.values():
                # 在多个字段中搜索
                search_fields = [
                    config.name,
                    config.location,
                    config.description,
                    config.source,
                    " ".join(config.tags)
                ]
                
                # 检查是否匹配
                match = any(
                    keyword_lower in str(field).lower() 
                    for field in search_fields if field
                )
                
                if match:
                    config_dict = asdict(config)
                    config_dict["camera_type"] = config.camera_type.value
                    config_dict["status"] = config.status.value
                    results.append(config_dict)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索摄像头失败: {e}")
            return []
    
    def export_config(self, file_path: str) -> bool:
        """
        导出配置到文件
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "cameras": []
            }
            
            for config in self.cameras.values():
                config_dict = asdict(config)
                config_dict["camera_type"] = config.camera_type.value
                config_dict["status"] = config.status.value
                export_data["cameras"].append(config_dict)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已导出到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path: str, merge: bool = True) -> bool:
        """
        从文件导入配置
        
        Args:
            file_path: 导入文件路径
            merge: 是否合并现有配置
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            imported_count = 0
            
            for cam_data in import_data.get("cameras", []):
                try:
                    # 转换枚举类型
                    if "camera_type" in cam_data:
                        cam_data["camera_type"] = CameraType(cam_data["camera_type"])
                    
                    # 如果合并模式且ID已存在，跳过
                    camera_id = cam_data.get("camera_id")
                    if merge and camera_id and camera_id in self.cameras:
                        logger.warning(f"摄像头ID已存在，跳过: {camera_id}")
                        continue
                    
                    # 添加摄像头
                    if self.add_camera(cam_data):
                        imported_count += 1
                        
                except Exception as e:
                    logger.error(f"导入摄像头配置失败: {e}")
                    continue
            
            logger.info(f"成功导入 {imported_count} 个摄像头配置")
            return imported_count > 0
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取配置统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {
                "total": len(self.cameras),
                "by_type": {},
                "by_status": {},
                "recently_updated": []
            }
            
            # 按类型统计
            for config in self.cameras.values():
                cam_type = config.camera_type.value
                status = config.status.value
                
                stats["by_type"][cam_type] = stats["by_type"].get(cam_type, 0) + 1
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # 最近更新的摄像头
            recent_cameras = sorted(
                self.cameras.values(),
                key=lambda x: x.updated_at,
                reverse=True
            )[:5]
            
            for config in recent_cameras:
                stats["recently_updated"].append({
                    "id": config.camera_id,
                    "name": config.name,
                    "updated_at": config.updated_at
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

class CameraPresetManager:
    """摄像头预设管理器"""
    
    def __init__(self, config_manager: CameraConfigManager):
        self.config_manager = config_manager
        self.presets_file = Path("camera_presets.json")
        self.presets: Dict[str, List[Dict[str, Any]]] = self._load_presets()
    
    def _load_presets(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载预设"""
        try:
            if not self.presets_file.exists():
                return {}
            
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                return json.load(f)
            
        except Exception as e:
            logger.error(f"加载预设失败: {e}")
            return {}
    
    def _save_presets(self) -> bool:
        """保存预设"""
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存预设失败: {e}")
            return False
    
    def add_preset(self, preset_name: str, camera_ids: List[str]) -> bool:
        """添加预设"""
        try:
            # 验证摄像头ID
            valid_camera_ids = []
            for camera_id in camera_ids:
                if camera_id in self.config_manager.cameras:
                    valid_camera_ids.append(camera_id)
            
            if not valid_camera_ids:
                logger.error("没有有效的摄像头ID")
                return False
            
            self.presets[preset_name] = valid_camera_ids
            return self._save_presets()
            
        except Exception as e:
            logger.error(f"添加预设失败: {e}")
            return False
    
    def get_preset_cameras(self, preset_name: str) -> List[Dict[str, Any]]:
        """获取预设的摄像头列表"""
        try:
            if preset_name not in self.presets:
                return []
            
            cameras = []
            for camera_id in self.presets[preset_name]:
                camera = self.config_manager.get_camera(camera_id)
                if camera:
                    cameras.append(camera)
            
            return cameras
            
        except Exception as e:
            logger.error(f"获取预设摄像头失败: {e}")
            return []

# 使用示例
def example_usage():
    """使用示例"""
    
    # 1. 创建配置管理器
    config_manager = CameraConfigManager("config/cameras.json")
    
    # 2. 添加新摄像头
    new_camera = {
        "name": "实验室摄像头",
        "camera_type": "webcam",
        "source": "2",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "location": "实验室",
        "description": "实验室监控摄像头",
        "tags": ["室内", "高清", "实验室"],
        "auto_start": True
    }
    
    camera_id = config_manager.add_camera(new_camera)
    if camera_id:
        print(f"摄像头添加成功，ID: {camera_id}")
    
    # 3. 获取所有摄像头（前端可用格式）
    camera_list = config_manager.get_frontend_camera_list()
    print(f"摄像头数量: {len(camera_list)}")
    
    # 4. 更新摄像头状态
    if camera_id:
        config_manager.update_camera_status(camera_id, CameraStatus.ACTIVE)
    
    # 5. 搜索摄像头
    search_results = config_manager.search_cameras("实验室")
    print(f"搜索到 {len(search_results)} 个相关摄像头")
    
    # 6. 获取统计信息
    stats = config_manager.get_statistics()
    print(f"统计信息: {stats}")
    
    # 7. 创建预设管理器
    preset_manager = CameraPresetManager(config_manager)
    preset_manager.add_preset("实验室监控", [camera_id] if camera_id else [])
    
    # 8. 导出配置
    config_manager.export_config("cameras_backup.json")

# 工具函数
def create_camera_from_webcam(index: int, name: str = None) -> Dict[str, Any]:
    """从Webcam索引创建配置"""
    return {
        "name": name or f"摄像头_{index}",
        "camera_type": "webcam",
        "source": str(index),
        "width": 1280,
        "height": 720,
        "fps": 30
    }

def create_camera_from_rtsp(url: str, name: str = None) -> Dict[str, Any]:
    """从RTSP URL创建配置"""
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    
    return {
        "name": name or f"RTSP摄像头",
        "camera_type": "rtsp",
        "source": url,
        "protocol": "rtsp",
        "host": parsed.hostname,
        "port": parsed.port or 554,
        "path": parsed.path,
        "username": parsed.username or "",
        "password": parsed.password or "",
        "width": 1920,
        "height": 1080,
        "fps": 25
    }

# Web API 适配器
class CameraConfigAPI:
    """为Web API提供适配器"""
    
    def __init__(self, config_manager: CameraConfigManager):
        self.manager = config_manager
    
    def list_cameras(self, page: int = 1, page_size: int = 10, 
                    filters: Optional[Dict] = None) -> Dict[str, Any]:
        """分页列出摄像头"""
        all_cameras = self.manager.get_frontend_camera_list()
        
        # 应用过滤
        if filters:
            filtered = []
            for camera in all_cameras:
                match = True
                for key, value in filters.items():
                    if camera.get(key) != value:
                        match = False
                        break
                if match:
                    filtered.append(camera)
            all_cameras = filtered
        
        # 分页
        total = len(all_cameras)
        start = (page - 1) * page_size
        end = start + page_size
        cameras_page = all_cameras[start:end]
        
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
            "cameras": cameras_page
        }
    
    def create_camera(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建摄像头API"""
        camera_id = self.manager.add_camera(data)
        
        if camera_id:
            return {
                "success": True,
                "message": "摄像头创建成功",
                "camera_id": camera_id,
                "camera": self.manager.get_camera(camera_id)
            }
        else:
            return {
                "success": False,
                "message": "摄像头创建失败"
            }
    
    def get_camera_detail(self, camera_id: str) -> Dict[str, Any]:
        """获取摄像头详情API"""
        camera = self.manager.get_camera(camera_id)
        
        if camera:
            return {
                "success": True,
                "camera": camera
            }
        else:
            return {
                "success": False,
                "message": "摄像头不存在"
            }
    
    def update_camera(self, camera_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新摄像头API"""
        success = self.manager.update_camera(camera_id, data)
        
        if success:
            return {
                "success": True,
                "message": "摄像头更新成功"
            }
        else:
            return {
                "success": False,
                "message": "摄像头更新失败"
            }
    
    def delete_camera(self, camera_id: str) -> Dict[str, Any]:
        """删除摄像头API"""
        success = self.manager.delete_camera(camera_id)
        
        if success:
            return {
                "success": True,
                "message": "摄像头删除成功"
            }
        else:
            return {
                "success": False,
                "message": "摄像头删除失败"
            }

if __name__ == "__main__":
    # 运行示例
    example_usage()