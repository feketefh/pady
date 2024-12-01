import sys
from PyQt6.QtWidgets import QApplication
from modules.notepad import Notepad
from modules.updater import check_and_prompt_for_update

if __name__ == '__main__':
    app = QApplication(sys.argv)
    notepad = Notepad()
    notepad.show()

    sys.exit(app.exec())