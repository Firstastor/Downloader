import json
from PySide6.QtCore import QObject, Signal, Property, QDir, QFile, QUrl, QFileInfo

class DownloadHistory(QObject):
    historyChanged = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._history = []
        self._downloadFolder = settings.downloadFolder
        self._historyFile = QDir.current().filePath("Download_History.json")
        self._ensureHistoryFile()

    @Property(list, notify=historyChanged)
    def history(self):
        return self._history

    @Property(str)
    def downloadFolder(self):
        return self._downloadFolder

    def setDownloadFolder(self, path):
        if path and QDir(path).exists():
            self._downloadFolder = path

    def addRecord(self, url, filename):
        filePath = QDir(self._downloadFolder).filePath(filename)
        size = QFile(filePath).size() if QFile.exists(filePath) else 0
        if not any(d['url'] == url for d in self._history):
            self._history.append({
                'url': url,
                'filename': filename,
                'filesize': size
            })
            self._saveHistory()

    def removeRecord(self, url):
        self._history = [d for d in self._history if d['url'] != url]
        self._saveHistory()

    def getFileUrl(self, filename):
        filePath = QDir(self._downloadFolder).filePath(filename)
        return QUrl.fromLocalFile(filePath) if QFile.exists(filePath) else QUrl()

    def getFolderUrl(self, filename):
        if not self._downloadFolder:
            return QUrl()
        filePath = QDir(self._downloadFolder).filePath(filename)
        return QUrl.fromLocalFile(QFileInfo(filePath).absolutePath())

    def _ensureHistoryFile(self):
        if not QFile.exists(self._historyFile):
            self._saveHistory([])
        self._loadHistory()

    def _loadHistory(self):
        try:
            with open(self._historyFile, 'r', encoding='utf-8') as f:
                self._history = json.load(f)
            self.historyChanged.emit()
        except (json.JSONDecodeError, FileNotFoundError):
            self._history = []

    def _saveHistory(self):
        with open(self._historyFile, 'w', encoding='utf-8') as f:
            json.dump(self._history, f, indent=4, ensure_ascii=False)
        self.historyChanged.emit()