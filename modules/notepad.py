import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QTreeView, QSplitter, QFileDialog, QVBoxLayout, QWidget, QHeaderView, QStyle, QMessageBox
from PyQt6.QtGui import QAction, QKeySequence, QFileSystemModel, QActionGroup
from PyQt6.QtCore import Qt, QDir, QTimer, QSize, QRect, QSortFilterProxyModel
from PyQt6.QtCore import QLoggingCategory
from modules.editor import Editor
from modules.fileManager import FileManager
from modules.settings import Settings
from modules.themeManager import applyTheme
from packaging import version
import requests
import webbrowser

class FileNameProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self.foldersFirst = True
        self.sortOrder = Qt.SortOrder.AscendingOrder


    def columnCount(self, parent=None):
        return 1

    def data(self, index, role):
        if index.column() == 0:
            sourceIndex = self.mapToSource(index)
            if role == Qt.ItemDataRole.DisplayRole:
                return self.sourceModel().fileName(sourceIndex)
            elif role == Qt.ItemDataRole.DecorationRole:
                return self.sourceModel().fileIcon(sourceIndex)
        return None

    def lessThan(self, left, right):
        leftData: str = self.sourceModel().filePath(left)
        rightData: str = self.sourceModel().filePath(right)
        leftIsDir = self.sourceModel().isDir(left)
        rightIsDir = self.sourceModel().isDir(right)

        if leftIsDir != rightIsDir:
            return leftIsDir

        if self.sortOrder == Qt.SortOrder.AscendingOrder:
            return leftData.lower() < rightData.lower()
        else:
            return leftData.lower() > rightData.lower()

    def sort(self, column, order):
        self.sortOrder = order
        super().sort(column, order)

    def toggleSortOrder(self):
        self.sortOrder = Qt.SortOrder.DescendingOrder if self.sortOrder == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        self.invalidate()
        self.sort(0, self.sortOrder)

class CustomHeaderView(QHeaderView):
    def __init__(self, orientation, notepad, parent=None):
        super().__init__(orientation, parent)
        self.notepad: Notepad = notepad
        self.setSectionsClickable(True)
        self.setStretchLastSection(True)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        painter.fillRect(rect, self.palette().brush(self.backgroundRole()))
        
        if logicalIndex == 0:
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft)
            iconSize = QSize(16, 16)
            iconRect = QRect(rect.left() + 4, rect.top() + (rect.height() - iconSize.height()) // 2,
                             iconSize.width(), iconSize.height())
            icon.paint(painter, iconRect)

            textRect = QRect(rect.left() + iconSize.width() + 8, rect.top(), rect.width() - iconSize.width() - 8, rect.height())
            painter.drawText(textRect, Qt.AlignmentFlag.AlignVCenter, "Name")

        painter.restore()

    def sizeHint(self):
        return QSize(self.length(), 25)

    def mousePressEvent(self, event):
        index = self.logicalIndexAt(event.position().toPoint())
        if index == 0:
            iconWidth = 20
            if event.position().x() <= iconWidth:
                self.notepad.goUpDirectory()
            else:
                proxyModel: FileNameProxyModel = self.notepad.fileExplorer.model()
                proxyModel.toggleSortOrder()
                self.notepad.fileExplorer.sortByColumn(0, proxyModel.sortOrder)
        else:
            super().mousePressEvent(event)

