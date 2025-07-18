import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Dialogs
import QtQuick.Layouts

GroupBox {

    property bool backendAvailable: settingsBackend !== null

    ColumnLayout {
        width: parent.width
        spacing: 15

        GridLayout {
            columns: 2
            columnSpacing: 10
            rowSpacing: 10
            Layout.fillWidth: true

            Label {
                text: "Download Folder:"
                Layout.alignment: Qt.AlignRight
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                TextField {
                    id: downloadFolderInput
                    Layout.fillWidth: true
                    text: backendAvailable ? settingsBackend.downloadFolder : ""
                    placeholderText: "Enter download folder path (e.g. C:\\Downloads)"
                    enabled: backendAvailable
                    
                    onEditingFinished: {
                        if (backendAvailable && settingsBackend.isValidPath(text)) {
                            settingsBackend.downloadFolder = text
                        } else {
                            text = backendAvailable ? settingsBackend.downloadFolder : ""
                            invalidPathToast.text = "Invalid path! Contains illegal characters or format"
                            invalidPathToast.open()
                        }
                    }
                    
                    Keys.onReturnPressed: focus = false
                    Keys.onEnterPressed: focus = false
                }

                Button {
                    text: "Browse..."
                    onClicked: if (backendAvailable) folderDialog.open()
                    enabled: backendAvailable
                }
            }
        }

        GridLayout {
            columns: 2
            columnSpacing: 10
            rowSpacing: 10
            Layout.fillWidth: true

            Label {
                text: "Max Concurrent Downloads:"
                Layout.alignment: Qt.AlignRight
            }

            RowLayout {
                Slider {
                    id: concurrentDownloadsInput
                    from: 1
                    to: 10
                    value: backendAvailable ? settingsBackend.concurrentDownloads : 1
                    onMoved: if (backendAvailable) settingsBackend.concurrentDownloads = value
                    stepSize: 1
                    snapMode: Slider.SnapAlways
                    Layout.fillWidth: true
                    enabled: backendAvailable
                }
                Label {
                    text: concurrentDownloadsInput.value.toFixed(0)
                }
            }
        }

        GridLayout {
            columns: 2
            columnSpacing: 10
            rowSpacing: 10
            Layout.fillWidth: true

            Label {
                text: "Max Threads per Download:"
                Layout.alignment: Qt.AlignRight
            }

            RowLayout {
                Slider {
                    id: maxThreadsInput
                    from: 1
                    to: 64
                    value: backendAvailable ? settingsBackend.maxThreadsPerDownload : 1
                    onMoved: if (backendAvailable) settingsBackend.maxThreadsPerDownload = value
                    stepSize: 1
                    snapMode: Slider.SnapAlways
                    Layout.fillWidth: true
                    enabled: backendAvailable
                }
                Label {
                    text: maxThreadsInput.value.toFixed(0)
                }
            }
        }

        Item { Layout.fillHeight: true }
    }

    FolderDialog {
        id: folderDialog
        title: "Select Download Folder"
        onAccepted: {
            if (backendAvailable) {
                settingsBackend.downloadFolder = selectedFolder
                downloadFolderInput.text = settingsBackend.downloadFolder
            }
        }
    }

    Popup {
        id: invalidPathToast
        x: (parent.width - width) / 2
        y: parent.height - height - 20
        width: 200
        height: 60
        modal: false
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        property string text: "Invalid folder path!"

        Label {
            anchors.centerIn: parent
            text: invalidPathToast.text
            color: "red"
        }

        Timer {
            interval: 2000
            running: invalidPathToast.opened
            onTriggered: invalidPathToast.close()
        }
    }
}