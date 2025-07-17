import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

ColumnLayout {
    // 错误弹窗
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

    function showErrorPopup(message) {
        errorMessage.text = message
        errorPopup.open()
    }

    // URL 输入框和下载按钮
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
                if (urlInput.text.trim() !== "") {
                    // 先检查是否已经在下载列表中
                    var isDuplicate = false;
                    for (var i = 0; i < downloadModel.count; i++) {
                        if (downloadModel.get(i).url === urlInput.text) {
                            isDuplicate = true;
                            break;
                        }
                    }
                    
                    if (isDuplicate) {
                        showErrorPopup("This download is already in progress");
                    } else {
                        downloadingPageBackend.startDownload(urlInput.text);
                        urlInput.clear();
                    }
                }
            }
        }
    }

    // 下载项列表
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
                        id: filenameLabel
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
                    Label {
                        text: formatSpeed(model.speed)
                    }
                
                    Label {
                        text: "Progress: " + model.progress.toFixed(1) + "%"
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
        if (speed < 1024) return speed.toFixed(0) + " B/s"
        if (speed < 1024 * 1024) return (speed / 1024).toFixed(1) + " KB/s"
        return (speed / (1024 * 1024)).toFixed(1) + " MB/s"
    }

    function initializeDownloads() {
        downloadModel.clear()
        var downloads = downloadingPageBackend.getActiveDownloads()
        for (var i = 0; i < downloads.length; i++) {
            var url = downloads[i]
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
        }
    }

    Component.onCompleted: initializeDownloads()

    Timer {
        id: errorCleanupTimer
        interval: 5000  
        repeat: true
        onTriggered: {
            var itemsToRemove = []
            for (var i = 0; i < downloadModel.count; i++) {
                var item = downloadModel.get(i)
                if (item.isError || item.isCompleted) {
                    itemsToRemove.push(i)
                }
            }
            for (var j = itemsToRemove.length - 1; j >= 0; j--) {
                downloadModel.remove(itemsToRemove[j])
            }
        }
    }

    Connections {
        target: downloadingPageBackend

        function onDownloadStarted(url, filename, savePath) {
            // 这个信号现在只会在通过检查后才会触发，所以不需要重复检查
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
            for (var i = 0; i < downloadModel.count; i++) {
                if (downloadModel.get(i).url === url) {
                    downloadModel.setProperty(i, "progress", progress)
                    downloadModel.setProperty(i, "speed", speed)
                    break
                }
            }
        }

        function onDownloadCompleted(url, savePath) {
            for (var i = 0; i < downloadModel.count; i++) {
                if (downloadModel.get(i).url === url) {
                    downloadModel.setProperty(i, "isCompleted", true)
                    downloadModel.setProperty(i, "progress", 100)
                    errorCleanupTimer.start()
                    break
                }
            }
            if (typeof downloadedPageBackend !== "undefined") {
                downloadedPageBackend.addDownload(url, savePath.split("/").pop())
            }
        }

        function onDownloadError(url, errorMessage) {
            showErrorPopup(errorMessage)
            
            for (var i = 0; i < downloadModel.count; i++) {
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
                    errorCleanupTimer.start()
                    break
                }
            }
        }

        function onDownloadCancelled(url) {
            removeDownloadItem(url)
        }
    }

    function removeDownloadItem(url) {
        for (var i = 0; i < downloadModel.count; i++) {
            if (downloadModel.get(i).url === url) {
                downloadModel.remove(i)
                break
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
