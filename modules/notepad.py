import os
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QTreeView, QSplitter, QFileDialog, QVBoxLayout, QWidget, QPushButton, QToolBar, QHeaderView, QTableWidgetItem, QStyleOptionHeader, QStyle, QMessageBox
from PyQt6.QtGui import QAction, QKeySequence, QFileSystemModel, QActionGroup, QIcon, QPainter
from PyQt6.QtCore import Qt, QDir, QTimer, QSize, QRect, QSortFilterProxyModel
from PyQt6.QtCore import QLoggingCategory, QCoreApplication
from modules.editor import Editor
from modules.file_manager import FileManager
from modules.settings import Settings
from modules.updater import check_and_prompt_for_update
import qdarktheme
from packaging import version
import requests
import subprocess


class FileNameProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self.folders_first = True
        self.sort_order = Qt.SortOrder.AscendingOrder
        QTimer.singleShot(0, self.check_for_updates_silently)


    def columnCount(self, parent=None):
        return 1

    def data(self, index, role):
        if index.column() == 0:
            source_index = self.mapToSource(index)
            if role == Qt.ItemDataRole.DisplayRole:
                return self.sourceModel().fileName(source_index)
            elif role == Qt.ItemDataRole.DecorationRole:
                return self.sourceModel().fileIcon(source_index)
        return None

    def lessThan(self, left, right):
        left_data = self.sourceModel().filePath(left)
        right_data = self.sourceModel().filePath(right)
        left_is_dir = self.sourceModel().isDir(left)
        right_is_dir = self.sourceModel().isDir(right)

        if left_is_dir != right_is_dir:
            return left_is_dir

        if self.sort_order == Qt.SortOrder.AscendingOrder:
            return left_data.lower() < right_data.lower()
        else:
            return left_data.lower() > right_data.lower()

    def sort(self, column, order):
        self.sort_order = order
        super().sort(column, order)

    def toggle_sort_order(self):
        self.sort_order = Qt.SortOrder.DescendingOrder if self.sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        self.invalidate()
        self.sort(0, self.sort_order)

class CustomHeaderView(QHeaderView):
    def __init__(self, orientation, notepad, parent=None):
        super().__init__(orientation, parent)
        self.notepad = notepad
        self.setSectionsClickable(True)
        self.setStretchLastSection(True)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        painter.fillRect(rect, self.palette().brush(self.backgroundRole()))
        
        if logicalIndex == 0:
            # Draw the arrow icon
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft)
            icon_size = QSize(16, 16)
            icon_rect = QRect(rect.left() + 4, rect.top() + (rect.height() - icon_size.height()) // 2,
                              icon_size.width(), icon_size.height())
            icon.paint(painter, icon_rect)

            # Draw the "Name" text
            text_rect = QRect(rect.left() + icon_size.width() + 8, rect.top(), rect.width() - icon_size.width() - 8, rect.height())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, "Name")
        
        painter.restore()

    def sizeHint(self):
        return QSize(self.length(), 25)

    def mousePressEvent(self, event):
        index = self.logicalIndexAt(event.position().toPoint())
        if index == 0:
            # Check if the click is on the arrow icon
            icon_width = 20  # Approximate width of the icon
            if event.position().x() <= icon_width:
                self.notepad.go_up_directory()
            else:
                # Toggle sorting order
                proxy_model = self.notepad.file_explorer.model()
                proxy_model.toggle_sort_order()
                self.notepad.file_explorer.sortByColumn(0, proxy_model.sort_order)
        else:
            super().mousePressEvent(event)

