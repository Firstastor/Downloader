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
    property bool isPaused: false
    property alias errorMessage: errorLabel.text
    property bool canCancel: !isError && !isCompleted
    property bool canPause: canCancel && !isPaused
    property bool canResume: canCancel && isPaused
    
    signal cancelRequested()
    signal pauseRequested()
    signal resumeRequested()
    
    width: ListView.view ? ListView.view.width : parent.width
    padding: 10



    ColumnLayout {
        width: parent.width

        RowLayout {
            Label {
                id: filenameLabel
                elide: Text.ElideMiddle
                Layout.fillWidth: true
                color: isError ? "red" : (isPaused ? "orange" : palette.text)
            }

            Button {
                text: qsTr("Pause")
                visible: canPause
                onClicked: pauseRequested()
            }

            Button {
                text: qsTr("Resume")
                visible: canResume
                onClicked: resumeRequested()
            }

            Button {
                text: qsTr("Cancel")
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

        Label {
            visible: isPaused
            text: qsTr("Download paused")
            color: "orange"
            Layout.fillWidth: true
        }
    }
}