import json
from PySide6.QtCore import (QObject, Signal, Property, Slot, QUrl, QFileSystemWatcher, 
                           QFile, QDir, QDateTime, QFileInfo )

class DownloadedPage(QObject):
    """管理下载文件的页面类，处理下载记录的添加、删除和验证"""
    
    downloadsChanged = Signal()
    downloadRemoved = Signal(str)
    removeError = Signal(str, str)  # 添加错误信号
    folderChanged = Signal(str)
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._downloads = []
        self._settings = settings
        self._download_folder = ""  # 确保 _download_folder 被初始化
        self._history_file = QDir(QDir.current()).filePath("Download_History.json")
        self._file_watcher = QFileSystemWatcher()
        self._file_watcher.directoryChanged.connect(self._auto_verify)
        # 从 Settings 实例获取下载目录
        self.downloadFolder = self._settings.downloadFolder
        # 连接信号，以便在设置更改时更新下载目录
        self._settings.downloadFolderChanged.connect(self._update_download_folder)
        self._load_downloads()

    def _update_download_folder(self, new_folder):
        self.downloadFolder = new_folder
        
    # 属性声明
    @Property(list, notify=downloadsChanged)
    def downloads(self):
        """供QML绑定的下载记录属性"""
        return self._downloads
    
    @Property(str, notify=folderChanged)
    def downloadFolder(self):
        return self._download_folder
    
    @downloadFolder.setter
    def downloadFolder(self, value):
        """设置下载文件夹路径并开始监视"""
        if self._download_folder:
            self._file_watcher.removePath(self._download_folder)
        
        # 验证路径有效性
        dir = QDir(value)
        if value and dir.exists() and dir.isReadable():
            self._download_folder = value
            self._file_watcher.addPath(value)
            self.folderChanged.emit(value)
        else:
            self._download_folder = ""
            self.folderChanged.emit("")
            print(f"无效的下载路径: {value}")
            
        self._verify_downloads()
    
    # 方法声明
    @Slot(result=list)
    def getDownloadsList(self):
        return self.downloads  # 简化调用，直接返回属性
    
    @Slot(str, result=bool)
    def fileExists(self, filename):
        return QFile.exists(self._get_file_path(filename))  # 简化调用
    
    @Slot(str, str)
    def addDownload(self, url, filename):
        if not self._download_folder:
            print("下载文件夹未设置，无法添加下载记录")
            return
        
        if next((d for d in self._downloads if d["url"] == url), None):
            return

        file = QFile(self._get_file_path(filename))
        file_size = file.size() if file.exists() else 0
        timestamp = QDateTime.currentSecsSinceEpoch()

        self._downloads.append({
            "url": url,
            "filename": filename,
            "timestamp": timestamp,
            "filesize": file_size
        })
        self._save_downloads()
        self.downloadsChanged.emit()
    
    @Slot(str)
    def removeDownload(self, url):
        to_remove = [d for d in self._downloads if d["url"] == url]
        if not to_remove:
            return

        filename = to_remove[0]["filename"]
        file_path = self._get_file_path(filename)
        file = QFile(file_path)

        try:
            if file.exists() and file.permissions() & QFile.WriteUser:
                if not file.remove():
                    self.removeError.emit(url, f"删除失败: {file.errorString()}")
            elif file.exists():
                self.removeError.emit(url, "没有删除权限")

            self._downloads = [d for d in self._downloads if d["url"] != url]
            self._save_downloads()
            self.downloadsChanged.emit()
        except Exception as e:
            self.removeError.emit(url, str(e))
            print(f"删除文件失败: {e}")
    
    @Slot(str, result=QUrl)
    def getFileUrl(self, filename):
        file_path = self._get_file_path(filename)
        return QUrl.fromLocalFile(file_path) if QFile.exists(file_path) else QUrl()

    @Slot(str, result=QUrl)
    def getFolderUrl(self, filename):
        # 1. 检查下载文件夹是否有效
        if not self._download_folder or not QDir(self._download_folder).exists():
            print("错误：下载文件夹未设置或路径无效")
            return QUrl()
        
        # 2. 获取文件的完整路径
        file_path = self._get_file_path(filename)
        
        # 3. 检查文件是否存在
        if not QFile.exists(file_path):
            print(f"错误：文件不存在 - {file_path}")
            return QUrl()
        
        # 4. 使用QFileInfo获取规范的文件夹路径
        folder_path = QFileInfo(file_path).absolutePath()
        
        # 5. 返回文件夹URL（确保路径使用正斜杠）
        return QUrl.fromLocalFile(folder_path.replace("\\", "/"))
    
    # 内部方法
    def _load_downloads(self):
        file = QFile(self._history_file)
        if file.exists() and file.open(QFile.ReadOnly | QFile.Text):
            try:
                json_data = file.readAll().data().decode('utf-8')
                self._downloads = json.loads(json_data)
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                self._downloads = []
            file.close()
        self._verify_downloads()
    
    def _save_downloads(self):
        try:
            json_data = json.dumps(self._downloads, indent=4, ensure_ascii=False).encode('utf-8')
            file = QFile(self._history_file)
            if file.open(QFile.WriteOnly | QFile.Text):
                file.write(json_data)
                file.close()
        except Exception as e:
            print(f"保存历史记录错误: {e}")
    
    def _auto_verify(self):
        self._verify_downloads()
    
    def _verify_downloads(self):
        if not self._download_folder:
            return
        
        updated = []
        removed = []
        for item in self._downloads:
            file_path = self._get_file_path(item["filename"])
            file = QFile(file_path)
            if file.exists():
                item.update({
                    "filesize": file.size(),
                    "mtime": file.fileTime(QFile.FileModificationTime).toSecsSinceEpoch()
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
                print(f"文件已不存在，移除记录: {url}")
    
    # 辅助方法
    def _get_file_path(self, filename):
        return QDir(self._download_folder).filePath(filename)