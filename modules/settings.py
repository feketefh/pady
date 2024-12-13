from PyQt6.QtCore import QSettings

class Settings:
    def __init__(self):
        self.settings = QSettings("Kirilov", "Pady")

    def save_open_files(self, file_paths):
        self.settings.setValue("open_files", file_paths)

    def get_open_files(self):
        return self.settings.value("open_files", [])

    def save_window_geometry(self, geometry):
        self.settings.setValue("window_geometry", geometry)

    def get_window_geometry(self):
        return self.settings.value("window_geometry")

    def save_window_state(self, state):
        self.settings.setValue("window_state", state)

    def get_window_state(self):
        return self.settings.value("window_state")
    
    def get_autosave_enabled(self):
        return self.settings.value("autosave_enabled", True, type=bool)

    def set_autosave_enabled(self, enabled):
        self.settings.setValue("autosave_enabled", enabled)

    def get_theme(self):
        return self.settings.value("theme", "system", type=str)

    def set_theme(self, theme):
        self.settings.setValue("theme", theme)