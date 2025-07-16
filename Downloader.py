import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from Data.Code.DownloadingPage import DownloadingPage
from Data.Code.DownloadedPage import DownloadedPage
from Data.Code.SettingPage import Settings

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    
    engine = QQmlApplicationEngine()

    engine.rootContext().setContextProperty("downloadingPageBackend", DownloadingPage())
    engine.rootContext().setContextProperty("downloadedPageBackend", DownloadedPage())
    engine.rootContext().setContextProperty("settingsBackend", Settings())

    engine.load("Data/QML/Main.qml") 
    
    if not engine.rootObjects():
        sys.exit(-1)
    
    sys.exit(app.exec())