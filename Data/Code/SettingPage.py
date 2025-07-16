import os
from pathlib import Path
from configparser import ConfigParser
from PySide6.QtCore import QObject, Signal, Property, QStandardPaths, QUrl, Slot
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "io.downloader.settings"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class Settings(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 配置文件路径
        self.config_file = Path(__file__).parent.parent.parent.parent / "Downloader.ini"
        self.config = ConfigParser()
        self.config.read_dict({"Settings": {}})
        
        # 读取现有配置
        if self.config_file.exists():
            self.config.read(self.config_file)
        
        # 获取默认下载文件夹
        default_folder = self._get_default_download_folder()
        saved_folder = self.config.get("Settings", "download_folder", fallback=default_folder)
        self._download_folder = self._sanitize_path(saved_folder)

    # 下载文件夹变更信号
    downloadFolderChanged = Signal()

    @Property(str, notify=downloadFolderChanged)
    def downloadFolder(self):
        return self._download_folder

    @downloadFolder.setter
    def downloadFolder(self, value):
        sanitized = self._sanitize_path(value)
        if sanitized != self._download_folder:
            self._download_folder = sanitized
            self.config["Settings"]["download_folder"] = self._download_folder
            self._save_settings()
            self.downloadFolderChanged.emit()

    @Slot(result=QUrl)
    def get_download_folder_url(self):
        """获取下载文件夹的QUrl形式"""
        return QUrl.fromLocalFile(self._download_folder)

    def _sanitize_path(self, path):
        """清理路径，处理file:///前缀"""
        if path.startswith("file:///"):
            return QUrl(path).toLocalFile()
        return str(Path(path).resolve()) 

    def _get_default_download_folder(self):
        """获取系统默认下载文件夹"""
        return QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)

    def _save_settings(self):
        """保存设置到配置文件"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)