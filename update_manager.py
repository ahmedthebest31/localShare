# update_manager.py
# Replicates the ImageType project's update mechanism exactly:
# same version.json format (version + direct_download_url + whats_new string),
# custom compare_versions, and a silent Inno Setup install (/VERYSILENT) after download.
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import requests

from PySide6.QtCore import QCoreApplication, QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

GITHUB_VERSION_URL = "https://raw.githubusercontent.com/ahmedthebest31/localShare/main/version.json"


def _tr(tr_func: Callable, key: str, fallback: str, *args) -> str:
    """Return a translated string with a fallback when the key is missing."""
    text = tr_func(key, *args)
    if not text or text == key:
        return fallback
    return text


def compare_versions(v1: str, v2: str) -> int:
    """Compare dotted version strings numerically. Returns 1, -1, or 0."""
    p1 = [int(x) for x in v1.split(".")]
    p2 = [int(x) for x in v2.split(".")]
    p1.extend([0] * (len(p2) - len(p1)))
    p2.extend([0] * (len(p1) - len(p2)))
    if p1 > p2:
        return 1
    if p1 < p2:
        return -1
    return 0


class VersionChecker(QThread):
    update_available = Signal(dict)
    no_update = Signal()
    error = Signal(str)

    def __init__(self, current_version: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.current_version = current_version

    def run(self) -> None:
        try:
            response = requests.get(GITHUB_VERSION_URL, timeout=5)
            response.raise_for_status()
            data = response.json()

            latest_version = data.get("version")
            if latest_version and compare_versions(latest_version, self.current_version) > 0:
                self.update_available.emit(data)
            else:
                self.no_update.emit()
        except requests.exceptions.RequestException as e:
            self.error.emit(str(e))
        except (json.JSONDecodeError, KeyError) as e:
            self.error.emit(f"Data error: {e}")


class Downloader(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, url: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.url = url

    def run(self) -> None:
        try:
            temp_dir = Path(tempfile.gettempdir())
            filename = self.url.rstrip("/").split("/")[-1] or "localshare_update.exe"
            save_path = temp_dir / filename

            response = requests.get(self.url, stream=True, timeout=10)
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))

            downloaded = 0
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)

            self.finished.emit(str(save_path))
        except Exception as e:
            self.error.emit(str(e))


