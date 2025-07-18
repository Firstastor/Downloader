import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

ColumnLayout {
    id: root
    
    DownloadingPageErrorPopup {
        id: errorPopup
    }

    function showError(message) {
        errorPopup.message = message
        errorPopup.open()
    }

    DownloadingPageControls {
        id: downloadControls
        Layout.fillWidth: true
        
        onDownloadRequested: function(url) {
            console.log("[1] Download requested:", url)
            if (isDuplicateUrl(url)) {
                console.log("[2] Blocked: Duplicate in current downloads")
                showError(qsTr("This download is already in progress"))
                return
            }
            if (downloadingPageBackend.isUrlInHistory(url)) {
                console.log("[3] Blocked: Found in history")
                showError(qsTr("This file has already been downloaded"))
                return
            }
            console.log("[4] Starting download...")
            downloadingPageBackend.startDownload(url)
            downloadControls.clearUrl()
        }
    }

    function isDuplicateUrl(url) {
        for (let i = 0; i < downloadModel.count; i++) {
            if (downloadModel.get(i).url === url) {
                return true
            }
        }
        return false
    }

    ListView {
        id: downloadList
        Layout.fillWidth: true
        Layout.fillHeight: true
        spacing: 5
        model: ListModel { id: downloadModel }

        delegate: DownloadingPageItemDelegate {
            filename: model.filename
            progress: model.progress / 100
            speed: root.formatSpeed(model.speed)
            progressText: qsTr("Progress: %1%").arg(model.progress.toFixed(1))
            isError: model.isError
            isCompleted: model.isCompleted
            errorMessage: model.errorMessage
            
            onCancelRequested: downloadingPageBackend.cancelDownload(model.url)
        }
    }

    function formatSpeed(speed) {
        if (speed <= 0) return qsTr("Calculating...")
        if (speed < 1024) return `${speed.toFixed(0)} B/s`
        if (speed < 1024 * 1024) return `${(speed / 1024).toFixed(1)} KB/s`
        return `${(speed / (1024 * 1024)).toFixed(1)} MB/s`
    }

    function initializeDownloads() {
        downloadModel.clear()
        const downloads = downloadingPageBackend.getActiveDownloads()
        downloads.forEach(url => {
            downloadModel.append({
                url: url,
                filename: downloadingPageBackend.getDownloadFilename(url) || "Unknown",
                savePath: downloadingPageBackend.getDownloadSavePath(url) || "",
                progress: downloadingPageBackend.getDownloadProgress(url),
                speed: downloadingPageBackend.getDownloadSpeed(url),
                isError: false,
                isCompleted: false,
                errorMessage: ""
            })
        })
    }

    Component.onCompleted: initializeDownloads()

    Timer {
        interval: 5000
        repeat: true
        running: true
        onTriggered: {
            for (let i = downloadModel.count - 1; i >= 0; i--) {
                const item = downloadModel.get(i)
                if (item.isError || item.isCompleted) {
                    downloadModel.remove(i)
                }
            }
        }
    }

    Connections {
        target: downloadingPageBackend

        function onDownloadStarted(url, filename, savePath) {
            downloadModel.append({
                url: url,
                filename: filename,
                savePath: savePath,
                progress: 0.1,
                speed: 0,
                isError: false,
                isCompleted: false,
                errorMessage: ""
            })
        }

        function onDownloadProgress(url, progress, speed) {
            for (let i = 0; i < downloadModel.count; i++) {
                if (downloadModel.get(i).url === url) {
                    downloadModel.setProperty(i, "progress", progress)
                    downloadModel.setProperty(i, "speed", speed)
                    break
                }
            }
        }

        function onDownloadCompleted(url, savePath) {
            for (let i = 0; i < downloadModel.count; i++) {
                if (downloadModel.get(i).url === url) {
                    downloadModel.setProperty(i, "isCompleted", true)
                    downloadModel.setProperty(i, "progress", 100)
                    break
                }
            }
            if (typeof downloadedPageBackend !== "undefined") {
                const filename = savePath.split("/").pop()
                const folder = savePath.substring(0, savePath.lastIndexOf("/"))
                const file = Qt.resolvedUrl(savePath)
                if (file.toString().length > 0) {
                    downloadedPageBackend.addDownload(url, filename, folder)
                }
            }
        }

        function onDownloadError(url, errorMessage) {
            for (let i = 0; i < downloadModel.count; i++) {
                if (downloadModel.get(i).url === url) {
                    downloadModel.set(i, {
                        url: url,
                        filename: downloadModel.get(i).filename,
                        savePath: downloadModel.get(i).savePath,
                        progress: downloadModel.get(i).progress,
                        speed: 0,
                        isError: true,
                        isCompleted: false,
                        errorMessage: errorMessage
                    })
                    break
                }
            }
            
            Qt.callLater(() => {
                showError(errorMessage)
            })
        }

        function onDownloadCancelled(url) {
            for (let i = 0; i < downloadModel.count; i++) {
                if (downloadModel.get(i).url === url) {
                    downloadModel.remove(i)
                    break
                }
            }
        }
    }

    Connections {
        target: downloadingLoader
        function onVisibleChanged() {
            if (downloadingLoader.visible) {
                initializeDownloads()
            }
        }
    }
}