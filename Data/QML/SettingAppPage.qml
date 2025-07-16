import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Dialogs
import QtQuick.Layouts

GroupBox {
    ColumnLayout {
        width: parent.width
        spacing: 15

        // 下载目录设置部分
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
                text: settingsBackend.downloadFolder
                placeholderText: "Enter download folder path (e.g. C:\\Downloads)"
                
                // 编辑完成时验证路径
                onEditingFinished: {
                    if (settingsBackend.isValidPath(text)) {
                        settingsBackend.downloadFolder = text
                    } else {
                        text = settingsBackend.downloadFolder
                        invalidPathToast.text = "Invalid path! Contains illegal characters or format"
                        invalidPathToast.open()
                    }
                }
                
                Keys.onReturnPressed: focus = false
                Keys.onEnterPressed: focus = false
            }

                Button {
                    text: "Browse..."
                    onClicked: folderDialog.open()
                }
            }
        }

        // 网络设置部分
        GridLayout {
            columns: 2
            columnSpacing: 10
            rowSpacing: 10
            Layout.fillWidth: true

            Label {
                text: "Download Speed Limit:"
                Layout.alignment: Qt.AlignRight
            }

            RowLayout {
                SpinBox {
                    id: speedLimitInput
                    from: 0
                    to: 1024000
                    value: settingsBackend.speedLimit
                    onValueModified: settingsBackend.speedLimit = value
                    editable: true
                    stepSize: 100
                    Layout.fillWidth: true
                    Keys.onReturnPressed: focus = false
                    Keys.onEnterPressed: focus = false

                    // 自定义显示文本
                    property string prefix: "Max Speed: "
                    property string suffix: " KB"
                    
                    validator: IntValidator {
                        bottom: speedLimitInput.from
                        top: speedLimitInput.to
                    }

                    textFromValue: function(value) {
                        return value === 0 ? "Unlimited" : (prefix + value + suffix)
                    }

                    valueFromText: function(text) {
                        if (text === "Unlimited") return 0
                        return parseInt(text.replace(prefix, "").replace(suffix, ""))
                    }

                    onActiveFocusChanged: {
                        if (activeFocus) {
                            const rawValue = value === 0 ? "" : value.toString()
                            contentItem.text = rawValue
                        } else {
                            contentItem.text = textFromValue(value)
                        }
                    }
                }
            }
        }
        
        // 并发下载设置部分（使用 Slider）
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
                    value: settingsBackend.concurrentDownloads
                    onMoved: settingsBackend.concurrentDownloads = value
                    stepSize: 1
                    snapMode: Slider.SnapAlways // 确保取整
                    Layout.fillWidth: true
                }
                Label {
                    text: concurrentDownloadsInput.value.toFixed(0)
                }
            }
        }

        // 单文件下载线程数设置（使用 Slider）
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
                    value: settingsBackend.maxThreadsPerDownload
                    onMoved: settingsBackend.maxThreadsPerDownload = value
                    stepSize: 1
                    snapMode: Slider.SnapAlways
                    Layout.fillWidth: true
                }
                Label {
                    text: maxThreadsInput.value.toFixed(0)
                }
            }
        }

        Item { Layout.fillHeight: true }
    }

    // 文件夹选择对话框
    FolderDialog {
        id: folderDialog
        title: "Select Download Folder"
        onAccepted: {
            settingsBackend.downloadFolder = selectedFolder
            downloadFolderInput.text = settingsBackend.downloadFolder
        }
    }

    // 无效路径提示弹窗
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
            text: "Invalid folder path!"
            color: "red"
        }

        Timer {
            interval: 2000
            running: invalidPathToast.opened
            onTriggered: invalidPathToast.close()
        }
    }
}