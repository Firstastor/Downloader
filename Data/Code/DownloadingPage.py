from PySide6.QtCore import QObject, Signal, Property, Slot, QUrl, QFile, QIODevice, QDir, QFileInfo, QTimer, QElapsedTimer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

class DownloadingPage(QObject):
    # 信号定义
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

    @Property(str)
    def downloadFolder(self):
        return self._settings.downloadFolder

    def _is_valid_url(self, url_str):
        url = QUrl(url_str)
        return url.isValid() and url.scheme() in ('http', 'https') and url.host()

    def _ensure_directory_exists(self, path):
        dir_info = QFileInfo(path)
        parent_dir = dir_info.dir()
        return parent_dir.mkpath(".")

    def _get_safe_filename(self, filename):
        if not filename:
            return "download"
        
        decoded = QUrl.fromPercentEncoding(filename.encode())
        
        keepchars = (' ', '-', '_', '.', '(', ')', '[', ']')
        safe_name = ""
        for c in decoded:
            if c.isalnum() or c in keepchars or ('\u4e00' <= c <= '\u9fff'):
                safe_name += c
        
        safe_name = ' '.join(safe_name.split())
        if len(safe_name) > 255:
            safe_name = safe_name[:255]
        
        if safe_name.startswith('.'):
            safe_name = "download" + safe_name
            
        return safe_name

    def _get_available_filename(self, desired_path):
        file_info = QFileInfo(desired_path)
        if not file_info.exists():
            return desired_path
            
        dir_path = file_info.dir()
        base_name = file_info.completeBaseName()
        suffix = file_info.suffix()
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}.{suffix}" if suffix else f"{base_name}_{counter}"
            new_path = dir_path.filePath(new_name)
            if not QFileInfo(new_path).exists():
                return new_path
            counter += 1

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
            safe_name = self._get_safe_filename(filename)
            
            save_dir = QDir(self.downloadFolder)
            save_path = save_dir.filePath(safe_name)
            final_path = self._get_available_filename(save_path)
            temp_path = f"{final_path}.downloading"
            
            if not self._ensure_directory_exists(final_path):
                raise Exception("Cannot create directory")
            
            file = QFile(temp_path)
            if not file.open(QIODevice.WriteOnly):
                raise Exception("Cannot create temp file")
            
            request = QNetworkRequest(QUrl(url_str))
            # 正确设置HTTP/2属性
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
                lambda br, bt, url=url_str: self._handle_download_progress(url, br, bt)
            )
            reply.finished.connect(
                lambda url=url_str, reply=reply: self._handle_download_finished(url, reply)
            )
            reply.errorOccurred.connect(
                lambda error, url=url_str, reply=reply: self._handle_download_error(url, reply, error)
            )
            
            self._active_downloads[url_str]["reply"] = reply
            reply.readyRead.connect(lambda: self._write_to_file(url_str, reply, file))
            
        except Exception as e:
            self.downloadError.emit(url_str, f"Download failed: {str(e)}")
            self._cleanup_download(url_str)

    def _write_to_file(self, url_str, reply, file):
        if url_str not in self._active_downloads or self._active_downloads[url_str]["is_cancelled"]:
            return
            
        data = reply.readAll()
        if data.size() > 0:
            file.write(data)
            self._active_downloads[url_str]["bytes_received"] += data.size()

    def _handle_download_progress(self, url_str, bytesReceived, bytesTotal):
        if url_str not in self._active_downloads or self._active_downloads[url_str]["is_cancelled"]:
            return
            
        download_info = self._active_downloads[url_str]
        elapsed = download_info["timer"].elapsed() / 1000.0  # 转换为秒
        speed = bytesReceived / max(0.001, elapsed)
        progress = (bytesReceived / bytesTotal * 100) if bytesTotal > 0 else 0
        progress = max(0, min(100, progress))
        
        self.downloadProgress.emit(url_str, progress, speed)

    def _handle_download_finished(self, url_str, reply):
        if url_str not in self._active_downloads:
            return
            
        download_info = self._active_downloads[url_str]
        
        if download_info["is_cancelled"]:
            return
            
        try:
            if reply.error() != QNetworkReply.NoError:
                if reply.error() != QNetworkReply.OperationCanceledError:
                    self.downloadError.emit(url_str, reply.errorString())
                return
                
            download_info["file"].flush()
            download_info["file"].close()
            
            temp_path = download_info["temp_path"]
            final_path = download_info["save_path"]
            
            temp_file = QFile(temp_path)
            if temp_file.exists():
                final_file = QFile(final_path)
                if final_file.exists():
                    final_file.remove()
                if not temp_file.rename(final_path):
                    raise Exception("Rename failed")
            
            self.downloadCompleted.emit(url_str, final_path)
            
        except Exception as e:
            self.downloadError.emit(url_str, f"Download completion error: {str(e)}")
        finally:
            self._cleanup_download(url_str)

    def _handle_download_error(self, url_str, reply, error):
        if url_str not in self._active_downloads:
            return
            
        if error == QNetworkReply.OperationCanceledError:
            return
                
        self.downloadError.emit(url_str, reply.errorString())
        self._cleanup_download(url_str)
        
    def _safe_abort_reply(self, reply, url_str):
        try:
            if reply.isRunning():
                reply.abort()
            self._cleanup_reply(reply, url_str)
        except Exception as e:
            self.downloadError.emit(url_str, f"Error aborting reply: {str(e)}")

    def _cleanup_reply(self, reply, url_str):
        try:
            reply.deleteLater()
        except Exception as e:
            self.downloadError.emit(url_str, f"Error deleting reply: {str(e)}")

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

    def _cleanup_download(self, url_str):
        if url_str not in self._active_downloads:
            return
            
        download_info = self._active_downloads.pop(url_str, None)
        if not download_info:
            return

        # 清理文件资源
        if "file" in download_info:
            try:
                if download_info["file"].isOpen():
                    download_info["file"].close()
                if not download_info.get("is_cancelled", False) and "temp_path" in download_info:
                    temp_file = QFile(download_info["temp_path"])
                    if temp_file.exists():
                        temp_file.remove()
            except Exception as e:
                self.downloadError.emit(url_str, f"Error cleaning up file: {str(e)}")

        # 清理网络回复
        if "reply" in download_info and download_info["reply"]:
            reply = download_info["reply"]
            try:
                if reply.isRunning():
                    reply.abort()
                reply.deleteLater()
            except Exception as e:
                self.downloadError.emit(url_str, f"Error cleaning up reply: {str(e)}")

    def _get_filename_from_url(self, url_str):
        url = QUrl(url_str)
        path = url.path()
        if path:
            return path.split('/')[-1]
        return "download"

    @Slot(QUrl, result=float)
    def getDownloadProgress(self, url):
        url_str = url.toString()
        if url_str in self._active_downloads:
            bytesReceived = self._active_downloads[url_str]["bytes_received"]
            reply = self._active_downloads[url_str].get("reply")
            bytesTotal = reply.header(QNetworkRequest.ContentLengthHeader) if reply else 0
            return (bytesReceived / bytesTotal * 100) if bytesTotal > 0 else 0
        return 0

    @Slot(QUrl, result=float)
    def getDownloadSpeed(self, url):
        url_str = url.toString()
        if url_str in self._active_downloads:
            download_info = self._active_downloads[url_str]
            elapsed = download_info["timer"].elapsed() / 1000.0  # 转换为秒
            return download_info["bytes_received"] / max(0.001, elapsed)
        return 0

    @Slot(QUrl, result=str)
    def getDownloadFilename(self, url):
        url_str = url.toString()
        return self._active_downloads.get(url_str, {}).get("filename", "")

    @Slot(result=list)
    def getActiveDownloads(self):
        return list(self._active_downloads.keys())