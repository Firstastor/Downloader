import os
import re
import time
import hashlib
from pathlib import Path
from urllib.parse import urlparse, unquote
from PySide6.QtCore import QObject, Signal, Property, Slot, QUrl
from PySide6.QtQml import QmlElement
import requests
from concurrent.futures import ThreadPoolExecutor

QML_IMPORT_NAME = "io.downloader.downloading"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class DownloadingPage(QObject):
    # 信号定义
    downloadStarted = Signal(str, str, str)  # url, filename, save_path
    downloadProgress = Signal(str, float, float)  # url, progress, speed (bytes/sec)
    downloadCompleted = Signal(str, str, str)  # url, save_path, file_hash
    downloadError = Signal(str, str)  # url, error_message
    downloadCancelled = Signal(str)  # url

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_downloads = {}
        self._download_folder = ""
        self.thread_pool = ThreadPoolExecutor(max_workers=64)
        self.session = requests.Session()

    @Property(str)
    def downloadFolder(self):
        return self._download_folder

    @downloadFolder.setter
    def downloadFolder(self, value):
        """设置下载文件夹路径"""
        self._download_folder = value

    def _ensure_directory_exists(self, path):
        """确保目标目录存在"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.downloadError.emit("", f"创建目录失败: {str(e)}")
            return False

    def _get_safe_filename(self, filename):
        """生成安全的文件名"""
        if not filename:
            return "download"
        
        try:
            filename = unquote(filename)
        except:
            pass
        
        keepchars = (' ', '-', '_', '.', '(', ')', '[', ']')
        safe_name = "".join(
            c for c in filename 
            if c.isalnum() or c in keepchars or '\u4e00' <= c <= '\u9fff'
        ).strip()
        
        safe_name = ' '.join(safe_name.split())
        safe_name = safe_name[:255]
        
        if safe_name.startswith('.'):
            safe_name = "download" + safe_name
            
        return safe_name

    def _get_available_filename(self, desired_path):
        """处理文件名冲突"""
        if not os.path.exists(desired_path):
            return desired_path
            
        directory, filename = os.path.split(desired_path)
        base, ext = os.path.splitext(filename)
        counter = 1
        
        while True:
            new_path = os.path.join(directory, f"{base}_{counter}{ext}")
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    def _get_filename_from_response(self, response):
        """从响应头获取文件名"""
        content_disp = response.headers.get('content-disposition', '')
        if 'filename=' in content_disp:
            match = re.search(r'filename=["\']?(.+?)["\']?$', content_disp)
            if match:
                return match.group(1)
        return None

    def _get_filename_from_url(self, url):
        """从URL提取文件名"""
        try:
            path = urlparse(url).path
            filename = os.path.basename(path)
            return filename if filename else "download"
        except:
            return "download"

    def _calculate_file_hash(self, file_path):
        """计算文件哈希值"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _download_file(self, url, save_path):
        """执行下载任务"""
        temp_path = f"{save_path}.downloading"
        final_path = None
        downloaded = 0
        total_size = 0
        start_time = time.time()
        
        try:
            # 检查是否已被取消
            if url not in self._active_downloads:
                raise Exception("Download cancelled before start")

            with self.session.get(url, stream=True, timeout=(30, 60)) as response:
                response.raise_for_status()
                
                # 再次检查是否已被取消
                if url not in self._active_downloads:
                    raise Exception("Download cancelled during connection")

                # 获取文件信息
                total_size = int(response.headers.get('content-length', 0))
                filename = (
                    self._get_filename_from_response(response) or 
                    self._get_filename_from_url(response.url)
                )
                safe_name = self._get_safe_filename(filename)
                desired_path = os.path.join(os.path.dirname(save_path), safe_name)
                final_path = self._get_available_filename(desired_path)
                temp_path = f"{final_path}.downloading"
                
                # 确保目录存在
                if not self._ensure_directory_exists(final_path):
                    raise Exception("Failed to create directory")

                # 开始下载
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        # 检查是否已被取消
                        if url not in self._active_downloads:
                            raise Exception("Download cancelled by user")
                        
                        # 检查是否为空块（连接结束）
                        if not chunk:
                            if total_size > 0 and downloaded < total_size:
                                raise Exception("Incomplete download: connection closed prematurely")
                            break
                            
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 计算进度和速度
                        elapsed = time.time() - start_time
                        progress = (downloaded / total_size * 100) if total_size > 0 else (
                            (downloaded / (downloaded + 1)) * 100)  # 避免除以零
                        speed = downloaded / max(0.001, elapsed)
                        self.downloadProgress.emit(url, progress, speed)
                
                # 验证文件完整性
                if total_size > 0 and os.path.getsize(temp_path) != total_size:
                    raise Exception(f"Size mismatch: expected {total_size}, got {os.path.getsize(temp_path)}")
                
                # 重命名为最终文件名
                os.replace(temp_path, final_path)
                
                # 计算文件哈希
                file_hash = self._calculate_file_hash(final_path)
                
                # 发送完成信号
                self.downloadCompleted.emit(url, final_path, file_hash)
                
        except Exception as e:
            error_msg = str(e)
            if "cancelled" in error_msg.lower():
                self.downloadCancelled.emit(url)
            else:
                self.downloadError.emit(url, f"下载错误: {error_msg}")
            raise  # 重新抛出异常以便线程池处理
        finally:
            self._active_downloads.pop(url, None)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    @Slot(str)
    def startDownload(self, url):
        """QML调用的下载接口"""
        if not url:
            self.downloadError.emit("", "URL不能为空")
            return

        if url in self._active_downloads:
            self.downloadError.emit(url, "下载已在进行中")
            return

        try:
            # 生成初始路径
            filename = self._get_filename_from_url(url)
            safe_name = self._get_safe_filename(filename)
            save_path = os.path.join(self._download_folder, safe_name)
            
            # 添加到活动下载
            self._active_downloads[url] = {
                "filename": safe_name,
                "save_path": save_path,
                "progress": 0,
                "speed": 0,
                "future": None
            }
            
            # 开始下载并存储future
            self.downloadStarted.emit(url, safe_name, save_path)
            future = self.thread_pool.submit(self._download_file, url, save_path)
            self._active_downloads[url]["future"] = future
            
            # 添加异常回调
            future.add_done_callback(lambda f: self._handle_download_future(url, f))
            
        except Exception as e:
            self.downloadError.emit(url, f"下载失败: {str(e)}")
            self._active_downloads.pop(url, None)

    def _handle_download_future(self, url, future):
        """处理下载完成的future"""
        if url not in self._active_downloads:
            return
            
        try:
            future.result()  # 如果出错会抛出异常
        except Exception as e:
            if "cancelled" not in str(e).lower():
                self.downloadError.emit(url, f"下载失败: {str(e)}")

    @Slot(str)
    def cancelDownload(self, url):
        """取消下载"""
        if url in self._active_downloads:
            # 取消future
            future = self._active_downloads[url].get("future")
            if future and not future.done():
                future.cancel()
            
            # 删除临时文件
            save_path = self._active_downloads[url]["save_path"]
            temp_path = f"{save_path}.downloading"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            
            # 发送取消信号
            self.downloadCancelled.emit(url)
            self._active_downloads.pop(url, None)

    @Slot(str, result=float)
    def getDownloadProgress(self, url):
        """获取下载进度"""
        return self._active_downloads.get(url, {}).get("progress", 0)

    @Slot(str, result=float)
    def getDownloadSpeed(self, url):
        """获取下载速度"""
        return self._active_downloads.get(url, {}).get("speed", 0)

    @Slot(result=list)
    def getActiveDownloads(self):
        """获取活动下载列表"""
        return list(self._active_downloads.keys())