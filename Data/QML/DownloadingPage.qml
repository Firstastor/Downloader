import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

ColumnLayout {

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

                // 文件名和删除按钮
                RowLayout {
                    Label {
                        text: filename
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                    }

                    Button {
                        text: "Cancel"
                        onClicked: {
                            downloadingPageBackend.cancelDownload(url)
                            downloadModel.remove(index)
                        }
                    }
                }

                // 进度条
                ProgressBar {
                    value: progress / 100 
                    Layout.fillWidth: true
                }

                // 下载速度和进度文本
                RowLayout {
                    Label {
                        text: {
                            if (speed <= 0) {
                                return "Calculating..."
                            } else if (speed < 1024 * 1024) {
                                return "Speed: " + (speed / 1024).toFixed(2) + " KB/s"
                            } else {
                                return "Speed: " + (speed / (1024 * 1024)).toFixed(2) + " MB/s"
                            }
                        }
                    }
                
                    Label {
                        text: "Progress: " + progress.toFixed(1) + "%"
                        horizontalAlignment: Text.AlignRight
                        Layout.fillWidth: true
                    }
                }
            }
        }
    }

    // 连接后端信号
    Connections {
        target: downloadingPageBackend

        function onDownloadStarted(url, filename, savePath) {
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
                    downloadModel.setProperty(i, "progress", progress)
                    downloadModel.setProperty(i, "speed", speed)
                    break
                }
            }
        }

        function onDownloadCompleted(url, savePath) {
            // 通知 DownloadedPage 添加记录
            downloadedPageBackend.addDownload(url, savePath.split("/").pop())
            
            // 从下载列表中移除
            for (var i = 0; i < downloadModel.count; i++) {
                if (downloadModel.get(i).url === url) {
                    downloadModel.remove(i)
                    break
                }
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
    }
}