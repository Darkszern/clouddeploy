# LXCC Cloud Deploy Tool

A GUI-based deployment tool for managing LXCC bots on a remote Linux server via SSH/SFTP.

## Features

- **SSH/SFTP Connectivity** - Secure connection to your cloud server
- **Script Deployment** - Upload, replace, and restart bot scripts remotely
- **Bot Status Monitoring** - Real-time Online/Offline status display
- **Multi-Bot Manager** - Manage multiple bots via tmux sessions (create, rename, delete, start, stop)
- **Deployer Tracking** - Each deployment logs who deployed (name prompt before deploy)
- **Deployment Log** - View full deployment history with timestamps, deployer names, and computer names
- **venv Support** - Optional venv activation when creating new tmux sessions
- **Requirements Installation** - Install pip packages on the remote server
- **Cloud Configuration** - Bot configs and deployment logs stored on the server
- **Shell Access** - Open a terminal with SSH connection to any tmux session
- **Configurable Connection** - IP, password, and bot settings stored locally, editable via Config button
- **Auto-Update** - Checks GitHub Releases on startup, downloads and runs the installer automatically
- **Cross-Platform Shell** - Supports Windows CMD, macOS Terminal, and Linux terminal emulators
- **Light/Dark Mode** - Toggle between light and dark theme, preference is saved
- **Professional Installer** - Windows installer with GUI, progress bar, and uninstaller

## Installation (End User)

### Download & Install

