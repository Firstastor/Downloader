import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: mainWindow
    width: 1080
    height: 720
    visible: true
    title: "Downloader"
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.Window 

    Rectangle {
        id : background
        anchors.fill: parent
        color: palette.window
        radius: mainWindow.visibility === Window.FullScreen ? 0 : 20
        
        TitleBar {
            id: titleBar
            anchors.fill: parent
            color: "transparent"
        }

        Rectangle {
            id: titleBarLine
            width: parent.width
            y: 50
            height: 1
            color: palette.mid
        }
        
        SideBar{
            id: sideBar 
            width: 100
            anchors.top: titleBarLine.bottom
            anchors.left: parent.left
            anchors.margins: 10 
            onSwitchPage: (index) => {
                mainPage.currentPage = index;
            }       
        }

        MainPage {
            id: mainPage
            anchors.top: titleBarLine.bottom
            anchors.bottom: parent.bottom
            anchors.left: sideBar.right
            anchors.right: parent.right
            padding: 0
        }
    }
}