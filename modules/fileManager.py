import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from modules.editor import Editor

class FileManager:
    def __init__(self, notepad):
        self.notepad = notepad
        self.file_paths = {}
        self.untitled_count = 0
        self.last_saved_content = {}

    def open_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self.notepad, "Open File", "", "Text Files (*.txt);;All Files (*)")
        
        if file_path:
            self.notepad.settings.add_recent_file(file_path)
            
            editor = Editor(path=file_path, settings=self.notepad.settings)
            if editor.load_file_with_error_handling(file_path):
                self.notepad.tab_widget.addTab(editor, os.path.basename(file_path))
                self.file_paths[editor] = file_path
            else:
                editor.deleteLater()

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
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.file_paths[editor] = file_path
            self.last_saved_content[editor] = content

            self.notepad.settings.add_recent_file(file_path)
            
            tab_index = self.notepad.tab_widget.indexOf(editor)
            if tab_index != -1:
                self.notepad.tab_widget.setTabText(tab_index, os.path.basename(file_path))
        except Exception as e:
            QMessageBox.critical(self.notepad, "Error", f"Failed to save file: {str(e)}")

    def open_file_from_explorer(self, index):
        file_path = self.notepad.file_model.filePath(index)
        if not self.notepad.file_model.isDir(index):
            self.open_file(file_path)
            
    def autosave(self):
        """Autosave all open files that have been saved before (not untitled files)"""
        try:
            for i in range(self.notepad.tab_widget.count()):
                editor = self.notepad.tab_widget.widget(i)
                if isinstance(editor, Editor):
                    file_path = self.file_paths.get(editor, "")
                    
                    if file_path and file_path != "" and os.path.exists(os.path.dirname(file_path)):
                        try:
                            content = editor.toPlainText()
                            
                            if self.last_saved_content.get(editor) != content:
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                self.last_saved_content[editor] = content
                                print(f"Autosaved: {file_path}")
                            
                        except Exception as e:
                            print(f"Autosave failed for {file_path}: {e}")
                    else:
                        tab_name = self.notepad.tab_widget.tabText(i)
                        print(f"Skipping autosave for untitled file: {tab_name}")
        except Exception as e:
            print(f"Autosave error: {e}")

    def new_file(self):
        editor = Editor(settings=self.notepad.settings)
        self.untitled_count += 1
        index = self.notepad.tab_widget.addTab(editor, f"Untitled-{self.untitled_count}")
        self.notepad.tab_widget.setCurrentIndex(index)
        self.file_paths[editor] = ""

    def get_all_open_files(self):
        """Get all currently open files with their tab information"""
        open_files = []
        for i in range(self.notepad.tab_widget.count()):
            editor = self.notepad.tab_widget.widget(i)
            if isinstance(editor, Editor):
                file_path = self.file_paths.get(editor, "")
                tab_text = self.notepad.tab_widget.tabText(i)
                
                is_untitled = (not file_path or 
                              file_path == "" or 
                              tab_text.startswith("Untitled-"))
                
                file_info = {
                    'tab_name': tab_text,
                    'file_path': file_path if (file_path and not tab_text.startswith("Untitled-")) else None,
                    'is_untitled': is_untitled,
                    'content': editor.toPlainText() if is_untitled else None,
                    'cursor_position': editor.textCursor().position()
                }
                open_files.append(file_info)
        
        return open_files

    def open_files_from_session(self, session_data):
        """Restore files from session data"""
        open_files = session_data.get('recent_files', [])
        active_tab = session_data.get('active_tab', 0)
        
        if not open_files:
            self.new_file()
            return
            
        for file_info in open_files:
            if isinstance(file_info, dict):
                file_path = file_info.get('file_path')
                is_untitled = file_info.get('is_untitled', False)
                content = file_info.get('content', '')
                tab_name = file_info.get('tab_name', 'Untitled')
                cursor_position = file_info.get('cursor_position', 0)
                
                if is_untitled or not file_path:
                    editor = Editor(settings=self.notepad.settings)
                    if content:
                        editor.setPlainText(content)
                        cursor = editor.textCursor()
                        cursor.setPosition(min(cursor_position, len(content)))
                        editor.setTextCursor(cursor)
                    
                    if tab_name.startswith('Untitled-'):
                        try:
                            num = int(tab_name.split('-')[1])
                            if num > self.untitled_count:
                                self.untitled_count = num
                        except:
                            pass
                    
                    self.notepad.tab_widget.addTab(editor, tab_name)
                    self.file_paths[editor] = ""
                else:
                    if os.path.exists(file_path):
                        try:
                            editor = Editor(path=file_path, settings=self.notepad.settings)
                            if editor.load_file_with_error_handling(file_path):
                                tab_name = os.path.basename(file_path)
                                self.notepad.tab_widget.addTab(editor, tab_name)
                                self.file_paths[editor] = file_path
                                
                                cursor = editor.textCursor()
                                cursor.setPosition(min(cursor_position, len(editor.toPlainText())))
                                editor.setTextCursor(cursor)
                        except Exception as e:
                            print(f"Error opening file {file_path}: {e}")
                            continue
                    else:
                        print(f"File not found: {file_path}")
                        
        if 0 <= active_tab < self.notepad.tab_widget.count():
            self.notepad.tab_widget.setCurrentIndex(active_tab)
        
        if self.notepad.tab_widget.count() == 0:
            self.new_file()

    def get_current_file_path(self):
        current_editor = self.notepad.tab_widget.currentWidget()
        return self.file_paths.get(current_editor)