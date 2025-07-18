import QtQuick
import QtQuick.Controls
import QtQuick.Controls.FluentWinUI3
import QtQuick.Layouts
import QtQuick.Window

Frame {
    property alias filename: filenameLabel.text
    property alias progress: progressBar.value
    property alias speed: speedLabel.text
    property alias progressText: progressLabel.text
    property bool isError: false
    property bool isCompleted: false
    property alias errorMessage: errorLabel.text
    property bool canCancel: !isError && !isCompleted
    
    signal cancelRequested()
    
    width: ListView.view ? ListView.view.width : parent.width
    padding: 10

    ColumnLayout {
        width: parent.width

        RowLayout {
            Label {
                id: filenameLabel
                elide: Text.ElideMiddle
                Layout.fillWidth: true
                color: isError ? "red" : palette.text
            }

            Button {
                text:  qsTr("Cancel")
                enabled: canCancel
                onClicked: cancelRequested()
            }
        }

        ProgressBar {
            id: progressBar
            Layout.fillWidth: true
            visible: canCancel
        }

        RowLayout {
            visible: canCancel
            Label { id: speedLabel }
        
            Label {
                id: progressLabel
                horizontalAlignment: Text.AlignRight
                Layout.fillWidth: true
            }
        }

        Label {
            id: errorLabel
            visible: isError
            color: "red"
            Layout.fillWidth: true
        }

        Label {
            visible: isCompleted
            text: qsTr("Download completed")
            color: "green"
            Layout.fillWidth: true
        }
    }
}