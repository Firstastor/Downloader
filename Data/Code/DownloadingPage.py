from PySide6.QtCore import QObject, Signal, Property, Slot, QUrl, QFile, QIODevice, QDir, QFileInfo, QTimer, QElapsedTimer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

class DownloadingPage(QObject):
    # Signals
    downloadStarted = Signal(str, str, str)  # url, filename, save_path
    downloadProgress = Signal(str, float, float)  # url, progress, speed
    downloadCompleted = Signal(str, str)  # url, save_path
    downloadError = Signal(str, str)  # url, error_message
    downloadCancelled = Signal(str)  # url

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._active_downloads = {}
        self._network_manager = QNetworkAccessManager(self)

    @Property(str, constant=True)
    def downloadFolder(self):
        return self._settings.downloadFolder

    @Slot(QUrl)
    def startDownload(self, url):
        url_str = url.toString()
        if not url_str:
            self.downloadError.emit("", "URL cannot be empty")
            return

        if not self._is_valid_url(url_str):
            self.downloadError.emit(url_str, "Invalid URL")
            return

        if url_str in self._active_downloads:
            self.downloadError.emit(url_str, "Download already in progress")
            return

        try:
            filename = self._get_filename_from_url(url_str)
            safe_name = self._sanitize_filename(filename)
            final_path = self._get_available_path(QDir(self.downloadFolder).filePath(safe_name))
            temp_path = f"{final_path}.downloading"

            if not self._ensure_directory_exists(final_path):
                raise Exception("Cannot create directory")

            file = QFile(temp_path)
            if not file.open(QIODevice.WriteOnly):
                raise Exception("Cannot create temp file")

            request = QNetworkRequest(QUrl(url_str))
            request.setAttribute(QNetworkRequest.Http2AllowedAttribute, True)
            request.setAttribute(QNetworkRequest.Http2CleartextAllowedAttribute, True)

            timer = QElapsedTimer()
            timer.start()

            self._active_downloads[url_str] = {
                "filename": safe_name,
                "save_path": final_path,
                "temp_path": temp_path,
                "file": file,
                "timer": timer,
                "bytes_received": 0,
                "reply": None,
                "is_cancelled": False
            }

            self.downloadStarted.emit(url_str, safe_name, final_path)
            reply = self._network_manager.get(request)

            reply.downloadProgress.connect(
                lambda br, bt, url=url_str: self._handle_progress(url, br, bt)
            )
            reply.finished.connect(
                lambda url=url_str, reply=reply: self._handle_finished(url, reply)
            )
            reply.errorOccurred.connect(
                lambda error, url=url_str: self._handle_error(url, error)
            )
            reply.readyRead.connect(lambda: self._write_data(url_str, reply, file))

            self._active_downloads[url_str]["reply"] = reply

        except Exception as e:
            self.downloadError.emit(url_str, f"Download failed: {str(e)}")
            self._cleanup_download(url_str)

    @Slot(QUrl)
    def cancelDownload(self, url):
        url_str = url.toString()
        if url_str not in self._active_downloads:
            return

        download_info = self._active_downloads[url_str]
        download_info["is_cancelled"] = True

        # 1. 暂停数据接收
        if "reply" in download_info and download_info["reply"]:
            reply = download_info["reply"]
            try:
                # 暂停接收数据
                reply.setReadBufferSize(0)
            except Exception as e:
                self.downloadError.emit(url_str, f"Error pausing reply: {str(e)}")

        # 2. 断开所有信号连接
        if "reply" in download_info and download_info["reply"]:
            reply = download_info["reply"]
            try:
                reply.downloadProgress.disconnect()
                reply.finished.disconnect()
                reply.errorOccurred.disconnect()
                reply.readyRead.disconnect()
            except TypeError:
                # 处理信号未连接的情况
                pass
            except Exception as e:
                self.downloadError.emit(url_str, f"Error disconnecting signals: {str(e)}")

        # 3. 中止网络请求
        if "reply" in download_info and download_info["reply"]:
            reply = download_info["reply"]
            try:
                if reply.isRunning():
                    # 使用单次定时器确保在事件循环中安全中止
                    QTimer.singleShot(50, lambda: self._safe_abort_reply(reply, url_str))
                else:
                    self._cleanup_reply(reply, url_str)
            except Exception as e:
                self.downloadError.emit(url_str, f"Error handling reply: {str(e)}")

        # 4. 关闭并删除临时文件
        if "file" in download_info:
            try:
                if download_info["file"].isOpen():
                    download_info["file"].close()
                if "temp_path" in download_info:
                    temp_file = QFile(download_info["temp_path"])
                    if temp_file.exists():
                        temp_file.remove()
            except Exception as e:
                self.downloadError.emit(url_str, f"Error closing or removing temp file: {str(e)}")

        # 5. 清理网络管理器缓存
        self._network_manager.clearAccessCache()
        
        # 6. 发送信号并清理记录
        self.downloadCancelled.emit(url_str)
        self._active_downloads.pop(url_str, None)

    def _safe_abort_reply(self, reply, url_str):
        try:
            reply.abort()  # 先中止再删除
            reply.deleteLater()
        except RuntimeError as e:
            print(f"安全中止失败: {e}")

    def _finalize_cancellation(self, url_str):
        if url_str not in self._active_downloads:
            return

        download_info = self._active_downloads.pop(url_str)
        
        # 5. 安全删除临时文件
        temp_path = download_info.get("temp_path")
        if temp_path:
            temp_file = QFile(temp_path)
            if temp_file.exists():
                # 确保文件可访问后再删除
                QTimer.singleShot(0, lambda: (
                    temp_file.remove() if temp_file.exists() else None
                ))

        # 6. 发送取消信号（最后执行）
        self.downloadCancelled.emit(url_str)

    # Helper methods
    def _is_valid_url(self, url_str):
        url = QUrl(url_str)
        return url.isValid() and url.scheme() in ('http', 'https') and url.host()

    def _ensure_directory_exists(self, path):
        return QFileInfo(path).dir().mkpath(".")

    def _sanitize_filename(self, filename):
        if not filename:
            return "download"
        
        safe_chars = (' ', '-', '_', '.', '(', ')', '[', ']')
        safe_name = ''.join(c for c in QUrl.fromPercentEncoding(filename.encode()) 
                           if c.isalnum() or c in safe_chars or ('\u4e00' <= c <= '\u9fff'))
        
        safe_name = ' '.join(safe_name.split())
        if len(safe_name) > 255:
            safe_name = safe_name[:255]
        if safe_name.startswith('.'):
            safe_name = "download" + safe_name
            
        return safe_name

    def _get_available_path(self, desired_path):
        file_info = QFileInfo(desired_path)
        if not file_info.exists():
            return desired_path
            
        base = file_info.completeBaseName()
        suffix = file_info.suffix()
        dir_path = file_info.dir()
        counter = 1
        
        while True:
            new_path = dir_path.filePath(f"{base}_{counter}.{suffix}" if suffix else f"{base}_{counter}")
            if not QFileInfo(new_path).exists():
                return new_path
            counter += 1

    def _get_filename_from_url(self, url_str):
        path = QUrl(url_str).path()
        return path.split('/')[-1] if path else "download"

    def _write_data(self, url_str, reply, file):
        if url_str not in self._active_downloads or self._active_downloads[url_str]["is_cancelled"]:
            return
            
        data = reply.readAll()
        if data.size() > 0:
            file.write(data)
            self._active_downloads[url_str]["bytes_received"] += data.size()

    def _handle_progress(self, url_str, bytes_received, bytes_total):
        if url_str not in self._active_downloads or self._active_downloads[url_str]["is_cancelled"]:
            return
            
        info = self._active_downloads[url_str]
        elapsed = info["timer"].elapsed() / 1000.0
        speed = bytes_received / max(0.001, elapsed)
        progress = (bytes_received / bytes_total * 100) if bytes_total > 0 else 0
        progress = max(0, min(100, progress))
        
        self.downloadProgress.emit(url_str, progress, speed)

    def _handle_finished(self, url_str, reply):
        if url_str not in self._active_downloads:
            return
            
        info = self._active_downloads[url_str]
        
        if info["is_cancelled"] or reply.error() != QNetworkReply.NoError:
            return
            
        try:
            info["file"].close()
            temp_file = QFile(info["temp_path"])
            if temp_file.exists():
                final_file = QFile(info["save_path"])
                if final_file.exists():
                    final_file.remove()
                if not temp_file.rename(info["save_path"]):
                    raise Exception("Rename failed")
            
            self.downloadCompleted.emit(url_str, info["save_path"])
        except Exception as e:
            self.downloadError.emit(url_str, f"Completion error: {str(e)}")
        finally:
            self._cleanup_download(url_str)

    def _handle_error(self, url_str, error):
        if url_str not in self._active_downloads or error == QNetworkReply.OperationCanceledError:
            return
            
        self.downloadError.emit(url_str, self._active_downloads[url_str]["reply"].errorString())
        self._cleanup_download(url_str)

    def _abort_reply(self, reply, url_str):
        try:
            if reply.isRunning():
                reply.abort()
            reply.deleteLater()
        except Exception as e:
            self.downloadError.emit(url_str, f"Error aborting reply: {str(e)}")

    def _cleanup_download(self, url_str):
        if url_str not in self._active_downloads:
            return
            
        info = self._active_downloads.pop(url_str, None)
        if not info:
            return

        if info["file"].isOpen():
            info["file"].close()
            
        if not info.get("is_cancelled", False):
            temp_file = QFile(info["temp_path"])
            if temp_file.exists():
                temp_file.remove()

        reply = info.get("reply")
        if reply:
            reply.deleteLater()

    # QML interface methods
    @Slot(QUrl, result=float)
    def getDownloadProgress(self, url):
        url_str = url.toString()
        if url_str in self._active_downloads:
            bytes_received = self._active_downloads[url_str]["bytes_received"]
            reply = self._active_downloads[url_str].get("reply")
            bytes_total = reply.header(QNetworkRequest.ContentLengthHeader) if reply else 0
            return (bytes_received / bytes_total * 100) if bytes_total > 0 else 0
        return 0

    @Slot(QUrl, result=float)
    def getDownloadSpeed(self, url):
        url_str = url.toString()
        if url_str in self._active_downloads:
            info = self._active_downloads[url_str]
            elapsed = info["timer"].elapsed() / 1000.0
            return info["bytes_received"] / max(0.001, elapsed)
        return 0

    @Slot(QUrl, result=str)
    def getDownloadFilename(self, url):
        url_str = url.toString()
        return self._active_downloads.get(url_str, {}).get("filename", "")

    @Slot(result=list)
    def getActiveDownloads(self):
        return list(self._active_downloads.keys())
    
    @Slot(QUrl, result=bool)
    def isUrlInHistory(self, url):
        url_str = url.toString()
        if not hasattr(self, '_settings') or not hasattr(self._settings, 'downloadHistory'):
            return False
        return any(record['url'] == url_str for record in self._settings.downloadHistory.history)