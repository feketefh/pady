from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout, QLineEdit, QHBoxLayout, QPushButton
from PyQt6.QtGui import QTextCursor, QKeySequence
from PyQt6.QtCore import Qt, QPoint

class FindWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find...")
        layout.addWidget(self.find_input)

        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.hide)
        layout.addWidget(close_button)

        self.setLayout(layout)

class Editor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_find_widget()

    def init_ui(self):
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(40)

    def init_find_widget(self):
        self.find_widget = FindWidget()
        self.find_widget.find_input.returnPressed.connect(self.find_text)
        self.find_widget.hide()

    def show_find_widget(self):
        if not self.find_widget.isVisible():
            # Position the find widget in the top-right corner of the editor
            editor_rect = self.rect()
            find_widget_width = 200
            find_widget_height = 30
            x = editor_rect.width() - find_widget_width
            y = 0
            self.find_widget.setGeometry(x, y, find_widget_width, find_widget_height)
            self.find_widget.show()
        self.find_widget.find_input.setFocus()
        self.find_widget.find_input.selectAll()

    def find_text(self):
        search_text = self.find_widget.find_input.text()
        if search_text:
            cursor = self.textCursor()
            # Start searching from the current cursor position
            found_cursor = self.document().find(search_text, cursor)
            if found_cursor.isNull():
                # If not found, start from the beginning
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                found_cursor = self.document().find(search_text, cursor)
            if not found_cursor.isNull():
                self.setTextCursor(found_cursor)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Find):
            self.show_find_widget()
        elif event.key() == Qt.Key.Key_F and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.show_find_widget()
        else:
            super().keyPressEvent(event)

    def show_find_widget(self):
        if not self.find_widget.isVisible():
            # Set the parent of the find widget to this editor
            self.find_widget.setParent(self)
    
            # Calculate the position for the find widget
            find_widget_width = 200
            find_widget_height = 30
            x = self.width() - find_widget_width - 5  # 5 pixels padding from the right
            y = 5  # 5 pixels padding from the top
    
            # Resize and move the find widget
            self.find_widget.resize(find_widget_width, find_widget_height)
            self.find_widget.move(x, y)
            
            self.find_widget.show()
        
        self.find_widget.find_input.setFocus()
        self.find_widget.find_input.selectAll()