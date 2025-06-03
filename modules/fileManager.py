from PyQt6.QtWidgets import QFileDialog, QMessageBox
from modules.editor import Editor, PythonHighlighter
import chardet
import os

class FileManager:
    def __init__(self, notepad):
        self.notepad = notepad
        self.file_paths = {}
        self.untitled_count = 0

    def open_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self.notepad, "Open File", "", "All Files (*)")
        
        if file_path:
            for i in range(self.notepad.tab_widget.count()):
                editor = self.notepad.tab_widget.widget(i)
                if editor in self.file_paths and self.file_paths[editor] == file_path:
                    self.notepad.tab_widget.setCurrentIndex(i)
                    return

            try:
                with open(file_path, 'rb') as file:
                    raw_data = file.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding']
    
                if not encoding:
                    encoding = 'utf-8'
    
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
    
                editor = Editor()
                editor.setPlainText(content)
                path = self.get_current_file_path()
                PythonHighlighter.highlightBlock(content, path)
                index = self.notepad.tab_widget.addTab(editor, os.path.basename(file_path))
                self.notepad.tab_widget.setCurrentIndex(index)
                self.file_paths[editor] = file_path
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as file:
                        content = file.read()
                    
                    editor = Editor()
                    editor.setPlainText(content)
                    index = self.notepad.tab_widget.addTab(editor, os.path.basename(file_path))
                    self.notepad.tab_widget.setCurrentIndex(index)
                    self.file_paths[editor] = file_path
                    
                    QMessageBox.warning(self.notepad, "Encoding Warning", 
                                        "The file encoding could not be detected accurately. "
                                        "The file has been opened, but some characters may not display correctly.")
                except Exception as e:
                    QMessageBox.critical(self.notepad, "Error", f"Unable to open file: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self.notepad, "Error", f"Unable to open file: {str(e)}")

    def save_file(self):
        current_editor = self.notepad.tab_widget.currentWidget()
        if current_editor in self.file_paths:
            file_path = self.file_paths[current_editor]
            self._save_to_file(current_editor, file_path)
        else:
            self.save_file_as()

    def save_file_as(self):
        current_editor = self.notepad.tab_widget.currentWidget()
        file_path, _ = QFileDialog.getSaveFileName(self.notepad, "Save File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            self._save_to_file(current_editor, file_path)
            self.file_paths[current_editor] = file_path
            self.notepad.tab_widget.setTabText(self.notepad.tab_widget.currentIndex(), os.path.basename(file_path))

    def _save_to_file(self, editor, file_path):
        content = editor.toPlainText()
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
        except Exception as e:
            QMessageBox.critical(self.notepad, "Error", f"Save failed for {file_path}: {str(e)}")

    def open_file_from_explorer(self, index):
        file_path = self.notepad.file_model.filePath(index)
        if not self.notepad.file_model.isDir(index):
            self.open_file(file_path)
            
    def autosave(self):
        for index in range(self.notepad.tab_widget.count()):
            editor = self.notepad.tab_widget.widget(index)
            if editor in self.file_paths:
                file_path = self.file_paths[editor]
                content = editor.toPlainText()
                try:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(content)
                except Exception as e:
                    QMessageBox.critical(self.notepad, "Error", f"Autosave failed for {file_path}: {str(e)}")

    def new_file(self):
        editor = Editor()
        self.untitled_count += 1
        index = self.notepad.tab_widget.addTab(editor, f"Untitled-{self.untitled_count}")
        self.notepad.tab_widget.setCurrentIndex(index)
        self.file_paths[editor] = f"Untitled-{self.untitled_count}"

    def get_all_open_files(self):
        open_files = []
        for i in range(self.notepad.tab_widget.count()):
            editor = self.notepad.tab_widget.widget(i)
            if editor in self.file_paths:
                file_path = self.file_paths[editor]
                content = editor.toPlainText()
                open_files.append((file_path, content))
        return open_files

    def open_files_from_session(self, files):
        for file_path, content in files:
            editor = Editor()
            editor.setPlainText(content)
            if file_path.startswith("Untitled-"):
                self.untitled_count += 1
                index = self.notepad.tab_widget.addTab(editor, file_path)
            else:
                index = self.notepad.tab_widget.addTab(editor, os.path.basename(file_path))
            self.notepad.tab_widget.setCurrentIndex(index)
            self.file_paths[editor] = file_path

    def get_current_file_path(self):
        current_editor = self.notepad.tab_widget.currentWidget()
        return self.file_paths.get(current_editor)