import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

RowLayout {
    property alias urlText: urlInput.text
    
    signal downloadRequested(string url)
    signal showError(string message)
    
    function clearUrl() {
        urlInput.clear()
    }
    
    TextField {
        id: urlInput
        Layout.fillWidth: true
        placeholderText: qsTr("Enter download URL")
        selectByMouse: true
    }

    Button {
        text: qsTr("Download")
        onClicked: {
            const url = urlInput.text.trim()
            if (url) {
                downloadRequested(url)
            }
        }
    }
}