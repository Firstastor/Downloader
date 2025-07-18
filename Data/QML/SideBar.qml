import QtQuick
import QtQuick.Controls 
import QtQuick.Controls.FluentWinUI3 
import QtQuick.Layouts
import QtQuick.Window 

// 侧边栏
Rectangle{

    signal switchPage(int index)

    ColumnLayout{

        property int currentIndex: 0

        Button {
            id: pushbtndownload
            icon.source: "../Image/download.png"
            display: AbstractButton.TextUnderIcon
            text:"Download"
            flat:true
            onClicked: switchPage(0)
        }

        Button {
            id: pushbtnsetting
            icon.source: "../Image/setting.png"
            display: AbstractButton.TextUnderIcon
            text:"Setting"
            flat:true
            onClicked: switchPage(1)
        }
    }
}
