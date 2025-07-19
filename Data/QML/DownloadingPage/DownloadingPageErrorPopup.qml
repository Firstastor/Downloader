import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

Popup {
    width: 300
    height: 150
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    
    property alias message: errorMessage.text
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 20
        anchors.margins: 20
        
        Label {
            id: errorMessage
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignCenter
            horizontalAlignment: Text.AlignHCenter
            text: message
            color: "red"
            font.bold: true
            wrapMode: Text.Wrap
        }
        
        Button {
            Layout.alignment: Qt.AlignCenter
            text: qsTr("OK")
            onClicked: {
                errorPopup.close();
            }
        }
    }
}