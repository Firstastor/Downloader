import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

ColumnLayout {

    // 下载历史列表
    ListView {
        id: historyList
        Layout.fillWidth: true
        Layout.fillHeight: true
        spacing: 5
        model: downloadedPageBackend.getDownloadsList()

        delegate: Frame {
            width: historyList.width
            padding: 10

            ColumnLayout {
                width: parent.width

                // 文件名
                Label {
                    text: modelData.filename
                    elide: Text.ElideMiddle
                    Layout.fillWidth: true
                }

                // 操作按钮行
                RowLayout {
                    Button {
                        text: "Open"
                        onClicked: Qt.openUrlExternally(downloadedPageBackend.getFileUrl(modelData.filename))
                    }

                    Button {
                        text: "Open Folder"
                        onClicked: Qt.openUrlExternally(downloadedPageBackend.getFolderUrl(modelData.filename))
                    }

                    Button {
                        text: "Delete"
                        onClicked: {
                            downloadedPageBackend.removeDownload(modelData.url)
                        }
                    }
                }

            }
        }
    }

    // 连接后端信号
    Connections {
        target: downloadedPageBackend
        function onDownloadsChanged() {
            historyList.model = downloadedPageBackend.getDownloadsList()
        }
    }
    
    // 监听设置变化
    Connections {
        target: settings
        function onDownloadFolderChanged() {
            downloadedPageBackend.downloadFolder = settings.downloadFolder
        }
    }
}