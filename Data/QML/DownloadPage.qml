import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

Page {
    Frame {
        id: downloadPage
        anchors.fill: parent
    
        ColumnLayout {
            id: mainColumnLayout
            anchors.fill: parent
            spacing: 10
            
            TabBar {
                id: tabBar
                Layout.fillWidth: true
                
                TabButton { text: "Downloading" }
                TabButton { text: "Downloaded" }
            }
            
            StackLayout {
                id: stackLayout
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: tabBar.currentIndex
                
                Loader {
                    id: downloadingLoader
                    source: "DownloadingPage/DownloadingPage.qml"
                    active: true
                }

                Loader {
                    id: downloadedLoader
                    source: "DownloadedPage/DownloadedPage.qml"
                    active: true
                }
            }
        }
    }
}