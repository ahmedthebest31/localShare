# localShare

Seamless File Sharing over Local Network.

**localShare** is a lightweight desktop application that turns your PC into a local server. It allows you to share files between your computer and any other device (Android, iPhone, Tablet, or another PC) connected to the same Wi-Fi network.

The core philosophy is simplicity: the receiving device does **not** need to install any application. It only requires a web browser.

## Key Features

- **No Receiver App Required:** The other device downloads or uploads files directly via a web browser.
- **Fully Offline:** Works entirely on your Local Area Network (LAN). No internet connection is required.
- **Cross-Platform Receiver:** Compatible with any OS (Android, iOS, Linux, Windows, macOS).
- **Two-Way Transfer:** Supports both downloading files from the PC and uploading files to the PC.
- **Security:** Includes optional password protection and upload file size limits.
- **Clean UI:** Built with PySide6 for a native look and feel.

## Download

Grab the latest release from the [Releases page](https://github.com/ahmedthebest31/localShare/releases):

- **Windows Installer** (`localShare_Setup.exe`): Inno Setup installer, installs per user into `%LOCALAPPDATA%\localShare`.
- **Windows Portable** (`localShare-win-x64-Portable.zip`): self-contained executable, no installation required.
- **Linux** (`localShare-linux-x64.zip`) and **macOS** (`localShare-mac-x64.zip`): self-contained portable executables.
- **checksums-*.txt**: SHA256 checksums for verifying each asset.

## How to Use

1. Run the application.
2. Click **Select Folder** to choose the directory you want to share.
3. (Optional) Check **Enable Password** or **Allow Uploads** in the settings.
4. Click **Start Server**.
5. Scan the displayed QR code with your mobile camera, or type the URL into any browser on the local network.

## Technical Details

This project is built using:
- **Python 3.14**
- **PySide6** (GUI)
- **Flask** (Server Backend)
- **uv** (Dependency Management)

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE). Feel free to contribute, fork, or report issues.