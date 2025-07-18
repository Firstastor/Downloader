from PySide6.QtCore import QCoreApplication, QObject, Signal, Property, QUrl, Slot, QDir, QStandardPaths, QFile, QFileInfo, QTextStream, QRegularExpression

class Settings(QObject):
    def __init__(self):
        super().__init__()
        # 获取应用程序根目录路径
        app_dir = QCoreApplication.applicationDirPath()
        
        # 配置文件路径改为应用程序根目录下的 Downloader.ini
        self.config_file = f"{app_dir}/Downloader.ini"
        self._load_config()  # 加载配置

    def _load_config(self):
        """从配置文件加载设置"""
        config = QFile(self.config_file)
        if not config.exists():
            self._set_default_values()
            self._saveConfig()
            return

        if not config.open(QFile.ReadOnly | QFile.Text):
            print(f"Error opening config file for reading: {config.errorString()}")
            self._set_default_values()
            return

        stream = QTextStream(config)
        self._downloadFolder = self._read_config_value(stream, "download_folder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation))
        self._concurrentDownloads = int(self._read_config_value(stream, "concurrentDownloads", "5"))
        self._maxThreadsPerDownload = int(self._read_config_value(stream, "maxThreadsPerDownload", "32"))
        config.close()

    def _read_config_value(self, stream, key, default):
        regex = QRegularExpression(f"^{key}=(.*)$")
        while not stream.atEnd():
            line = stream.readLine()
            match = regex.match(line)
            if match.hasMatch():
                return match.captured(1)
        return default

    def _set_default_values(self):
        """设置默认值"""
        self._downloadFolder = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        self._concurrentDownloads = 5
        self._maxThreadsPerDownload = 32

    def _saveConfig(self):
        """保存当前设置到配置文件"""
        config = QFile(self.config_file)
        if not config.open(QFile.WriteOnly | QFile.Text):
            print(f"Error opening config file for writing: {config.errorString()}")
            return

        stream = QTextStream(config)
        stream << f"download_folder={self._downloadFolder}\n"
        stream << f"concurrentDownloads={self._concurrentDownloads}\n"
        stream << f"maxThreadsPerDownload={self._maxThreadsPerDownload}\n"
        config.close()

    # -------------------- 信号定义 --------------------
    downloadFolderChanged = Signal(str)
    concurrentDownloadsChanged = Signal(int)
    maxThreadsPerDownloadChanged = Signal(int)

    # -------------------- 属性定义 --------------------
    # Download Folder
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
            self._saveConfig()

    # Concurrent Downloads
    @Property(int, notify=concurrentDownloadsChanged)
    def concurrentDownloads(self):
        return self._concurrentDownloads

    @concurrentDownloads.setter
    def concurrentDownloads(self, value):
        if self._concurrentDownloads != value:
            self._concurrentDownloads = value
            self.concurrentDownloadsChanged.emit(value)
            self._saveConfig()

    # Max Threads per Download
    @Property(int, notify=maxThreadsPerDownloadChanged)
    def maxThreadsPerDownload(self):
        return self._maxThreadsPerDownload

    @maxThreadsPerDownload.setter
    def maxThreadsPerDownload(self, value):
        if self._maxThreadsPerDownload != value:
            self._maxThreadsPerDownload = value
            self.maxThreadsPerDownloadChanged.emit(value)
            self._saveConfig()

    # -------------------- 方法定义 --------------------

    @Slot(str, result=bool)
    def isValidPath(self, path):
        """验证路径是否有效且存在"""
        if not path:
            return False

        if path.startswith("file:///"):
            path = path[8:]
        
        # Windows 路径验证
        if QDir.separator() == '\\':
            # 修正正则表达式：允许驱动器号后的冒号，只禁止文件名中的冒号
            regex = QRegularExpression(r'^(?:[a-zA-Z]:[\\/]|\\\\[^\\/*?"<>|]+[\\/][^\\/:*?"<>|]+)')
            if not regex.match(path).hasMatch():
                return False
            illegal_chars = r'<>"|?*'  # 文件名中禁止的字符，不包括冒号
            if any(char in path for char in illegal_chars):
                return False
