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
        Label {
            id: errorMessage
            text: message
            color: "red"
            font.bold: true
        }
        Button {
            text: qsTr("OK")
            onClicked: {
                errorPopup.close();
            }
        }
    }
}