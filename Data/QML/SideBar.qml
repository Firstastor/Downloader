import QtQuick
import QtQuick.Controls 
import QtQuick.Controls.FluentWinUI3 
import QtQuick.Layouts
import QtQuick.Window 

Rectangle {
    signal switchPage(int index)
    property int currentIndex: 0

    ColumnLayout {
        Button {
            id: pushbtndownload
            icon.source: "../Image/download.png"
            display: AbstractButton.TextUnderIcon
            text: qsTr("Download")
            flat: true
            highlighted: parent.parent.currentIndex === 0
            onClicked: {
                parent.parent.currentIndex = 0
                switchPage(0)
            }
        }

        Button {
            id: pushbtnsetting
            icon.source: "../Image/setting.png"
            display: AbstractButton.TextUnderIcon
            text: qsTr("Setting")
            flat: true
            highlighted: parent.parent.currentIndex === 1
            onClicked: {
                parent.parent.currentIndex = 1
                switchPage(1)
            }
        }
    }
}