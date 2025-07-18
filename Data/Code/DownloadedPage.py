from PySide6.QtCore import QObject, Signal, Property, Slot, QUrl, QFile, QDir, QFileInfo, QFileSystemWatcher
from .DownloadHistory import DownloadHistory

class DownloadedPage(QObject):
    downloadsChanged = Signal()
    folderChanged = Signal(str)
    errorOccurred = Signal(str, str)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._history = DownloadHistory(self)
        self._file_watcher = QFileSystemWatcher(self)
        
        # 确保settings中有downloadHistory属性
        if not hasattr(settings, 'downloadHistory'):
            settings.downloadHistory = self._history
        
        # 初始化设置
        self.downloadFolder = settings.downloadFolder
        self._file_watcher.directoryChanged.connect(self._verify_files)
        self._history.historyChanged.connect(self.downloadsChanged)

    @Property(list, notify=downloadsChanged)
    def downloads(self):
        return self._history.history

    @Property(str, notify=folderChanged)
    def downloadFolder(self):
        return self._file_watcher.directories()[0] if self._file_watcher.directories() else ""

    @downloadFolder.setter
    def downloadFolder(self, path):
        if not path or not QDir(path).exists():
            return
            
        if self._file_watcher.directories():
            self._file_watcher.removePaths(self._file_watcher.directories())
        
        self._file_watcher.addPath(path)
        self.folderChanged.emit(path)
        self._verify_files()

    @Slot(str, str)
    def addDownload(self, url, filename):
        file_path = QDir(self.downloadFolder).filePath(filename)
        file = QFile(file_path)
        try:
            self._history.add_record(
                url,
                filename,
                file.size() if file.exists() else 0
            )
        except Exception as e:
            self.errorOccurred.emit(url, str(e))

    @Slot(str)
    def removeDownload(self, url):
        if record := next((d for d in self._history.history if d['url'] == url), None):
            try:
                file = QFile(QDir(self.downloadFolder).filePath(record['filename']))
                if file.exists() and not file.remove():
                    raise IOError(file.errorString())
                self._history.remove_record(url)
            except Exception as e:
                self.errorOccurred.emit(url, str(e))

    @Slot(str, result=QUrl)
    def getFileUrl(self, filename):
        file_path = QDir(self.downloadFolder).filePath(filename)
        return QUrl.fromLocalFile(file_path) if QFile.exists(file_path) else QUrl()

    @Slot(str, result=QUrl)
    def getFolderUrl(self, filename):
        if not self.downloadFolder:
            return QUrl()
        file_path = QDir(self.downloadFolder).filePath(filename)
        return QUrl.fromLocalFile(QFileInfo(file_path).absolutePath())

    def _verify_files(self):
        """验证文件是否存在并同步记录"""
        if not self.downloadFolder:
            return
            
        removed = [
            record['url'] for record in self._history.history
            if not QFile.exists(QDir(self.downloadFolder).filePath(record['filename']))
        ]
        
        for url in removed:
            self._history.remove_record(url)