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
        model: downloadedPageBackend.downloads

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
                        text: "Open File"
                        onClicked: {
                            var fileUrl = downloadedPageBackend.getFileUrl(modelData.filename)
                            if (fileUrl.toString() !== "") {
                                Qt.openUrlExternally(fileUrl)
                            } else {
                                console.log("无法获取文件URL")
                            }
                        }
                    }

                    Button {
                        text: "Open Folder"
                        onClicked: {
                            var folderUrl = downloadedPageBackend.getFolderUrl(modelData.filename)
                            if (folderUrl.toString() !== "") {
                                Qt.openUrlExternally(folderUrl)
                            } else {
                                console.log("无法获取文件夹URL")
                            }
                        }
                    }

                    Button {
                        text: "Delete"
                        onClicked: {
                            deleteDialog.url = modelData.url
                            deleteDialog.filename = modelData.filename
                            deleteDialog.open()
                        }
                    }
                }
            }
        }
    }

    // 删除确认对话框
    Dialog {
        id: deleteDialog
        title: "Confirm Delete"
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        
        property string url
        property string filename

        ColumnLayout {
            spacing: 10
            Label {
                text: "Are you sure you want to delete:"
            }
            Label {
                text: deleteDialog.filename
                font.bold: true
                elide: Text.ElideMiddle
                Layout.maximumWidth: 300
            }
        }

        onAccepted: {
            downloadedPageBackend.removeDownload(deleteDialog.url)
        }
    }

    // 连接后端信号
    Connections {
        target: downloadedPageBackend
        function onDownloadsChanged() {
            historyList.model = downloadedPageBackend.downloads
        }
    }
}