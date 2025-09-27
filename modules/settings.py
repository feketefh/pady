import json
import os
import shutil
import base64
from PyQt6.QtCore import QByteArray

class Settings:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.settings_file = os.path.join(self.data_dir, "settings.json")
        self.session_file = os.path.join(self.data_dir, "session.json")
        
        self.default_settings = {
            "theme": "system",
            "autosave_enabled": False,
            "autosave_interval": 5000,
            "show_line_numbers": True,
            "font_family": "Consolas",
            "font_size": 10,
            "tab_width": 4,
            "word_wrap": False,
            "recent_files": [],
            "max_recent_files": 10,
            "window_geometry": None,
            "window_state": None
        }
        
        self.settings = self.load_settings()

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        print("Settings file is empty, using defaults")
                        return self.default_settings.copy()
                    
                    loaded_settings = json.loads(content)
                    
                    if 'window_geometry' in loaded_settings and loaded_settings['window_geometry']:
                        try:
                            geometry_data = base64.b64decode(loaded_settings['window_geometry'])
                            loaded_settings['window_geometry'] = QByteArray(geometry_data)
                        except:
                            loaded_settings['window_geometry'] = None
                    
                    if 'window_state' in loaded_settings and loaded_settings['window_state']:
                        try:
                            state_data = base64.b64decode(loaded_settings['window_state'])
                            loaded_settings['window_state'] = QByteArray(state_data)
                        except:
                            loaded_settings['window_state'] = None
                    
                    settings = self.default_settings.copy()
                    settings.update(loaded_settings)
                    return settings
        except json.JSONDecodeError as e:
            print(f"Settings file corrupted: {e}. Using defaults and backing up corrupted file.")
            if os.path.exists(self.settings_file):
                backup_file = self.settings_file + '.backup'
                shutil.copy2(self.settings_file, backup_file)
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return self.default_settings.copy()

    def save_settings(self):
        try:
            settings_to_save = self.settings.copy()
            
            if 'window_geometry' in settings_to_save and isinstance(settings_to_save['window_geometry'], QByteArray):
                settings_to_save['window_geometry'] = base64.b64encode(settings_to_save['window_geometry']).decode('utf-8')
            
            if 'window_state' in settings_to_save and isinstance(settings_to_save['window_state'], QByteArray):
                settings_to_save['window_state'] = base64.b64encode(settings_to_save['window_state']).decode('utf-8')
            
            temp_file = self.settings_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, indent=2, ensure_ascii=False)
            
            if os.path.exists(self.settings_file):
                os.remove(self.settings_file)
            os.rename(temp_file, self.settings_file)
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def add_recent_file(self, file_path):
        """Add a file to recent files list (separate from session)"""
        if not file_path:
            return
        
        recent_files = self.get('recent_files', [])
        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        recent_files = recent_files[:self.get('max_recent_files', 10)]
        self.set('recent_files', recent_files)

    def save_session(self, session_data):
        try:
            temp_file = self.session_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            os.rename(temp_file, self.session_file)
            
        except Exception as e:
            print(f"Error saving session: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def load_session(self):
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
        return {}