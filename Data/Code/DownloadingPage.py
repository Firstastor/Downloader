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
        
        if hasattr(self._settings, 'downloadHistory') and self._settings.downloadHistory.isUrlValid(urlStr):
            self.downloadError.emit(urlStr, "This URL has already been downloaded")
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
            request.setHeader(QNetworkRequest.UserAgentHeader, "Mozilla/5.0")

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

        # 1. Pause data reception
        if "reply" in downloadInfo and downloadInfo["reply"]:
            reply = downloadInfo["reply"]
            try:
                # Pause data reception
                reply.setReadBufferSize(0)
            except Exception as e:
                self.downloadError.emit(urlStr, f"Error pausing reply: {str(e)}")

        # 2. Disconnect all signals
        if "reply" in downloadInfo and downloadInfo["reply"]:
            reply = downloadInfo["reply"]
            try:
                reply.downloadProgress.disconnect()
                reply.finished.disconnect()
                reply.errorOccurred.disconnect()
                reply.readyRead.disconnect()
            except TypeError:
                # Handle case where signals weren't connected
                pass
            except Exception as e:
                self.downloadError.emit(urlStr, f"Error disconnecting signals: {str(e)}")

        # 3. Abort network request
        if "reply" in downloadInfo and downloadInfo["reply"]:
            reply = downloadInfo["reply"]
            try:
                if reply.isRunning():
                    # Use single-shot timer to safely abort in event loop
                    QTimer.singleShot(50, lambda: self._safeAbortReply(reply, urlStr))
                else:
                    self._cleanupReply(reply, urlStr)
            except Exception as e:
                self.downloadError.emit(urlStr, f"Error handling reply: {str(e)}")

        # 4. Close and remove temp file
        if "file" in downloadInfo:
            try:
                if downloadInfo["file"].isOpen():
                    downloadInfo["file"].close()
                if "tempPath" in downloadInfo:
                    tempFile = QFile(downloadInfo["tempPath"])
                    if tempFile.exists():
                        tempFile.remove()
            except Exception as e:
                self.downloadError.emit(urlStr, f"Error closing/removing temp file: {str(e)}")
                
        # 5. Clear access cache
        self._networkManager.clearAccessCache()
        self.downloadCancelled.emit(urlStr)
        self._activeDownloads.pop(urlStr, None)

    def _safeAbortReply(self, reply, urlStr):
        try:
            reply.abort()
            self._cleanupReply(reply, urlStr)
        except Exception as e:
            self.downloadError.emit(urlStr, f"Error during safe abort: {str(e)}")

    def _cleanupReply(self, reply, urlStr):
        reply.deleteLater()

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
        print(f"Writing {data.size()} bytes for URL: {urlStr}")
        if data.size() > 0:
            bytesWritten = file.write(data)
            if bytesWritten == -1:
                print(f"Error writing to file: {file.errorString()}")
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
            
            if hasattr(self._settings, 'downloadHistory'):
                self._settings.downloadHistory.addRecord(
                    urlStr, 
                    QFileInfo(info["savePath"]).fileName(),
                    QFileInfo(info["savePath"]).path()
                )
            
            self.downloadCompleted.emit(urlStr, info["savePath"])
        except Exception as e:
            self.downloadError.emit(urlStr, f"Completion error: {str(e)}")
        finally:
            self._cleanupDownload(urlStr)

    def _handleError(self, urlStr, error):
        if urlStr not in self._activeDownloads or error == QNetworkReply.OperationCanceledError:
            return
            
        errorMsg = self._activeDownloads[urlStr]["reply"].errorString()
        self.downloadError.emit(urlStr, errorMsg)
        self._cleanupDownload(urlStr)

    def _cleanupDownload(self, urlStr):
        if urlStr in self._activeDownloads:
            info = self._activeDownloads.pop(urlStr)
            if info["file"].isOpen():
                info["file"].close()
            if not info.get("isCancelled", False):
                tempFile = QFile(info["tempPath"])
                if tempFile.exists():
                    tempFile.remove()
            reply = info.get("reply")
            if reply:
                reply.deleteLater()
        print(f"Cleaned up download: {urlStr}")

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
    
    @Slot(str, result=bool)
    def isUrlDownloaded(self, url):
        return self._history.isUrlValid(url)