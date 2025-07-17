import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from Data.Code.DownloadingPage import DownloadingPage
from Data.Code.DownloadedPage import DownloadedPage
from Data.Code.SettingPage import Settings

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)

    settings = Settings()
    downloadingPage = DownloadingPage(settings)
    downloadedPage = DownloadedPage()
    
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("settingsBackend", settings)
    engine.rootContext().setContextProperty("downloadingPageBackend", downloadingPage)
    engine.rootContext().setContextProperty("downloadedPageBackend", downloadedPage)
    
    engine.load("Data/QML/Main.qml") 
    
    if not engine.rootObjects():
        sys.exit(-1)
    
    def shutdown():
        settings.cleanup()
        engine.deleteLater()

    app.aboutToQuit.connect(shutdown)
    sys.exit(app.exec())