class Notepad(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()
        self.setWindowTitle("Pady")
        self.setGeometry(100, 100, 1000, 600)
        self.setAcceptDrops(True)

        self.settings = Settings()
        self.fileManager = FileManager(self)
        self.app = app

        QLoggingCategory.setFilterRules("qt.modelview.debug=true")
        self.initUi()
        self.setupAutosave()
        self.loadSettings()
        self.loadLastSession()

        QTimer.singleShot(2000, lambda: self.checkForUpdates(silent=True))

        geometry = self.settings.get('window_geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.get('window_state')
        if state:
            self.restoreState(state)

    def initUi(self):
        self.createMenuBar()
        self.createMainLayout()

    def createMenuBar(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('File')
        editMenu = menubar.addMenu('Edit')
        viewMenu = menubar.addMenu('View')
        settingsMenu = menubar.addMenu('Settings')

        newAction = QAction('New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.triggered.connect(self.newFile)
        fileMenu.addAction(newAction)

        openAction = QAction('Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.fileManager.openFile)
        fileMenu.addAction(openAction)

        openFolderAction = QAction('Open Folder', self)
        openFolderAction.setShortcut('Ctrl+Shift+O')
        openFolderAction.triggered.connect(self.openFolder)
        fileMenu.addAction(openFolderAction)

        saveAction = QAction('Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.fileManager.saveFile)
        fileMenu.addAction(saveAction)

        saveAsAction = QAction('Save As', self)
        saveAsAction.setShortcut('Ctrl+Shift+S')
        saveAsAction.triggered.connect(self.fileManager.saveFileAs)
        fileMenu.addAction(saveAsAction)

        undoAction = QAction('Undo', self)
        undoAction.setShortcut(QKeySequence.StandardKey.Undo)
        undoAction.triggered.connect(self.undo)
        editMenu.addAction(undoAction)

        redoAction = QAction('Redo', self)
        redoAction.setShortcut(QKeySequence.StandardKey.Redo)
        redoAction.triggered.connect(self.redo)
        editMenu.addAction(redoAction)

        findAction = QAction("Find", self)
        findAction.setShortcut(QKeySequence.StandardKey.Find)
        findAction.triggered.connect(self.findInCurrentEditor)

        toggleFileExplorer = QAction('Toggle File Explorer', self)
        toggleFileExplorer.setShortcut('Ctrl+B')
        toggleFileExplorer.triggered.connect(self.toggleFileExplorer)
        viewMenu.addAction(toggleFileExplorer)

        self.autosaveAction = QAction('Autosave', self, checkable=True)
        self.autosaveAction.setChecked(self.settings.get('autosave_enabled', True))
        self.autosaveAction.triggered.connect(self.toggleAutosave)
        settingsMenu.addAction(self.autosaveAction)
        checkUpdatesAction = QAction('Check for Updates', self)
        checkUpdatesAction.triggered.connect(self.checkForUpdates)
        settingsMenu.addAction(checkUpdatesAction)
        self.lineNumber = QAction('Line Numbers', self, checkable=True)
        self.lineNumber.setChecked(self.settings.get('show_line_numbers', True))
        self.lineNumber.triggered.connect(self.toggleLineNumbers)
        settingsMenu.addAction(self.lineNumber)
        themeMenu = settingsMenu.addMenu('Theme')
        themeGroup = QActionGroup(self)

        themes = [('System', 'system'), ('Light', 'light'), ('Dark', 'dark')]
        for themeName, themeValue in themes:
            themeAction = QAction(themeName, self, checkable=True)
            themeAction.setData(themeValue)
            themeGroup.addAction(themeAction)
            themeMenu.addAction(themeAction)
            if themeValue == self.settings.get('theme', 'system'):
                themeAction.setChecked(True)

        themeGroup.triggered.connect(self.changeTheme)

    
    def createMainLayout(self):
        self.mainSplitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.mainSplitter)
    
        fileExplorerWidget = QWidget()
        fileExplorerLayout = QVBoxLayout(fileExplorerWidget)
        fileExplorerLayout.setContentsMargins(0, 0, 0, 0)

    
        try:
            self.fileExplorer = QTreeView()
            self.fileModel = QFileSystemModel()
            self.setupFileExplorer()
    

            homePath = os.path.expanduser('~')
            downloadsPath = os.path.join(homePath, "Downloads")
            sourceIndex = self.fileModel.index(downloadsPath)

            proxyIndex = self.proxyModel.mapFromSource(sourceIndex)

            self.fileExplorer.setRootIndex(proxyIndex)

            self.fileExplorer.clicked.connect(self.onFileExplorerSingleClicked)
            self.fileExplorer.doubleClicked.connect(self.onFileExplorerDoubleClicked)

            fileExplorerLayout.addWidget(self.fileExplorer)
            self.mainSplitter.addWidget(fileExplorerWidget)
    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in create_main_layout: {str(e)}")
    
        self.tabWidget = QTabWidget()
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.mainSplitter.addWidget(self.tabWidget)
    
        self.mainSplitter.setStretchFactor(1, 1)
        self.mainSplitter.setSizes([200, 800])
        self.tabWidget.currentChanged.connect(self.onTabChanged)
    
    def onHeaderClicked(self, logicalIndex):
        pass

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            for filePath in files:
                if os.path.isfile(filePath):
                    # Open each dropped file in a new tab
                    self.fileManager.openFile(filePath)
        event.accept()

    def toggleLineNumbers(self, checked):
        self.settings.set('show_line_numbers', checked)
        for i in range(self.tabWidget.count()):
            editor = self.tabWidget.widget(i)
            if isinstance(editor, Editor):
                editor.toggleLineNumbers()

    def newFile(self):
        self.fileManager.newFile()

    def onTabChanged(self, index):
        currentEditor = self.tabWidget.widget(index)
        if isinstance(currentEditor, Editor):
            if currentEditor in self.fileManager.filePaths:
                self.setWindowTitle(f"Pady - {self.fileManager.filePaths[currentEditor]}")
            else:
                self.setWindowTitle("Pady - Untitled")

    def closeTab(self, index):
        """Clean up when a tab is closed"""
        self.fileManager.closeTab(index)

    def undo(self):
        currentEditor = self.tabWidget.currentWidget()
        if isinstance(currentEditor, Editor):
            currentEditor.undo()

    def redo(self):
        currentEditor = self.tabWidget.currentWidget()
        if isinstance(currentEditor, Editor):
            currentEditor.redo()

    def find(self):
        currentEditor = self.tabWidget.currentWidget()
        if isinstance(currentEditor, Editor):
            currentEditor.findDialog()

    def toggleFileExplorer(self):
        if self.fileExplorer.isVisible():
            self.fileExplorer.hide()
        else:
            self.fileExplorer.show()

    def loadLastSession(self):
        sessionData = self.settings.loadSession()
        if sessionData and sessionData.get('recent_files'):
            self.fileManager.openFilesFromSession(sessionData)
        else:
            self.fileManager.newFile()

    def closeEvent(self, event):
        sessionData = {
            'recent_files': self.fileManager.getAllOpenFiles(),
            'active_tab': self.tabWidget.currentIndex()
        }
        
        self.settings.saveSession(sessionData)
        self.settings.set('window_geometry', self.saveGeometry())
        self.settings.set('window_state', self.saveState())
        
        event.accept()

    def openFolder(self):
        folderPath = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folderPath:
            sourceIndex = self.fileModel.index(folderPath)
            proxyIndex = self.proxyModel.mapFromSource(sourceIndex)
            self.fileExplorer.setRootIndex(proxyIndex)
            self.currentFolder = folderPath

    def onFileExplorerDoubleClicked(self, index):
        sourceIndex = self.proxyModel.mapToSource(index)
        if self.fileModel.isDir(sourceIndex):
            self.fileExplorer.setRootIndex(index)
        else:
            filePath = self.fileModel.filePath(sourceIndex)
            self.fileManager.openFile(filePath)

    def onFileExplorerSingleClicked(self, index):
        sourceIndex = self.proxyModel.mapToSource(index)
        if self.fileModel.isDir(sourceIndex):
            if self.fileExplorer.isExpanded(index):
                self.fileExplorer.collapse(index)
            else:
                self.fileExplorer.expand(index)
        else:
            filePath = self.fileModel.filePath(sourceIndex)
            self.fileManager.openFile(filePath)


    def setupFileExplorer(self):
        self.fileModel = QFileSystemModel()
        homePath = os.path.expanduser("~")
        self.downloadsPath = os.path.join(homePath, "Downloads")
        self.fileModel.setRootPath(self.downloadsPath)

        self.proxyModel = FileNameProxyModel(self)
        self.proxyModel.setSourceModel(self.fileModel)

        self.fileExplorer.setModel(self.proxyModel)
        self.fileExplorer.setHeader(CustomHeaderView(Qt.Orientation.Horizontal, self))
        self.fileExplorer.setColumnWidth(0, 200)
        self.fileExplorer.setHeaderHidden(False)
        self.fileExplorer.setAlternatingRowColors(True)
        self.fileExplorer.setSortingEnabled(True)
        self.fileExplorer.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        
        self.fileExplorer.header().sectionClicked.connect(self.onHeaderClicked)
        
        self.fileModel.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.Hidden)
        
        self.fileExplorer.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.proxyModel.sort(0, Qt.SortOrder.AscendingOrder)

        self.setFileExplorerRoot(self.downloadsPath)

    def setFileExplorerRoot(self, path):
        sourceRootIndex = self.fileModel.index(path)
        proxyRootIndex = self.proxyModel.mapFromSource(sourceRootIndex)
        self.fileExplorer.setRootIndex(proxyRootIndex)
        self.currentFolder = path

    def goUpDirectory(self):
        currentIndex = self.fileExplorer.rootIndex()
        parentIndex = currentIndex.parent()
        if parentIndex.isValid():
            self.fileExplorer.setRootIndex(parentIndex)
            self.currentFolder = self.fileModel.filePath(self.proxyModel.mapToSource(parentIndex))

    def loadSettings(self):
        self.setTheme(self.settings.get('theme', 'system'))
        if self.settings.get('autosave_enabled', True):
            self.autosaveTimer.start()
        else:
            self.autosaveTimer.stop()

    def setupAutosave(self):
        self.autosaveTimer = QTimer(self)
        self.autosaveTimer.timeout.connect(self.fileManager.autosave)
        if self.settings.get('autosave_enabled', True):
            self.autosaveTimer.start(5000)
        else:
            self.autosaveTimer.stop()

    def toggleAutosave(self, enabled):
        self.settings.set('autosave_enabled', enabled)
        if enabled:
            self.autosaveTimer.start(5000)
        else:
            self.autosaveTimer.stop()

    def changeTheme(self, action):
        theme = action.data()
        self.setTheme(theme)
        self.settings.set('theme', theme)

    def setTheme(self, theme):
        if theme == 'system':
            applyTheme(self.app, theme="system")
        elif theme == 'light':
            applyTheme(self.app, theme="light")
        elif theme == 'dark':
            applyTheme(self.app, theme="dark")
        
    def findInCurrentEditor(self):
        currentEditor = self.tabWidget.currentWidget()
        if isinstance(currentEditor, Editor):
            currentEditor.showFindWidget()

    def checkForUpdates(self, silent=False):
        currentVersion = version.Version("pady-v1.7".strip("pady-"))
        githubApiUrl = "https://api.github.com/repos/feketefh/pady/releases/latest"

        try:
            response: requests.Response = requests.get(githubApiUrl, timeout=3)  # Add timeout
            response.raise_for_status()
            latestRelease: dict = response.json()
            latestVersion = version.Version(latestRelease['tag_name'].strip("pady-"))

            if latestVersion > currentVersion:
                reply = QMessageBox.question(
                    self,
                    "Update Available",
                    f"A new version ({latestVersion}) is available. Do you want to download it from GitHub?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        webbrowser.open(latestRelease['html_url'], new=1)
                    except Exception as e:
                        QMessageBox.critical(self, "Update Error", f"Failed to open release: {str(e)}")
            else:
                if not silent:
                    QMessageBox.information(self, "No Updates", "You are using the latest version.")
        except requests.RequestException:
            if not silent:
                QMessageBox.warning(self, "Update Check Failed", "Failed to check for updates. Please try again later.")
        except Exception as e:
            if not silent:
                QMessageBox.warning(self, "Update Check Failed", f"An unexpected error occurred: {str(e)}")
