"""
=============================================================================
LXCC Bot Deployment Tool
=============================================================================
Author: [Your Name]
Date: December 2024

Version History:
------------------
v1.0  - Creation of basic framework with SSH connection
v1.1  - Added SFTP upload function
v1.2  - GUI implementation with tkinter
v1.3  - Deployment function with automatic restart
v1.4  - Login window with password verification
v1.5  - Status display (Online/Offline) added
v1.6  - Start/Stop buttons for bot control
v1.7  - Download function for script backup
v1.8  - Interactive shell window implemented
v1.9  - Threading for shell output added
v1.10 - Improved status detection (ps aux instead of tmux)
v1.11 - Complete code commenting and documentation
v1.12 - Multi-Bot Manager added (manage tmux sessions)
v1.13 - Requirements installation for Main-Bot and Custom-Bots
v1.14 - Automatic icon download from server via SFTP
v1.15 - English translation and CMD shell integration
v1.16 - Removed hardcoded IP, added local config, installer,
        Config button, and auto-update check
v1.17 - Light/Dark mode toggle with persistent theme preference
v1.18 - Main Bot settings configurable via Config window

Current Version: v1.18
=============================================================================
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import paramiko
import os
import sys
import threading
import subprocess
import platform
import json
import urllib.request
import tempfile
from datetime import datetime

# =============================================================================
# Version & Update Constants
# =============================================================================
CURRENT_VERSION = "1.19"
GITHUB_REPO = "Darkszern/clouddeploy"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# =============================================================================
# Default configuration values
# =============================================================================
DEFAULT_SSH_USER = "root"
DEFAULT_REMOTE_SCRIPT_PATH = "/root/blbot/LXCCBot/lxccbot.py"
DEFAULT_TMUX_SESSION = "LXCCBot"
DEFAULT_BOT_NAME = "LXCCBot (Main)"
REMOTE_ICON_PATH = "/root/blbot/lico/LXCCICON.ico"
REMOTE_CONFIG_DIR = "/root/deployset"
REMOTE_CONFIG_FILE = "/root/deployset/bot_config.json"
REMOTE_LOG_FILE = "/root/deployset/deployment_log.txt"

# =============================================================================
# Local paths (resolved at runtime)
# =============================================================================

def get_install_dir():
    """Returns the installation directory (Windows Program Files or fallback)."""
    if platform.system() == "Windows":
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        return os.path.join(prog_files, "LXCC Cloud Deploy")
    else:
        return os.path.join(os.path.expanduser("~"), ".lxcc-cloud-deploy")


def get_config_dir():
    """Returns a writable directory for user config files."""
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(appdata, "LXCC Cloud Deploy")
    else:
        return os.path.join(os.path.expanduser("~"), ".lxcc-cloud-deploy")


def get_config_path():
    """Returns the path to the local configuration file."""
    return os.path.join(get_config_dir(), "config.json")


def get_local_icon_path():
    """Returns the path to the local icon file."""
    return os.path.join(get_install_dir(), "LXCCLOGO.ico")


# =============================================================================
# Configuration Management (local)
# =============================================================================

def load_local_config():
    """Loads the local configuration file. Returns None if not found."""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_local_config(config):
    """Saves the local configuration file."""
    config_path = get_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_ssh_host():
    """Returns the SSH host from local config."""
    config = load_local_config()
    if config:
        return config.get("ssh_host", "")
    return ""


def get_ssh_password():
    """Returns the saved SSH password from local config."""
    config = load_local_config()
    if config:
        return config.get("ssh_password", "")
    return ""


def get_ssh_user():
    """Returns the SSH user from config, or default."""
    config = load_local_config()
    if config:
        return config.get("ssh_user", DEFAULT_SSH_USER)
    return DEFAULT_SSH_USER


def get_remote_script_path():
    """Returns the remote script path from config, or default."""
    config = load_local_config()
    if config:
        return config.get("remote_script_path", DEFAULT_REMOTE_SCRIPT_PATH)
    return DEFAULT_REMOTE_SCRIPT_PATH


def get_tmux_session():
    """Returns the tmux session name from config, or default."""
    config = load_local_config()
    if config:
        return config.get("tmux_session", DEFAULT_TMUX_SESSION)
    return DEFAULT_TMUX_SESSION


def get_bot_name():
    """Returns the main bot display name from config, or default."""
    config = load_local_config()
    if config:
        return config.get("bot_name", DEFAULT_BOT_NAME)
    return DEFAULT_BOT_NAME


# =============================================================================
# Theme System (Light / Dark Mode)
# =============================================================================

THEMES = {
    "light": {
        "bg": "#F0F0F0",
        "fg": "#000000",
        "entry_bg": "#FFFFFF",
        "entry_fg": "#000000",
        "frame_bg": "#F0F0F0",
        "label_fg": "#000000",
        "label_secondary": "gray",
        "listbox_bg": "#FFFFFF",
        "listbox_fg": "#000000",
        "text_bg": "#FFFFFF",
        "text_fg": "#000000",
        "btn_bg": "#E0E0E0",
        "btn_fg": "#000000",
        "status_online": "#4CAF50",
        "status_offline": "#F44336",
        # Colored buttons keep their colors in both modes
        "btn_deploy": "#4CAF50",
        "btn_download": "#2196F3",
        "btn_start": "#FF9800",
        "btn_stop": "#F44336",
        "btn_shell": "#9C27B0",
        "btn_manager": "#00BCD4",
        "btn_config": "#795548",
        "btn_req": "#673AB7",
        "btn_new": "#4CAF50",
        "btn_rename": "#2196F3",
        "btn_delete": "#F44336",
        "btn_addbot": "#9C27B0",
        "btn_startbot": "#FF9800",
        "btn_stopbot": "#FF5722",
        "btn_deployscript": "#00BCD4",
        "btn_dlscript": "#009688",
        "btn_openshell": "#607D8B",
    },
    "dark": {
        "bg": "#1E1E1E",
        "fg": "#D4D4D4",
        "entry_bg": "#2D2D2D",
        "entry_fg": "#D4D4D4",
        "frame_bg": "#1E1E1E",
        "label_fg": "#D4D4D4",
        "label_secondary": "#808080",
        "listbox_bg": "#2D2D2D",
        "listbox_fg": "#D4D4D4",
        "text_bg": "#2D2D2D",
        "text_fg": "#D4D4D4",
        "btn_bg": "#3C3C3C",
        "btn_fg": "#D4D4D4",
        "status_online": "#4CAF50",
        "status_offline": "#F44336",
        "btn_deploy": "#388E3C",
        "btn_download": "#1976D2",
        "btn_start": "#F57C00",
        "btn_stop": "#D32F2F",
        "btn_shell": "#7B1FA2",
        "btn_manager": "#0097A7",
        "btn_config": "#5D4037",
        "btn_req": "#512DA8",
        "btn_new": "#388E3C",
        "btn_rename": "#1976D2",
        "btn_delete": "#D32F2F",
        "btn_addbot": "#7B1FA2",
        "btn_startbot": "#F57C00",
        "btn_stopbot": "#E64A19",
        "btn_deployscript": "#0097A7",
        "btn_dlscript": "#00796B",
        "btn_openshell": "#455A64",
    },
}

# Global current theme name
_current_theme = "light"


def get_current_theme():
    """Returns the current theme dict."""
    return THEMES[_current_theme]


def get_theme_name():
    """Returns 'light' or 'dark'."""
    return _current_theme


def set_theme_name(name):
    """Sets the theme globally and saves to config."""
    global _current_theme
    _current_theme = name if name in THEMES else "light"
    try:
        config = load_local_config() or {}
        config["theme"] = _current_theme
        save_local_config(config)
    except Exception:
        pass  # Theme still applies in memory even if save fails


def load_theme_from_config():
    """Loads the saved theme preference from config."""
    global _current_theme
    config = load_local_config()
    if config and "theme" in config:
        _current_theme = config["theme"] if config["theme"] in THEMES else "light"


def apply_theme(window, is_root=False):
    """Recursively applies the current theme to a window and all its children."""
    t = get_current_theme()

    if is_root or isinstance(window, (tk.Tk, tk.Toplevel)):
        window.configure(bg=t["bg"])

    _apply_theme_to_children(window, t)


def _apply_theme_to_children(widget, t):
    """Recursively themes all child widgets."""
    for child in widget.winfo_children():
        widget_class = child.winfo_class()

        try:
            if widget_class == "Frame" or widget_class == "Labelframe":
                child.configure(bg=t["frame_bg"])
            elif widget_class == "Label":
                child.configure(bg=t["frame_bg"])
                # Don't override colored status labels
                current_fg = str(child.cget("fg"))
                if current_fg not in ("#4CAF50", "#F44336", "#388E3C", "#D32F2F",
                                       "green", "red", "blue", "orange", "gray",
                                       t["status_online"], t["status_offline"]):
                    child.configure(fg=t["label_fg"])
            elif widget_class == "Entry":
                child.configure(bg=t["entry_bg"], fg=t["entry_fg"],
                              insertbackground=t["entry_fg"])
            elif widget_class == "Button":
                # Don't override colored action buttons (they have explicit bg)
                current_bg = str(child.cget("bg"))
                if current_bg in ("#E0E0E0", "#F0F0F0", "#3C3C3C", "#1E1E1E",
                                  "SystemButtonFace", "#d9d9d9"):
                    child.configure(bg=t["btn_bg"], fg=t["btn_fg"],
                                  activebackground=t["bg"])
            elif widget_class == "Listbox":
                child.configure(bg=t["listbox_bg"], fg=t["listbox_fg"],
                              selectbackground="#0078D4", selectforeground="white")
            elif widget_class == "Text":
                child.configure(bg=t["text_bg"], fg=t["text_fg"],
                              insertbackground=t["text_fg"])
            elif widget_class == "Scrollbar":
                child.configure(bg=t["frame_bg"])
        except tk.TclError:
            pass

        # Recurse into children
        _apply_theme_to_children(child, t)


# =============================================================================
# Dark Title Bar (native Windows dark mode titlebar)
# =============================================================================

def apply_dark_titlebar(window):
    """Apply dark mode to the native Windows title bar using DWM API."""
    if platform.system() != "Windows":
        return
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value), ctypes.sizeof(value)
        )
    except Exception:
        pass

    # Center window on screen after packing
    window.update_idletasks()
    w = window.winfo_width()
    h = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (w // 2)
    y = (window.winfo_screenheight() // 2) - (h // 2)
    window.geometry(f"+{x}+{y}")


# =============================================================================
# Auto-Update Check
# =============================================================================

def check_for_update():
    """Checks GitHub Releases for a newer version. Returns (has_update, remote_version, download_url) or (False, None, None) on error."""
    try:
        req = urllib.request.Request(GITHUB_API_LATEST, headers={"User-Agent": "LXCC-CloudDeploy"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        remote_version = data.get("tag_name", "").lstrip("v")
        if not remote_version:
            return (False, None, None)

        # Find the .exe asset
        download_url = None
        for asset in data.get("assets", []):
            if asset["name"].lower().endswith(".exe") and "setup" not in asset["name"].lower():
                download_url = asset["browser_download_url"]
                break

        if not download_url:
            return (False, None, None)

        # Compare versions
        local_parts = [int(x) for x in CURRENT_VERSION.split(".")]
        remote_parts = [int(x) for x in remote_version.split(".")]
        if remote_parts > local_parts:
            return (True, remote_version, download_url)
        return (False, remote_version, None)
    except Exception:
        return (False, None, None)


def perform_auto_update(download_url, progress_callback=None):
    """Downloads the new EXE from GitHub and restarts the application.
    Returns (success, message). progress_callback(text, percent) for UI updates."""
    try:
        if progress_callback:
            progress_callback("Connecting to GitHub...", 10)

        # Download to a temp file next to the current EXE
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
        else:
            return (False, "Auto-update only works with the compiled EXE.")

        update_exe = current_exe + ".update"

        if progress_callback:
            progress_callback("Downloading update...", 30)

        req = urllib.request.Request(download_url, headers={"User-Agent": "LXCC-CloudDeploy"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(update_exe, "wb") as f:
                f.write(resp.read())

        if progress_callback:
            progress_callback("Preparing restart...", 80)

        # Create a batch script that waits for the old process to exit,
        # replaces the EXE, and restarts
        bat_path = os.path.join(os.path.dirname(current_exe), "_update.bat")
        with open(bat_path, "w") as bat:
            bat.write(f'@echo off\n')
            bat.write(f'timeout /t 2 /nobreak >nul\n')
            bat.write(f'del "{current_exe}"\n')
            bat.write(f'move "{update_exe}" "{current_exe}"\n')
            bat.write(f'start "" "{current_exe}"\n')
            bat.write(f'del "%~f0"\n')

        if progress_callback:
            progress_callback("Restarting...", 100)

        # Launch the updater batch and exit
        subprocess.Popen(
            [bat_path],
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
            shell=True
        )
        return (True, "Update downloaded. Restarting...")

    except Exception as e:
        # Clean up partial download
        try:
            update_path = sys.executable + ".update"
            if os.path.exists(update_path):
                os.remove(update_path)
        except Exception:
            pass
        return (False, f"Update failed: {e}")


# =============================================================================
# Icon Management
# =============================================================================

def download_icon_from_server(ssh_host, password):
    """Downloads the icon from the server via SFTP."""
    local_icon = get_local_icon_path()
    if os.path.exists(local_icon):
        return True

    try:
        os.makedirs(os.path.dirname(local_icon), exist_ok=True)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=get_ssh_user(), password=password)

        sftp = ssh.open_sftp()
        sftp.get(REMOTE_ICON_PATH, local_icon)
        sftp.close()
        ssh.close()

        return True
    except Exception as e:
        print(f"Icon download failed: {e}")
        return False


def set_window_icon(window):
    """Sets the icon for a window."""
    local_icon = get_local_icon_path()
    if os.path.exists(local_icon):
        try:
            window.iconbitmap(local_icon)
        except:
            pass


# =============================================================================
# SSH / Remote Operations
# =============================================================================

def verify_password(ssh_host, pw, ssh_user=None):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=ssh_user or get_ssh_user(), password=pw, timeout=10)
        ssh.close()
        return True
    except paramiko.AuthenticationException:
        return False
    except Exception as e:
        raise Exception(f"Connection error: {str(e)}")


def check_bot_status(ssh_host, pw):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=get_ssh_user(), password=pw, timeout=10)
        stdin, stdout, stderr = ssh.exec_command(f"ps aux | grep '{get_remote_script_path()}' | grep -v grep")
        output = stdout.read().decode().strip()
        ssh.close()
        return len(output) > 0
    except:
        return False


def start_bot(ssh_host, pw):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, username=get_ssh_user(), password=pw)
    ssh.exec_command(f"tmux send-keys -t {get_tmux_session()} 'python3.13 {get_remote_script_path()}' Enter")
    ssh.close()


def stop_bot(ssh_host, pw):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, username=get_ssh_user(), password=pw)
    ssh.exec_command(f"tmux send-keys -t {get_tmux_session()} C-c")
    ssh.close()


def upload_and_replace(file_path, ssh_host, pw):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, username=get_ssh_user(), password=pw)
    sftp = ssh.open_sftp()
    sftp.put(file_path, get_remote_script_path())
    sftp.close()
    ssh.exec_command(f"tmux send-keys -t {get_tmux_session()} C-c")
    ssh.exec_command(f"tmux send-keys -t {get_tmux_session()} 'python3.13 {get_remote_script_path()}' Enter")
    ssh.close()


def download_remote_script(save_path, ssh_host, pw):
    ssh = None
    sftp = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=get_ssh_user(), password=pw)
        sftp = ssh.open_sftp()
        sftp.get(get_remote_script_path(), save_path)
    finally:
        if sftp:
            sftp.close()
        if ssh:
            ssh.close()


def get_tmux_sessions(ssh_host, pw):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=get_ssh_user(), password=pw, timeout=10)
        stdin, stdout, stderr = ssh.exec_command("tmux list-sessions 2>/dev/null")
        output = stdout.read().decode().strip()
        ssh.close()

        if not output:
            return []

        sessions = []
        for line in output.split('\n'):
            if ':' in line:
                parts = line.split(':')
                name = parts[0].strip()
                sessions.append({'name': name, 'info': ':'.join(parts[1:]).strip()})
        return sessions
    except:
        return []


def create_tmux_session(ssh_host, pw, session_name):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, username=get_ssh_user(), password=pw)
    ssh.exec_command(f"tmux new-session -d -s {session_name}")
    ssh.close()


def delete_tmux_session(ssh_host, pw, session_name):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, username=get_ssh_user(), password=pw)
    ssh.exec_command(f"tmux kill-session -t {session_name}")
    ssh.close()


def rename_tmux_session(ssh_host, pw, old_name, new_name):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, username=get_ssh_user(), password=pw)
    ssh.exec_command(f"tmux rename-session -t {old_name} {new_name}")
    ssh.close()


def install_requirements(ssh_host, pw, requirements_path, remote_dir):
    ssh = None
    sftp = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=get_ssh_user(), password=pw)
        sftp = ssh.open_sftp()
        remote_req_path = f"{remote_dir}/requirements.txt"
        sftp.put(requirements_path, remote_req_path)
        sftp.close()
        stdin, stdout, stderr = ssh.exec_command(f"cd {remote_dir} && python3.13 -m pip install -r requirements.txt")
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        return (True, output + error)
    except Exception as e:
        if sftp:
            sftp.close()
        if ssh:
            ssh.close()
        return (False, str(e))


def load_bot_config_from_cloud(ssh_host, pw):
    """Loads bot configuration from cloud server."""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=get_ssh_user(), password=pw)

        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {REMOTE_CONFIG_DIR}")
        stdout.read()

        sftp = ssh.open_sftp()
        try:
            remote_file = sftp.file(REMOTE_CONFIG_FILE, 'r')
            config_data = remote_file.read().decode('utf-8')
            remote_file.close()
            sftp.close()
            ssh.close()

            config = json.loads(config_data)
            return config
        except FileNotFoundError:
            sftp.close()
            ssh.close()
            return {get_tmux_session(): {'script': get_remote_script_path(), 'name': get_bot_name(), 'main': True}}
    except Exception as e:
        print(f"Error loading config from cloud: {e}")
        return {get_tmux_session(): {'script': get_remote_script_path(), 'name': get_bot_name(), 'main': True}}


def save_bot_config_to_cloud(ssh_host, pw, config):
    """Saves bot configuration to cloud server."""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=get_ssh_user(), password=pw)

        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {REMOTE_CONFIG_DIR}")
        stdout.read()

        sftp = ssh.open_sftp()

        config_json = json.dumps(config, indent=2)
        remote_file = sftp.file(REMOTE_CONFIG_FILE, 'w')
        remote_file.write(config_json.encode('utf-8'))
        remote_file.close()

        sftp.close()
        ssh.close()
        return True
    except Exception as e:
        print(f"Error saving config to cloud: {e}")
        return False


def log_action_to_cloud(ssh_host, pw, action, details=""):
    """Logs an action to the cloud deployment log."""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=get_ssh_user(), password=pw)

        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {REMOTE_CONFIG_DIR}")
        stdout.read()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        computer_name = platform.node()

        log_entry = f"[{timestamp}] [{computer_name}] {action}"
        if details:
            log_entry += f" - {details}"
        log_entry += "\n"

        stdin, stdout, stderr = ssh.exec_command(f"echo '{log_entry}' >> {REMOTE_LOG_FILE}")
        stdout.read()

        ssh.close()
        return True
    except Exception as e:
        print(f"Error logging to cloud: {e}")
        return False


def download_cloud_log(ssh_host, pw, save_path):
    """Downloads the deployment log from cloud server."""
    ssh = None
    sftp = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=get_ssh_user(), password=pw)
        sftp = ssh.open_sftp()

        try:
            sftp.get(REMOTE_LOG_FILE, save_path)
            sftp.close()
            ssh.close()
            return True
        except FileNotFoundError:
            sftp.close()
            ssh.close()
            with open(save_path, 'w') as f:
                f.write("No log entries yet.\n")
            return True
    except Exception as e:
        if sftp:
            sftp.close()
        if ssh:
            ssh.close()
        raise e


def open_ssh_in_cmd(ssh_host, password, session_name):
    """Opens SSH connection in CMD/Terminal with tmux session attached."""
    try:
        system = platform.system()

        if system == "Windows":
            batch_content = f"""@echo off
