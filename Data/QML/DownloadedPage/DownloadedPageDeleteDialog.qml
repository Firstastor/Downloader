import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

Dialog {
    id: deleteDialog
    title: qsTr("Confirm Delete") 
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    width: Math.min(400, parent.width * 0.8)  
    
    property string url
    property string filename
    
    onAboutToShow: {
        if (!filename) console.error("Filename not specified")
    }

    ColumnLayout {
        spacing: 10
        anchors.fill: parent
        anchors.margins: 10
        
        Label {
            text: qsTr("Are you sure you want to delete:")
            Layout.alignment: Qt.AlignHCenter
        }
        
        Label {
            text: deleteDialog.filename
            font.bold: true
            elide: Text.ElideMiddle
            maximumLineCount: 2
            wrapMode: Text.Wrap
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
            Layout.maximumWidth: parent.width
        }
    }

    onAccepted: {
        if (url) {
            downloadedPageBackend.removeDownload(url)
        } else {
            console.error("Invalid URL specified for deletion")
        }
    }
}