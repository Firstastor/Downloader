import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Dialogs
import QtQuick.Layouts


Page {
    id: settingPage
    padding: 0

    Frame {
        anchors.fill: parent
        padding: 0
        
        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            SettingAppPage {
                id: settingAppPage
                title: "Application Settings"
                Layout.fillWidth: true
            }

            SettingAboutPage {
                id: settingAboutPage
                title: "About"
                Layout.fillWidth: true
            }
        }
    }


}