class Notepad(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pady")
        self.setGeometry(100, 100, 1000, 600)

        self.settings = Settings()
        self.file_manager = FileManager(self)

        QLoggingCategory.setFilterRules("qt.modelview.debug=true")
        self.init_ui()
        self.setup_autosave()  # Move this before load_settings
        self.load_settings()
        self.load_last_session()

        # Load saved window geometry and state
        geometry = self.settings.get_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.get_window_state()
        if state:
            self.restoreState(state)

    def init_ui(self):
        self.create_menu_bar()
        self.create_main_layout()

    def create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('File')
        edit_menu = menubar.addMenu('Edit')
        view_menu = menubar.addMenu('View')
        settings_menu = menubar.addMenu('Settings')

        # File menu actions
        new_action = QAction('New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.file_manager.open_file)
        file_menu.addAction(open_action)

        # Add Open Folder action
        open_folder_action = QAction('Open Folder', self)
        open_folder_action.setShortcut('Ctrl+Shift+O')
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.file_manager.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction('Save As', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.file_manager.save_file_as)
        file_menu.addAction(save_as_action)

        # Edit menu actions
        undo_action = QAction('Undo', self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction('Redo', self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)

        find_action = QAction("Find", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self.find_in_current_editor)

        # View menu actions
        toggle_file_explorer = QAction('Toggle File Explorer', self)
        toggle_file_explorer.setShortcut('Ctrl+B')
        toggle_file_explorer.triggered.connect(self.toggle_file_explorer)
        view_menu.addAction(toggle_file_explorer)

        self.autosave_action = QAction('Autosave', self, checkable=True)
        self.autosave_action.setChecked(self.settings.get_autosave_enabled())
        self.autosave_action.triggered.connect(self.toggle_autosave)
        settings_menu.addAction(self.autosave_action)
        check_updates_action = QAction('Check for Updates', self)
        check_updates_action.triggered.connect(self.check_for_updates)
        settings_menu.addAction(check_updates_action)

        theme_menu = settings_menu.addMenu('Theme')
        theme_group = QActionGroup(self)

        themes = [('System', 'system'), ('Light', 'light'), ('Dark', 'dark')]
        for theme_name, theme_value in themes:
            theme_action = QAction(theme_name, self, checkable=True)
            theme_action.setData(theme_value)
            theme_group.addAction(theme_action)
            theme_menu.addAction(theme_action)
            if theme_value == self.settings.get_theme():
                theme_action.setChecked(True)

        theme_group.triggered.connect(self.change_theme)

    
    def create_main_layout(self):
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.main_splitter)
    
        file_explorer_widget = QWidget()
        file_explorer_layout = QVBoxLayout(file_explorer_widget)
        file_explorer_layout.setContentsMargins(0, 0, 0, 0)

    
        try:
            self.file_explorer = QTreeView()
            self.file_model = QFileSystemModel()
            # self.file_model.setRootPath(QDir.rootPath())
            self.setup_file_explorer()
            self.file_explorer.setModel(self.file_model)
    

            # # Set the root path to the user's home directory
            home_path = os.path.expanduser('~')
            downloads_path = os.path.join(home_path, "Downloads")
            self.file_explorer.setRootIndex(self.file_model.index(downloads_path))

            # Connect signals
            self.file_explorer.clicked.connect(self.on_file_explorer_single_clicked)
            self.file_explorer.doubleClicked.connect(self.on_file_explorer_double_clicked)
    
            file_explorer_layout.addWidget(self.file_explorer)
            self.main_splitter.addWidget(file_explorer_widget)
    
        except Exception as e:
            print(f"Error in create_main_layout: {str(e)}")
    
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.main_splitter.addWidget(self.tab_widget)
    
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([200, 800])
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def on_header_clicked(self, logical_index):
        pass


    def new_file(self):
        self.file_manager.new_file()

    def on_tab_changed(self, index):
        current_editor = self.tab_widget.widget(index)
        if isinstance(current_editor, Editor):
            if current_editor in self.file_manager.file_paths:
                self.setWindowTitle(f"Notepad - {self.file_manager.file_paths[current_editor]}")
            else:
                self.setWindowTitle("Notepad - Untitled")

    def close_tab(self, index):
        self.tab_widget.removeTab(index)

    def undo(self):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, Editor):
            current_editor.undo()

    def redo(self):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, Editor):
            current_editor.redo()

    def find(self):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, Editor):
            current_editor.find_dialog()

    def toggle_file_explorer(self):
        if self.file_explorer.isVisible():
            self.file_explorer.hide()
        else:
            self.file_explorer.show()

    def load_last_session(self):
        open_files = self.settings.get_open_files()
        if open_files:
            self.file_manager.open_files_from_session(open_files)
        else:
            self.file_manager.new_file()

    def closeEvent(self, event):
        open_files = self.file_manager.get_all_open_files()
        self.settings.save_open_files(open_files)
        self.settings.save_window_geometry(self.saveGeometry())
        self.settings.save_window_state(self.saveState())
        event.accept()

    def setup_autosave(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.file_manager.autosave)
        self.autosave_timer.start(5000)  # Autosave every 5 minutes (300,000 ms)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            source_index = self.file_model.index(folder_path)
            proxy_index = self.proxy_model.mapFromSource(source_index)
            self.file_explorer.setRootIndex(proxy_index)
            self.current_folder = folder_path

    def on_file_explorer_double_clicked(self, index):
        source_index = self.proxy_model.mapToSource(index)
        if self.file_model.isDir(source_index):
            # If it's a directory, set it as the root index
            self.file_explorer.setRootIndex(index)
        else:
            # If it's a file, open it
            file_path = self.file_model.filePath(source_index)
            self.file_manager.open_file(file_path)
    
    def on_file_explorer_single_clicked(self, index):
        source_index = self.proxy_model.mapToSource(index)
        if self.file_model.isDir(source_index):
            if self.file_explorer.isExpanded(index):
                self.file_explorer.collapse(index)
            else:
                self.file_explorer.expand(index)
        else:
            # If it's a file, open it
            file_path = self.file_model.filePath(source_index)
            self.file_manager.open_file(file_path)

    def setup_file_explorer(self):
        # Set up the model and root path
        self.file_model = QFileSystemModel()
        home_path = os.path.expanduser("~")
        self.downloads_path = os.path.join(home_path, "Downloads")
        self.file_model.setRootPath(self.downloads_path)
        
        # Set up the proxy model
        self.proxy_model = FileNameProxyModel(self)
        self.proxy_model.setSourceModel(self.file_model)
        
        # Configure the file explorer
        self.file_explorer.setModel(self.proxy_model)
        self.file_explorer.setHeader(CustomHeaderView(Qt.Orientation.Horizontal, self))
        self.file_explorer.setColumnWidth(0, 200)
        self.file_explorer.setHeaderHidden(False)
        self.file_explorer.setAlternatingRowColors(True)
        self.file_explorer.setSortingEnabled(True)
        self.file_explorer.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        
        # Connect signals
        self.file_explorer.header().sectionClicked.connect(self.on_header_clicked)
        
        # Configure the file model
        self.file_model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.Hidden)
        
        # Set initial sorting
        self.file_explorer.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.proxy_model.sort(0, Qt.SortOrder.AscendingOrder)
        
        # Set the root index to the Downloads directory
        self._set_file_explorer_root(self.downloads_path)
    
    def _set_file_explorer_root(self, path):
        source_root_index = self.file_model.index(path)
        proxy_root_index = self.proxy_model.mapFromSource(source_root_index)
        self.file_explorer.setRootIndex(proxy_root_index)
        self.current_folder = path
    
    def go_up_directory(self):
        current_index = self.file_explorer.rootIndex()
        parent_index = current_index.parent()
        if parent_index.isValid():
            self.file_explorer.setRootIndex(parent_index)
            self.current_folder = self.file_model.filePath(self.proxy_model.mapToSource(parent_index))

    def load_settings(self):
        self.set_theme(self.settings.get_theme())
        if self.settings.get_autosave_enabled():
            self.autosave_timer.start()
        else:
            self.autosave_timer.stop()

    def setup_autosave(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.file_manager.autosave)
        if self.settings.get_autosave_enabled():
            self.autosave_timer.start(5000)
        else:
            self.autosave_timer.stop()

    def toggle_autosave(self, enabled):
        self.settings.set_autosave_enabled(enabled)
        if enabled:
            self.autosave_timer.start(5000)
        else:
            self.autosave_timer.stop()

    def change_theme(self, action):
        theme = action.data()
        self.set_theme(theme)
        self.settings.set_theme(theme)

    def set_theme(self, theme):
        if theme == 'system':
            qdarktheme.setup_theme('auto')
        elif theme == 'light':
            qdarktheme.setup_theme('light')
        elif theme == 'dark':
            qdarktheme.setup_theme('dark')
        
    def find_in_current_editor(self):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, Editor):
            current_editor.show_find_widget()

    def check_for_updates_silently(self):
        self.check_for_updates(silent=True)

    def check_for_updates(self, silent=False):
        current_version = "1.0.0"  # Replace with your current version
        github_api_url = "https://api.github.com/repos/feketefh/pady/releases/latest"
        
        # Get the AppData path for Pady
        appdata_path = os.path.join(os.getenv('APPDATA'), 'Pady')
        update_exe = os.path.join(appdata_path, 'updater.exe')

        try:
            response = requests.get(github_api_url)
            response.raise_for_status()
            latest_release = response.json()
            latest_version = latest_release['tag_name'].lstrip('v')  # Remove 'v' prefix if present

            if version.parse(latest_version) > version.parse(current_version):
                if not silent:
                    reply = QMessageBox.question(
                        self,
                        "Update Available",
                        f"A new version ({latest_version}) is available. Do you want to update?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        try:
                            if os.path.exists(update_exe):
                                subprocess.Popen(update_exe)
                                self.close()  # Close the current application
                            else:
                                QMessageBox.critical(self, "Update Error", f"Updater not found at {update_exe}")
                        except Exception as e:
                            QMessageBox.critical(self, "Update Error", f"Failed to start the update process: {str(e)}")
                else:
                    # Silently log that an update is available
                    print(f"Update available: version {latest_version}")
            else:
                if not silent:
                    QMessageBox.information(self, "No Updates", "You are using the latest version.")
        except requests.RequestException:
            if not silent:
                QMessageBox.warning(self, "Update Check Failed", "Failed to check for updates. Please try again later.")
        except Exception as e:
            # Catch any other exceptions and ignore them in silent mode
            if not silent:
                QMessageBox.warning(self, "Update Check Failed", f"An unexpected error occurred while checking for updates: {str(e)}")