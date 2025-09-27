import os
from PyQt6.QtWidgets import (QPlainTextEdit, QWidget, QLineEdit, QHBoxLayout, 
                           QPushButton, QTextEdit, QMessageBox, QProgressDialog)
from PyQt6.QtGui import QTextCursor, QKeySequence, QPainter, QColor, QTextFormat, QFont
from PyQt6.QtCore import Qt, QRect, QSize, QThread, pyqtSignal
from modules.syntaxHighlighter import SyntaxHighlighter


class FileLoadThread(QThread):
    chunk_loaded = pyqtSignal(str)
    finished_loading = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, file_path, chunk_size=1024*1024):
        super().__init__()
        self.file_path = file_path
        self.chunk_size = chunk_size

    def run(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    self.chunk_loaded.emit(chunk)
            self.finished_loading.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


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
    def __init__(self, path=None, settings=None):
        super().__init__()
        self.file_path = path
        self.settings = settings
        self.show_line_numbers = True if settings is None else settings.get('show_line_numbers', True)
        self.large_file_threshold = 5 * 1024 * 1024  # 5MB
        
        self.init_ui()
        self.init_find_widget()
        self.init_line_numbers()
        self.setup_drag_drop()
        
        try:
            self.syntax = SyntaxHighlighter(self.document(), path)
        except Exception as e:
            print(f"Error initializing syntax highlighter: {e}")
            self.syntax = None

    def init_ui(self):
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(40)
        font = QFont("Consolas", 10)
        self.setFont(font)

    def init_find_widget(self):
        self.find_widget = FindWidget()
        self.find_widget.find_input.returnPressed.connect(self.find_text)
        self.find_widget.hide()

    def init_line_numbers(self):
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)

    def setup_drag_drop(self):
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.load_file_with_error_handling(files[0])

    def load_file_with_error_handling(self, file_path):
        """Load file with proper error handling and large file support"""
        try:
            if not os.path.exists(file_path):
                QMessageBox.critical(self, "Error", f"File not found: {file_path}")
                return False

            file_size = os.path.getsize(file_path)
            
            if file_size > self.large_file_threshold:
                reply = QMessageBox.question(
                    self, "Large File", 
                    f"This file is {file_size / (1024*1024):.1f}MB. "
                    "Loading large files may be slow. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return False
                
                self.load_large_file(file_path)
            else:
                self.load_normal_file(file_path)
                
            self.file_path = file_path
            return True
            
        except PermissionError:
            QMessageBox.critical(self, "Error", "Permission denied accessing file")
            return False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
            return False

    def load_normal_file(self, file_path):
        """Load normal sized files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.setPlainText(content)
        except UnicodeDecodeError:
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    self.setPlainText(content)
                    QMessageBox.information(self, "Encoding", f"File loaded with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise UnicodeDecodeError("Unable to decode file with any supported encoding")

    def load_large_file(self, file_path):
        """Load large files in chunks"""
        self.setPlainText("")
        self.progress_dialog = QProgressDialog("Loading file...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        
        self.file_loader = FileLoadThread(file_path)
        self.file_loader.chunk_loaded.connect(self.append_chunk)
        self.file_loader.finished_loading.connect(self.finish_loading)
        self.file_loader.error_occurred.connect(self.handle_load_error)
        self.file_loader.start()

    def append_chunk(self, chunk):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)

    def finish_loading(self):
        self.progress_dialog.hide()
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.setTextCursor(cursor)

    def handle_load_error(self, error):
        self.progress_dialog.hide()
        QMessageBox.critical(self, "Error", f"Failed to load file: {error}")

    def line_number_area_width(self):
        if not self.show_line_numbers:
            return 0
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        if not self.show_line_numbers:
            return
            
        painter = QPainter(self.line_number_area)
        
        if hasattr(self, 'settings') and self.settings:
            theme = self.settings.get('theme', 'system')
        else:
            theme = 'light'
            
        if theme == 'dark' or (theme == 'system' and self.is_dark_theme()):
            bg_color = QColor(35, 38, 41)
            text_color = QColor(180, 180, 180)
        else:
            bg_color = QColor(240, 240, 240)
            text_color = QColor(120, 120, 120)

        painter.fillRect(event.rect(), bg_color)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(text_color)
                painter.drawText(0, int(top), self.line_number_area.width() - 3, 
                               self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def is_dark_theme(self):
        """Check if system is using dark theme"""
        try:
            from modules.themeManager import get_windows_theme
            return get_windows_theme() == 'dark'
        except:
            return False

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            
            if hasattr(self, 'settings') and self.settings:
                theme = self.settings.get('theme', 'system')
            else:
                theme = 'light'
                
            if theme == 'dark' or (theme == 'system' and self.is_dark_theme()):
                line_color = QColor(45, 45, 45)
            else:
                line_color = QColor(Qt.GlobalColor.yellow).lighter(160)

            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def toggle_line_numbers(self):
        self.show_line_numbers = not self.show_line_numbers
        if self.show_line_numbers:
            self.line_number_area.show()
        else:
            self.line_number_area.hide()
        self.update_line_number_area_width(0)
        
        if hasattr(self, 'settings') and self.settings:
            self.settings.set('show_line_numbers', self.show_line_numbers)

    def show_find_widget(self):
        if not self.find_widget.isVisible():
            self.find_widget.setParent(self)
            find_widget_width = 200
            find_widget_height = 30
            x = self.width() - find_widget_width - 5
            y = 5
            self.find_widget.resize(find_widget_width, find_widget_height)
            self.find_widget.move(x, y)
            self.find_widget.show()
        
        self.find_widget.find_input.setFocus()
        self.find_widget.find_input.selectAll()

    def find_text(self):
        search_text = self.find_widget.find_input.text()
        if search_text:
            cursor = self.textCursor()
            found_cursor = self.document().find(search_text, cursor)
            if found_cursor.isNull():
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