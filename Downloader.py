import sys

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from Data.Code.DownloadingPage import DownloadingPage
from Data.Code.DownloadedPage import DownloadedPage
from Data.Code.DownloadHistory import DownloadHistory
from Data.Code.SettingPage import Settings

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    app.setWindowIcon(QIcon("Data/Image/downloader.ico"))
    settings = Settings()
    downloadingPage = DownloadingPage(settings)
    downloadedPage = DownloadedPage(settings)
    downloadHistory = DownloadHistory()
    
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("settingsBackend", settings)
    engine.rootContext().setContextProperty("downloadingPageBackend", downloadingPage)
    engine.rootContext().setContextProperty("downloadedPageBackend", downloadedPage)
    engine.rootContext().setContextProperty("downloadHistoryBackend", downloadHistory)
    engine.load("Data/QML/Main.qml") 
    
    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())