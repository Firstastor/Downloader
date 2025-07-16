from PySide6.QtCore import QObject, Signal, Property, QUrl, Slot
import os
import re
import sys
import configparser
from pathlib import Path

class Settings(QObject):
    def __init__(self):
        super().__init__()
        # 获取应用程序根目录路径
        if getattr(sys, 'frozen', False):
            # 打包后的应用（如 PyInstaller）
            app_dir = Path(sys.executable).parent
        else:
            # 开发环境（直接运行 Python 脚本）
            app_dir = Path(__file__).parent.parent.parent

        # 配置文件路径改为应用程序根目录下的 Downloader.ini
        self.config_file = str(app_dir / "Downloader.ini")
        self._load_config()  # 加载配置

    def _load_config(self):
        """从配置文件加载设置"""
        config = configparser.ConfigParser()
        
        # 如果配置文件不存在，则创建默认配置
        if not os.path.exists(self.config_file):
            self._set_default_values()
            self._save_config()
            return

        try:
            config.read(self.config_file)
            # 读取配置值（带默认值回退）
            self._download_folder = config.get(
                "DEFAULT", "download_folder", 
                fallback=str(Path.home() / "Downloads")
            )
            self._speed_limit = config.getint("DEFAULT", "speed_limit", fallback=0)
            self._concurrent_downloads = config.getint("DEFAULT", "concurrent_downloads", fallback=3)
            self._max_threads_per_download = config.getint("DEFAULT", "max_threads_per_download", fallback=4)
        except Exception as e:
            print(f"Error loading config: {e}")
            self._set_default_values()

    def _set_default_values(self):
        """设置默认值"""
        self._download_folder = str(Path.home() / "Downloads")
        self._speed_limit = 0
        self._concurrent_downloads = 5
        self._max_threads_per_download = 32

    def _save_config(self):
        """保存当前设置到配置文件"""
        try:
            config = configparser.ConfigParser()
            config["DEFAULT"] = {
                "download_folder": self._download_folder,
                "speed_limit": str(self._speed_limit),
                "concurrent_downloads": str(self._concurrent_downloads),
                "max_threads_per_download": str(self._max_threads_per_download)
            }
            
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, "w") as f:
                config.write(f)
        except Exception as e:
            print(f"Error saving config: {e}")

    # -------------------- 信号定义 --------------------
    downloadFolderChanged = Signal(str)
    speedLimitChanged = Signal(int)
    concurrentDownloadsChanged = Signal(int)
    maxThreadsPerDownloadChanged = Signal(int)

    # -------------------- 属性定义 --------------------
    # Download Folder
    @Property(str, notify=downloadFolderChanged)
    def downloadFolder(self):
        return self._download_folder

    @downloadFolder.setter
    def downloadFolder(self, value):
        if value.startswith("file:///"):
            value = value[8:]
        normalized_path = os.path.normpath(value)
        if self._download_folder != normalized_path:
            self._download_folder = normalized_path
            self.downloadFolderChanged.emit(normalized_path)
            self._save_config()

    # Speed Limit (KB/s)
    @Property(int, notify=speedLimitChanged)
    def speedLimit(self):
        return self._speed_limit

    @speedLimit.setter
    def speedLimit(self, value):
        if self._speed_limit != value:
            self._speed_limit = value
            self.speedLimitChanged.emit(value)
            self._save_config()

    # Concurrent Downloads
    @Property(int, notify=concurrentDownloadsChanged)
    def concurrentDownloads(self):
        return self._concurrent_downloads

    @concurrentDownloads.setter
    def concurrentDownloads(self, value):
        if self._concurrent_downloads != value:
            self._concurrent_downloads = value
            self.concurrentDownloadsChanged.emit(value)
            self._save_config()

    # Max Threads per Download
    @Property(int, notify=maxThreadsPerDownloadChanged)
    def maxThreadsPerDownload(self):
        return self._max_threads_per_download

    @maxThreadsPerDownload.setter
    def maxThreadsPerDownload(self, value):
        if self._max_threads_per_download != value:
            self._max_threads_per_download = value
            self.maxThreadsPerDownloadChanged.emit(value)
            self._save_config()

    # -------------------- 方法定义 --------------------
    @Slot(result=QUrl)
    def get_download_folder_url(self):
        """返回当前下载目录的 QUrl 格式（用于 FolderDialog）"""
        return QUrl.fromLocalFile(self._download_folder)

    @Slot(str, result=bool)
    def isValidPath(self, path):
        """验证路径是否有效且存在"""
        try:
            if not path:
                return False
                
            if path.startswith("file:///"):
                path = path[8:]
            
            normalized_path = os.path.normpath(path)
            
            # Windows 路径验证
            if os.name == 'nt':
                if not re.match(r'^(?:[a-zA-Z]:\\|\\\\[^\\/:*?"<>|]+\\[^\\/:*?"<>|]+)', normalized_path):
                    return False
                illegal_chars = r'<>"|?*'
                if any(char in normalized_path for char in illegal_chars):
                    return False
                    
            # 检查路径是否存在且可写
            if not os.path.exists(normalized_path):
                return False
                
            return os.path.isdir(normalized_path) and os.access(normalized_path, os.W_OK)
        except Exception as e:
            print(f"Path validation error: {e}")
            return False
        
    def cleanup(self):
        # 清理资源
        pass