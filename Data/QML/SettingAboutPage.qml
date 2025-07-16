import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

GroupBox {
    
    ColumnLayout {
        id: aboutContent
        width: parent.width
        spacing: 5

        Label {
            text: "Downloader"
            font.bold: true
            font.pixelSize: 16
        }
        Label { 
            text: "Version 0.0.2" 
            font.pixelSize: 14
        }
        Label {
            text: "© 2025 Downloader Team"
            font.pixelSize: 12
            opacity: 0.8
        }
    }
}