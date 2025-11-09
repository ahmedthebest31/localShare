# main.py
import sys
import json
import os
import requests 
import socket 
import qrcode 
import io 
import functools # <-- NEEDED FOR THE FIX

# NEW: Import our server logic from the new file
from server_handler import ServerThread, WorkerSignals

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QMessageBox, QDialog, QHBoxLayout, QPushButton, QMenuBar,
    QGridLayout, QLineEdit, QCheckBox, QSpinBox, QPlainTextEdit,
    QFileDialog, QSizePolicy 
)
from PySide6.QtGui import QDesktopServices, QAction, QActionGroup, QPixmap, QImage, QGuiApplication
from PySide6.QtCore import Qt, QUrl

# --- 1. Constants (Unchanged) ---
APP_VERSION = "0.1.0"
GITHUB_REPO_URL = "https://github.com/ahmedthebest31/localShare" 
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/ahmedthebest31/localShare/main/version.json" 
CONFIG_FILE = "config.json"
LANGUAGES_DIR = "languages"
THEMES_DIR = "themes"
TRANSLATIONS = {}
CURRENT_LANG = "en" 

# --- 2. Boilerplate Functions (Unchanged) ---

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            config.setdefault("language", "en")
            config.setdefault("theme", "dark_theme.qss")
            return config
    return {
        "language": "en", 
        "theme": "dark_theme.qss",
        "port": 8000,
        "allow_upload": False
    }

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def load_translations():
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
    text = TRANSLATIONS.get("en", {}).get(key)
    if text is None:
        text = key 
    try:
        return text.format(*args)
    except (KeyError, TypeError):
        return text 

# --- 3. About Dialog (Unchanged) ---

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dialog_title_about"))
        self.setFixedSize(400, 250)
        self.setAccessibleName(tr("dialog_title_about") + " Dialog")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        name_label = QLabel(f"<b>{tr('app_name')}</b>")
        layout.addWidget(name_label)
        version_label = QLabel(f"<b>{tr('about_dialog_version', APP_VERSION)}</b>")
        layout.addWidget(version_label)
        description_label = QLabel(tr("about_dialog_description_text"))
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        developer_label = QLabel(f"{tr('about_dialog_developer')}: Ahmed Samy")
        layout.addWidget(developer_label)
        email_label = QLabel(f"{tr('about_dialog_email')}: ahmedthebest31@gmail.com")
        email_label.setOpenExternalLinks(True)
        layout.addWidget(email_label)
        layout.addStretch()
        close_button = QPushButton(tr("about_dialog_close_button"))
        close_button.clicked.connect(self.accept)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

# --- 4. Main Application Window (Now imports server) ---

class LocalShareApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        global CURRENT_LANG
        self.config = load_config() 
        CURRENT_LANG = self.config.get("language", "en")
        
        self.apply_theme(self.config.get("theme", "dark_theme.qss"))

        self.setWindowTitle(tr("app_name"))
        self.resize(1000, 700) 
        
        self.share_path = None 
        self.server_thread = None 

        self.setup_ui()
        self.retranslate_ui()
        self.connect_signals() 
        self.load_themes_to_menu()
    
    def setup_menubar(self):
        # (Unchanged from previous step)
        menubar = self.menuBar()
        menubar.clear()
        file_menu = menubar.addMenu(tr("menu_file"))
        self.select_file_action = file_menu.addAction(tr("menu_file_select_file")) 
        self.select_folder_action = file_menu.addAction(tr("menu_file_select_folder")) 
        self.select_file_action.setEnabled(False) 
        file_menu.addSeparator()
        exit_action = file_menu.addAction(tr("menu_file_exit"))
        exit_action.triggered.connect(self.close)
        settings_menu = menubar.addMenu(tr("menu_settings"))
        self.themes_menu = settings_menu.addMenu(tr("menu_settings_themes"))
        self.language_menu = settings_menu.addMenu(tr("menu_settings_language"))
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)
        for lang_code, translations in sorted(TRANSLATIONS.items()):
            lang_name = translations.get("lang_name", lang_code)
            action = self.language_menu.addAction(lang_name)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, lang=lang_code: self.change_language(lang))
            lang_group.addAction(action)
            if lang_code == CURRENT_LANG:
                action.setChecked(True)
        help_menu = menubar.addMenu(tr("menu_help"))
        about_action = help_menu.addAction(tr("about_action"))
        about_action.triggered.connect(self.show_about_dialog)
        check_for_updates_action = help_menu.addAction(tr("check_for_updates_action"))
        check_for_updates_action.triggered.connect(self.check_for_updates)
        help_menu.addSeparator()
        github_action = help_menu.addAction(tr("about_dialog_github"))
        github_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL)))

    def load_themes_to_menu(self):
        # (Unchanged)
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
        # (Unchanged)
        self.apply_theme(theme_file)
        self.config["theme"] = theme_file
        save_config(self.config)

    def apply_theme(self, theme_file):
        # (Unchanged)
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
        # (Unchanged from previous step)
        """Sets up the UI for localShare with proper accessibility."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        left_layout = QVBoxLayout()
        controls_layout = QGridLayout()
        self.start_server_button = QPushButton()
        self.start_server_button.setMinimumHeight(40)
        controls_layout.addWidget(self.start_server_button, 0, 0, 1, 2)
        self.stop_server_button = QPushButton()
        self.stop_server_button.setMinimumHeight(40)
        self.stop_server_button.setEnabled(False) 
        controls_layout.addWidget(self.stop_server_button, 0, 2, 1, 2)
        self.port_label = QLabel()
        self.port_spinbox = QSpinBox()
        self.port_spinbox.setRange(1024, 65535)
        self.port_spinbox.setValue(self.config.get("port", 8000))
        controls_layout.addWidget(self.port_label, 1, 0)
        controls_layout.addWidget(self.port_spinbox, 1, 1)
        self.port_label.setBuddy(self.port_spinbox) 
        self.allow_upload_checkbox = QCheckBox()
        self.allow_upload_checkbox.setChecked(self.config.get("allow_upload", False))
        controls_layout.addWidget(self.allow_upload_checkbox, 1, 2, 1, 2)
        self.rename_uploads_checkbox = QCheckBox()
        self.rename_uploads_checkbox.setChecked(True) 
        controls_layout.addWidget(self.rename_uploads_checkbox, 2, 2, 1, 2)
        self.password_checkbox = QCheckBox() 
        controls_layout.addWidget(self.password_checkbox, 2, 0, 1, 2)
        self.password_label = QLabel()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        controls_layout.addWidget(self.password_label, 3, 0) 
        controls_layout.addWidget(self.password_edit, 3, 1, 1, 3) 
        self.password_label.setBuddy(self.password_edit) 
        self.password_label.setVisible(False)
        self.password_edit.setVisible(False)
        left_layout.addLayout(controls_layout)
        self.log_label = QLabel()
        left_layout.addWidget(self.log_label)
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        left_layout.addWidget(self.log_display) 
        self.log_label.setBuddy(self.log_display) 
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(self.status_label)
        self.url_label = QLabel()
        self.url_edit = QLineEdit()
        self.url_edit.setReadOnly(True)
        self.copy_url_button = QPushButton()
        url_layout = QHBoxLayout()
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.url_edit)
        url_layout.addWidget(self.copy_url_button)
        right_layout.addLayout(url_layout)
        self.url_label.setBuddy(self.url_edit) 
        self.qr_code_label = QLabel()
        self.qr_code_label.setMinimumSize(250, 250)
        self.qr_code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_code_label.setStyleSheet("border: 1px solid gray;")
        right_layout.addWidget(self.qr_code_label)
        right_layout.addStretch() 
        main_layout.addLayout(left_layout, 7) 
        main_layout.addLayout(right_layout, 3) 

    def connect_signals(self):
        # (Unchanged from previous step)
        """Connects all UI signals to their functions."""
        self.password_checkbox.toggled.connect(self.toggle_password_fields)
        self.start_server_button.clicked.connect(self.start_server)
        self.stop_server_button.clicked.connect(self.stop_server)
        self.select_folder_action.triggered.connect(self.select_folder)
        self.copy_url_button.clicked.connect(self.copy_url)

    def toggle_password_fields(self, checked):
        # (Unchanged)
        self.password_label.setVisible(checked)
        self.password_edit.setVisible(checked)
        if checked:
            self.password_edit.setFocus()
        
    def retranslate_ui(self):
        # (Unchanged from previous step)
        self.setWindowTitle(tr("app_name"))
        self.setup_menubar() 
        self.start_server_button.setText(tr("start_server_button"))
        self.stop_server_button.setText(tr("stop_server_button"))
        self.port_label.setText(tr("port_label"))
        self.password_checkbox.setText(tr("password_checkbox")) 
        self.password_label.setText(tr("password_label"))
        self.allow_upload_checkbox.setText(tr("allow_upload_checkbox"))
        self.rename_uploads_checkbox.setText(tr("rename_uploads_checkbox"))
        self.log_label.setText(tr("log_label"))
        self.status_label.setText(tr("status_stopped"))
        self.url_label.setText(tr("url_label"))
        self.copy_url_button.setText(tr("copy_url_button"))
        self.qr_code_label.setText(tr("qr_code_placeholder"))
        self.select_file_action.setText(tr("menu_file_select_file"))
        self.select_folder_action.setText(tr("menu_file_select_folder"))

    # --- Server Control Functions (Modified to use translated logs) ---

    def select_folder(self):
        """Opens a dialog to select a folder to share."""
        path = QFileDialog.getExistingDirectory(self, tr("menu_file_select_folder"))
        if path:
            self.share_path = path
            self.log(tr("log_share_folder_selected", path))
            self.start_server_button.setEnabled(True)

    def start_server(self):
        """Starts the web server in a new thread."""
        if not self.share_path:
            QMessageBox.warning(self, tr("dialog_title_error"), tr("msg_select_folder_first"))
            return

        port = self.port_spinbox.value()
        self.log(tr("log_server_starting", port))

        self.set_ui_state(running=True)
        self.status_label.setText(tr("status_starting"))

        self.server_thread = ServerThread(port, self.share_path)
        self.server_thread.signals.server_started.connect(self.on_server_started)
        self.server_thread.signals.log_message.connect(self.log) # Pass log messages directly
        self.server_thread.signals.server_stopped.connect(self.on_server_stopped)
        self.server_thread.start()

    def stop_server(self):
        """Stops the web server thread."""
        if self.server_thread:
            # log_server_stopping is now emitted from the thread
            self.server_thread.stop()
        
    def on_server_started(self, ip, port):
        """Callback when the server thread confirms it has started."""
        url = f"http://{ip}:{port}"
        self.log(tr("log_server_started", url))
        
        self.status_label.setText(tr("status_running", url))
        self.url_edit.setText(url)
        
        self.generate_qr_pixmap(url)

    def on_server_stopped(self):
        """Callback when the server thread confirms it has stopped."""
        self.log(tr("log_server_stopped"))
        self.set_ui_state(running=False)
        self.server_thread = None

    def log(self, message):
        """Appends a message to the activity log."""
        # Check if the message is a key or a raw string
        if message.startswith("[Access]") or message.startswith("[Error]"):
            self_translated_message = message
        else:
            self_translated_message = tr(message) # Translate log keys
        
        self.log_display.appendPlainText(self_translated_message)
    
    def copy_url(self):
        """Copies the sharing URL to the clipboard."""
        if self.url_edit.text():
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.url_edit.text())
            self.log("log_url_copied") # Use the key

    def set_ui_state(self, running):
        """Enables/disables UI elements based on server state."""
        self.start_server_button.setEnabled(not running)
        self.stop_server_button.setEnabled(running)
        
        self.port_spinbox.setEnabled(not running)
        self.password_checkbox.setEnabled(not running)
        self.password_edit.setEnabled(not running)
        self.allow_upload_checkbox.setEnabled(not running)
        self.rename_uploads_checkbox.setEnabled(not running)
        self.select_file_action.setEnabled(not running and False) # Keep disabled for now
        self.select_folder_action.setEnabled(not running)
        
        if not running:
            self.status_label.setText(tr("status_stopped"))
            self.url_edit.clear()
            self.qr_code_label.setText(tr("qr_code_placeholder"))
            self.qr_code_label.setPixmap(QPixmap()) # Clear the pixmap
            self.start_server_button.setEnabled(self.share_path is not None)

    def generate_qr_pixmap(self, text):
        """Generates a QPixmap from the given text."""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, "PNG")
            qt_image = QImage.fromData(buffer.getvalue(), "PNG")
            pixmap = QPixmap.fromImage(qt_image)
            
            self.qr_code_label.setPixmap(pixmap.scaled(
                self.qr_code_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            self.qr_code_label.setAccessibleName(tr("qr_code_desc", text))
        except Exception as e:
            self.log(f"[Error] Could not generate QR code: {e}")

    # --- Boilerplate Functions (Unchanged) ---
    
    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def check_for_updates(self):
        try:
            response = requests.get(GITHUB_VERSION_URL, timeout=5)
            response.raise_for_status()
            latest_version_data = response.json()
            latest_version = latest_version_data.get("version")
            if latest_version and self.compare_versions(latest_version, APP_VERSION) > 0:
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
        p1 = [int(x) for x in v1.split('.')]
        p2 = [int(x) for x in v1.split('.')]
        p1.extend([0] * (len(p2) - len(p1)))
        p2.extend([0] * (len(p1) - len(p2)))
        if p1 > p2: return 1
        if p1 < p2: return -1
        return 0

    def change_language(self, lang_code):
        global CURRENT_LANG
        CURRENT_LANG = lang_code
        self.config["language"] = lang_code
        save_config(self.config)
        self.retranslate_ui()
        self.load_themes_to_menu()
        
    def closeEvent(self, event):
        """Ensure the server thread is stopped when closing the window."""
        self.stop_server()
        event.accept()

# --- 6. Main Execution ---
        
def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCheckOpenGLContextThreadAffinity)
    load_translations()
    app = QApplication(sys.argv)
    window = LocalShareApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()