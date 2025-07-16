import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts

ColumnLayout {
    id: root

    // URL 输入框和下载按钮
    RowLayout {
        Layout.fillWidth: true
        
        TextField {
            id: urlInput
            Layout.fillWidth: true
            placeholderText: "Enter URL"
            selectByMouse: true
        }

        Button {
            text: "Download"
            onClicked: {
                if (urlInput.text.trim() !== "") {
                    downloadingPageBackend.startDownload(urlInput.text)
                    urlInput.clear()
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
                        text: model.filename
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                    }

                    Button {
                        text: "Cancel"
                        onClicked: {
                            downloadingPageBackend.cancelDownload(model.url)
                        }
                    }
                }

                ProgressBar {
                    value: model.progress / 100
                    Layout.fillWidth: true
                }

                RowLayout {
                    Label {
                        text: formatSpeed(model.speed)
                    }
                
                    Label {
                        text: "Progress: " + model.progress.toFixed(1) + "%"
                        horizontalAlignment: Text.AlignRight
                        Layout.fillWidth: true
                    }
                }
            }
        }
    }

    // 格式化速度显示
    function formatSpeed(speed) {
        if (speed <= 0) return "Calculating..."
        if (speed < 1024 * 1024) return "Speed: " + (speed / 1024).toFixed(2) + " KB/s"
        return "Speed: " + (speed / (1024 * 1024)).toFixed(2) + " MB/s"
    }

    // 初始化下载列表
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
                speed: downloadingPageBackend.getDownloadSpeed(url)
            })
        }
    }

    // 组件加载时初始化
    Component.onCompleted: {
        initializeDownloads()
    }

    // 连接后端信号
    Connections {
        target: downloadingPageBackend

        function onDownloadStarted(url, filename, savePath) {
            for (var i = 0; i < downloadModel.count; i++) {
                if (downloadModel.get(i).url === url) return
            }
            
            downloadModel.append({
                url: url,
                filename: filename,
                savePath: savePath,
                progress: 0,
                speed: 0
            })
        }

        function onDownloadProgress(url, progress, speed) {
            for (var i = 0; i < downloadModel.count; i++) {
                if (downloadModel.get(i).url === url) {
                    downloadModel.set(i, {
                        url: url,
                        filename: downloadModel.get(i).filename,
                        savePath: downloadModel.get(i).savePath,
                        progress: progress,
                        speed: speed
                    })
                    break
                }
            }
        }

        function onDownloadCompleted(url, savePath) {
            removeDownloadItem(url)
            if (typeof downloadedPageBackend !== "undefined") {
                downloadedPageBackend.addDownload(url, savePath.split("/").pop())
            }
        }

        function onDownloadError(url, errorMessage) {
            for (var i = 0; i < downloadModel.count; i++) {
                if (downloadModel.get(i).url === url) {
                    downloadModel.setProperty(i, "filename", "Error: " + errorMessage)
                    break
                }
            }
        }

        function onDownloadCancelled(url) {
            removeDownloadItem(url)
        }
    }

    // 移除下载项
    function removeDownloadItem(url) {
        for (var i = 0; i < downloadModel.count; i++) {
            if (downloadModel.get(i).url === url) {
                downloadModel.remove(i)
                break
            }
        }
    }

    // 当页面变为可见时刷新列表
    Connections {
        target: root
        function onVisibleChanged() {
            if (root.visible) {
                initializeDownloads()
            }
        }
    }
}