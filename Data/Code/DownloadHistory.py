import json
from PySide6.QtCore import QObject, Signal, Property, QDir, QFile, QDateTime

class DownloadHistory(QObject):
    historyChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._history_file = QDir(QDir.current()).filePath("Download_History.json")
        self._ensure_history_file()

    @Property(list, notify=historyChanged)
    def history(self):
        return self._history

    def _ensure_history_file(self):
        """确保历史文件存在"""
        if not QFile.exists(self._history_file):
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        self._load_history()

    def _load_history(self):
        """加载历史记录"""
        try:
            with open(self._history_file, 'r', encoding='utf-8') as f:
                self._history = json.load(f)
            self.historyChanged.emit()
        except (json.JSONDecodeError, FileNotFoundError):
            self._history = []

    def add_record(self, url, filename, filesize):
        """添加新记录"""
        if not any(d['url'] == url for d in self._history):
            self._history.append({
                'url': url,
                'filename': filename,
                'timestamp': QDateTime.currentSecsSinceEpoch(),
                'filesize': filesize
            })
            self._save_history()

    def remove_record(self, url):
        """移除记录"""
        self._history = [d for d in self._history if d['url'] != url]
        self._save_history()

    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, indent=4, ensure_ascii=False)
            self.historyChanged.emit()
        except IOError as e:
            print(f"保存历史记录失败: {e}")

    def clear_history(self):
        """清空历史"""
        self._history = []
        self._save_history()