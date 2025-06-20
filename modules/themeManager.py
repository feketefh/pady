import sys
import platform
import winreg
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

def get_windows_theme():
    is_dark = False
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        key = winreg.OpenKey(registry, key_path)
        try:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        except FileNotFoundError:
            value, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
        is_dark = (value == 0)
        winreg.CloseKey(key)
    except Exception:
        pass
    return "dark" if is_dark else "light"

def apply_theme(app, theme="system", main_window=None):
    app.setStyle("Fusion")
    if theme == "system":
        theme = get_windows_theme()
    palette = QPalette()
    if theme == "dark":
        palette.setColor(QPalette.ColorRole.Window, QColor("#232629"))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor("#181a1b"))
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#3d6ea8"))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor("#232629"))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        if main_window is not None:
            main_window.setStyleSheet("")
    else:
        palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Base, QColor("#f5f5f5"))
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#3d6ea8"))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        if main_window is not None:
            main_window.setStyleSheet("""
            QMenuBar {
                background: white;
                color: black;
            }
            QMenuBar::item {
                background: white;
                color: black;
            }
            QMenuBar::item:selected {
                background: #e0e0e0;
            }
            QMenu {
                background: white;
                color: black;
                border: 1px solid #bdbdbd;
            }
            QMenu::item:selected {
                background: #3d6ea8;
                color: white;
            }
            """)
    app.setPalette(palette)