class UpdateDialog(QDialog):
    def __init__(self, new_version: str, whats_new: str, tr_func: Callable, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.tr_func = tr_func
        self.setWindowTitle(_tr(tr_func, "dialog_title_update_available", "Update Available"))
        self.setMinimumSize(450, 350)
        self.setAccessibleName("Update available dialog")

        layout = QVBoxLayout(self)

        title_label = QLabel(f"<b>{_tr(tr_func, 'dialog_title_update_available', 'Update Available')} - v{new_version}</b>")
        title_label.setAccessibleName(f"New version {new_version} available")
        layout.addWidget(title_label)

        whats_new_label = QLabel(f"<b>{_tr(tr_func, 'whats_new_title', 'Whats New')}:</b>")
        layout.addWidget(whats_new_label)

        self.text_area = QPlainTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlainText(whats_new)
        self.text_area.setAccessibleName("What's new")
        layout.addWidget(self.text_area)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_skip = QPushButton(_tr(tr_func, "button_skip_version", "Skip This Version"))
        self.btn_skip.setAccessibleName("Skip this version")
        self.btn_remind = QPushButton(_tr(tr_func, "button_remind_later", "Remind Me Later"))
        self.btn_remind.setAccessibleName("Remind me later")
        self.btn_update = QPushButton(_tr(tr_func, "button_update_now", "Update Now"))
        self.btn_update.setAccessibleName("Update now")
        self.btn_update.setStyleSheet("font-weight: bold;")

        btn_layout.addWidget(self.btn_skip)
        btn_layout.addWidget(self.btn_remind)
        btn_layout.addWidget(self.btn_update)
        layout.addLayout(btn_layout)

        self.btn_skip.clicked.connect(self.reject_skip)
        self.btn_remind.clicked.connect(self.reject_remind)
        self.btn_update.clicked.connect(self.accept_update)

        self.action: str = "remind"

    def reject_skip(self) -> None:
        self.action = "skip"
        self.reject()

    def reject_remind(self) -> None:
        self.action = "remind"
        self.reject()

    def accept_update(self) -> None:
        self.action = "update"
        self.accept()


class UpdateManager(QObject):
    def __init__(
        self,
        parent_widget: QWidget,
        tr_func: Callable,
        load_config: Callable,
        save_config: Callable,
        current_version: str,
    ) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.tr = tr_func
        self.load_config = load_config
        self.save_config = save_config
        self.current_version = current_version
        self.silent: bool = False
        self.progress_dialog: Optional[QProgressDialog] = None
        self.checker_thread: Optional[VersionChecker] = None
        self.downloader_thread: Optional[Downloader] = None

    def check_for_updates(self, silent: bool = True) -> None:
        self.silent = silent

        if sys.platform != "win32":
            if not silent:
                QMessageBox.information(
                    self.parent_widget,
                    _tr(self.tr, "dialog_title_no_update", "No Update"),
                    "Automatic updates are currently available on Windows only. Please download the latest release manually.",
                )
            return

        if not silent:
            self.progress_dialog = QProgressDialog(
                _tr(self.tr, "checking_updates", "Checking for updates..."),
                "",
                0,
                0,
                self.parent_widget,
            )
            self.progress_dialog.setWindowTitle(_tr(self.tr, "app_name", "localShare"))
            self.progress_dialog.setCancelButton(None)
            self.progress_dialog.setModal(True)
            self.progress_dialog.show()

        self.checker_thread = VersionChecker(self.current_version, self)
        self.checker_thread.update_available.connect(self._on_update_available)
        self.checker_thread.no_update.connect(self._on_no_update)
        self.checker_thread.error.connect(self._on_error)
        self.checker_thread.finished.connect(self._cleanup_checker)
        self.checker_thread.start()

    def _cleanup_checker(self) -> None:
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def _on_update_available(self, data: Dict[str, Any]) -> None:
        new_version = data.get("version", "")

        if self.silent:
            config = self.load_config()
            if config.get("skipped_version") == new_version:
                return

        whats_new_data = data.get("whats_new", "")
        config = self.load_config()
        lang = config.get("language", "en")

        if isinstance(whats_new_data, dict):
            whats_new = whats_new_data.get(lang, _tr(self.tr, "msg_no_new_features", "No new features listed."))
        else:
            whats_new = str(whats_new_data)

        dialog = UpdateDialog(new_version, whats_new, self.tr, self.parent_widget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.action == "update":
                self._start_download(data.get("direct_download_url", ""))
        else:
            if dialog.action == "skip":
                config["skipped_version"] = new_version
                self.save_config(config)

    def _on_no_update(self) -> None:
        if not self.silent:
            QMessageBox.information(self.parent_widget, _tr(self.tr, "dialog_title_no_update", "No Update"), _tr(self.tr, "msg_no_update", "You are using the latest version."))

    def _on_error(self, error_msg: str) -> None:
        if not self.silent:
            QMessageBox.critical(self.parent_widget, _tr(self.tr, "dialog_title_error", "Error"), _tr(self.tr, "msg_network_error", "Network error: {0}", error_msg))

    def _start_download(self, url: str) -> None:
        if not url:
            QMessageBox.critical(self.parent_widget, _tr(self.tr, "dialog_title_error", "Error"), "Download URL is empty.")
            return

        self.progress_dialog = QProgressDialog(
            _tr(self.tr, "downloading_update_label", "Downloading update..."),
            _tr(self.tr, "button_cancel", "Cancel"),
            0,
            100,
            self.parent_widget,
        )
        self.progress_dialog.setWindowTitle(_tr(self.tr, "downloading_update_title", "Downloading Update"))
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)

        self.downloader_thread = Downloader(url, self)
        self.progress_dialog.canceled.connect(self.downloader_thread.terminate)

        self.downloader_thread.progress.connect(self.progress_dialog.setValue)
        self.downloader_thread.finished.connect(self._on_download_finished)
        self.downloader_thread.error.connect(self._on_download_error)
        self.downloader_thread.start()
        self.progress_dialog.show()

    def _on_download_finished(self, file_path: str) -> None:
        if self.progress_dialog:
            self.progress_dialog.close()

        try:
            subprocess.Popen([file_path, "/VERYSILENT", "/SUPPRESSMSGBOXES"])
            QCoreApplication.quit()
        except Exception as e:
            QMessageBox.critical(self.parent_widget, _tr(self.tr, "dialog_title_error", "Error"), f"Failed to launch installer:\n{e}")

    def _on_download_error(self, error_msg: str) -> None:
        if self.progress_dialog:
            self.progress_dialog.close()

        reply = QMessageBox.critical(
            self.parent_widget,
            _tr(self.tr, "dialog_title_error", "Error"),
            f"Download failed:\n{error_msg}\n\nDo you want to retry?",
            QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Retry:
            self._start_download(self.downloader_thread.url)
