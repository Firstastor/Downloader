import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

ColumnLayout {
    // Error popup component
    Popup {
        id: errorPopup
        width: 300
        height: 150
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        
        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            
            Label {
                id: errorMessage
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                color: "red"
            }
            
            Button {
                text: "OK"
                Layout.alignment: Qt.AlignHCenter
                onClicked: errorPopup.close()
            }
        }
    }

    function showError(message) {
        errorMessage.text = message
        errorPopup.open()
    }

    // URL input and download button
    RowLayout {
        Layout.fillWidth: true
        
        TextField {
            id: urlInput
            Layout.fillWidth: true
            placeholderText: "Enter download URL"
            selectByMouse: true
        }

        Button {
            text: "Download"
            onClicked: {
                const url = urlInput.text.trim()
                if (url) {
                    if (isDuplicateUrl(url)) {
                        showError("This download is already in progress")
                    } else if (downloadingPageBackend.isUrlInHistory(url)) {
                        showError("This file has already been downloaded")
                    } else {
                        downloadingPageBackend.startDownload(url)
                        urlInput.clear()
                    }
                }
            }
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

    // Download list view
    ListView {
        id: downloadList
        Layout.fillWidth: true
        Layout.fillHeight: true
        spacing: 5
        model: ListModel { id: downloadModel }

        delegate: Frame {
            width: downloadList.width
            padding: 10

            ColumnLayout {
                width: parent.width

                RowLayout {
                    Label {
                        text: model.filename
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                        color: model.isError ? "red" : palette.text
                    }

                    Button {
                        text: "Cancel"
                        enabled: !model.isError && !model.isCompleted
                        onClicked: downloadingPageBackend.cancelDownload(model.url)
                    }
                }

                ProgressBar {
                    value: model.progress / 100
                    Layout.fillWidth: true
                    visible: !model.isError && !model.isCompleted
                }

                RowLayout {
                    visible: !model.isError && !model.isCompleted
                    Label { text: formatSpeed(model.speed) }
                
                    Label {
                        text: `Progress: ${model.progress.toFixed(1)}%`
                        horizontalAlignment: Text.AlignRight
                        Layout.fillWidth: true
                    }
                }

                Label {
                    visible: model.isError
                    text: model.errorMessage
                    color: "red"
                    Layout.fillWidth: true
                }

                Label {
                    visible: model.isCompleted
                    text: "Download completed!"
                    color: "green"
                    Layout.fillWidth: true
                }
            }
        }
    }

    function formatSpeed(speed) {
        if (speed <= 0) return "Starting..."
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
                savePath: "",
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
                downloadedPageBackend.addDownload(url, savePath.split("/").pop())
            }
        }

        function onDownloadError(url, errorMessage) {
            // 先更新模型再显示弹窗，避免阻塞
            for (let i = 0; i < downloadModel.count; i++) {
                if (downloadModel.get(i).url === url) {
                    downloadModel.set(i, {
                        url: url,
                        filename: downloadModel.get(i).filename,
                        savePath: downloadModel.get(i).savePath,
                        progress: downloadModel.get(i).progress,
                        speed: 0, // 重置速度为0
                        isError: true,
                        isCompleted: false, // 确保完成状态为false
                        errorMessage: errorMessage
                    })
                    break
                }
            }
            
            // 使用定时器避免阻塞UI
            Qt.callLater(() => {
                showError(errorMessage)
                errorCleanupTimer.start() // 确保自动清理定时器启动
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

