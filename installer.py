import sys
import os
import requests
import zipfile
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton, QProgressBar, QStackedWidget, QHBoxLayout
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class InstallerWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, install_path, create_desktop_shortcut, create_start_menu_shortcut):
        super().__init__()
        self.install_path = install_path
        self.create_desktop_shortcut = create_desktop_shortcut
        self.create_start_menu_shortcut = create_start_menu_shortcut
        self.github_api_url = "https://api.github.com/repos/yourusername/yourrepo/releases/latest"
        self.github_download_url = ""

    def run(self):
        try:
            self.status.emit("Checking for latest version...")
            self.get_latest_release()
            
            self.status.emit("Downloading latest version...")
            self.download_file(self.github_download_url, "latest_release.zip")
            
            self.status.emit("Extracting files...")
            self.extract_files("latest_release.zip", self.install_path)
            
            self.status.emit("Creating shortcuts...")
            if self.create_desktop_shortcut:
                self.create_shortcut("Desktop")
            if self.create_start_menu_shortcut:
                self.create_shortcut("StartMenu")
            
            self.status.emit("Adding to registry...")
            self.add_to_registry()
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def get_latest_release(self):
        response = requests.get(self.github_api_url)
        response.raise_for_status()
        release_data = response.json()
        self.github_download_url = release_data['assets'][0]['browser_download_url']

    def download_file(self, url, path):
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 KB
        downloaded = 0
        with open(path, 'wb') as f:
            for data in response.iter_content(block_size):
                size = f.write(data)
                downloaded += size
                self.progress.emit(int(downloaded / total_size * 100))

    def extract_files(self, zip_path, extract_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        os.remove(zip_path)

    def create_shortcut(self, location):
        # Implement shortcut creation logic here
        pass

    def add_to_registry(self):
        # Implement registry addition logic here
        pass

class InstallerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Notepad Installer')
        self.setGeometry(300, 300, 400, 200)

        self.stacked_widget = QStackedWidget()
        
        # Options page
        options_widget = QWidget()
        options_layout = QVBoxLayout()
        
        self.desktop_shortcut = QCheckBox('Create Desktop Shortcut')
        self.start_menu_shortcut = QCheckBox('Create Start Menu Shortcut')
        
        options_layout.addWidget(self.desktop_shortcut)
        options_layout.addWidget(self.start_menu_shortcut)
        
        install_button = QPushButton('Install')
        install_button.clicked.connect(self.start_installation)
        options_layout.addWidget(install_button)
        
        options_widget.setLayout(options_layout)
        
        # Progress page
        progress_widget = QWidget()
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.status_label = QLabel('Preparing installation...')
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        progress_widget.setLayout(progress_layout)
        
        self.stacked_widget.addWidget(options_widget)
        self.stacked_widget.addWidget(progress_widget)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

    def start_installation(self):
        self.stacked_widget.setCurrentIndex(1)
        install_path = os.path.expanduser("~/Notepad")
        self.worker = InstallerWorker(install_path, self.desktop_shortcut.isChecked(), self.start_menu_shortcut.isChecked())
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.installation_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.status_label.setText(message)

    def show_error(self, message):
        self.status_label.setText(f"Error: {message}")

    def installation_finished(self):
        self.status_label.setText("Installation completed successfully!")
        finish_button = QPushButton('Finish')
        finish_button.clicked.connect(self.close)
        self.stacked_widget.currentWidget().layout().addWidget(finish_button)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    installer = InstallerGUI()
    installer.show()
    sys.exit(app.exec())