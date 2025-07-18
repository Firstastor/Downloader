from PySide6.QtCore import QCoreApplication, QObject, Signal, Property, QUrl, Slot, QDir, QStandardPaths, QFile, QTextStream, QRegularExpression
from .DownloadHistory import DownloadHistory

class Settings(QObject):
    def __init__(self):
        super().__init__()
        appDir = QCoreApplication.applicationDirPath()
        self.configFile = f"{appDir}/Downloader.ini"
        self._downloadFolder = ""
        self._concurrentDownloads = 0
        self._maxThreadsPerDownload = 0
        self.downloadHistory = DownloadHistory(self)
        self.loadConfig()

    def loadConfig(self):
        config = QFile(self.configFile)
        if not config.exists():
            self.setDefaultValues()
            self.saveConfig()
            return

        if not config.open(QFile.ReadOnly | QFile.Text):
            print(f"Error opening config file for reading: {config.errorString()}")
            self.setDefaultValues()
            return

        stream = QTextStream(config)
        self.downloadFolder = self.readConfigValue(stream, "download_folder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation))
        self.concurrentDownloads = int(self.readConfigValue(stream, "concurrentDownloads", "5"))
        self.maxThreadsPerDownload = int(self.readConfigValue(stream, "maxThreadsPerDownload", "32"))
        config.close()

    def readConfigValue(self, stream, key, default):
        regex = QRegularExpression(f"^{key}=(.*)$")
        while not stream.atEnd():
            line = stream.readLine()
            match = regex.match(line)
            if match.hasMatch():
                return match.captured(1)
        return default

    def setDefaultValues(self):
        self.downloadFolder = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        self.concurrentDownloads = 5
        self.maxThreadsPerDownload = 32

    def saveConfig(self):
        config = QFile(self.configFile)
        if not config.open(QFile.WriteOnly | QFile.Text):
            print(f"Error opening config file for writing: {config.errorString()}")
            return

        stream = QTextStream(config)
        stream << f"download_folder={self._downloadFolder}\n"
        stream << f"concurrentDownloads={self._concurrentDownloads}\n"
        stream << f"maxThreadsPerDownload={self._maxThreadsPerDownload}\n"
        config.close()

    downloadFolderChanged = Signal(str)
    concurrentDownloadsChanged = Signal(int)
    maxThreadsPerDownloadChanged = Signal(int)

    @Property(str, notify=downloadFolderChanged)
    def downloadFolder(self):
        return self._downloadFolder

    @downloadFolder.setter
    def downloadFolder(self, value):
        if value.startswith("file:///"):
            value = value[8:]
        if self._downloadFolder != value:
            self._downloadFolder = value
            self.downloadFolderChanged.emit(value)
            self.saveConfig()

    @Property(int, notify=concurrentDownloadsChanged)
    def concurrentDownloads(self):
        return self._concurrentDownloads

    @concurrentDownloads.setter
    def concurrentDownloads(self, value):
        if self._concurrentDownloads != value:
            self._concurrentDownloads = value
            self.concurrentDownloadsChanged.emit(value)
            self.saveConfig()

    @Property(int, notify=maxThreadsPerDownloadChanged)
    def maxThreadsPerDownload(self):
        return self._maxThreadsPerDownload

    @maxThreadsPerDownload.setter
    def maxThreadsPerDownload(self, value):
        if self._maxThreadsPerDownload != value:
            self._maxThreadsPerDownload = value
            self.maxThreadsPerDownloadChanged.emit(value)
            self.saveConfig()

    @Slot(str, result=bool)
    def isValidPath(self, path):
        if not path:
            return False

        if path.startswith("file:///"):
            path = path[8:]
        
        if QDir.separator() == '\\':
            regex = QRegularExpression(r'^(?:[a-zA-Z]:[\\/]|\\\\[^\\/*?"<>|]+[\\/][^\\/:*?"<>|]+)')
            if not regex.match(path).hasMatch():
                return False
            illegalChars = r'<>"|?*'
            if any(char in path for char in illegalChars):
                return False
        return True