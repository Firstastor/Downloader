from PySide6.QtCore import QObject, Signal, Property, Slot, QUrl
from .DownloadHistory import DownloadHistory

class DownloadedPage(QObject):
    downloadsChanged = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._history = DownloadHistory(settings, self) 
        self._history.historyChanged.connect(self.downloadsChanged)

    @Property(list, notify=downloadsChanged)
    def downloads(self):
        return self._history.history

    @Property(str)
    def downloadFolder(self):
        return self._history.downloadFolder

    @downloadFolder.setter
    def downloadFolder(self, path):
        self._history.setDownloadFolder(path)

    @Slot(str, str, str)
    def addDownload(self, url, filename, folder=None):
        self._history.addRecord(url, filename, folder)

    @Slot(str, bool) 
    def removeDownload(self, url, deleteFile=False):
        self._history.removeRecord(url, deleteFile) 

    @Slot(str, str, result=QUrl)
    def getFileUrl(self, filename, folder=None):
        return self._history.getFileUrl(filename, folder)

    @Slot(str, str, result=QUrl)
    def getFolderUrl(self, filename, folder=None):
        return self._history.getFolderUrl(filename, folder)