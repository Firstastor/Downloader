import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window 

// 系统栏
Rectangle {
    
    MouseArea {
        anchors.fill: parent
        property point clickPos: "0,0"
        onPressed: function(mouse) { clickPos = Qt.point(mouse.x, mouse.y) }
        onPositionChanged: function(mouse) {
            if (mainWindow.visibility !== Window.Maximized) {
                var delta = Qt.point(mouse.x - clickPos.x, mouse.y - clickPos.y)
                mainWindow.x += delta.x
                mainWindow.y += delta.y
            }
        }
        onDoubleClicked: mainWindow.visibility === Window.Maximized ? mainWindow.showNormal() : mainWindow.showMaximized()
    }

    Row {
        anchors.right: parent.right
        anchors.top: parent.top 
        spacing: 0

        Button {
            id: pushbtnWindowsMinimize
            width: 40
            height: 40
            text: "一"
            flat: true
            font.pixelSize: height * 0.3
            onClicked: mainWindow.showMinimized()
        }

        Button {
            id: pushbtnWindowsMaximize
            width: 40
            height: 40
            text: mainWindow.visibility === Window.Maximized ? "❐" : "口"
            flat: true
            font.pixelSize: height * 0.3
            onClicked: mainWindow.visibility === Window.Maximized ? mainWindow.showNormal() : mainWindow.showMaximized()
        }

        Button {
            id: pushbtnWindowsClose
            width: 40
            height: 40
            text: "X"
            flat: true
            font.pixelSize: height * 0.3
            onClicked: mainWindow.close()
        }
    }

    Label {
        anchors {
            horizontalCenter: parent.horizontalCenter
            top: parent.top 
            margins: 10
        }
        text: mainWindow.title
        font.pixelSize: 20
    }
}