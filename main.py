import sys
from PyQt6.QtWidgets import QApplication
from modules.notepad import Notepad
import kirilov_updater

if __name__ == '__main__':
    updater = kirilov_updater.UpdateChecker("feketefh/pady", "pady", "main")
    updater.run()
    app = QApplication(sys.argv)
    notepad = Notepad()
    notepad.show()

    sys.exit(app.exec())