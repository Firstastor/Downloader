import os
import json
import time
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Property, Slot, QUrl, QFileSystemWatcher
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "io.downloader.downloaded"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class DownloadedPage(QObject):
    downloadsChanged = Signal()
    downloadRemoved = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._downloads = []
        self._download_folder = ""
        self._history_file = Path(__file__).parent.parent.parent.parent / "Download_History.json"
        self._file_watcher = QFileSystemWatcher()
        self._file_watcher.directoryChanged.connect(self._auto_verify)
        self._load_downloads()

    # 属性声明
    @Property(list, notify=downloadsChanged)
    def downloads(self):
        """供QML绑定的下载记录属性"""
        return self._downloads

    @Property(str)
    def downloadFolder(self):
        return self._download_folder

    @downloadFolder.setter
    def downloadFolder(self, value):
        """设置下载文件夹路径并开始监视"""
        if self._download_folder:
            self._file_watcher.removePath(self._download_folder)
        self._download_folder = value
        if value:
            self._file_watcher.addPath(value)
        self._verify_downloads()

    # 方法声明
    @Slot(result=list)
    def getDownloadsList(self):
        """获取下载列表(兼容旧版)"""
        return self._downloads

    @Slot(str, result=bool)
    def fileExists(self, filename):
        """检查文件是否存在"""
        return os.path.exists(os.path.join(self._download_folder, filename))

    @Slot(str, str)
    def addDownload(self, url, filename):
        """添加下载记录"""
        existing = next((d for d in self._downloads if d["url"] == url), None)
        if existing:
            return
            
        filepath = os.path.join(self._download_folder, filename)
        self._downloads.append({
            "url": url,
            "filename": filename,
            "timestamp": int(time.time()),
            "filesize": os.path.getsize(filepath) if os.path.exists(filepath) else 0
        })
        self._save_downloads()
        self.downloadsChanged.emit()

    @Slot(str)
    def removeDownload(self, url):
        """移除下载记录和对应的文件"""
        # 查找要删除的记录
        to_remove = [d for d in self._downloads if d["url"] == url]
        
        if not to_remove:
            return  # 没有找到对应记录
        
        # 获取文件路径
        filename = to_remove[0]["filename"]
        filepath = os.path.join(self._download_folder, filename)
        
        try:
            # 删除物理文件
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"已删除文件: {filepath}")
            else:
                print(f"文件不存在: {filepath}")
            
            # 移除记录
            self._downloads = [d for d in self._downloads if d["url"] != url]
            self._save_downloads()
            self.downloadsChanged.emit()
            
        except Exception as e:
            print(f"删除文件失败: {e}")

    @Slot(str, result=QUrl)
    def getFileUrl(self, filename):
        """获取文件URL"""
        return QUrl.fromLocalFile(os.path.join(self._download_folder, filename))

    @Slot(str, result=QUrl)
    def getFolderUrl(self, filename):
        """获取文件夹URL"""
        return QUrl.fromLocalFile(self._download_folder)

    # 内部方法
    def _load_downloads(self):
        """从文件加载下载历史"""
        if self._history_file.exists():
            try:
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    self._downloads = json.load(f)
            except Exception as e:
                print(f"加载历史记录错误: {e}")
                self._downloads = []
        self._verify_downloads()

    def _save_downloads(self):
        """保存下载历史到文件"""
        with open(self._history_file, 'w', encoding='utf-8') as f:
            json.dump(self._downloads, f, ensure_ascii=False, indent=2)

    def _auto_verify(self):
        """自动验证文件变化"""
        self._verify_downloads()

    def _verify_downloads(self):
        """验证下载文件是否存在并更新状态"""
        updated = []
        removed = []
        
        for item in self._downloads:
            path = os.path.join(self._download_folder, item["filename"])
            if os.path.exists(path):
                item.update({
                    "filesize": os.path.getsize(path),
                    "mtime": os.path.getmtime(path)
                })
                updated.append(item)
            else:
                removed.append(item["url"])
        
        if len(updated) != len(self._downloads):
            self._downloads = updated
            self._save_downloads()
            self.downloadsChanged.emit()
            for url in removed:
                self.downloadRemoved.emit(url)