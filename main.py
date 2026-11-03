# main.py
import sys
import json
import os
import qrcode 
import io 
from pathlib import Path

from server_handler import ServerThread

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QMessageBox, QDialog, QHBoxLayout, QPushButton,
    QGridLayout, QLineEdit, QCheckBox, QSpinBox, QPlainTextEdit,
    QFileDialog
)
from PySide6.QtGui import QDesktopServices, QActionGroup, QPixmap, QImage, QGuiApplication, QIcon
from PySide6.QtCore import QCoreApplication, Qt, QUrl, QStandardPaths

# --- 1. Constants ---
APP_VERSION = "1.0.0"
GITHUB_REPO_URL = "https://github.com/ahmedthebest31/localShare" 

def get_app_version() -> str:
    """Return the installed version, falling back to the constant when frozen."""
    try:
        import importlib.metadata
        return importlib.metadata.version("localshare")
    except Exception:
        return APP_VERSION

class PathProvider:
    """Resolves resource and data directories for both source and frozen runs."""

    @staticmethod
    def is_frozen() -> bool:
        return getattr(sys, "frozen", False)

    @classmethod
    def resource_dir(cls) -> Path:
        if cls.is_frozen():
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass and Path(meipass) != Path(sys.executable).parent:
                return Path(meipass)
            return Path(sys.executable).parent
        return Path(__file__).resolve().parent

    @classmethod
    def data_dir(cls) -> Path:
        if cls.is_frozen():
            base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
            data = Path(base)
            data.mkdir(parents=True, exist_ok=True)
            return data
        return Path(__file__).resolve().parent

QCoreApplication.setApplicationName("localShare")

RESOURCE_DIR = PathProvider.resource_dir()
DATA_DIR = PathProvider.data_dir()
CONFIG_FILE = str(DATA_DIR / "config.json")
LANGUAGES_DIR = str(RESOURCE_DIR / "languages")
THEMES_DIR = str(RESOURCE_DIR / "themes")
ICON_PATH = RESOURCE_DIR / "assets" / "icon_64.png"

TRANSLATIONS = {}
CURRENT_LANG = "en" 

# --- 2. Boilerplate Functions ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            config.setdefault("language", "en")
            config.setdefault("theme", "dark_theme.qss")
            config.setdefault("port", 8000)
            config.setdefault("allow_upload", False)
            return config
    return {
        "language": "en", 
        "theme": "dark_theme.qss",
        "port": 8000,
        "allow_upload": False
    }

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except OSError as e:
        print(f"[Error] Could not save config to {CONFIG_FILE}: {e}")

def load_translations():
    global TRANSLATIONS, CURRENT_LANG
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
    CURRENT_LANG = load_config().get("language", "en")

def tr(key, *args):
    text = TRANSLATIONS.get(CURRENT_LANG, {}).get(key, TRANSLATIONS.get("en", {}).get(key))
    if text is None:
        text = key 
    try:
        return text.format(*args)
    except (IndexError, KeyError, TypeError):
        return text 

# --- 3. About Dialog ---
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
        version_label = QLabel(f"<b>{tr('about_dialog_version', get_app_version())}</b>")
        layout.addWidget(version_label)
        description_label = QLabel(tr("about_dialog_description_text"))
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        developer_label = QLabel(f"{tr('about_dialog_developer')}: Ahmed Samy")
        layout.addWidget(developer_label)
        email_label = QLabel('<a href="mailto:ahmedthebest31@gmail.com">ahmedthebest31@gmail.com</a>')
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

