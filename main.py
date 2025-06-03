import sys
from PyQt6.QtWidgets import QApplication
from modules.notepad import Notepad

if __name__ == '__main__':
    app = QApplication(sys.argv)
    notepad = Notepad(app)
    notepad.show()

    sys.exit(app.exec())