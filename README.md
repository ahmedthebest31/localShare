# localShare

![License](https://img.shields.io/badge/License-GPLv3-blue)
![Python](https://img.shields.io/badge/Python-3.14-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Release](https://img.shields.io/github/v/release/ahmedthebest31/localShare)
![Downloads](https://img.shields.io/github/downloads/ahmedthebest31/localShare/total)

**Seamless file sharing over your local network.**

**localShare** is a lightweight, cross-platform desktop app that turns your PC into a local server. Share files between your computer and any other device (Android, iPhone, tablet, or another PC) on the same Wi-Fi network.

The core philosophy is simplicity: the receiving device needs **no app at all** — just a web browser.

## ✨ Key Features

- 📡 **No Receiver App Required** — any device with a browser downloads or uploads files directly.
- 🔀 **Two-Way Transfer** — download from the PC and upload to the PC.
- 🔐 **Optional Password Protection** — keep your shared files private with a password.
- 📏 **Upload Size Limit** — cap uploads from 1 MB to 1 GB.
- 🏷️ **Smart Upload Naming** — uploaded files are auto-renamed with the sender device name, and duplicates get a unique suffix.
- 🖥️ **Clean File Browser** — list or grid view with per-type icons (video, audio, image, text, archives), saved between visits.
- 📱 **QR Code Access** — scan the code with your phone to open the share instantly.
- 🌙 **Dark & Light Themes** — switchable from the menu.
- 🔄 **Automatic Updates** — the app checks for new versions and installs them silently.
- 🛡️ **Security First** — hardened against path-traversal attacks and uploads with unsafe filenames.
- 💻 **Truly Cross-Platform** — one codebase for Windows, macOS, and Linux.

## 📥 Download

Grab the latest release from the [Releases page](https://github.com/ahmedthebest31/localShare/releases):

- 🪟 **Windows Installer** (`localShare_Setup.exe`) — Inno Setup installer, installs per user into `%LOCALAPPDATA%\localShare`.
- 📦 **Windows Portable** (`localShare-win-x64-Portable.zip`) — self-contained executable, no installation required.
- 🐧 **Linux** (`localShare-linux-x64.zip`) — self-contained portable executable.
- 🍎 **macOS** (`localShare-mac-x64.zip`) — self-contained portable executable.
- ✅ **checksums-*.txt** — SHA256 checksums for verifying every asset.

## 🚀 How to Use

1. Run the application.
2. Click **Share Folder...** and choose the directory you want to share.
3. (Optional) Enable **Use Password** or **Allow Uploads**, and set an upload size limit.
4. Click **Start Server**.
5. Scan the displayed QR code with your phone, or type the shown URL into any browser on the local network.

## 🛠️ Technical Details

Built with:

- 🐍 **Python 3.14**
- 🧩 **PySide6** — modern desktop GUI
- 🏭 **Flask** — web server backend
- 📦 **uv** — fast, reliable dependency management
- 📦 **PyInstaller** — standalone executables
- 🪟 **Inno Setup** — Windows installer

## 🔄 Automatic Updates

localShare checks for updates on startup. When a new version is available, you can update with one click: the installer downloads automatically and installs silently, then the app restarts.

## 📄 License

This project is licensed under the [GNU General Public License v3.0](LICENSE). Feel free to contribute, fork, or report issues.
