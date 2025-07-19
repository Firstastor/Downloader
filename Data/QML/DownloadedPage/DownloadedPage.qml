import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

ColumnLayout {
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

                Label {
                    text: modelData.filename
                    elide: Text.ElideMiddle
                    Layout.fillWidth: true
                }

                RowLayout {
                    Button {
                        text: "Open File"
                        onClicked: {
                            var fileUrl = downloadedPageBackend.getFileUrl(modelData.filename, modelData.folder)
                            if (fileUrl.toString() !== "") {
                                Qt.openUrlExternally(fileUrl)
                            } else {
                                console.log("Cannot get File URL")
                            }
                        }
                    }

                    Button {
                        text: "Open Folder"
                        onClicked: {
                            var folderUrl = downloadedPageBackend.getFolderUrl(modelData.filename, modelData.folder)
                            if (folderUrl.toString() !== "") {
                                Qt.openUrlExternally(folderUrl)
                            } else {
                                console.log("Cannot get File Folder URL")
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

    DownloadedPageDeleteDialog {
        id: deleteDialog
    }

    Connections {
        target: downloadedPageBackend
        function onDownloadsChanged() {
            historyList.model = downloadedPageBackend.downloads
        }
    }
}