1. Download `LXCC_CloudDeploy_Setup_v1.22.1.exe` from the [Releases page](https://github.com/Darkszern/clouddeploy/releases)
2. Run the installer - it will guide you through the setup:
   - Choose installation directory (default: `C:\Program Files\LXCC Cloud Deploy`)
   - Select shortcuts (Desktop, Start Menu)
   - Watch the progress bar during installation
3. Launch **DeployTool** from the desktop shortcut or Start Menu

### First Start

On the first launch, you will be prompted to enter:
- **Server IP** - The IP address of your cloud server
- **Password** - The SSH root password

These credentials are saved locally in `%APPDATA%\LXCC Cloud Deploy\config.json` and are reused for all future connections.

### Reinstall / Update / Uninstall

Simply run the installer again. If the application is already installed, you will be asked:
- **Reinstall / Update** - Overwrites the existing installation with the new version
- **Uninstall** - Removes the application (optionally keeps your config)
- **Cancel** - Exit without changes

You can also uninstall via **Windows Settings > Apps > LXCC Cloud Deploy**.

## Building the Installer (Developer)

### Prerequisites

- **Python 3.8+** with `pip` ([Download](https://www.python.org/downloads/))
- **Inno Setup 6** ([Download](https://jrsoftware.org/isdl.php))
- Both must be in PATH or installed in their default locations

### Build Steps

1. Clone this repository
2. Run `build_installer.bat`
3. The script will:
   - Install Python packages (`paramiko`, `pyinstaller`)
   - Build `DeployTool.exe` using PyInstaller
   - Package everything into a professional installer using Inno Setup
4. Output:
   - `dist_installer\LXCC_CloudDeploy_Setup_v1.22.1.exe` - The installer to distribute
   - `dist\DeployTool.exe` - Standalone EXE (without installer)

### Build Output Structure

```
clouddeploy/
  dist/
    DeployTool.exe              <- Standalone application
  dist_installer/
    LXCC_CloudDeploy_Setup_v1.22.1.exe  <- Installer to distribute
```

## Usage

### Login

After setup, each start shows a login window with the saved password pre-filled. Simply click **Login** to connect.

### Main Window

| Button | Description |
|--------|-------------|
| **Select Script** | Choose a local `.py` file to deploy |
| **Deploy** | Upload the selected script and restart the bot |
| **Download Script** | Download the current remote script as backup |
| **Start Bot** | Start the main LXCCBot |
| **Stop Bot** | Stop the main LXCCBot |
| **Install Requirements** | Upload and install `requirements.txt` on the server |
| **Open Shell** | Open a terminal with SSH connection to the bot's tmux session |
| **Bot Manager** | Open the Multi-Bot Manager for managing multiple bots |
| **Config** | Edit server IP, password, and main bot settings |
| **Deployment Log** | View full deployment history with timestamps and deployer names |

### Config Button

Click **Config** in the main window to change the server IP, password, SSH user, bot name, script path, or tmux session name at any time. Connection settings are tested before saving.

### Multi-Bot Manager

Manage multiple tmux sessions and bots:
- Create, rename, and delete tmux sessions
- Optionally activate a venv when creating a new session
- Add bots with custom names and script paths
- Start/stop individual bots
- Deploy scripts to specific bots (with deployer name tracking)
- Download scripts from bots
- Install requirements per bot
- Open shell to any session

## File Structure

### Source Repository

```
clouddeploy/
  cdpl.py              - Main application (source code)
  installer.iss        - Inno Setup installer script
  build_installer.bat  - Build script (PyInstaller + Inno Setup)
  LXCCLOGO.ico         - Application icon
  README.md            - This file
```

### After Installation on Windows

```
C:\Program Files\LXCC Cloud Deploy\
  DeployTool.exe       - Main application
  LXCCLOGO.ico         - Application icon
  unins000.exe         - Uninstaller
  unins000.dat         - Uninstaller data

%APPDATA%\LXCC Cloud Deploy\
  config.json          - Local configuration (created on first start)
```

## Auto-Update

On each startup, the tool checks the [latest GitHub Release](https://github.com/Darkszern/clouddeploy/releases/latest) for a newer version. If a newer version is available, a dialog is shown with **Update now** and **Later** buttons.

When updating, the tool downloads the Inno Setup installer from the release and runs it silently with `/VERYSILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /NORESTART`. The app auto-restarts after the update.

To publish a new version:
1. Update `CURRENT_VERSION` in `cdpl.py`
2. Create a Git tag (e.g. `v1.22.1`) and push it
3. GitHub Actions builds the EXE + installer and creates the release automatically

## Installer Features

The installer (`LXCC_CloudDeploy_Setup_v1.22.1.exe`) provides:

- **Welcome screen** with version info
- **Language selection** (English / German)
- **Installation directory chooser**
- **Progress bar** showing installation steps
- **Desktop shortcut** (optional)
- **Start Menu entry** (optional)
- **Launch after install** option
- **Reinstall / Uninstall detection** when already installed
- **Clean uninstall** via Add/Remove Programs with option to keep config
- **Admin elevation** when required

## Version History

| Version | Changes |
|---------|---------|
| v1.0 | Basic framework with SSH connection |
| v1.1 | SFTP upload function |
| v1.2 | GUI implementation with tkinter |
| v1.3 | Deployment with automatic restart |
| v1.4 | Login window with password verification |
| v1.5 | Status display (Online/Offline) |
| v1.6 | Start/Stop buttons for bot control |
| v1.7 | Download function for script backup |
| v1.8 | Interactive shell window |
| v1.9 | Threading for shell output |
| v1.10 | Improved status detection (ps aux) |
| v1.11 | Code commenting and documentation |
| v1.12 | Multi-Bot Manager |
| v1.13 | Requirements installation |
| v1.14 | Automatic icon download from server |
| v1.15 | English translation and CMD shell integration |
| v1.16 | Removed hardcoded IP, local config, Config button, professional Inno Setup installer, auto-update check |
| v1.17 | Light/Dark mode toggle with persistent theme preference |
| v1.18 | Configurable main bot settings (bot name, script path, tmux session, SSH user) via Config window |
| v1.19 | Auto-update via GitHub Releases, native dark Windows titlebar, custom gradient titlebar removed |
| v1.20 | Auto-update downloads Inno Setup installer instead of standalone EXE, improved update dialog with Update now / Later buttons |
| v1.20.2 | Seamless silent auto-update (no dialogs), app auto-restarts after update |
| v1.21.0 | Deployer name prompt before deploy, deployment log viewer |
| v1.22 | venv activation when creating new tmux sessions |
| v1.22.1 | Fixed Bot Manager deploy button crash |

## CI/CD

Releases are built automatically via **GitHub Actions**. When you push a tag like `v1.22.1`:

1. GitHub Actions builds `DeployTool.exe` with PyInstaller on Windows
2. Inno Setup compiles the installer with the version from the tag
3. Both files are attached to a new GitHub Release

Workflow: [`.github/workflows/build-release.yml`](.github/workflows/build-release.yml)

## Requirements

### End User
- Windows 10 or later (64-bit)

### Developer (for building)
- Python 3.8+
- paramiko (SSH/SFTP)
- pyinstaller (for building EXE)
- Inno Setup 6 (for building installer)