# --- 4. Main Application Window ---
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

        from update_manager import UpdateManager
        self.update_manager = UpdateManager(self, tr, load_config, save_config, get_app_version())
        self.update_manager.check_for_updates(silent=True)
    
    def setup_menubar(self):
        menubar = self.menuBar()
        menubar.clear()
        file_menu = menubar.addMenu(tr("menu_file"))
        self.select_folder_action = file_menu.addAction(tr("menu_file_select_folder")) 
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
        self.apply_theme(theme_file)
        self.config["theme"] = theme_file
        save_config(self.config)

    def apply_theme(self, theme_file):
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

        self.limit_upload_size_checkbox = QCheckBox()
        controls_layout.addWidget(self.limit_upload_size_checkbox, 4, 0, 1, 2)

        self.upload_size_limit_label = QLabel()
        self.upload_size_spinbox = QSpinBox()
        self.upload_size_spinbox.setRange(1, 1024) # 1MB to 1GB
        self.upload_size_spinbox.setValue(16) # Default to 16MB
        self.upload_size_spinbox.setSuffix(" MB")
        controls_layout.addWidget(self.upload_size_limit_label, 5, 0)
        controls_layout.addWidget(self.upload_size_spinbox, 5, 1)
        self.upload_size_limit_label.setBuddy(self.upload_size_spinbox)
        self.upload_size_limit_label.setVisible(False)
        self.upload_size_spinbox.setVisible(False)

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
        """Connects all UI signals to their functions."""
        self.password_checkbox.toggled.connect(self.toggle_password_fields)
        self.start_server_button.clicked.connect(self.start_server)
        self.stop_server_button.clicked.connect(self.stop_server)
        self.select_folder_action.triggered.connect(self.select_folder)
        self.copy_url_button.clicked.connect(self.copy_url)
        self.limit_upload_size_checkbox.toggled.connect(self.toggle_upload_limit_fields)

    def toggle_password_fields(self, checked):
        self.password_label.setVisible(checked)
        self.password_edit.setVisible(checked)
        if checked:
            self.password_edit.setFocus()

    def toggle_upload_limit_fields(self, checked):
        self.upload_size_limit_label.setVisible(checked)
        self.upload_size_spinbox.setVisible(checked)
        if checked:
            self.upload_size_spinbox.setFocus()
        
    def retranslate_ui(self):
        self.setWindowTitle(tr("app_name"))
        self.setup_menubar() 
        self.start_server_button.setText(tr("start_server_button"))
        self.stop_server_button.setText(tr("stop_server_button"))
        self.port_label.setText(tr("port_label"))
        self.password_checkbox.setText(tr("password_checkbox")) 
        self.password_label.setText(tr("password_label"))
        self.allow_upload_checkbox.setText(tr("allow_upload_checkbox")) 
        self.rename_uploads_checkbox.setText(tr("rename_uploads_checkbox")) 
        self.limit_upload_size_checkbox.setText(tr("limit_upload_size_checkbox"))
        self.upload_size_limit_label.setText(tr("upload_size_limit_label"))
        self.log_label.setText(tr("log_label"))
        self.status_label.setText(tr("status_stopped"))
        self.url_label.setText(tr("url_label"))
        self.copy_url_button.setText(tr("copy_url_button"))
        self.qr_code_label.setText(tr("qr_code_placeholder"))
        self.select_folder_action.setText(tr("menu_file_select_folder"))

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
        
        password = None
        if self.password_checkbox.isChecked():
            password = self.password_edit.text()
            if not password:
                QMessageBox.warning(self, tr("dialog_title_error"), tr("msg_password_empty"))
                return
            self.log(tr("log_password_enabled"))
        
        allow_upload = self.allow_upload_checkbox.isChecked()
        rename_upload = self.rename_uploads_checkbox.isChecked()
        if allow_upload:
            self.log(tr("log_uploads_enabled"))

        max_upload_size = 0
        if self.limit_upload_size_checkbox.isChecked():
            max_upload_size = self.upload_size_spinbox.value()

        self.config["port"] = port
        self.config["allow_upload"] = allow_upload
        save_config(self.config)

        self.log(tr("log_server_starting", port))
        self.set_ui_state(running=True)
        self.status_label.setText(tr("status_starting"))

        self.server_thread = ServerThread(
            port, 
            self.share_path, 
            password, 
            allow_upload, 
            rename_upload,
            max_upload_size
        )
        
        self.server_thread.signals.server_started.connect(self.on_server_started)
        self.server_thread.signals.log_message.connect(self.log) 
        self.server_thread.signals.server_stopped.connect(self.on_server_stopped)
        self.server_thread.start()

    def stop_server(self):
        """Stops the web server thread."""
        if self.server_thread and self.server_thread.is_alive():
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
        if message.startswith(("[Access]", "[Error]", "[Auth]", "[Upload]", "[Security]")):
            self_translated_message = message
        else:
            self_translated_message = tr(message) 
        
        self.log_display.appendPlainText(self_translated_message)
    
    def copy_url(self):
        """Copies the sharing URL to the clipboard."""
        if self.url_edit.text():
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.url_edit.text())
            self.log("log_url_copied") 

    def set_ui_state(self, running):
        """Enables/disables UI elements based on server state."""
        self.start_server_button.setEnabled(not running)
        self.stop_server_button.setEnabled(running)
        self.port_spinbox.setEnabled(not running)
        self.password_checkbox.setEnabled(not running)
        self.password_edit.setEnabled(not running and self.password_checkbox.isChecked())
        self.allow_upload_checkbox.setEnabled(not running) 
        self.rename_uploads_checkbox.setEnabled(not running) 
        self.limit_upload_size_checkbox.setEnabled(not running)
        self.upload_size_spinbox.setEnabled(not running and self.limit_upload_size_checkbox.isChecked())
        self.select_folder_action.setEnabled(not running)
        
        if not running:
            self.status_label.setText(tr("status_stopped"))
            self.url_edit.clear()
            self.qr_code_label.setText(tr("qr_code_placeholder"))
            self.qr_code_label.setPixmap(QPixmap())
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
    
    def show_about_dialog(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def check_for_updates(self):
        self.update_manager.check_for_updates(silent=False)

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
    load_translations()
    app = QApplication(sys.argv)
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = LocalShareApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
