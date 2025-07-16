import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Dialogs
import QtQuick.Layouts


GroupBox {

    ColumnLayout {

        width: parent.width
        
        RowLayout {
            Layout.fillWidth: true
            Label {
                text: "Download Folder:"
            }

            TextField {
                id: downloadFolderInput
                Layout.fillWidth: true
                text: settingsBackend.downloadFolder
                
                onEditingFinished: {
                    settingsBackend.downloadFolder = text
                }
                Keys.onReturnPressed: {
                    focus = false 
                }
                Keys.onEnterPressed: {
                    focus = false 
                }
            }

            Button {
                text: "Browse..."
                onClicked: folderDialog.open()
            }
        }
        
        Item { Layout.fillHeight: true }
    }
    
    FolderDialog {
        id: folderDialog
        currentFolder: settingsBackend.get_download_folder_url()
        onAccepted: {
            settingsBackend.downloadFolder = selectedFolder
            downloadFolderInput.text = settingsBackend.downloadFolder
        }
    }
}
