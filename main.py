# main.py
import sys
import json
import os
import requests 
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QMessageBox, QDialog, QHBoxLayout, QPushButton, QMenuBar
)
from PySide6.QtGui import QDesktopServices, QAction, QActionGroup # <-- تم نقلها هنا
from PySide6.QtCore import Qt, QUrl

# --- 1. Constants (Modified for localShare) ---
APP_VERSION = "0.1.0"
GITHUB_REPO_URL = "https://github.com/ahmedthebest31/localShare" # Updated name
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/ahmedthebest31/localShare/main/version.json" # Updated name

CONFIG_FILE = "config.json"
LANGUAGES_DIR = "languages"
THEMES_DIR = "themes"
TRANSLATIONS = {}
CURRENT_LANG = "en" # Focus on English as requested

# Ensure directories exist
for dir_path in [LANGUAGES_DIR, THEMES_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# --- 2. Boilerplate Functions (From your file) ---
# (load_config, save_config, load_translations, tr)

def load_config():
    """Loads configuration from file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            config.setdefault("language", "en")
            config.setdefault("theme", "dark_theme.qss") # Assuming you have this theme
            return config
    # NEW: Default settings for the server (will use later)
    return {
        "language": "en", 
        "theme": "dark_theme.qss",
        "port": 8000,
        "allow_upload": False
    }

def save_config(config):
    """Saves configuration to file."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def load_translations():
    """Loads all translation files from the languages directory."""
    global TRANSLATIONS
    if not os.path.exists(LANGUAGES_DIR):
        print("Warning: 'languages' directory not found.")
        return
    for filename in os.listdir(LANGUAGES_DIR):
        if filename.endswith(".json"):
            lang_code = filename.split(".")[0]
            try:
                with open(os.path.join(LANGUAGES_DIR, filename), "r", encoding="utf-8") as f:
                    TRANSLATIONS[lang_code] = json.load(f)
            except Exception as e:
                print(f"Failed to load language {lang_code}: {e}")

def tr(key, *args):
    """Translates a given key based on the current language."""
    # (Focus on English as requested)
    text = TRANSLATIONS.get("en", {}).get(key)
    if text is None:
        text = key # Fallback to the key itself if not found
    try:
        return text.format(*args)
    except (KeyError, TypeError):
        return text 

# --- 3. About Dialog (Adapted from your file) ---

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dialog_title_about"))
        self.setFixedSize(400, 250)
        self.setAccessibleName(tr("dialog_title_about") + " Dialog")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Updated text for localShare
        name_label = QLabel(f"<b>{tr('app_name')}</b>")
        name_label.setAccessibleName(tr("app_name"))
        layout.addWidget(name_label)

        version_label = QLabel(f"<b>{tr('about_dialog_version', APP_VERSION)}</b>")
        version_label.setAccessibleName(tr('about_dialog_version', APP_VERSION))
        layout.addWidget(version_label)

        description_label = QLabel(tr("about_dialog_description_text"))
        description_label.setWordWrap(True)
        description_label.setAccessibleName(tr("about_dialog_description_text"))
        layout.addWidget(description_label)

        developer_label = QLabel(f"{tr('about_dialog_developer')}: Ahmed Samy")
        developer_label.setAccessibleName(tr("about_dialog_developer"))
        layout.addWidget(developer_label)

        email_label = QLabel(f"{tr('about_dialog_email')}: ahmedthebest31@gmail.com")
        email_label.setOpenExternalLinks(True)
        email_label.setAccessibleName(tr("about_dialog_email"))
        layout.addWidget(email_label)

        layout.addStretch()

        close_button = QPushButton(tr("about_dialog_close_button"))
        close_button.setAccessibleName(tr("about_dialog_close_button") + " Button")
        close_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

# --- 4. Main Application Window (The new 'gutted' class) ---

class LocalShareApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        global CURRENT_LANG
        self.config = load_config() # Load config into self
        CURRENT_LANG = self.config.get("language", "en")
        
        self.apply_theme(self.config.get("theme", "dark_theme.qss"))

        self.setWindowTitle(tr("app_name"))
        self.resize(800, 600)
        self.setup_ui()
        self.retranslate_ui()
        self.connect_signals()
        self.load_themes_to_menu()
    
    def setup_menubar(self):
        menubar = self.menuBar()
        menubar.clear()

        # File Menu (Simplified from your file)
        file_menu = menubar.addMenu(tr("menu_file"))
        exit_action = file_menu.addAction(tr("menu_file_exit"))
        exit_action.triggered.connect(self.close)

        # Settings Menu (Kept from your file)
        settings_menu = menubar.addMenu(tr("menu_settings"))
        self.themes_menu = settings_menu.addMenu(tr("menu_settings_themes"))
        self.language_menu = settings_menu.addMenu(tr("menu_settings_language"))
        
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)
        # (We keep this logic, but will only load 'en.json' for now)
        for lang_code, translations in sorted(TRANSLATIONS.items()):
            lang_name = translations.get("lang_name", lang_code)
            action = self.language_menu.addAction(lang_name)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, lang=lang_code: self.change_language(lang))
            lang_group.addAction(action)
            if lang_code == CURRENT_LANG:
                action.setChecked(True)

        # Help Menu (Kept from your file)
        help_menu = menubar.addMenu(tr("menu_help"))
        about_action = help_menu.addAction(tr("about_action"))
        about_action.triggered.connect(self.show_about_dialog)
        check_for_updates_action = help_menu.addAction(tr("check_for_updates_action"))
        check_for_updates_action.triggered.connect(self.check_for_updates)
        help_menu.addSeparator()
        github_action = help_menu.addAction(tr("about_dialog_github"))
        github_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL)))

    def load_themes_to_menu(self):
        """Loads available themes (Identical to your file)"""
        self.themes_menu.clear()
        current_theme = self.config.get("theme", "dark_theme.qss")

        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)

        try:
            theme_files = [f for f in os.listdir(THEMES_DIR) if f.endswith(".qss")]
            for filename in sorted(theme_files):
                theme_name = os.path.splitext(filename)[0].replace("_", " ").title()
                action = self.themes_menu.addAction(theme_name)
                action.setCheckable(True)
                action.triggered.connect(lambda checked, file=filename: self.change_theme(file))
                theme_group.addAction(action)
                if filename == current_theme:
                    action.setChecked(True)
        except Exception as e:
            QMessageBox.critical(self, tr("dialog_title_error"), f"Could not load themes: {e}")

    def change_theme(self, theme_file):
        """Applies theme (Identical to your file)"""
        self.apply_theme(theme_file)
        self.config["theme"] = theme_file
        save_config(self.config)

    def apply_theme(self, theme_file):
        """Reads QSS file (Identical to your file)"""
        theme_path = os.path.join(THEMES_DIR, theme_file)
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                style_sheet = f.read()
            QApplication.instance().setStyleSheet(style_sheet)
        except FileNotFoundError:
            print(f"Warning: Theme file not found at {theme_path}. Using default.")
            QApplication.instance().setStyleSheet("")
        except Exception as e:
            QMessageBox.critical(self, tr("dialog_title_error"), f"Could not apply theme: {e}")

    def setup_ui(self):
        """Sets up the *new* UI for localShare."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # This is a placeholder layout. We will replace this.
        layout = QVBoxLayout(central_widget)
        self.placeholder_label = QLabel(tr("welcome_message"))
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(self.placeholder_label)

    def connect_signals(self):
        """We will add signals here later."""
        pass

    def retranslate_ui(self):
        """Updates all UI text for the current language."""
        self.setWindowTitle(tr("app_name"))
        if hasattr(self, 'placeholder_label'):
             self.placeholder_label.setText(tr("welcome_message"))
        self.setup_menubar()

    def show_about_dialog(self):
        """Shows About dialog (From your file)"""
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def check_for_updates(self):
        """Checks GitHub for updates (Adapted from your file)"""
        try:
            response = requests.get(GITHUB_VERSION_URL, timeout=5)
            response.raise_for_status()
            latest_version_data = response.json()
            latest_version = latest_version_data.get("version")
            
            if latest_version and self.compare_versions(latest_version, APP_VERSION) > 0:
                # (Simplified 'whats_new' as we only have 'en' now)
                whats_new = latest_version_data.get("en", tr("msg_no_new_features"))
                download_url = latest_version_data.get("direct_download_url", GITHUB_REPO_URL + "/releases")
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(tr("dialog_title_update_available"))
                info_text = tr("msg_update_info", APP_VERSION, latest_version)
                full_text = f"{info_text}\n\n**{tr('whats_new_title')}:**\n{whats_new}"
                msg_box.setText(full_text)
                msg_box.setIcon(QMessageBox.Icon.Information)
                
                download_button = msg_box.addButton(tr("button_direct_download"), QMessageBox.ButtonRole.ActionRole)
                open_page_button = msg_box.addButton(tr("button_open_download_page"), QMessageBox.ButtonRole.ActionRole)
                msg_box.addButton(QMessageBox.StandardButton.Ok)

                msg_box.exec()

                if msg_box.clickedButton() == download_button:
                    QDesktopServices.openUrl(QUrl(download_url))
                elif msg_box.clickedButton() == open_page_button:
                    QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL + "/releases"))
            else:
                QMessageBox.information(self, tr("dialog_title_no_update"), tr("msg_no_update"))
        except ImportError:
            QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_requests_missing"))
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_network_error", e))
        except (json.JSONDecodeError, KeyError):
            QMessageBox.critical(self, tr("dialog_title_error"), tr("msg_update_parse_error"))

    def compare_versions(self, v1, v2):
        """Compares two version strings (From your file)"""
        p1 = [int(x) for x in v1.split('.')]
        p2 = [int(x) for x in v2.split('.')]
        p1.extend([0] * (len(p2) - len(p1)))
        p2.extend([0] * (len(p1) - len(p2)))
        if p1 > p2: return 1
        if p1 < p2: return -1
        return 0

    def change_language(self, lang_code):
        """Changes language and saves (From your file)"""
        global CURRENT_LANG
        CURRENT_LANG = lang_code
        self.config["language"] = lang_code
        save_config(self.config)
        self.retranslate_ui()
        self.load_themes_to_menu()

# --- 5. Main Execution ---
        
def main():
    # Fix for high-DPI scaling
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    load_translations()
    app = QApplication(sys.argv)
    window = LocalShareApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()