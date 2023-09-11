import sys
from PySide6.QtCore import QDir, QUrl, QSaveFile, Slot, QIODevice
from PySide6.QtWidgets import QWidget, QApplication, QLineEdit, QProgressBar, QPushButton, QVBoxLayout, QHBoxLayout, \
    QStyle, QFileDialog
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.link_box = QLineEdit()
        self.destination_box = QLineEdit()
        self.progress_bar = QProgressBar()
        self.start_button = QPushButton("Download")
        self.cancel_button = QPushButton("Cancel")

        self.link_box.setPlaceholderText("Download Link ...")
        self._open_folder_action = self.destination_box.addAction(
            self.style().standardIcon(QStyle.SP_DirOpenIcon), QLineEdit.TrailingPosition
        )
        self._open_folder_action.triggered.connect(self.on_open_folder)

        # horizontal layout for buttons
        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.start_button)
        horizontal_layout.addWidget(self.cancel_button)
        # main layout
        vertical_layout = QVBoxLayout(self)
        vertical_layout.addWidget(self.link_box)
        vertical_layout.addWidget(self.destination_box)
        vertical_layout.addWidget(self.progress_bar)
        vertical_layout.addLayout(horizontal_layout)

        # for sending network requests and receiving replies
        self.manager = QNetworkAccessManager(self)
        self.reply = None
        self.file = None

        self.start_button.clicked.connect(self.on_download)
        self.cancel_button.clicked.connect(self.on_cancel)

    @Slot
    def on_download(self):
        self.start_button.setDisabled(True)
        # Create destination file path
        url_file = QUrl(self.link_box.text())
        destination_path = QDir.fromNativeSeparators(self.destination_box.text().strip())
        destination_file = QDir(destination_path).filePath(url_file.fileName())
        # Create the file in write mode to append bytes
        self.file = QSaveFile(destination_file)
        if self.file.open(QIODevice.WriteOnly):

            # Start a GET HTTP request
            self.reply = self.manager.get(QNetworkRequest(url_file))
            self.reply.downloadProgress.connect(self.on_progress)
            self.reply.readyRead.connect(self.on_ready_read)
            self.reply.finished.connect(self.on_finished)
            self.reply.errorOccurred.connect(self.on_error)
        else:
            error = self.file.errorString()
            print(f"Cannot open device: {error}")

    @Slot(int, int)
    def on_progress(self, bytes_received: int, bytes_total: int):
        """ Update progress bar"""
        self.progress_bar.setRange(0, bytes_total)
        self.progress_bar.setValue(bytes_received)

    @Slot()
    def on_ready_read(self):
        """ Get available bytes and store them into the file"""
        if self.reply:
            if self.reply.error() == QNetworkReply.NoError:
                self.file.write(self.reply.readAll())

    @Slot()
    def on_finished(self):
        """ Delete reply and close the file"""
        if self.reply:
            self.reply.deleteLater()

        if self.file:
            self.file.commit()

        self.start_button.setDisabled(False)

    @Slot(QNetworkReply.NetworkError)
    def on_error(self):
        """ Show a message if an error happen """
        if self.reply:
            QMessageBox.warning(self, "Error Occurred", self.reply.errorString())

    @Slot()
    def on_cancel(self):
        if self.reply:
            self.reply.abort()
            self.progress_bar.setValue(0)

        if self.file:
            self.file.cancelWriting()

        self.start_button.setDisabled(False)

    @Slot()
    def on_open_folder(self):

        dir_path = QFileDialog.getExistingDirectory(
            self, "Choose Directory", QDir.homePath(), QFileDialog.ShowDirsOnly
        )

        if dir_path:
            destination_dir = QDir(dir_path)
            self.destination_box.setText(QDir.fromNativeSeparators(destination_dir.path()))


app = QApplication(sys.argv)
app.setApplicationName("MyDownloader")
window = MainWindow()
window.show()
app.exec()