title LXCC Bot - {session_name}
echo Connecting to {ssh_host}...
echo Session: {session_name}
echo.
echo NOTE: You will need to enter the password manually.
echo.
ssh {get_ssh_user()}@{ssh_host} -t "tmux attach -t {session_name}"
pause
"""
            batch_path = os.path.join(os.environ.get('TEMP', '.'), f'lxcc_shell_{session_name}.bat')
            with open(batch_path, 'w') as f:
                f.write(batch_content)

            subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', batch_path], shell=True)

        elif system == "Darwin":
            applescript = f'''
            tell application "Terminal"
                do script "ssh {get_ssh_user()}@{ssh_host} -t 'tmux attach -t {session_name}'"
                activate
            end tell
            '''
            subprocess.Popen(['osascript', '-e', applescript])

        else:
            terminals = ['gnome-terminal', 'konsole', 'xterm', 'xfce4-terminal']
            for terminal in terminals:
                try:
                    if terminal == 'gnome-terminal':
                        subprocess.Popen([terminal, '--', 'bash', '-c',
                                        f'ssh {get_ssh_user()}@{ssh_host} -t "tmux attach -t {session_name}"; exec bash'])
                    else:
                        subprocess.Popen([terminal, '-e',
                                        f'ssh {get_ssh_user()}@{ssh_host} -t "tmux attach -t {session_name}"'])
                    break
                except FileNotFoundError:
                    continue

    except Exception as e:
        messagebox.showerror("Error", f"Could not open terminal:\n{e}")


# =============================================================================
# GUI: First-Start Setup Window
# =============================================================================

class SetupWindow:
    """Shown on first start when no config.json exists. Collects IP and password."""
    def __init__(self, root):
        self.root = root
        self.root.withdraw()
        self.root.title("LXCC Cloud Deploy - Setup")
        self.root.geometry("420x382")
        self.result = None
        self.password_visible = False
        apply_dark_titlebar(self.root)

        # Theme toggle in top-right corner
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.theme_btn = tk.Button(top_frame, text="Dark Mode", command=self.toggle_theme, width=10)
        self.theme_btn.pack(side="right")

        tk.Label(root, text="LXCC Cloud Deploy", font=("Arial", 14, "bold")).pack(pady=(10, 5))
        tk.Label(root, text="First-time setup - please enter your cloud connection details.",
                 font=("Arial", 9), fg="gray").pack(pady=(0, 15))

        frame = tk.Frame(root)
        frame.pack(pady=10)

        tk.Label(frame, text="Server IP:", font=("Arial", 10)).grid(row=0, column=0, padx=10, pady=8, sticky="e")
        self.ip_entry = tk.Entry(frame, width=25, font=("Arial", 10))
        self.ip_entry.grid(row=0, column=1, padx=10, pady=8)

        tk.Label(frame, text="Password:", font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=8, sticky="e")
        self.pw_entry = tk.Entry(frame, show="*", width=25, font=("Arial", 10))
        self.pw_entry.grid(row=1, column=1, padx=10, pady=8)
        self.toggle_btn = tk.Button(frame, text="Show", command=self.toggle_password, width=5)
        self.toggle_btn.grid(row=1, column=2, padx=5, pady=8)

        self.status_label = tk.Label(root, text="", font=("Arial", 9))
        self.status_label.pack(pady=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Test & Save", command=self.test_and_save,
                  width=14, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Cancel", command=root.quit,
                  width=14, font=("Arial", 10)).grid(row=0, column=1, padx=10)

        self.ip_entry.focus()
        self.ip_entry.bind('<Return>', lambda e: self.pw_entry.focus())
        self.pw_entry.bind('<Return>', lambda e: self.test_and_save())
        apply_theme(self.root, is_root=True)
        self._update_theme_btn()
        self.root.deiconify()

    def toggle_theme(self):
        set_theme_name("dark" if get_theme_name() == "light" else "light")
        apply_theme(self.root, is_root=True)
        self._update_theme_btn()

    def _update_theme_btn(self):
        self.theme_btn.config(text="Light Mode" if get_theme_name() == "dark" else "Dark Mode")

    def toggle_password(self):
        if self.password_visible:
            self.pw_entry.config(show="*")
            self.toggle_btn.config(text="Show")
            self.password_visible = False
        else:
            self.pw_entry.config(show="")
            self.toggle_btn.config(text="Hide")
            self.password_visible = True

    def test_and_save(self):
        ip = self.ip_entry.get().strip()
        pw = self.pw_entry.get().strip()

        if not ip:
            messagebox.showerror("Error", "Please enter the server IP address.")
            return
        if not pw:
            messagebox.showerror("Error", "Please enter the password.")
            return

        self.status_label.config(text="Testing connection...", fg="blue")
        self.root.update()

        try:
            if verify_password(ip, pw):
                config = {
                    "ssh_host": ip,
                    "ssh_password": pw
                }
                save_local_config(config)
                download_icon_from_server(ip, pw)
                self.status_label.config(text="Connection successful! Configuration saved.", fg="green")
                self.result = config
                self.root.after(1000, self.root.destroy)
            else:
                self.status_label.config(text="Wrong password!", fg="red")
                self.pw_entry.delete(0, tk.END)
                self.pw_entry.focus()
        except Exception as e:
            self.status_label.config(text=f"Connection error: {e}", fg="red")


# =============================================================================
# GUI: Config Window (edit IP and password)
# =============================================================================

class ConfigWindow:
    """Allows the user to edit connection settings and main bot configuration."""
    def __init__(self, parent, current_config, on_save_callback=None):
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("Configuration")
        self.window.geometry("480x512")
        self.window.transient(parent)
        self.window.grab_set()
        set_window_icon(self.window)
        apply_dark_titlebar(self.window)
        self.on_save_callback = on_save_callback
        self.password_visible = False

        # -- Connection Settings --
        tk.Label(self.window, text="Connection Settings", font=("Arial", 12, "bold")).pack(pady=(10, 5))

        conn_frame = tk.Frame(self.window)
        conn_frame.pack(pady=5, padx=15, fill=tk.X)

        tk.Label(conn_frame, text="Server IP:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=4, sticky="e")
        self.ip_entry = tk.Entry(conn_frame, width=28, font=("Arial", 10))
        self.ip_entry.grid(row=0, column=1, padx=5, pady=4, sticky="w")
        self.ip_entry.insert(0, current_config.get("ssh_host", ""))

        tk.Label(conn_frame, text="Password:", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=4, sticky="e")
        self.pw_entry = tk.Entry(conn_frame, show="*", width=28, font=("Arial", 10))
        self.pw_entry.grid(row=1, column=1, padx=5, pady=4, sticky="w")
        self.pw_entry.insert(0, current_config.get("ssh_password", ""))
        self.toggle_btn = tk.Button(conn_frame, text="Show", command=self.toggle_password, width=5)
        self.toggle_btn.grid(row=1, column=2, padx=3, pady=4)

        tk.Label(conn_frame, text="SSH User:", font=("Arial", 10)).grid(row=2, column=0, padx=5, pady=4, sticky="e")
        self.user_entry = tk.Entry(conn_frame, width=28, font=("Arial", 10))
        self.user_entry.grid(row=2, column=1, padx=5, pady=4, sticky="w")
        self.user_entry.insert(0, current_config.get("ssh_user", DEFAULT_SSH_USER))

        # -- Main Bot Settings --
        sep = tk.Frame(self.window, height=1, bg="gray")
        sep.pack(fill=tk.X, padx=15, pady=8)

        tk.Label(self.window, text="Main Bot Settings", font=("Arial", 12, "bold")).pack(pady=(0, 5))

        bot_frame = tk.Frame(self.window)
        bot_frame.pack(pady=5, padx=15, fill=tk.X)

        tk.Label(bot_frame, text="Bot Name:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=4, sticky="e")
        self.botname_entry = tk.Entry(bot_frame, width=28, font=("Arial", 10))
        self.botname_entry.grid(row=0, column=1, padx=5, pady=4, sticky="w")
        self.botname_entry.insert(0, current_config.get("bot_name", DEFAULT_BOT_NAME))

        tk.Label(bot_frame, text="Script Path:", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=4, sticky="e")
        self.script_entry = tk.Entry(bot_frame, width=28, font=("Arial", 10))
        self.script_entry.grid(row=1, column=1, padx=5, pady=4, sticky="w")
        self.script_entry.insert(0, current_config.get("remote_script_path", DEFAULT_REMOTE_SCRIPT_PATH))

        tk.Label(bot_frame, text="tmux Session:", font=("Arial", 10)).grid(row=2, column=0, padx=5, pady=4, sticky="e")
        self.tmux_entry = tk.Entry(bot_frame, width=28, font=("Arial", 10))
        self.tmux_entry.grid(row=2, column=1, padx=5, pady=4, sticky="w")
        self.tmux_entry.insert(0, current_config.get("tmux_session", DEFAULT_TMUX_SESSION))

        # -- Status & Buttons --
        self.status_label = tk.Label(self.window, text="", font=("Arial", 9))
        self.status_label.pack(pady=5)

        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Test & Save", command=self.test_and_save,
                  width=14, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Cancel", command=self.window.destroy,
                  width=14, font=("Arial", 10)).grid(row=0, column=1, padx=10)

        apply_theme(self.window, is_root=True)
        self.window.deiconify()

    def toggle_password(self):
        if self.password_visible:
            self.pw_entry.config(show="*")
            self.toggle_btn.config(text="Show")
            self.password_visible = False
        else:
            self.pw_entry.config(show="")
            self.toggle_btn.config(text="Hide")
            self.password_visible = True

    def test_and_save(self):
        ip = self.ip_entry.get().strip()
        pw = self.pw_entry.get().strip()

        if not ip:
            messagebox.showerror("Error", "Please enter the server IP address.")
            return
        if not pw:
            messagebox.showerror("Error", "Please enter the password.")
            return

        self.status_label.config(text="Testing connection...", fg="blue")
        self.window.update()

        ssh_user = self.user_entry.get().strip() or DEFAULT_SSH_USER

        try:
            if verify_password(ip, pw, ssh_user=ssh_user):
                config = load_local_config() or {}
                config["ssh_host"] = ip
                config["ssh_password"] = pw
                config["ssh_user"] = ssh_user
                config["bot_name"] = self.botname_entry.get().strip() or DEFAULT_BOT_NAME
                config["remote_script_path"] = self.script_entry.get().strip() or DEFAULT_REMOTE_SCRIPT_PATH
                config["tmux_session"] = self.tmux_entry.get().strip() or DEFAULT_TMUX_SESSION
                save_local_config(config)
                self.status_label.config(text="Connection successful! Settings saved.", fg="green")
                if self.on_save_callback:
                    self.on_save_callback(config)
                self.window.after(1000, self.window.destroy)
            else:
                self.status_label.config(text="Wrong password!", fg="red")
        except Exception as e:
            self.status_label.config(text=f"Connection error: {e}", fg="red")


# =============================================================================
# GUI: Login Window
# =============================================================================

class LoginWindow:
    def __init__(self, root, ssh_host, saved_password=None):
        self.root = root
        self.root.withdraw()
        self.root.title("LXCC Bot - Login")
        self.root.geometry("350x272")
        self.ssh_host = ssh_host
        self.password = None
        self.password_visible = False

        set_window_icon(self.root)
        apply_dark_titlebar(self.root)

        # Theme toggle in top-right corner
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.theme_btn = tk.Button(top_frame, text="Dark Mode", command=self.toggle_theme, width=10)
        self.theme_btn.pack(side="right")

        tk.Label(root, text="Enter Cloud Password", font=("Arial", 12, "bold")).pack(pady=15)
        frame = tk.Frame(root)
        frame.pack(pady=10)
        tk.Label(frame, text="Password:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.pw_entry = tk.Entry(frame, show="*", width=20)
        self.pw_entry.grid(row=0, column=1, padx=5, pady=5)
        self.pw_entry.bind('<Return>', lambda e: self.login())

        if saved_password:
            self.pw_entry.insert(0, saved_password)

        self.toggle_button = tk.Button(frame, text="Show", command=self.toggle_password, width=5)
        self.toggle_button.grid(row=0, column=2, padx=2, pady=5)
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Login", command=self.login, width=12, bg="#4CAF50", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Cancel", command=root.quit, width=12).grid(row=0, column=1, padx=5)
        self.pw_entry.focus()
        apply_theme(self.root, is_root=True)
        self._update_theme_btn()
        self.root.deiconify()

    def toggle_theme(self):
        set_theme_name("dark" if get_theme_name() == "light" else "light")
        apply_theme(self.root, is_root=True)
        self._update_theme_btn()

    def _update_theme_btn(self):
        self.theme_btn.config(text="Light Mode" if get_theme_name() == "dark" else "Dark Mode")

    def toggle_password(self):
        if self.password_visible:
            self.pw_entry.config(show="*")
            self.toggle_button.config(text="Show")
            self.password_visible = False
        else:
            self.pw_entry.config(show="")
            self.toggle_button.config(text="Hide")
            self.password_visible = True

    def login(self):
        pw = self.pw_entry.get().strip()
        if not pw:
            messagebox.showerror("Error", "Please enter password.")
            return
        try:
            if verify_password(self.ssh_host, pw):
                if download_icon_from_server(self.ssh_host, pw):
                    set_window_icon(self.root)
                # Update saved password in config
                config = load_local_config() or {}
                config["ssh_password"] = pw
                save_local_config(config)
                self.password = pw
                self.root.destroy()
            else:
                messagebox.showerror("Error", "Wrong password!")
                self.pw_entry.delete(0, tk.END)
                self.pw_entry.focus()
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))


# =============================================================================
# GUI: Bot Manager Window
# =============================================================================

class BotManagerWindow:
    def __init__(self, parent, ssh_host, password):
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("Multi-Bot Manager")
        self.window.geometry("700x582")
        set_window_icon(self.window)
        apply_dark_titlebar(self.window)
        self.ssh_host = ssh_host
        self.password = password

        self.bots = load_bot_config_from_cloud(ssh_host, password)

        if get_tmux_session() not in self.bots:
            self.bots[get_tmux_session()] = {'script': get_remote_script_path(), 'name': get_bot_name(), 'main': True}

        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        tk.Label(left_frame, text="tmux Sessions", font=("Arial", 11, "bold")).pack(pady=5)
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sessions_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Consolas", 10))
        self.sessions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.sessions_listbox.yview)
        tk.Button(left_frame, text="Refresh", command=self.refresh_sessions, width=20).pack(pady=5)

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        tk.Label(right_frame, text="Session Actions", font=("Arial", 11, "bold")).pack(pady=5)
        tk.Button(right_frame, text="New Session", command=self.create_session, width=20, bg="#4CAF50", fg="white").pack(pady=5)
        tk.Button(right_frame, text="Rename", command=self.rename_session, width=20, bg="#2196F3", fg="white").pack(pady=5)
        tk.Button(right_frame, text="Delete", command=self.delete_session, width=20, bg="#F44336", fg="white").pack(pady=5)
        tk.Label(right_frame, text="", height=1).pack()
        tk.Label(right_frame, text="Bot Actions", font=("Arial", 11, "bold")).pack(pady=5)
        tk.Button(right_frame, text="Add Bot", command=self.add_bot, width=20, bg="#9C27B0", fg="white").pack(pady=5)
        tk.Button(right_frame, text="Requirements", command=self.install_requirements_dialog, width=20, bg="#673AB7", fg="white").pack(pady=5)
        tk.Button(right_frame, text="Start Bot", command=self.start_selected_bot, width=20, bg="#FF9800", fg="white").pack(pady=5)
        tk.Button(right_frame, text="Stop Bot", command=self.stop_selected_bot, width=20, bg="#FF5722", fg="white").pack(pady=5)
        tk.Button(right_frame, text="Deploy Script", command=self.deploy_to_bot, width=20, bg="#00BCD4", fg="white").pack(pady=5)
        tk.Button(right_frame, text="Download Script", command=self.download_bot_script, width=20, bg="#009688", fg="white").pack(pady=5)
        tk.Button(right_frame, text="Open Shell", command=self.open_bot_shell, width=20, bg="#607D8B", fg="white").pack(pady=5)

        info_frame = tk.Frame(self.window)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(info_frame, text="Bot Info:", font=("Arial", 9, "bold")).pack(anchor="w")
        self.info_label = tk.Label(info_frame, text="No session selected", font=("Consolas", 9), fg="gray", justify=tk.LEFT)
        self.info_label.pack(anchor="w", padx=20)

        self.refresh_sessions()
        self.sessions_listbox.bind('<<ListboxSelect>>', self.on_session_select)
        apply_theme(self.window, is_root=True)
        self.window.deiconify()

    def refresh_sessions(self):
        self.sessions_listbox.delete(0, tk.END)
        sessions = get_tmux_sessions(self.ssh_host, self.password)
        if not sessions:
            self.sessions_listbox.insert(tk.END, "No sessions found")
            return
        for session in sessions:
            if session['name'] == get_tmux_session():
                display = f"* {session['name']} (Main) - {session['info']}"
            elif session['name'] in self.bots:
                display = f"[Bot] {session['name']} - {session['info']}"
            else:
                display = f"  {session['name']} - {session['info']}"
            self.sessions_listbox.insert(tk.END, display)

    def on_session_select(self, event):
        selection = self.sessions_listbox.curselection()
        if not selection:
            return
        selected_text = self.sessions_listbox.get(selection[0])
        if " - " in selected_text:
            name_part = selected_text.split(" - ")[0]
            for prefix in ["* ", "[Bot] ", "  "]:
                if name_part.startswith(prefix):
                    name_part = name_part[len(prefix):]
                    break
            session_name = name_part.replace(" (Main)", "").strip()
        else:
            return
        if session_name in self.bots:
            bot = self.bots[session_name]
            info_text = f"Session: {session_name}\nBot: {bot['name']}\nScript: {bot['script']}"
            self.info_label.config(text=info_text, fg=get_current_theme()["label_fg"])
        else:
            self.info_label.config(text=f"Session: {session_name}\n(No bot configured)", fg="gray")

    def get_selected_session(self):
        selection = self.sessions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a session.")
            return None
        selected_text = self.sessions_listbox.get(selection[0])
        if " - " in selected_text:
            name_part = selected_text.split(" - ")[0]
            for prefix in ["* ", "[Bot] ", "  "]:
                if name_part.startswith(prefix):
                    name_part = name_part[len(prefix):]
                    break
            return name_part.replace(" (Main)", "").strip()
        return None

    def create_session(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Create New Session")
        dialog.geometry("300x152")
        apply_dark_titlebar(dialog)
        tk.Label(dialog, text="Session Name:").pack(pady=10)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        name_entry.focus()
        def create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a name.")
                return
            try:
                create_tmux_session(self.ssh_host, self.password, name)
                log_action_to_cloud(self.ssh_host, self.password, "SESSION_CREATED", f"Created new tmux session '{name}'")
                messagebox.showinfo("Success", f"Session '{name}' created.")
                dialog.destroy()
                self.refresh_sessions()
            except Exception as e:
                messagebox.showerror("Error", f"Could not create session:\n{e}")
        tk.Button(dialog, text="Create", command=create, bg="#4CAF50", fg="white").pack(pady=10)
        apply_theme(dialog, is_root=True)

    def delete_session(self):
        session_name = self.get_selected_session()
        if not session_name:
            return
        if session_name == get_tmux_session():
            result = messagebox.askyesno("Warning", f"This is the Main session '{get_tmux_session()}'!\nReally delete?")
            if not result:
                return
        confirm = messagebox.askyesno("Confirmation", f"Really delete session '{session_name}'?")
        if confirm:
            try:
                delete_tmux_session(self.ssh_host, self.password, session_name)

                if session_name in self.bots:
                    del self.bots[session_name]
                    save_bot_config_to_cloud(self.ssh_host, self.password, self.bots)

                log_action_to_cloud(self.ssh_host, self.password, "SESSION_DELETED", f"Deleted tmux session '{session_name}'")

                messagebox.showinfo("Success", f"Session '{session_name}' deleted.")
                self.refresh_sessions()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete session:\n{e}")

    def rename_session(self):
        old_name = self.get_selected_session()
        if not old_name:
            return
        dialog = tk.Toplevel(self.window)
        dialog.title("Rename Session")
        dialog.geometry("300x182")
        apply_dark_titlebar(dialog)
        tk.Label(dialog, text=f"Current Name: {old_name}", font=("Arial", 9, "bold")).pack(pady=10)
        tk.Label(dialog, text="New Name:").pack(pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        name_entry.insert(0, old_name)
        name_entry.focus()
        name_entry.select_range(0, tk.END)
        def rename():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Please enter a name.")
                return
            try:
                rename_tmux_session(self.ssh_host, self.password, old_name, new_name)
                if old_name in self.bots:
                    self.bots[new_name] = self.bots.pop(old_name)
                    save_bot_config_to_cloud(self.ssh_host, self.password, self.bots)

                log_action_to_cloud(self.ssh_host, self.password, "SESSION_RENAMED", f"Renamed session '{old_name}' to '{new_name}'")

                messagebox.showinfo("Success", f"Session renamed:\n{old_name} -> {new_name}")
                dialog.destroy()
                self.refresh_sessions()
            except Exception as e:
                messagebox.showerror("Error", f"Could not rename session:\n{e}")
        tk.Button(dialog, text="Rename", command=rename, bg="#2196F3", fg="white").pack(pady=10)
        apply_theme(dialog, is_root=True)

    def add_bot(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Bot")
        dialog.geometry("400x282")
        apply_dark_titlebar(dialog)
        tk.Label(dialog, text="Bot Configuration", font=("Arial", 11, "bold")).pack(pady=10)
        tk.Label(dialog, text="Session Name:").pack(anchor="w", padx=20)
        session_entry = tk.Entry(dialog, width=40)
        session_entry.pack(padx=20, pady=5)
        tk.Label(dialog, text="Bot Name:").pack(anchor="w", padx=20)
        name_entry = tk.Entry(dialog, width=40)
        name_entry.pack(padx=20, pady=5)
        tk.Label(dialog, text="Script Path on Server:").pack(anchor="w", padx=20)
        script_entry = tk.Entry(dialog, width=40)
        script_entry.pack(padx=20, pady=5)
        script_entry.insert(0, "/root/")
        def save_bot():
            session = session_entry.get().strip()
            name = name_entry.get().strip()
            script = script_entry.get().strip()
            if not session or not name or not script:
                messagebox.showerror("Error", "Please fill all fields.")
                return
            self.bots[session] = {'name': name, 'script': script, 'main': False}

            if save_bot_config_to_cloud(self.ssh_host, self.password, self.bots):
                log_action_to_cloud(self.ssh_host, self.password, "BOT_ADDED", f"Bot '{name}' added to session '{session}' with script '{script}'")
                messagebox.showinfo("Success", f"Bot '{name}' added and saved to cloud.")
            else:
                messagebox.showwarning("Warning", f"Bot '{name}' added but cloud save failed.")

            dialog.destroy()
            self.refresh_sessions()
        tk.Button(dialog, text="Add Bot", command=save_bot, bg="#9C27B0", fg="white", width=15).pack(pady=15)
        apply_theme(dialog, is_root=True)

    def start_selected_bot(self):
        session_name = self.get_selected_session()
        if not session_name:
            return
        if session_name not in self.bots:
            messagebox.showwarning("No Bot", "No bot configured for this session.\nUse 'Add Bot' to configure one.")
            return
        bot = self.bots[session_name]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ssh_host, username=get_ssh_user(), password=self.password)
            ssh.exec_command(f"tmux send-keys -t {session_name} 'python3.13 {bot['script']}' Enter")
            ssh.close()
            log_action_to_cloud(self.ssh_host, self.password, "BOT_STARTED", f"Started bot '{bot['name']}' in session '{session_name}'")
            messagebox.showinfo("Success", f"Bot '{bot['name']}' is starting...")
        except Exception as e:
            messagebox.showerror("Error", f"Could not start bot:\n{e}")

    def stop_selected_bot(self):
        session_name = self.get_selected_session()
        if not session_name:
            return
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ssh_host, username=get_ssh_user(), password=self.password)
            ssh.exec_command(f"tmux send-keys -t {session_name} C-c")
            ssh.close()

            bot_name = self.bots[session_name]['name'] if session_name in self.bots else session_name
            log_action_to_cloud(self.ssh_host, self.password, "BOT_STOPPED", f"Stopped bot in session '{session_name}' ({bot_name})")

            messagebox.showinfo("Success", "Bot stopped.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not stop bot:\n{e}")

    def deploy_to_bot(self):
        session_name = self.get_selected_session()
        if not session_name:
            return
        if session_name not in self.bots:
            messagebox.showwarning("No Bot", "No bot configured for this session.")
            return
        bot = self.bots[session_name]
        file_path = filedialog.askopenfilename(title=f"Select script for {bot['name']}", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if not file_path:
            return
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ssh_host, username=get_ssh_user(), password=self.password)
            sftp = ssh.open_sftp()
            sftp.put(file_path, bot['script'])
            sftp.close()
            ssh.exec_command(f"tmux send-keys -t {session_name} C-c")
            ssh.exec_command(f"tmux send-keys -t {session_name} 'python3.13 {bot['script']}' Enter")
            ssh.close()

            log_action_to_cloud(self.ssh_host, self.password, "SCRIPT_DEPLOYED", f"Deployed '{os.path.basename(file_path)}' to bot '{bot['name']}' ({session_name})")

            messagebox.showinfo("Success", f"Script deployed and bot '{bot['name']}' restarted.")
        except Exception as e:
            messagebox.showerror("Error", f"Deployment failed:\n{e}")

    def download_bot_script(self):
        session_name = self.get_selected_session()
        if not session_name:
            return
        if session_name not in self.bots:
            messagebox.showwarning("No Bot", "No bot configured for this session.")
            return

        bot = self.bots[session_name]
        script_name = os.path.basename(bot['script'])

        save_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            initialfile=script_name,
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
            title=f"Save script from {bot['name']}"
        )
        if not save_path:
            return

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ssh_host, username=get_ssh_user(), password=self.password)
            sftp = ssh.open_sftp()
            sftp.get(bot['script'], save_path)
            sftp.close()
            ssh.close()

            log_action_to_cloud(self.ssh_host, self.password, "SCRIPT_DOWNLOADED", f"Downloaded script from bot '{bot['name']}' ({session_name})")

            messagebox.showinfo("Success", f"Script downloaded to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Download failed:\n{e}")

    def open_bot_shell(self):
        session_name = self.get_selected_session()
        if not session_name:
            return
        open_ssh_in_cmd(self.ssh_host, self.password, session_name)

    def install_requirements_dialog(self):
        session_name = self.get_selected_session()
        if not session_name:
            return
        if session_name not in self.bots:
            messagebox.showwarning("No Bot", "No bot configured for this session.\nRequirements can only be installed for configured bots.")
            return
        bot = self.bots[session_name]
        req_file = filedialog.askopenfilename(title="Select requirements.txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")], initialfile="requirements.txt")
        if not req_file:
            return
        confirm = messagebox.askyesno("Install Requirements", f"Install requirements for '{bot['name']}'?\n\nFile: {os.path.basename(req_file)}\nTarget: {os.path.dirname(bot['script'])}\n\nThis may take several minutes.")
        if not confirm:
            return
        progress_dialog = tk.Toplevel(self.window)
        progress_dialog.title("Installing Requirements")
        progress_dialog.geometry("400x232")
        progress_dialog.transient(self.window)
        progress_dialog.grab_set()
        apply_dark_titlebar(progress_dialog)
        tk.Label(progress_dialog, text="Installing Requirements...", font=("Arial", 11, "bold")).pack(pady=20)
        status_label = tk.Label(progress_dialog, text="Uploading...", fg="blue")
        status_label.pack(pady=10)
        output_text = tk.Text(progress_dialog, height=6, width=45, font=("Consolas", 8))
        output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        def install_thread():
            try:
                remote_dir = os.path.dirname(bot['script'])
                status_label.config(text="Installing packages...", fg="orange")
                success, output = install_requirements(self.ssh_host, self.password, req_file, remote_dir)
                output_text.insert(tk.END, output)
                output_text.see(tk.END)
                if success:
                    log_action_to_cloud(self.ssh_host, self.password, "REQUIREMENTS_INSTALLED", f"Installed requirements for bot '{bot['name']}' ({session_name})")
                    status_label.config(text="Installation complete!", fg="green")
                    progress_dialog.after(3000, progress_dialog.destroy)
                else:
                    status_label.config(text="Installation error", fg="red")
            except Exception as e:
                status_label.config(text=f"Error: {str(e)}", fg="red")
                output_text.insert(tk.END, f"\n\nError: {str(e)}")
        apply_theme(progress_dialog, is_root=True)
        install_thread_obj = threading.Thread(target=install_thread, daemon=True)
        install_thread_obj.start()


# =============================================================================
# GUI: Main Application Window
# =============================================================================

class App:
    def __init__(self, root, ssh_host, password):
        self.root = root
        self.root.withdraw()
        self.ssh_host = ssh_host
        self.password = password
        self.root.title(f"LXCC Bot Deployment Tool v{CURRENT_VERSION}")
        self.root.geometry("450x552")
        set_window_icon(self.root)
        apply_dark_titlebar(self.root)
        self.selected_file = None

        # Top bar with theme toggle
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.theme_btn = tk.Button(top_frame, text="Dark Mode", command=self.toggle_theme, width=10)
        self.theme_btn.pack(side="right")

        status_frame = tk.Frame(root)
        status_frame.pack(anchor="ne", padx=10, pady=5)
        tk.Label(status_frame, text="Bot Status:", font=("Arial", 9)).pack(side="left", padx=5)
        self.status_label = tk.Label(status_frame, text="*", font=("Arial", 16), fg="gray")
        self.status_label.pack(side="left")
        self.status_text = tk.Label(status_frame, text="Checking...", font=("Arial", 9))
        self.status_text.pack(side="left", padx=5)
        tk.Button(status_frame, text="Refresh", command=self.update_status, font=("Arial", 9), width=6).pack(side="left", padx=2)

        tk.Label(root, text="Upload and Replace New Script", font=("Arial", 11, "bold")).pack(pady=15)
        tk.Button(root, text="Select Script", command=self.pick_file, width=20).pack(pady=5)
        self.file_label = tk.Label(root, text="No file selected", fg="gray")
        self.file_label.pack(pady=5)
        tk.Button(root, text="Install Requirements", command=self.install_main_requirements, width=20, bg="#673AB7", fg="white").pack(pady=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        t = get_current_theme()
        tk.Button(btn_frame, text="Deploy", command=self.deploy, width=15, bg=t["btn_deploy"], fg="white", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10, pady=5)
        tk.Button(btn_frame, text="Download Script", command=self.download, width=15, bg=t["btn_download"], fg="white", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=10, pady=5)
        tk.Button(btn_frame, text="Start Bot", command=self.start_bot, width=15, bg=t["btn_start"], fg="white", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=10, pady=5)
        tk.Button(btn_frame, text="Stop Bot", command=self.stop_bot, width=15, bg=t["btn_stop"], fg="white", font=("Arial", 10, "bold")).grid(row=1, column=1, padx=10, pady=5)
        tk.Button(btn_frame, text="Open Shell", command=self.open_shell, width=32, bg=t["btn_shell"], fg="white", font=("Arial", 10, "bold")).grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        tk.Button(btn_frame, text="Bot Manager", command=self.open_bot_manager, width=32, bg=t["btn_manager"], fg="white", font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=2, padx=10, pady=5)
        tk.Button(btn_frame, text="Config", command=self.open_config, width=32, bg=t["btn_config"], fg="white", font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        tk.Button(btn_frame, text="Quit", command=root.quit, width=32).grid(row=5, column=0, columnspan=2, padx=10, pady=10)

        apply_theme(self.root, is_root=True)
        self._update_theme_btn()
        self.root.deiconify()
        self.update_status()
        self.check_update_on_start()

    def toggle_theme(self):
        set_theme_name("dark" if get_theme_name() == "light" else "light")
        apply_theme(self.root, is_root=True)
        self._update_theme_btn()

    def _update_theme_btn(self):
        self.theme_btn.config(text="Light Mode" if get_theme_name() == "dark" else "Dark Mode")

    def check_update_on_start(self):
        """Check for updates via GitHub Releases in background thread on startup."""
        def _check():
            has_update, remote_version, download_url = check_for_update()
            if has_update:
                self.root.after(0, lambda: self._prompt_update(remote_version, download_url))
        threading.Thread(target=_check, daemon=True).start()

    def _prompt_update(self, remote_version, download_url):
        """Ask user if they want to auto-update, then do it."""
        result = messagebox.askyesno(
            "Update Available",
            f"A new version (v{remote_version}) is available!\n"
            f"You are running v{CURRENT_VERSION}.\n\n"
            f"Update now automatically?"
        )
        if not result:
            return

        # Show progress dialog
        progress = tk.Toplevel(self.root)
        progress.title("Updating...")
        progress.geometry("350x132")
        progress.transient(self.root)
        progress.grab_set()
        apply_dark_titlebar(progress)
        tk.Label(progress, text="Auto-Update", font=("Arial", 11, "bold")).pack(pady=10)
        status_lbl = tk.Label(progress, text="Starting update...", font=("Arial", 9))
        status_lbl.pack(pady=5)
        apply_theme(progress, is_root=True)

        def do_update():
            def on_progress(text, percent):
                self.root.after(0, lambda: status_lbl.config(text=text))

            success, msg = perform_auto_update(download_url, on_progress)
            if success:
                self.root.after(0, lambda: self.root.destroy())
            else:
                self.root.after(0, lambda: [
                    status_lbl.config(text=msg, fg="red"),
                    progress.after(5000, progress.destroy)
                ])

        threading.Thread(target=do_update, daemon=True).start()

    def update_status(self):
        try:
            is_running = check_bot_status(self.ssh_host, self.password)
            if is_running:
                self.status_label.config(fg="#4CAF50")
                self.status_text.config(text="Online")
            else:
                self.status_label.config(fg="#F44336")
                self.status_text.config(text="Offline")
        except Exception as e:
            self.status_label.config(fg="gray")
            self.status_text.config(text="Error")

    def pick_file(self):
        path = filedialog.askopenfilename(filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if path:
            self.selected_file = path
            self.file_label.config(text=os.path.basename(path), fg=get_current_theme()["label_fg"])

    def deploy(self):
        if not self.selected_file:
            messagebox.showerror("Error", "No script selected.")
            return
        tmp_path = "lxccbot.py"
        try:
            os.replace(self.selected_file, tmp_path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not prepare temp file: {e}")
            return
        try:
            upload_and_replace(tmp_path, self.ssh_host, self.password)
            log_action_to_cloud(self.ssh_host, self.password, "MAIN_BOT_DEPLOYED", f"Deployed main bot script: {os.path.basename(self.selected_file)}")
            messagebox.showinfo("Success", "Script deployed and bot restarted.")
            self.root.after(2000, self.update_status)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            try:
                os.replace(tmp_path, self.selected_file)
            except Exception:
                messagebox.showwarning("Warning", "Temporary file couldn't be restored automatically.")

    def download(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".py", initialfile=os.path.basename(get_remote_script_path()), filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if not save_path:
            return
        try:
            download_remote_script(save_path, self.ssh_host, self.password)
            messagebox.showinfo("Success", f"Script downloaded to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Download failed:\n{e}")

    def start_bot(self):
        try:
            start_bot(self.ssh_host, self.password)
            log_action_to_cloud(self.ssh_host, self.password, "MAIN_BOT_STARTED", "Started main LXCCBot")
            messagebox.showinfo("Success", "Bot is starting...")
            self.root.after(2000, self.update_status)
        except Exception as e:
            messagebox.showerror("Error", f"Could not start bot:\n{e}")

    def stop_bot(self):
        try:
            stop_bot(self.ssh_host, self.password)
            log_action_to_cloud(self.ssh_host, self.password, "MAIN_BOT_STOPPED", "Stopped main LXCCBot")
            messagebox.showinfo("Success", "Bot stopped.")
            self.root.after(1000, self.update_status)
        except Exception as e:
            messagebox.showerror("Error", f"Could not stop bot:\n{e}")

    def open_shell(self):
        open_ssh_in_cmd(self.ssh_host, self.password, get_tmux_session())

    def open_bot_manager(self):
        BotManagerWindow(self.root, self.ssh_host, self.password)

    def open_config(self):
        """Opens the configuration window to edit IP and password."""
        current_config = load_local_config() or {}
        def on_config_saved(new_config):
            self.ssh_host = new_config["ssh_host"]
            self.password = new_config["ssh_password"]
            self.update_status()
        ConfigWindow(self.root, current_config, on_save_callback=on_config_saved)

    def install_main_requirements(self):
        req_file = filedialog.askopenfilename(title="Select requirements.txt for LXCCBot", filetypes=[("Text files", "*.txt"), ("All files", "*.*")], initialfile="requirements.txt")
        if not req_file:
            return
        confirm = messagebox.askyesno("Install Requirements", f"Install requirements for {get_bot_name()}?\n\nFile: {os.path.basename(req_file)}\nTarget: {os.path.dirname(get_remote_script_path())}\n\nThis may take several minutes.")
        if not confirm:
            return
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("Installing Requirements")
        progress_dialog.geometry("450x282")
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        apply_dark_titlebar(progress_dialog)
        tk.Label(progress_dialog, text="Installing Requirements for LXCCBot...", font=("Arial", 11, "bold")).pack(pady=20)
        status_label = tk.Label(progress_dialog, text="Uploading...", fg="blue")
        status_label.pack(pady=10)
        text_frame = tk.Frame(progress_dialog)
        text_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text = tk.Text(text_frame, height=8, width=50, font=("Consolas", 8), yscrollcommand=scrollbar.set)
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=output_text.yview)
        def install_thread():
            try:
                remote_dir = os.path.dirname(get_remote_script_path())
                status_label.config(text="Installing packages...", fg="orange")
                success, output = install_requirements(self.ssh_host, self.password, req_file, remote_dir)
                output_text.insert(tk.END, output)
                output_text.see(tk.END)
                if success:
                    log_action_to_cloud(self.ssh_host, self.password, "MAIN_REQUIREMENTS_INSTALLED", f"Installed requirements from {os.path.basename(req_file)} for main LXCCBot")
                    status_label.config(text="Installation complete!", fg="green")
                    progress_dialog.after(3000, progress_dialog.destroy)
                else:
                    status_label.config(text="Installation error", fg="red")
            except Exception as e:
                status_label.config(text=f"Error: {str(e)}", fg="red")
                output_text.insert(tk.END, f"\n\nError: {str(e)}")
        apply_theme(progress_dialog, is_root=True)
        install_thread_obj = threading.Thread(target=install_thread, daemon=True)
        install_thread_obj.start()


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    # Load saved theme preference
    load_theme_from_config()

    config = load_local_config()

    # First-time setup: no config file exists
    if config is None:
        setup_root = tk.Tk()
        setup_window = SetupWindow(setup_root)
        setup_root.mainloop()

        if setup_window.result is None:
            return

        config = setup_window.result

    ssh_host = config.get("ssh_host", "")
    saved_password = config.get("ssh_password", "")

    if not ssh_host:
        # Config exists but IP is missing - run setup again
        setup_root = tk.Tk()
        setup_window = SetupWindow(setup_root)
        setup_root.mainloop()

        if setup_window.result is None:
            return

        config = setup_window.result
        ssh_host = config["ssh_host"]
        saved_password = config.get("ssh_password", "")

    # Login window (pre-filled with saved password)
    login_root = tk.Tk()
    login_window = LoginWindow(login_root, ssh_host, saved_password=saved_password)
    login_root.mainloop()

    if login_window.password:
        root = tk.Tk()
        App(root, ssh_host, login_window.password)
        root.mainloop()


if __name__ == "__main__":
    main()
