from PySide6.QtCore import QObject, Signal, Property, Slot, QUrl, QFile, QIODevice, QDir, QFileInfo, QTimer, QElapsedTimer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

class DownloadingPage(QObject):
    downloadStarted = Signal(str, str, str)  # url, filename, savePath
    downloadProgress = Signal(str, float, float)  # url, progress, speed
    downloadCompleted = Signal(str, str)  # url, savePath
    downloadError = Signal(str, str)  # url, errorMessage
    downloadCancelled = Signal(str)  # url

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._activeDownloads = {}
        self._networkManager = QNetworkAccessManager(self)
        self._history = settings.downloadHistory  # Store reference to history

    @Property(str, constant=True)
    def downloadFolder(self):
        return self._settings.downloadFolder

    @Slot(QUrl)
    def startDownload(self, url):
        urlStr = url.toString()
        if not urlStr:
            self.downloadError.emit("", "URL cannot be empty")
            return

        if not self._isValidUrl(urlStr):
            self.downloadError.emit(urlStr, "Invalid URL")
            return

        if urlStr in self._activeDownloads:
            self.downloadError.emit(urlStr, "Download already in progress")
            return

        try:
            filename = self._getFilenameFromUrl(urlStr)
            safeName = self._sanitizeFilename(filename)
            finalPath = self._getAvailablePath(QDir(self.downloadFolder).filePath(safeName))
            tempPath = f"{finalPath}.downloading"

            if not self._ensureDirectoryExists(finalPath):
                raise Exception("Cannot create directory")

            file = QFile(tempPath)
            if not file.open(QIODevice.WriteOnly):
                raise Exception("Cannot create temp file")

            request = QNetworkRequest(QUrl(urlStr))
            request.setAttribute(QNetworkRequest.Http2AllowedAttribute, True)
            request.setAttribute(QNetworkRequest.Http2CleartextAllowedAttribute, True)

            timer = QElapsedTimer()
            timer.start()

            self._activeDownloads[urlStr] = {
                "filename": safeName,
                "savePath": finalPath,
                "tempPath": tempPath,
                "file": file,
                "timer": timer,
                "bytesReceived": 0,
                "reply": None,
                "isCancelled": False
            }

            self.downloadStarted.emit(urlStr, safeName, finalPath)
            reply = self._networkManager.get(request)

            reply.downloadProgress.connect(
                lambda br, bt, url=urlStr: self._handleProgress(url, br, bt)
            )
            reply.finished.connect(
                lambda url=urlStr, reply=reply: self._handleFinished(url, reply)
            )
            reply.errorOccurred.connect(
                lambda error, url=urlStr: self._handleError(url, error)
            )
            reply.readyRead.connect(lambda: self._writeData(urlStr, reply, file))

            self._activeDownloads[urlStr]["reply"] = reply

        except Exception as e:
            self.downloadError.emit(urlStr, f"Download failed: {str(e)}")
            self._cleanupDownload(urlStr)

    @Slot(QUrl)
    def cancelDownload(self, url):
        urlStr = url.toString()
        if urlStr not in self._activeDownloads:
            return

        downloadInfo = self._activeDownloads[urlStr]
        downloadInfo["isCancelled"] = True

        if "reply" in downloadInfo and downloadInfo["reply"]:
            reply = downloadInfo["reply"]
            try:
                reply.setReadBufferSize(0)
                reply.abort()
                reply.deleteLater()
            except Exception as e:
                self.downloadError.emit(urlStr, f"Error cancelling download: {str(e)}")

        if "file" in downloadInfo:
            try:
                if downloadInfo["file"].isOpen():
                    downloadInfo["file"].close()
                if "tempPath" in downloadInfo:
                    tempFile = QFile(downloadInfo["tempPath"])
                    if tempFile.exists():
                        tempFile.remove()
            except Exception as e:
                self.downloadError.emit(urlStr, f"Error cleaning up files: {str(e)}")

        self.downloadCancelled.emit(urlStr)
        self._activeDownloads.pop(urlStr, None)

    def _isValidUrl(self, urlStr):
        url = QUrl(urlStr)
        return url.isValid() and url.scheme() in ('http', 'https') and url.host()

    def _ensureDirectoryExists(self, path):
        return QFileInfo(path).dir().mkpath(".")

    def _sanitizeFilename(self, filename):
        if not filename:
            return "download"
        
        safeChars = (' ', '-', '_', '.', '(', ')', '[', ']')
        safeName = ''.join(c for c in QUrl.fromPercentEncoding(filename.encode()) 
                       if c.isalnum() or c in safeChars or ('\u4e00' <= c <= '\u9fff'))
        
        safeName = ' '.join(safeName.split())
        if len(safeName) > 255:
            safeName = safeName[:255]
        if safeName.startswith('.'):
            safeName = "download" + safeName
            
        return safeName

    def _getAvailablePath(self, desiredPath):
        fileInfo = QFileInfo(desiredPath)
        if not fileInfo.exists():
            return desiredPath
            
        base = fileInfo.completeBaseName()
        suffix = fileInfo.suffix()
        dirPath = fileInfo.dir()
        counter = 1
        
        while True:
            newPath = dirPath.filePath(f"{base}_{counter}.{suffix}" if suffix else f"{base}_{counter}")
            if not QFileInfo(newPath).exists():
                return newPath
            counter += 1

    def _getFilenameFromUrl(self, urlStr):
        path = QUrl(urlStr).path()
        return path.split('/')[-1] if path else "download"

    def _writeData(self, urlStr, reply, file):
        if urlStr not in self._activeDownloads or self._activeDownloads[urlStr]["isCancelled"]:
            return
            
        data = reply.readAll()
        if data.size() > 0:
            file.write(data)
            self._activeDownloads[urlStr]["bytesReceived"] += data.size()

    def _handleProgress(self, urlStr, bytesReceived, bytesTotal):
        if urlStr not in self._activeDownloads or self._activeDownloads[urlStr]["isCancelled"]:
            return
            
        info = self._activeDownloads[urlStr]
        elapsed = info["timer"].elapsed() / 1000.0
        speed = bytesReceived / max(0.001, elapsed)
        progress = (bytesReceived / bytesTotal * 100) if bytesTotal > 0 else 0
        progress = max(0, min(100, progress))
        
        self.downloadProgress.emit(urlStr, progress, speed)

    def _handleFinished(self, urlStr, reply):
        if urlStr not in self._activeDownloads:
            return
            
        info = self._activeDownloads[urlStr]
        
        if info["isCancelled"] or reply.error() != QNetworkReply.NoError:
            return
            
        try:
            info["file"].close()
            tempFile = QFile(info["tempPath"])
            if tempFile.exists():
                finalFile = QFile(info["savePath"])
                if finalFile.exists():
                    finalFile.remove()
                if not tempFile.rename(info["savePath"]):
                    raise Exception("Rename failed")
            
            self.downloadCompleted.emit(urlStr, info["savePath"])
        except Exception as e:
            self.downloadError.emit(urlStr, f"Completion error: {str(e)}")
        finally:
            self._cleanupDownload(urlStr)

    def _handleError(self, urlStr, error):
        if urlStr not in self._activeDownloads or error == QNetworkReply.OperationCanceledError:
            return
            
        self.downloadError.emit(urlStr, self._activeDownloads[urlStr]["reply"].errorString())
        self._cleanupDownload(urlStr)

    def _cleanupDownload(self, urlStr):
        if urlStr not in self._activeDownloads:
            return
            
        info = self._activeDownloads.pop(urlStr, None)
        if not info:
            return

        if info["file"].isOpen():
            info["file"].close()
            
        if not info.get("isCancelled", False):
            tempFile = QFile(info["tempPath"])
            if tempFile.exists():
                tempFile.remove()

        reply = info.get("reply")
        if reply:
            reply.deleteLater()

    @Slot(QUrl, result=float)
    def getDownloadProgress(self, url):
        urlStr = url.toString()
        if urlStr in self._activeDownloads:
            bytesReceived = self._activeDownloads[urlStr]["bytesReceived"]
            reply = self._activeDownloads[urlStr].get("reply")
            bytesTotal = reply.header(QNetworkRequest.ContentLengthHeader) if reply else 0
            return (bytesReceived / bytesTotal * 100) if bytesTotal > 0 else 0
        return 0

    @Slot(QUrl, result=float)
    def getDownloadSpeed(self, url):
        urlStr = url.toString()
        if urlStr in self._activeDownloads:
            info = self._activeDownloads[urlStr]
            elapsed = info["timer"].elapsed() / 1000.0
            return info["bytesReceived"] / max(0.001, elapsed)
        return 0

    @Slot(QUrl, result=str)
    def getDownloadFilename(self, url):
        urlStr = url.toString()
        return self._activeDownloads.get(urlStr, {}).get("filename", "")
    
    @Slot(QUrl, result=str)
    def getDownloadSavePath(self, url):
        urlStr = url.toString()
        if urlStr in self._activeDownloads:
            return self._activeDownloads[urlStr]["savePath"]
        return ""

    @Slot(result=list)
    def getActiveDownloads(self):
        return list(self._activeDownloads.keys())
    
    @Slot(QUrl, result=bool)
    def isUrlInHistory(self, url):
        if not hasattr(self._settings, 'downloadHistory'):
            return False
        self._settings.downloadHistory.cleanupInvalidEntries()
        return self._settings.downloadHistory.isUrlValid(url.toString())