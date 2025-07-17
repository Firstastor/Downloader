from PySide6.QtCore import QCoreApplication, QObject, Signal, Property, QUrl, Slot, QDir, QStandardPaths, QFile, QFileInfo, QTextStream, QRegularExpression

class Settings(QObject):
    def __init__(self):
        super().__init__()
        # 获取应用程序根目录路径
        app_dir = QCoreApplication.applicationDirPath()
        
        # 配置文件路径改为应用程序根目录下的 Downloader.ini
        self.config_file = f"{app_dir}/Downloader.ini"
        self._load_config()  # 加载配置

        # 配置文件路径改为应用程序根目录下的 Downloader.ini
        self.config_file = f"{app_dir}/Downloader.ini"
        self._load_config()  # 加载配置

    def _load_config(self):
        """从配置文件加载设置"""
        config = QFile(self.config_file)
        if not config.exists():
            self._set_default_values()
            self._save_config()
            return

        if not config.open(QFile.ReadOnly | QFile.Text):
            print(f"Error opening config file for reading: {config.errorString()}")
            self._set_default_values()
            return

        stream = QTextStream(config)
        self._download_folder = self._read_config_value(stream, "download_folder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation))
        self._speed_limit = int(self._read_config_value(stream, "speed_limit", "0"))
        self._concurrent_downloads = int(self._read_config_value(stream, "concurrent_downloads", "5"))
        self._max_threads_per_download = int(self._read_config_value(stream, "max_threads_per_download", "32"))
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
        self._download_folder = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        self._speed_limit = 0
        self._concurrent_downloads = 5
        self._max_threads_per_download = 32

    def _save_config(self):
        """保存当前设置到配置文件"""
        config = QFile(self.config_file)
        if not config.open(QFile.WriteOnly | QFile.Text):
            print(f"Error opening config file for writing: {config.errorString()}")
            return

        stream = QTextStream(config)
        stream << f"download_folder={self._download_folder}\n"
        stream << f"speed_limit={self._speed_limit}\n"
        stream << f"concurrent_downloads={self._concurrent_downloads}\n"
        stream << f"max_threads_per_download={self._max_threads_per_download}\n"
        config.close()

    # -------------------- 信号定义 --------------------
    downloadFolderChanged = Signal(str)
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
        if self._download_folder != value:
            self._download_folder = value
            self.downloadFolderChanged.emit(value)
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
        if not path:
            return False

        if path.startswith("file:///"):
            path = path[8:]

        # 使用 QDir.separator() 获取当前系统的路径分隔符
        from PySide6.QtCore import QDir, QFileInfo, QFile
        
        # Windows 路径验证
        if QDir.separator() == '\\':
            # 修正正则表达式：允许驱动器号后的冒号，只禁止文件名中的冒号
            regex = QRegularExpression(r'^(?:[a-zA-Z]:[\\/]|\\\\[^\\/*?"<>|]+[\\/][^\\/:*?"<>|]+)')
            if not regex.match(path).hasMatch():
                return False
            illegal_chars = r'<>"|?*'  # 文件名中禁止的字符，不包括冒号
            if any(char in path for char in illegal_chars):
                return False

        # 使用 QFileInfo 检查路径属性
        file_info = QFileInfo(path)
        return file_info.exists() and file_info.isDir() and file_info.permissions() & QFile.WriteUser

    def cleanup(self):
        # 清理资源
        pass