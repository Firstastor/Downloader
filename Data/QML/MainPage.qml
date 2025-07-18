import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

Page {
    property int currentPage: 0

    Loader {
        id: mainPageLoader
        anchors.fill: parent
        source: currentPage === 0 ? "DownloadPage.qml" : "SettingPage.qml"
    }
}