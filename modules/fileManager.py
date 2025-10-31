import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from modules.editor import Editor
import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.notepad import Notepad

class FileManager:
    def __init__(self, notepad: "Notepad"):
        self.notepad = notepad
        self.filePaths = {}
        self.untitledCount = 0
        self.lastSavedContent = {}

    
    def openFile(self, filePath=None):
        if not filePath:
            filePath, _ = QFileDialog.getOpenFileName(self.notepad, "Open File", "", "Text Files (*.txt);;All Files (*)")
        
        if filePath:
            for editor, existingPath in self.filePaths.items():
                if existingPath == filePath:
                    index = self.notepad.tabWidget.indexOf(editor)
                    if index != -1:
                        self.notepad.tabWidget.setCurrentIndex(index)
                    return

            self.notepad.settings.addRecentFile(filePath)

            editor = Editor(path=filePath, settings=self.notepad.settings)
            if editor.loadFile(filePath):
                index = self.notepad.tabWidget.addTab(editor, os.path.basename(filePath))
                self.notepad.tabWidget.setCurrentIndex(index)
                self.filePaths[editor] = filePath
            else:
                editor.deleteLater()

    def saveFile(self):
        currentEditor = self.notepad.tabWidget.currentWidget()
        if currentEditor in self.filePaths:
            filePath = self.filePaths[currentEditor]
            self.saveToFile(currentEditor, filePath)
        else:
            self.saveFileAs()

    def saveFileAs(self):
        currentEditor = self.notepad.tabWidget.currentWidget()
        filePath, _ = QFileDialog.getSaveFileName(self.notepad, "Save File", "", "Text Files (*.txt);;All Files (*)")
        if filePath:
            self.saveToFile(currentEditor, filePath)
            self.filePaths[currentEditor] = filePath
            self.notepad.tabWidget.setTabText(self.notepad.tabWidget.currentIndex(), os.path.basename(filePath))

    def saveToFile(self, editor: Editor, filePath: str):
        content = editor.toPlainText()
        try:
            with open(filePath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.filePaths[editor] = filePath

            # Hybrid: Store hash for large files, full content for small files
            if len(content) > 100_000:  # 100KB threshold
                self.lastSavedContent[editor] = hashlib.md5(content.encode()).hexdigest()
            else:
                self.lastSavedContent[editor] = content

            self.notepad.settings.addRecentFile(filePath)

            tabIndex = self.notepad.tabWidget.indexOf(editor)
            if tabIndex != -1:
                self.notepad.tabWidget.setTabText(tabIndex, os.path.basename(filePath))
        except Exception as e:
            QMessageBox.critical(self.notepad, "Error", f"Failed to save file: {str(e)}")

    def autosave(self):
        """Autosave all open files that have been saved before (not untitled files)"""
        try:
            for i in range(self.notepad.tabWidget.count()):
                editor = self.notepad.tabWidget.widget(i)
                if isinstance(editor, Editor):
                    filePath = self.filePaths.get(editor, "")

                    if filePath and filePath != "" and os.path.exists(os.path.dirname(filePath)):
                        try:
                            content = editor.toPlainText()
                            lastSaved = self.lastSavedContent.get(editor)

                            hasChanged = False
                            if len(content) > 100_000:
                                currentHash = hashlib.md5(content.encode()).hexdigest()
                                hasChanged = (lastSaved != currentHash)
                                if hasChanged:
                                    self.lastSavedContent[editor] = currentHash
                            else:
                                hasChanged = (lastSaved != content)
                                if hasChanged:
                                    self.lastSavedContent[editor] = content

                            if hasChanged:
                                with open(filePath, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                print(f"Autosaved: {filePath}")

                        except Exception as e:
                            print(f"Autosave failed for {filePath}: {e}")
                    else:
                        tabName = self.notepad.tabWidget.tabText(i)
                        print(f"Skipping autosave for untitled file: {tabName}")
        except Exception as e:
            print(f"Autosave error: {e}")

    def openFileFromExplorer(self, index):
        filePath = self.notepad.fileModel.filePath(index)
        if not self.notepad.fileModel.isDir(index):
            self.openFile(filePath)

    def newFile(self):
        editor = Editor(settings=self.notepad.settings)
        self.untitledCount += 1
        index = self.notepad.tabWidget.addTab(editor, f"Untitled-{self.untitledCount}")
        self.notepad.tabWidget.setCurrentIndex(index)
        self.filePaths[editor] = ""

    def getAllOpenFiles(self):
        """Get all currently open files with their tab information"""
        openFiles = []
        for i in range(self.notepad.tabWidget.count()):
            editor = self.notepad.tabWidget.widget(i)
            if isinstance(editor, Editor):
                filePath = self.filePaths.get(editor, "")
                tabText = self.notepad.tabWidget.tabText(i)

                isUntitled = (not filePath or
                              filePath == "" or
                              tabText.startswith("Untitled-"))

                fileInfo = {
                    'tab_name': tabText,
                    'filePath': filePath if (filePath and not tabText.startswith("Untitled-")) else None,
                    'is_untitled': isUntitled,
                    'content': editor.toPlainText() if isUntitled else None,
                    'cursor_position': editor.textCursor().position()
                }
                openFiles.append(fileInfo)

        return openFiles

    def openFilesFromSession(self, sessionData: dict):
        """Restore files from session data"""
        openFiles = sessionData.get('recent_files', [])
        activeTab = sessionData.get('active_tab', 0)

        if not openFiles:
            self.newFile()
            return

        for fileInfo in openFiles:
            if isinstance(fileInfo, dict):
                filePath = fileInfo.get('filePath')
                isUntitled = fileInfo.get('is_untitled', False)
                content = fileInfo.get('content', '')
                tabName: str = fileInfo.get('tab_name', 'Untitled')
                cursorPosition = fileInfo.get('cursor_position', 0)

                if isUntitled or not filePath:
                    editor = Editor(settings=self.notepad.settings)
                    if content:
                        editor.setPlainText(content)
                        cursor = editor.textCursor()
                        cursor.setPosition(min(cursorPosition, len(content)))
                        editor.setTextCursor(cursor)

                    if tabName.startswith('Untitled-'):
                        try:
                            num = int(tabName.split('-')[1])
                            if num > self.untitledCount:
                                self.untitledCount = num
                        except:
                            pass

                    self.notepad.tabWidget.addTab(editor, tabName)
                    self.filePaths[editor] = ""
                else:
                    if os.path.exists(filePath):
                        try:
                            editor = Editor(path=filePath, settings=self.notepad.settings)
                            if editor.loadFile(filePath):
                                tabName = os.path.basename(filePath)
                                self.notepad.tabWidget.addTab(editor, tabName)
                                self.filePaths[editor] = filePath
                                
                                cursor = editor.textCursor()
                                cursor.setPosition(min(cursorPosition, len(editor.toPlainText())))
                                editor.setTextCursor(cursor)
                        except Exception as e:
                            print(f"Error opening file {filePath}: {e}")
                            continue
                    else:
                        print(f"File not found: {filePath}")

        if 0 <= activeTab < self.notepad.tabWidget.count():
            self.notepad.tabWidget.setCurrentIndex(activeTab)

        if self.notepad.tabWidget.count() == 0:
            self.newFile()

    def getCurrentFilePath(self):
        currentEditor = self.notepad.tabWidget.currentWidget()
        return self.filePaths.get(currentEditor)

    def closeTab(self, index):
        """Clean up when a tab is closed"""
        editor = self.notepad.tabWidget.widget(index)
        if isinstance(editor, Editor):
            if editor in self.filePaths:
                del self.filePaths[editor]
            if hasattr(self, 'lastSavedContent') and editor in self.lastSavedContent:
                del self.lastSavedContent[editor]

        self.notepad.tabWidget.removeTab(index)