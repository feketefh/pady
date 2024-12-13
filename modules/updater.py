import requests
from PyQt6.QtWidgets import QMessageBox
import subprocess

class UpdateChecker:
    def __init__(self, current_version, update_url, update_exe):
        self.current_version = current_version
        self.update_url = update_url
        self.update_exe = update_exe

    def check_for_updates(self):
        try:
            response = requests.get(self.update_url)
            response.raise_for_status()
            latest_version = response.text.strip()
            
            if self.is_newer_version(latest_version):
                return latest_version
            return None
        except requests.RequestException:
            return None

    def is_newer_version(self, latest_version):
        return latest_version > self.current_version

    def prompt_for_update(self, parent, latest_version):
        reply = QMessageBox.question(parent, 'Update Available',
                                     f"A new version ({latest_version}) is available. Do you want to update?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

    def start_update(self):
        try:
            subprocess.Popen(self.update_exe)
        except Exception as e:
            QMessageBox.critical(None, "Update Error", f"Failed to start the update process: {str(e)}")

def check_and_prompt_for_update(parent, current_version, update_url, update_exe):
    checker = UpdateChecker(current_version, update_url, update_exe)
    latest_version = checker.check_for_updates()
    if latest_version:
        if checker.prompt_for_update(parent, latest_version):
            checker.start_update()
    else:
        QMessageBox.information(parent, "Update", "No updates available")