# ==== VERSION NUMBER ====
VERSION_NUMBER = "1.2.1"
# ========================
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import os
import threading
from pathlib import Path
import tkinter.filedialog as fd
import subprocess
import ctypes
import sys
import datetime
import time
import random
import hashlib
import json

# Global Constants for Design Language
BG_COLOR = "#c0c0c0"  # Default background color
CONNECTED_BG_COLOR = "#a4fba6"  # Background color when connected
STATUS_BG_PINGING = "#b8b8b8"   # Server-status pill: pinging
STATUS_BG_ONLINE  = "#6be86d"   # Server-status pill: online, low ping
STATUS_BG_MED     = "#f5d05a"   # Server-status pill: online, medium ping
STATUS_BG_SLOW    = "#f59855"   # Server-status pill: online, slow ping
STATUS_BG_OFFLINE = "#ee6868"   # Server-status pill: offline
CONSOLE_BG = "#0f0e0f"  # Console background
CONSOLE_FG = "lime"  # Console text color
FONT_FAMILY = "Arial"  # Font family
FONT_TITLE = (FONT_FAMILY, 14, "bold")
FONT_TEXT = (FONT_FAMILY, 12)
FONT_CONSOLE = ("Courier", 12)
BUTTON_HEIGHT = 2
BUTTON_WIDTH = 20

MAIN_BRANCH_NAME = 'main'
LAUNCHER_EXE_NAME = "FrontierLauncher.exe"

DISCORD_BUG_WEBHOOK_URL = "https://discord.com/api/webhooks/1499623650083602575/aZUKDLC65INPUnWfuN70kDMOZRTATEPTt-9omo0nk_JbV__Td6MQ-lI38BeY-rvmS72m"
CRASH_RECENT_WINDOW_SECS = 300          # 5 minutes

# Launcher stdout/stderr log — path depends on whether we're running as a frozen exe or raw script
if getattr(sys, 'frozen', False):
    LAUNCHER_LOG_PATH = Path(sys.executable).parent / "frontier_assets" / "launcher_log.log"
else:
    LAUNCHER_LOG_PATH = Path(__file__).parent / "launcher_log.log"

# Global Constants for Paths and Repo
REPO_URL = "https://github.com/collebrusco/frontier.git"
REPO_URL_SSH = "git@github.com:collebrusco/frontier.git"

# Application States
STATE_UNCONNECTED = "Unconnected"
STATE_NON_MANAGED = "NonManagedInstall"
STATE_NO_INSTALL = "NoInstall"
STATE_CONNECTED = "Connected"
import platform
import os
import sys
import shutil
import tkinter as tk
from tkinter import messagebox
import subprocess
import platform
import urllib.request


# Git download URL for Windows
GIT_DOWNLOAD_URL = "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.2/Git-2.47.1.2-64-bit.exe"
GIT_INSTALLER_PATH = os.path.join(os.getenv("TEMP"), "Git-Installer.exe")

# Detect OS
OS_WIN = "Windows"
OS_MAC = "Darwin"
OS_LIN = "Linux"


def get_current_os():
    """Detect the current operating system."""
    system = platform.system()
    if system not in [OS_LIN, OS_MAC, OS_WIN]:
        raise RuntimeError(f"Unsupported operating system: {system}")
    return system


def detect_git():
    """Check if Git is installed and accessible."""
    git_path = shutil.which("git")
    if git_path:
        return git_path
    return None


def set_git_env_var(git_path):
    # Now import git after setting up the environment
    import git
    git.refresh()  # Ensure GitPython picks up the new path:
    """Set the GIT_PYTHON_GIT_EXECUTABLE environment variable dynamically."""
    os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = git_path
    
    # Attempt to make the change persistent
    if get_current_os() == OS_WIN:
        try:
            subprocess.run(["setx", "GIT_PYTHON_GIT_EXECUTABLE", git_path], check=True, shell=True)
            return True
        except Exception as e:
            print(f"Failed to set persistent env var: {e}")
    elif get_current_os() in [OS_LIN, OS_MAC]:
        shell_config = os.path.expanduser("~/.bashrc")
        if not os.path.exists(shell_config):
            shell_config = os.path.expanduser("~/.zshrc")  # Try Zsh if Bash doesn't exist
        try:
            with open(shell_config, "a") as f:
                f.write(f"\nexport GIT_PYTHON_GIT_EXECUTABLE={git_path}\n")
            return True
        except Exception as e:
            print(f"Failed to update shell config: {e}")
    return False


def download_git_installer():
    """Download the latest Git for Windows installer."""
    try:
        print("Downloading Git installer...")
        urllib.request.urlretrieve(GIT_DOWNLOAD_URL, GIT_INSTALLER_PATH)
        print("Download complete.")
        return True
    except Exception as e:
        print(f"Failed to download Git installer: {e}")
        return False


def install_git_silently():
    """Install Git for Windows silently."""
    try:
        if not os.path.exists(GIT_INSTALLER_PATH):
            if not download_git_installer():
                return False
        print("Installing Git silently...")
        subprocess.run([GIT_INSTALLER_PATH, "/SILENT", "/NORESTART"], check=True)
        print("Git installation complete.")
        return True
    except Exception as e:
        print(f"Failed to install Git: {e}")
        return False


def handle_missing_git():
    """Handle cases where Git is not found."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    if get_current_os() == OS_WIN:
        result = messagebox.askyesno(
            "Git Not Found",
            "Git is required to run this application but was not found.\n\n"
            "Would you like to download and install Git automatically?"
        )
        if result:
            if install_git_silently():
                messagebox.showinfo("Success", "Git was installed successfully. Please restart the application.")
                sys.exit(0)
            else:
                messagebox.showerror("Error", "Failed to install Git. Please install it manually.")
                sys.exit(1)
    
    else:
        result = messagebox.askyesno(
            "Git Not Found",
            "Git is required to run this application but was not found.\n\n"
            "Would you like to download and install Git manually?"
        )
        if result:
            if get_current_os() == OS_MAC:
                subprocess.run(["open", "https://git-scm.com/download/mac"], check=True)
            elif get_current_os() == OS_LIN:
                subprocess.run(["xdg-open", "https://git-scm.com/download/linux"], check=True)
        sys.exit(1)


git_path = detect_git()
if not git_path:
    handle_missing_git()
else:
    print(f"Found Git at {git_path}")
    set_git_env_var(git_path)

import git  # Ensure GitPython is available after setup
git.refresh()

MINECRAFT_DEFAULT_DIR = Path.home()
if get_current_os() == OS_WIN:
    MINECRAFT_DEFAULT_DIR = MINECRAFT_DEFAULT_DIR / "AppData/Roaming/.minecraft"
if get_current_os() == OS_MAC:
    MINECRAFT_DEFAULT_DIR = MINECRAFT_DEFAULT_DIR / "Library/Application Support/minecraft"

def run_as_admin():
    """Attempt to restart the script as an administrator."""
    if get_current_os() != OS_WIN:
        raise NotImplementedError("mac/linux admin mode not implemented yet, we currently don't need admin and would rather keep it that way")
    if ctypes.windll.shell32.IsUserAnAdmin():
        # Already running as admin
        return True
    else:
        try:
            # Request admin privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
            return False  # If this call succeeds, the script restarts, and this line won't run
        except Exception as e:
            print(f"Failed to elevate privileges: {e}")
            return False


def format_progress(cur, max, message):
    return f"{cur}/{max if max else '?'} ({int((cur/max)*100) if max else '?'}%): {message.strip()}"

def _hash_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _parse_servers_dat(path):
    """Parse servers.dat NBT and return list of {'name': ..., 'ip': ...} dicts."""
    import struct
    from io import BytesIO
    with open(path, 'rb') as f:
        buf = BytesIO(f.read())
    def rb(n): return buf.read(n)
    def read_ubyte(): return struct.unpack('>B', rb(1))[0]
    def read_int(): return struct.unpack('>i', rb(4))[0]
    def read_string():
        n = struct.unpack('>H', rb(2))[0]
        return rb(n).decode('utf-8', errors='replace')
    def skip(tag_id):
        sizes = {1: 1, 2: 2, 3: 4, 4: 8, 5: 4, 6: 8}
        if tag_id in sizes: rb(sizes[tag_id])
        elif tag_id == 7: rb(read_int())
        elif tag_id == 8: rb(struct.unpack('>H', rb(2))[0])
        elif tag_id == 9:
            t = read_ubyte(); n = read_int()
            for _ in range(n): skip(t)
        elif tag_id == 10: read_compound()
        elif tag_id == 11: rb(read_int() * 4)
        elif tag_id == 12: rb(read_int() * 8)
    def read_compound():
        d = {}
        while True:
            t = read_ubyte()
            if t == 0: break
            name = read_string()
            if t == 8: d[name] = read_string()
            else: skip(t)
        return d
    read_ubyte(); read_string()  # root TAG_Compound header (type + empty name)
    servers = []
    while True:
        t = read_ubyte()
        if t == 0: break
        name = read_string()
        if t == 9 and name == 'servers':
            el_type = read_ubyte(); count = read_int()
            for _ in range(count):
                servers.append(read_compound() if el_type == 10 else skip(el_type))
        else:
            skip(t)
    return [s for s in servers if s]


def _get_server_info(minecraft_path):
    """Return {'addr': str, 'name': str} for the latest-joined server, or None.

    Picks lastServer from options.txt; falls back to first entry in servers.dat.
    Name is looked up in servers.dat by matching ip; falls back to the address.
    """
    import re
    minecraft_path = Path(minecraft_path)

    saved = []
    dat = minecraft_path / 'servers.dat'
    if dat.exists():
        try:
            saved = _parse_servers_dat(dat)
        except Exception:
            pass

    def clean(s):
        return re.sub(r'§.', '', s or '').strip()

    addr = None
    options = minecraft_path / 'options.txt'
    if options.exists():
        for line in options.read_text(encoding='utf-8', errors='replace').splitlines():
            if line.startswith('lastServer:'):
                a = line[len('lastServer:'):].strip()
                if a:
                    addr = a
                    break

    if addr:
        for s in saved:
            if s.get('ip', '').strip() == addr:
                return {'addr': addr, 'name': clean(s.get('name', '')) or addr}
        return {'addr': addr, 'name': addr}

    if saved:
        s = saved[0]
        ip = s.get('ip', '')
        return {'addr': ip, 'name': clean(s.get('name', '')) or ip}

    return None


def _pick_pixel_font(root):
    """Return the first installed pixel/retro font family, or 'Courier' as fallback."""
    try:
        import tkinter.font as tkfont
        families = set(tkfont.families(root))
    except Exception:
        return "Courier"
    for c in ("Pixelify Sans", "Press Start 2P", "Minecraftia", "Fixedsys", "Terminal", "Consolas", "Courier New", "Courier"):
        if c in families:
            return c
    return "Courier"


def _extract_motd_text(desc):
    """Flatten a Minecraft chat-component (str or dict-with-extra) to plain text, strip § codes."""
    import re
    def walk(node):
        if isinstance(node, str):
            return node
        if isinstance(node, dict):
            s = node.get('text', '')
            for child in node.get('extra', []):
                s += walk(child)
            return s
        if isinstance(node, list):
            return ''.join(walk(x) for x in node)
        return ''
    text = re.sub(r'§.', '', walk(desc))
    return text.replace('\n', ' ').strip()


def _ping_minecraft_server(host, port=25565, timeout=5):
    """Server List Ping — returns (players_online, players_max, ping_ms, motd) or raises."""
    import socket, struct, json
    from io import BytesIO

    def pack_varint(v):
        out = b''
        while True:
            b = v & 0x7F; v >>= 7
            if v: b |= 0x80
            out += bytes([b])
            if not v: break
        return out

    def read_varint_sock(s):
        result = shift = 0
        while True:
            b = s.recv(1)
            if not b: raise ConnectionError("socket closed")
            b = b[0]; result |= (b & 0x7F) << shift; shift += 7
            if not (b & 0x80): break
        return result

    def skip_varint_buf(buf):
        while True:
            b = buf.read(1)
            if not b: raise EOFError
            if not (b[0] & 0x80): break

    host_b = host.encode('utf-8')
    handshake = (b'\x00'
                 + pack_varint(765)
                 + pack_varint(len(host_b)) + host_b
                 + struct.pack('>H', port)
                 + pack_varint(1))
    t0 = time.time()
    with socket.create_connection((host, port), timeout=timeout) as s:
        s.sendall(pack_varint(len(handshake)) + handshake)
        s.sendall(b'\x01\x00')
        length = read_varint_sock(s)
        raw = b''
        while len(raw) < length:
            chunk = s.recv(length - len(raw))
            if not chunk: break
            raw += chunk
    ping_ms = int((time.time() - t0) * 1000)
    buf = BytesIO(raw)
    skip_varint_buf(buf)   # packet ID
    skip_varint_buf(buf)   # JSON length
    data = json.loads(buf.read().decode('utf-8'))
    players = data.get('players', {})
    motd = _extract_motd_text(data.get('description', ''))
    return players.get('online', 0), players.get('max', 0), ping_ms, motd


class GitBackend:
    def __init__(self, ui_callback, ui_bar_callback, quit_cb):
        self.ui_callback = ui_callback
        self.ui_bar_callback = ui_bar_callback
        self.quit_cb = quit_cb
        self.semaphore = threading.Semaphore(1)

    def fetch_remote_branches(self):
        """Fetch available remote branches from the repository."""
        try:
            repo = git.Repo(MINECRAFT_DEFAULT_DIR)
            repo.remotes.origin.fetch()
            branches = [ref.name.split("/")[-1] for ref in repo.remotes.origin.refs]
            return branches
        except Exception as e:
            self.ui_callback(f"Error fetching branches: {e}", "red")
            return ["master"]  # Default to 'master' if fetching fails

    def print_status(self, message, color="white"):
        """Send a status message to the UI console."""
        print(f'CONSOLE: {message}')
        self.ui_callback(message, color=color)

    def print_status_update(self, path, v=True):
        """Check Git status and print branch, commit hash, date, and update status."""
        try:
            # Ensure it's a valid Git repository
            repo = git.Repo(path)
            branch = repo.active_branch.name
            commit = repo.head.commit

            # Get commit date
            commit_date = datetime.datetime.fromtimestamp(commit.committed_date).strftime("%m-%d-%Y %H:%M")

            # Log branch, commit hash, and date
            status_message = f">> status: on branch '{branch}'\n>> commit: {commit.hexsha[:7]} ({'dirty' if len(repo.index.diff(None))!=0 else 'clean'}) \"{commit.message}\" <{commit_date}>"

            self.ui_callback(status_message, color="pink")

            if v:
                for item in repo.index.diff(None):
                    clr = ''
                    match item.change_type:
                        case 'M':
                            clr = 'cyan'
                        case 'A':
                            clr = 'lime'
                        case 'D':
                            clr = 'red'
                        case _:
                            clr = 'orange'
                    self.ui_callback(f'>> [{item.change_type}] {item.a_path}', clr)

            # Fetch remote changes
            self.ui_callback("Checking for new remote versions...", color="yellow")
            repo.remotes.origin.fetch()

            # Compare local and remote branch commits
            remote_branch = repo.remotes.origin.refs[branch]
            if commit.hexsha == remote_branch.commit.hexsha:
                self.ui_callback(f"You are up-to-date with version '{branch}'", color='lime')
            else:
                self.ui_callback(f"!! A newer version {remote_branch.commit.hexsha[:7]} is available on the remote branch '{branch}'", color="orange")

        except git.exc.InvalidGitRepositoryError:
            self.ui_callback("Invalid Git repository. Please check the path.", color="red")
        except git.exc.GitCommandError as e:
            self.ui_callback(f"Git command error: {e}", color="red")
        except Exception as e:
            self.ui_callback(f"Unexpected error: {e}", color="red")

    def run_in_thread(self, target, *args):
        """Run a function in a separate thread with semaphore protection."""
        def wrapper():
            if not self.semaphore.acquire(blocking=False):
                messagebox.showinfo("Console Busy", "A task is already running. Please wait.")
                return
            try:
                target(*args)
            finally:
                self.semaphore.release()
        thread = threading.Thread(target=wrapper, daemon=False)
        thread.start()

    def check_repo(self, path):
        """Check if the path is a valid Git repository."""
        try:
            repo = git.Repo(path)
            if repo.remotes.origin.url in [REPO_URL, REPO_URL_SSH]:
                return repo
            else:
                self.print_status("Remote URL does not match the expected repository.", "red")
                return None
        except git.exc.InvalidGitRepositoryError:
            self.print_status(f"{path} is not a Git repository.", "yellow")
            return None
        except Exception as e:
            self.print_status(f"Error checking repository: {e}", "red")
            return None
        
    def install_remote_at(self, path):
        def progress_cb_cci(op_code, cur_count, max_count=None, message=""):
            """Handles progress updates."""
            progress_message = format_progress(cur_count, max_count, message)
            self.print_status(progress_message, "cyan")
            if max_count is not None:
                self.ui_bar_callback(cur_count, max_count)
    
        self.ui_callback(f"init'ing git repo at {path}", color='yellow')
        repo = git.Repo.init(path)
        self.ui_callback(f"adding remote url {REPO_URL}", color='yellow')
        origin = repo.create_remote("origin", url=REPO_URL)
        self.ui_callback(f"fetching remote on network...", color='yellow')
        time.sleep(1)
        origin.fetch(progress=progress_cb_cci)
        self.ui_callback(f"done. installing..")
        try:
            repo.git.checkout(MAIN_BRANCH_NAME)
        except git.exc.GitCommandError as e:
            response = messagebox.askokcancel("WARNING: Overwrite files", f"you already have an install I don't know about and the files listed below would be overwritten by installing this modpack. Continue if you are ok with this, or cancel and back up / move your old files. From git: {e}")
            if response:
                self.ui_callback(f'forcing overwrites...', color='orange')
                repo.git.checkout(MAIN_BRANCH_NAME, force=True)
            else:
                return False
        return True


    def fetch_remote_branches(self, path):
        """Fetch available remote branches."""
        try:
            repo = git.Repo(path)
            repo.remotes.origin.fetch()
            branches = [ref.name.split("/")[-1] for ref in repo.remotes.origin.refs]
            return branches
        except Exception as e:
            self.ui_callback(f"Error fetching branches: {e}", "red")
            return ["master"]

    def install_repo(self, path):
        """Clone the repo into the specified directory with progress updates."""
        def progress_callback(op_code, cur_count, max_count=None, message=""):
            """Handles progress updates."""
            progress_message = format_progress(cur_count, max_count, message)
            self.print_status(progress_message, "cyan")
            if max_count is not None:
                self.ui_bar_callback(cur_count, max_count)

        self.print_status(f"Cloning repository into {path}...", "yellow")

        try:
            self.print_status(f"Cloning branch into {path}...", "yellow")
            git.Repo.clone_from(REPO_URL, path, progress=progress_callback)
            self.print_status("Clone successful!", 'lime')
        except Exception as e:
            self.print_status(f"Clone failed: {e}", "red")

    def update_modpack(self, repo_path, branch, mode='normal'):
        """Fetch and pull updates. mode: 'normal', 'preserve', or 'clean'."""
        def progress_callback(op_code, cur_count, max_count=None, message=""):
            progress_message = format_progress(cur_count, max_count, message)
            print(progress_message)
            self.ui_callback(progress_message, "cyan")

        repo_path = Path(repo_path)
        exe_path = repo_path / LAUNCHER_EXE_NAME
        pre_hash = _hash_file(exe_path) if (get_current_os() == OS_WIN and exe_path.exists()) else None
        exe_old_path = exe_path.with_suffix('.exe.old') if exe_path else None

        def rename_exe_out():
            if pre_hash is not None and exe_path.exists():
                if exe_old_path.exists():
                    exe_old_path.unlink()
                exe_path.rename(exe_old_path)
                repo.git.checkout('HEAD', '--', LAUNCHER_EXE_NAME)
                return True
            return False

        def restore_exe():
            exe_path.unlink(missing_ok=True)
            exe_old_path.rename(exe_path)

        try:
            repo = git.Repo(repo_path)

            if mode == 'clean':
                if not messagebox.askokcancel('Clean Install',
                        'This doesn\'t go full nuclear but should fix\n'
                        'problems with big updates.\n\n'
                        'Your saves, screenshots, resourcepacks, shaders, will NOT be affected.\n\nContinue?'):
                    raise UserWarning("user cancelled clean install")
                self.ui_callback("Fetching remote...", "yellow")
                repo.remotes.origin.fetch(progress=progress_callback)
                repo.git.checkout(branch)
                renamed_exe = rename_exe_out()
                try:
                    for d in ['bin', 'libraries', 'versions', 'config']:
                        if (repo_path / d).exists():
                            self.ui_callback(f"Cleaning {d}/...", "orange")
                            repo.git.clean('-fdx', d)
                    repo.git.reset('--hard', f'origin/{branch}')
                except Exception as err:
                    if renamed_exe:
                        restore_exe()
                    raise err

            else:
                stashed = False
                if repo.is_dirty():
                    if mode == 'preserve':
                        self.ui_callback("Stashing local settings...", "yellow")
                        repo.git.stash('push', '-m', 'frontier_launcher_auto_stash')
                        stashed = True
                    else:
                        result = messagebox.askokcancel('Warning',
                            'You have modifications to tracked files that will be reset.\n'
                            'Select "Preserve local settings" to save and re-apply them across the update.')
                        if not result:
                            raise UserWarning("user cancelled to check modifications")
                        if not repo.head.is_detached:
                            tracking_branch = repo.active_branch.tracking_branch()
                            if tracking_branch:
                                self.ui_callback(f"Tracking branch: {tracking_branch}", "green")
                                repo.git.reset('--hard')
                                repo.remotes.origin.fetch(progress=progress_callback)
                repo.git.checkout(branch)
                renamed_exe = rename_exe_out()
                try:
                    repo.remotes.origin.pull(progress=progress_callback)
                except Exception as pull_err:
                    if renamed_exe:
                        restore_exe()
                    raise pull_err
                if stashed:
                    self.ui_callback("Applying your settings...", "yellow")
                    try:
                        repo.git.stash('pop')
                        self.ui_callback("Settings applied successfully.", "lime")
                    except git.exc.GitCommandError:
                        repo.git.reset('--hard')
                        repo.git.stash('drop')
                        self.ui_callback("oops, some files you'd changed were updated in the same place, and I can't merge them automatically. I'll have to reset, sorry", "orange")

            self.ui_callback(f"Update on {branch} successful", 'lime')
            self.print_status_update(repo_path)

            if pre_hash is not None and exe_path.exists():
                post_hash = _hash_file(exe_path)
                if pre_hash != post_hash:
                    self.ui_callback("Launcher executable was updated!", "yellow")
                    if messagebox.askyesno("Launcher Updated", "The Frontier Launcher itself was updated.\nRestart now to run the new version?"):
                        subprocess.Popen([str(exe_path)])
                        self.quit_cb()

        except UserWarning as w:
            self.ui_callback(f'Update cancelled: {w}', 'orange')
        except Exception as e:
            self.ui_callback(f"Update failed: {e}", "red")

    def run_git_command(self, repo, command):
        """Run a Git command and stream output to the console."""
        try:
            process = repo.git.execute(command, with_extended_output=True, as_process=True)
            for line in iter(process.stdout.readline, b""):
                self.print_status(line.decode("utf-8").strip(), "white")
            process.stdout.close()
            process.wait()
        except Exception as e:
            self.print_status(f"Error running command '{command}': {e}", "red")

    def check_and_prepare(self, path):
        """Check the directory and prepare it for use."""
        self.print_status(f"Checking path: {path}", "white")
        if os.path.exists('{path}'):
            self.print_status(f"Path exists: {path}", "cyan")
            repo = self.check_repo(path)
            if repo:
                self.print_status("Repository found. Fetching status...", 'lime')
                self.print_status(f"Branch: {repo.active_branch.name}", "cyan")
                self.print_status(f"Latest Commit: {repo.head.commit.hexsha[:7]} - {repo.head.commit.message}", "cyan")
                return
            else:
                self.print_status("Non-Git directory detected.", "yellow")
        else:
            self.print_status(f"installing {path}", "yellow")
            self.install_repo(path)
          
class FrontEnd:
    def __init__(self, root):
        self.root = root
        self.root.title("Frontier Installer/Updater")
        self.root.geometry("600x720")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        self.cfglist = []

        # Initialize State
        self.current_branch = None
        self.current_state = STATE_UNCONNECTED

        # --- State Display Section ---
        self.setup_state_display(root)

        # --- Path Section ---
        self.setup_path_field()

        # --- Console Section ---
        self.setup_console(root, height=200, bg=CONSOLE_BG, fg=CONSOLE_FG, font=FONT_CONSOLE)

        # --- Prog bar ---
        self.setup_progress_bar(root)
        self.pgsema = threading.Semaphore(1)

        # --- Image Section ---
        # self.image_label = self.setup_image(root, image_url="https://raw.githubusercontent.com/collebrusco/frontier/refs/heads/main/frontier_assets/img/icon.png")

        # # --- Controls Section ---
        # self.setup_controls()

        self.setup_controls_and_image()

        # Update UI
        self.update_ui_for_state()

        self.cfglist.append(self.root)
        self.cfglist.append(self.path_frame)
        self.cfglist.append(self.state_frame)
        self.cfglist.append(self.path_buttons_frame)
        self.cfglist.append(self.path_label)
        self.cfglist.append(self.state_title_label)
        self.cfglist.append(self.state_label)
        self.cfglist.append(self.progress_canvas)
        self.cfglist.append(self.progress_frame)
        self.cfglist.append(self.image_label)
        self.cfglist.append(self.controls_image_frame)
        self.cfglist.append(self.inner_image_frame)
        self.cfglist.append(self.controls_frame)
        self.cfglist.append(self.branch_label)
        self.cfglist.append(self.update_row)
        # server_status_frame intentionally not in cfglist — its bg tracks server status, not app state

        self.bottom_bar = tk.Frame(self.root, bg=BG_COLOR)
        self.bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)
        _bottom_inner = tk.Frame(self.bottom_bar, bg=BG_COLOR)
        _bottom_inner.pack(expand=True, pady=2)  # no fill → shrinks to content, centers horizontally
        self.version_label = tk.Label(_bottom_inner, text=f"frontier launcher v{VERSION_NUMBER}", font=("Arial", 8), bg=BG_COLOR, fg="#999999")
        self.version_label.pack(side=tk.LEFT, padx=(0, 6))
        self.bug_report_button = tk.Button(_bottom_inner, text="problem...", font=("Arial", 8), bg="#c06060", fg="white", relief=tk.FLAT, padx=4, pady=2, command=None)
        self.bug_report_button.pack(side=tk.LEFT)

        self.cfglist.append(self.bottom_bar)
        self.cfglist.append(_bottom_inner)
        self.cfglist.append(self.version_label)
        # bug_report_button intentionally not in cfglist — keeps its reddish color regardless of state

    def setup_server_status(self, parent):
        """Compact server-status pill, click-to-refresh. bg color tracks status."""
        # Slot for server address/name could go here as a small subscript label;
        # _get_server_info() already resolves both.

        self.refresh_cb = None
        self.pixel_font_family = _pick_pixel_font(self.root)
        self.server_status_frame = tk.Frame(parent, bg=STATUS_BG_PINGING, relief=tk.RAISED, bd=2, cursor="hand2")
        self.server_status_frame.pack(pady=4)

        # width sized in chars for the longest state ("offline  ·  click to retry" — 26 chars)
        # so the pill stays a constant size across pinging / online / offline transitions.
        self.server_status_label = tk.Label(
            self.server_status_frame,
            text="pinging…",
            font=(self.pixel_font_family, 10, "bold"),
            bg=STATUS_BG_PINGING,
            fg="#222222",
            padx=8, pady=4,
            width=20,
            cursor="hand2",
        )
        self.server_status_label.pack()

        for w in (self.server_status_frame, self.server_status_label):
            w.bind("<Button-1>", lambda e: self._on_server_status_click())

    def _on_server_status_click(self):
        if self.refresh_cb:
            self.refresh_cb()

    def set_server_status_pinging(self):
        self.server_status_frame.config(bg=STATUS_BG_PINGING)
        self.server_status_label.config(text="pinging…", bg=STATUS_BG_PINGING)

    def setup_progress_bar(self, root):
        """Set up a progress bar below the console."""
        self.progress_frame = tk.Frame(root, bg=BG_COLOR)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)

        self.progress_canvas = tk.Canvas(self.progress_frame, height=10, bg=BG_COLOR, highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, padx=5, pady=5)

        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 10, fill=CONNECTED_BG_COLOR, outline="")
        self.progress_max_width = 580  # Adjust to match window width minus padding

    def setup_state_display(self, root):
        """Display the current application state."""
        self.state_frame = tk.Frame(root, bg=BG_COLOR)
        self.state_frame.pack(pady=10)
        self.state_title_label = tk.Label(self.state_frame, text="Current State:", font=FONT_TEXT, bg=BG_COLOR)
        self.state_title_label.pack(side=tk.LEFT, padx=5)
        self.state_label = tk.Label(self.state_frame, text=self.current_state, font=FONT_TEXT, bg=BG_COLOR, fg="black")
        self.state_label.pack(side=tk.LEFT, padx=5)

    def set_state(self, new_state, log=True):
        """Transition to a new application state."""
        if log:
            self.console_print(f'transitioning from {self.current_state} -> {new_state}', "yellow")
        self.current_state = new_state
        self.state_label.config(text=new_state)
        if new_state == STATE_CONNECTED:
            [item.configure(bg=CONNECTED_BG_COLOR) for item in self.cfglist]
        else:
            [item.configure(bg=BG_COLOR) for item in self.cfglist]
        self.update_ui_for_state()
    
    def update_progress_bar(self, current, max_value):
        """Update the progress bar based on current progress."""
        if max_value is None or max_value == 0:
            max_value = 1  # Avoid division by zero
        progress_ratio = min(max(current / max_value, 0), 1)  # Clamp ratio between 0 and 1
        bar_width = int(self.progress_max_width * progress_ratio)

        # Update the bar's width
        self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 10)

    def simulate_progress_bar(self, duration):
        max_value = 100  # Simulate progress as 0 to 100%
        current = 0      # Starting point
        start_time = time.time()
        end_time = start_time + duration

        while current < max_value:
            # Calculate elapsed time and progress
            elapsed_time = time.time() - start_time
            progress_ratio = elapsed_time / duration
            next_value = int(progress_ratio * max_value)

            # Jitter to make progress seem less linear
            jitter = random.randint(-1, 2)  # Small random fluctuations
            next_value = max(0, min(max_value, next_value + jitter))

            # If progress increases, update it
            if next_value > current:
                current = next_value
                self.update_progress_bar(current, max_value)

            # Sleep briefly to control update frequency
            time.sleep(0.05)

        # Ensure the progress bar reaches 100% at the end
        self.update_progress_bar(max_value, max_value)

    def update_ui_for_state(self):
        """Update UI elements based on the current state."""
        if self.current_state == STATE_UNCONNECTED:
            self.enable_path_editing(True)
            self.enable_install(False)
            self.enable_update(False)
            self.enable_opendir(True)
            self.enable_status(False)
            cache_file = Path(self.path_var.get()) / ".mc_launcher_path.cache"
            can_blind_launch = False
            if cache_file.exists():
                cached = cache_file.read_text().strip()
                can_blind_launch = Path(cached).is_file()
            self.enable_launch(can_blind_launch)
        elif self.current_state in (STATE_NON_MANAGED, STATE_NO_INSTALL):
            self.enable_path_editing(True)
            self.enable_update(False)
            self.enable_install(True)
            self.enable_opendir(True)
            self.enable_status(False)
            self.enable_launch(False)
        elif self.current_state == STATE_CONNECTED:
            self.enable_path_editing(False)
            self.enable_install(False)
            self.enable_update(True)
            self.enable_opendir(True)
            self.enable_status(True)
            self.enable_launch(True)

    def enable_path_editing(self, enable):
        """Enable or disable the path field and buttons."""
        state = tk.NORMAL if enable else tk.DISABLED
        self.path_entry.config(state=state)
        self.confirm_button.config(state=state)
        self.browse_button.config(state=state)

    def enable_update(self, enable):
        """Enable or disable the install and update buttons."""
        state = tk.NORMAL if enable else tk.DISABLED
        self.update_button.config(state=state)
        self.mode_menu.config(state=state)
        
    def enable_install(self, enable):
        """Enable or disable the install and update buttons."""
        state = tk.NORMAL if enable else tk.DISABLED
        self.install_button.config(state=state)

    def enable_opendir(self, enable):
        """Enable or disable the install and update buttons."""
        state = tk.NORMAL if enable else tk.DISABLED
        self.open_dir_button.config(state=state)

    def enable_status(self, enable):
        """Enable or disable the install and update buttons."""
        state = tk.NORMAL if enable else tk.DISABLED
        self.status_button.config(state=state)

    def enable_launch(self, enable):
        """Enable or disable the install and update buttons."""
        state = tk.NORMAL if enable else tk.DISABLED
        self.launch_button.config(state=state)

    def update_server_status(self, online, players_online=0, players_max=0, ping_ms=0, name=""):
        if online:
            if ping_ms < 80:
                bg = STATUS_BG_ONLINE
            elif ping_ms < 200:
                bg = STATUS_BG_MED
            else:
                bg = STATUS_BG_SLOW
            text = f"{players_online}/{players_max}  ·  {ping_ms}ms"
        else:
            bg = STATUS_BG_OFFLINE
            text = "offline  ·  click to retry"
        self.server_status_frame.config(bg=bg)
        self.server_status_label.config(text=text, bg=bg)

    # TODO controller called, pass cbs
    def setup_path_field(self):
        """Setup the Minecraft path field."""
        self.path_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.path_frame.pack(pady=10)

        self.path_label = tk.Label(self.path_frame, text="Minecraft Folder Path:", font=FONT_TEXT, bg=BG_COLOR)
        self.path_label.grid(row=0, column=0, padx=5)

        self.path_var = tk.StringVar(value=str(MINECRAFT_DEFAULT_DIR))
        self.path_entry = tk.Entry(self.path_frame, textvariable=self.path_var, width=50)
        self.path_entry.grid(row=0, column=1, padx=5)

        self.path_buttons_frame = tk.Frame(self.path_frame, bg=BG_COLOR)
        self.path_buttons_frame.grid(row=1, column=1, pady=5)

        self.browse_button = tk.Button(self.path_buttons_frame, text="Browse", command=None, height=BUTTON_HEIGHT, width=BUTTON_WIDTH)
        self.browse_button.pack(side=tk.LEFT, padx=5)

        self.confirm_button = tk.Button(self.path_buttons_frame, text="Confirm Path", command=None, height=BUTTON_HEIGHT, width=BUTTON_WIDTH, bg="lightblue", fg="black")
        self.confirm_button.pack(side=tk.LEFT, padx=5)

    def setup_controls(self):
        """Set up the controls section with buttons and dropdowns."""
        self.controls_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.controls_frame.pack(pady=10)

        self.branch_label = tk.Label(self.controls_frame, text="Branch:", font=FONT_TEXT, bg=BG_COLOR)
        self.branch_label.grid(row=0, column=0, padx=5)

        self.branch_var = tk.StringVar(value="master")
        self.branch_dropdown = ttk.Combobox(self.controls_frame, textvariable=self.branch_var, state="readonly", width=25)
        self.branch_dropdown.grid(row=0, column=1, padx=5)

        self.update_button = tk.Button(self.controls_frame, text="Update", command=None, height=BUTTON_HEIGHT, width=BUTTON_WIDTH)
        self.update_button.grid(row=0, column=2, padx=10)

        self.install_button = tk.Button(self.controls_frame, text="Install", command=None, height=BUTTON_HEIGHT, width=BUTTON_WIDTH)
        self.install_button.grid(row=1, column=2, padx=10, pady=5)

        self.open_dir_button = tk.Button(self.controls_frame, text="Open Minecraft Dir", command=None, height=BUTTON_HEIGHT, width=BUTTON_WIDTH, bg='lightgreen')
        self.open_dir_button.grid(row=1, column=1, padx=10, pady=5)

    def setup_callbacks(self, browse_cb, confirm_cb, update_cb, install_cb, open_cb, status_cb, launch_cb, bug_report_cb, refresh_server_cb=None):
        self.browse_button.config(command=browse_cb)
        self.confirm_button.config(command=confirm_cb)
        self.update_button.config(command=update_cb)
        self.install_button.config(command=install_cb)
        self.open_dir_button.config(command=open_cb)
        self.status_button.config(command=status_cb)
        self.launch_button.config(command=launch_cb)
        self.bug_report_button.config(command=bug_report_cb)
        self.refresh_cb = refresh_server_cb

    def setup_console(self, root, height=300, bg=CONSOLE_BG, fg=CONSOLE_FG, font=FONT_CONSOLE):
        """Set up the console for displaying messages."""
        console_frame = tk.Frame(root, bg=bg, height=height)
        console_frame.pack(fill=tk.X, padx=10, pady=5)

        self.console_text = tk.Text(console_frame, bg=bg, fg=fg, wrap='word', font=font, height=height // 20)
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def console_print(self, message, color=CONSOLE_FG, font=FONT_CONSOLE):
        """Print a message to the console in the given color and font."""
        print(f'CONSOLE: {message}')
        self.console_text.config(state=tk.NORMAL)
        self.console_text.tag_config(color, foreground=color, font=font)
        self.console_text.insert(tk.END, message + "\n", color)
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)

    def setup_image(self, root, image_url, width=200, height=200, bg=BG_COLOR):
        """Set up an image section."""
        image_frame = tk.Frame(root, bg=bg)
        image_frame.pack(pady=10)

        label = tk.Label(image_frame, bg=bg)
        label.pack()
        self.load_image_from_url(label, image_url, width, height)

        return label

    def setup_controls_and_image(self):
        """Set up the image and control buttons side-by-side with evenly spaced columns."""
        self.controls_image_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.controls_image_frame.pack(fill=tk.BOTH, padx=10, pady=10)

        # Configure grid weights for evenly spaced columns
        self.controls_image_frame.columnconfigure(0, weight=1)  # Image column
        self.controls_image_frame.columnconfigure(1, weight=1)  # Controls column

        # --- Image Section (Left) ---
        self.inner_image_frame = tk.Frame(self.controls_image_frame, bg=BG_COLOR)
        self.inner_image_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.image_label = tk.Label(self.inner_image_frame, bg=BG_COLOR)
        self.image_label.pack()
        self.load_image_from_url(
            self.image_label,
            "https://raw.githubusercontent.com/collebrusco/frontier/refs/heads/main/frontier_assets/img/icon.png",
            200,
            200
        )

        self.setup_server_status(self.inner_image_frame)

        self.launch_button = tk.Button(self.inner_image_frame, text="Launch!", command=None, height=BUTTON_HEIGHT, width=BUTTON_WIDTH, bg='lightgreen')
        self.launch_button.pack(pady=5)

        # --- Controls Section (Right) ---
        self.controls_frame = tk.Frame(self.controls_image_frame, bg=BG_COLOR)
        self.controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Branch Dropdown
        self.branch_label = tk.Label(self.controls_frame, text="Branch:", font=FONT_TEXT, bg=BG_COLOR)
        self.branch_label.pack(pady=5)
        self.branch_var = tk.StringVar(value="master")
        self.branch_dropdown = ttk.Combobox(self.controls_frame, textvariable=self.branch_var, state="readonly", width=25)
        self.branch_dropdown.pack(pady=5)

        # Buttons (Stacked)
        _MODE_COLORS = {'normal': 'lightblue', 'preserve': CONNECTED_BG_COLOR, 'clean': '#ffaa55'}
        self.update_row = tk.Frame(self.controls_frame, bg=BG_COLOR)
        self.update_row.pack(pady=5)
        self.update_button = tk.Button(self.update_row, text="Update", command=None, height=BUTTON_HEIGHT, width=12, bg='lightblue')
        self.update_button.pack(side=tk.LEFT)
        self.update_mode_var = tk.StringVar(value='normal')
        self.mode_menu = tk.OptionMenu(self.update_row, self.update_mode_var, 'normal', 'preserve', 'clean')
        self.mode_menu.config(height=BUTTON_HEIGHT, width=6, bg='lightblue', activebackground='lightblue')
        self.mode_menu.pack(side=tk.LEFT)
        def _sync_mode_color(*_):
            c = _MODE_COLORS.get(self.update_mode_var.get(), BG_COLOR)
            self.mode_menu.config(bg=c, activebackground=c)
        self.update_mode_var.trace_add('write', _sync_mode_color)

        self.install_button = tk.Button(self.controls_frame, text="Install", command=None, height=BUTTON_HEIGHT, width=BUTTON_WIDTH)
        self.install_button.pack(pady=5)

        self.status_button = tk.Button(self.controls_frame, text="Status", command=None, height=BUTTON_HEIGHT, width=BUTTON_WIDTH)
        self.status_button.pack(pady=5)

        self.open_dir_button = tk.Button(self.controls_frame, text="Open Minecraft Dir", command=None, height=BUTTON_HEIGHT, width=BUTTON_WIDTH, bg='lightgreen')
        self.open_dir_button.pack(pady=5)


    def load_image_from_url(self, label, url, width, height):
        """Load and display an image from a URL, resizing it to fit."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label.config(image=photo)
            label.image = photo  # Keep reference to avoid garbage collection
        except Exception as e:
            self.console_print(f"Error loading image: {e}", "red")



"""
Controller
    state change(), get()

    Frontend
        root
        on state chg
        console print
        init buttons(cbs)
    Backend
        run git cmds
        get file stuff
        more

    update press()
    install press()
    confirm press()
    ...
"""

class Controller:
    def __init__(self, root):
        self.frontend = FrontEnd(root)
        self.frontend.setup_callbacks(
            self.control_browse,
            self.control_confirm,
            self.control_update,
            self.control_install,
            self.control_open,
            self.control_status,
            self.control_launch,
            self.control_bug_report,
            refresh_server_cb=self.poll_server_status,
        )

        self.backend = GitBackend(self.frontend.console_print, self.frontend.update_progress_bar, self.frontend.root.quit)
        self.set_state(STATE_UNCONNECTED, False)

    def bootup_seq(self):
        self.frontend.console_print("Frontier - Forge Minecraft Server 2026")
        self.frontend.simulate_progress_bar(0.1)
        self.frontend.update_progress_bar(0,1)
        self.frontend.console_print("Welcome to the Frontier Client Modpack Installer/Updater")
        time.sleep(0.1)
        # Clean up leftover .old exe from a previous self-update rename
        if get_current_os() == OS_WIN:
            old_exe = Path(self.frontend.path_var.get()) / (LAUNCHER_EXE_NAME + '.old')
            if old_exe.exists():
                try:
                    old_exe.unlink()
                except Exception:
                    pass  # not critical
        self.frontend.console_print("Confirm your .minecraft path above to get started")

    def poll_server_status(self):
        if getattr(self, '_polling', False):
            return
        self._polling = True
        prev_after = getattr(self, '_poll_after_id', None)
        if prev_after is not None:
            try:
                self.frontend.root.after_cancel(prev_after)
            except Exception:
                pass
            self._poll_after_id = None
        self.frontend.set_server_status_pinging()

        def _run():
            try:
                info = _get_server_info(self.frontend.path_var.get())
                if not info:
                    self.frontend.root.after(0, lambda: self.frontend.update_server_status(False))
                    return
                addr = info['addr']
                name = info['name']
                if ':' in addr:
                    host, port = addr.rsplit(':', 1)
                    port = int(port)
                else:
                    host, port = addr, 25565
                online, max_p, ping, _motd = _ping_minecraft_server(host, port)
                self.frontend.root.after(0, lambda: self.frontend.update_server_status(True, online, max_p, ping, name))
            except Exception:
                self.frontend.root.after(0, lambda: self.frontend.update_server_status(False))
            finally:
                self._polling = False
                self._poll_after_id = self.frontend.root.after(120_000, self.poll_server_status)
        threading.Thread(target=_run, daemon=True).start()

    def run_app(self):
        self.backend.run_in_thread(self.bootup_seq)
        self.frontend.root.after(500, self.poll_server_status)
        self.frontend.root.mainloop()

    def set_state(self, state, log=True):
        self.__state = state
        self.frontend.set_state(self.get_state(), log)
        if (self.__state == STATE_CONNECTED):
            self.update_dropdown()
            self.backend.print_status_update(self.frontend.path_var.get())

    def get_state(self):
        return self.__state

    # TODO from fe
    def update_dropdown(self):
        """Update the dropdown with branches."""
        repo_path = Path(self.frontend.path_var.get())
        if not repo_path.exists():
            self.frontend.console_print("Invalid repository path.", "red")
            return

        branches = self.backend.fetch_remote_branches(repo_path)
        self.frontend.branch_dropdown["values"] = branches
        if branches:
            self.frontend.branch_var.set(branches[0])  # Default to first branch

    def install_modpack_internal(self, path):
        self.backend.check_and_prepare(path)
        self.control_confirm_internal()

    def control_confirm_internal(self):
        """Confirm the Minecraft folder path and determine the application state."""
        path = Path(self.frontend.path_var.get())
        if os.path.exists(f'{path.__str__()}'):
            self.frontend.console_print('verifying tracked install...', color='yellow')
            self.frontend.simulate_progress_bar(0.15)
            repo = self.backend.check_repo(path)
            if repo:
                self.update_dropdown()
                self.set_state(STATE_CONNECTED)
                self._check_for_recent_crashes(path)
            else:
                response = messagebox.askokcancel(title="Warning", message="You have an existing minecraft folder here not installed by this installer. I can install on top of this, but I may need to overwrite files. This installer does NOT track your saves or main options, but some other things. You will be warned again before any overwrites happen.\nPress ok to continue")
                if not response:
                    self.set_state(STATE_UNCONNECTED)
                else: #TODO error checkin?
                    if not self.backend.install_remote_at(path):
                        self.frontend.console_print('did not add remote, try again or try removing pre-existing install', color='red')
                        self.set_state(STATE_UNCONNECTED)
                        return
                    self.frontend.console_print('done. verifying...', color = 'yellow')
                    repo = self.backend.check_repo(path)
                    if not repo:
                        raise RuntimeError("failed to install remote")
                    self.frontend.console_print(f'successfully set up tracking for install at {path}')
                    self.set_state(STATE_CONNECTED)
                    self._check_for_recent_crashes(path)
        else:
            self.set_state(STATE_NO_INSTALL)


    def on_any_press(self, msg=None, clr='lime'):
        if msg is not None:
            self.frontend.console_print('msg', color=clr)
        if (False and self.get_state() == STATE_CONNECTED): # fix / remove
            self.update_dropdown()

    def control_confirm(self):
        self.on_any_press()
        self.backend.run_in_thread(self.control_confirm_internal)
    
    def control_browse(self):
        """Open a directory selection dialog and update the path field."""
        self.on_any_press()
        selected_path = fd.askdirectory(initialdir=str(MINECRAFT_DEFAULT_DIR), title="Select Minecraft Folder")
        if selected_path:
            self.frontend.path_var.set(selected_path)

    def control_install(self):
        """Handler for the Install Modpack button."""
        self.on_any_press()
        path = Path(self.frontend.path_var.get())
        self.backend.run_in_thread(self.install_modpack_internal, path)

    def control_update(self):
        self.on_any_press()
        repo_path = Path(self.frontend.path_var.get())
        branch = self.frontend.branch_var.get()
        mode = self.frontend.update_mode_var.get()
        self.backend.run_in_thread(self.backend.update_modpack, repo_path, branch, mode)
    
    def control_open_internal(self):
        thisos = get_current_os()
        if thisos == OS_WIN:
            os.startfile(self.frontend.path_var.get())
        if thisos == OS_MAC:
            subprocess.run(["open", self.frontend.path_var.get()], check=True)
        if thisos == OS_LIN:
            subprocess.run(["xdg-open", self.frontend.path_var.get()], check=True)

    def control_open(self):
        self.on_any_press()
        self.backend.run_in_thread(self.control_open_internal)
        
    def control_status(self):
        self.backend.run_in_thread(self.backend.print_status_update, self.frontend.path_var.get(), True)

    def launch_task(self):
        # Define the cache file path
        cache_file = os.path.join(self.frontend.path_var.get(), ".mc_launcher_path.cache")
        default_launcher_path = "C:\Program Files (x86)\Minecraft Launcher\MinecraftLauncher.exe"

        # Check if the cache file exists
        if os.path.exists(cache_file):
            # Read the cached path
            with open(cache_file, "r") as f:
                launcher_path = f.read().strip()
        else:
            # Create the cache file and populate it with the default path
            launcher_path = default_launcher_path
            with open(cache_file, "w") as f:
                f.write(launcher_path)

        # Validate if the launcher executable exists
        while not os.path.isfile(launcher_path):
            # Prompt the user with an error message
            self.frontend.console_print(f'no launcher at {launcher_path}', 'red')
            response = messagebox.askyesno(
                "Launcher Not Found",
                f"The launcher was not found at:\n{launcher_path}\n\nDo you want to browse for the launcher?"
            )

            if not response:
                self.frontend.console_print('User aborted launch', 'orange')
                return

            # Open a file dialog to browse for the launcher
            launcher_path = fd.askopenfilename(
                title="Select Minecraft Launcher",
                filetypes=[("Executable Files", "*.exe")]
            )

            # If the user cancels the file dialog, abort
            if not launcher_path:
                self.frontend.console_print('User aborted launch', 'orange')
                return

        # Update the cache file with the valid launcher path
        self.frontend.console_print(f'found launcher at {launcher_path}', 'lime')
        with open(cache_file, "w") as f:
            f.write(launcher_path)

        # Launch the Minecraft Launcher
        try:
            self.frontend.console_print('running launcher..', 'yellow')
            self.frontend.simulate_progress_bar(0.12)
            self.frontend.console_print('shutting down to save resources...', 'yellow')
            self.frontend.simulate_progress_bar(0.24)
            self.frontend.console_print('have fun!')
            subprocess.Popen([launcher_path])
            time.sleep(1)
            self.frontend.root.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Minecraft Launcher:\n{e}")


    def _find_recent_crashes(self, minecraft_path):
        crash_dir = Path(minecraft_path) / "crash-reports"
        if not crash_dir.exists():
            return []
        now = time.time()
        return sorted(
            [f for f in crash_dir.iterdir() if f.is_file() and (now - f.stat().st_mtime) < CRASH_RECENT_WINDOW_SECS],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

    def _check_for_recent_crashes(self, minecraft_path):
        crashes = self._find_recent_crashes(minecraft_path)
        if crashes:
            age_min = int((time.time() - crashes[0].stat().st_mtime) / 60)
            self.frontend.root.after(0, lambda: self._prompt_crash_report(minecraft_path, crashes, age_min))

    def _get_minecraft_username(self, minecraft_path):
        for fname in ("launcher_accounts_microsoft_store.json", "launcher_accounts.json"):
            try:
                p = Path(minecraft_path) / fname
                if not p.exists():
                    continue
                with open(p) as f:
                    d = json.load(f)
                active = d["activeAccountLocalId"]
                return d["accounts"][active]["minecraftProfile"]["name"]
            except Exception:
                continue
        return "Unknown"

    def _prompt_crash_report(self, minecraft_path, crash_files, age_min):
        msg = f"A Minecraft crash was detected {age_min} minute(s) ago.\n\nWould you like to send a bug report to the server admin?"
        if messagebox.askyesno("Crash Detected", msg):
            self._open_bug_report_dialog(minecraft_path, crash_files)

    def control_bug_report(self):
        minecraft_path = Path(self.frontend.path_var.get())
        crashes = self._find_recent_crashes(minecraft_path) if minecraft_path.exists() else []
        self._open_bug_report_dialog(minecraft_path, crashes)

    def _open_bug_report_dialog(self, minecraft_path, crash_files=None):
        username = self._get_minecraft_username(minecraft_path)

        dialog = tk.Toplevel(self.frontend.root)
        dialog.title("problem report")
        dialog.geometry("500x470")
        dialog.configure(bg=BG_COLOR)
        dialog.resizable(False, False)
        dialog.grab_set()

        tk.Label(dialog, text="Problem Report", font=FONT_TITLE, bg=BG_COLOR).pack(pady=(12, 4))

        info_parts = [f"Sorry {username}, pls report it", "your latest.log will be attached by default", "optionally add screenshots or more logs"]
        if crash_files:
            info_parts.append(f"crash report: {crash_files[0].name}")
        tk.Label(dialog, text="\n".join(info_parts), font=("Arial", 9), bg=BG_COLOR, fg="#555555", justify=tk.LEFT).pack(padx=16, pady=(0, 8))

        subject_frame = tk.Frame(dialog, bg=BG_COLOR)
        subject_frame.pack(padx=16, fill=tk.X, pady=(0, 6))
        tk.Label(subject_frame, text="problem:", font=FONT_TEXT, bg=BG_COLOR).pack(side=tk.LEFT, padx=(0, 6))
        subject_var = tk.StringVar()
        tk.Entry(subject_frame, textvariable=subject_var, font=("Arial", 10), width=38).pack(side=tk.LEFT)

        tk.Label(dialog, text="more details (if u want):", font=FONT_TEXT, bg=BG_COLOR, anchor='w').pack(padx=16, fill=tk.X)
        msg_text = tk.Text(dialog, height=6, width=56, font=("Arial", 10), wrap='word')
        msg_text.pack(padx=16, pady=(4, 12))

        ss_frame = tk.Frame(dialog, bg=BG_COLOR)
        ss_frame.pack(padx=16, fill=tk.X, pady=(0, 8))
        selected_screenshots = []
        ss_label_var = tk.StringVar(value="no screenshots attached")
        tk.Label(ss_frame, textvariable=ss_label_var, font=("Arial", 9), bg=BG_COLOR, fg="#555555").pack(side=tk.LEFT)

        def browse_screenshots():
            ss_dir = Path(minecraft_path) / "screenshots"
            initial = str(ss_dir) if ss_dir.exists() else str(Path(minecraft_path))
            paths = fd.askopenfilenames(
                title="Select Screenshots",
                initialdir=initial,
                filetypes=[("Images", "*.png *.jpg *.jpeg *.gif"), ("All files", "*.*")],
                parent=dialog,
            )
            if paths:
                selected_screenshots.clear()
                selected_screenshots.extend(Path(p) for p in paths)
                names = ", ".join(p.name for p in selected_screenshots[:3])
                if len(selected_screenshots) > 3:
                    names += f" (+{len(selected_screenshots) - 3} more)"
                ss_label_var.set(names)

        tk.Button(ss_frame, text="Attach Screenshots", font=("Arial", 9), command=browse_screenshots).pack(side=tk.RIGHT)

        el_frame = tk.Frame(dialog, bg=BG_COLOR)
        el_frame.pack(padx=16, fill=tk.X, pady=(0, 8))
        selected_extra_logs = []
        el_label_var = tk.StringVar(value="no extra logs attached")
        tk.Label(el_frame, textvariable=el_label_var, font=("Arial", 9), bg=BG_COLOR, fg="#555555").pack(side=tk.LEFT)

        def browse_extra_logs():
            paths = fd.askopenfilenames(
                title="Attach Extra Log",
                initialdir=str(Path(minecraft_path)),
                filetypes=[("Log / text files", "*.log *.txt *.json *.xml *.csv"), ("All files", "*.*")],
                parent=dialog,
            )
            if paths:
                selected_extra_logs.clear()
                selected_extra_logs.extend(Path(p) for p in paths)
                names = ", ".join(p.name for p in selected_extra_logs[:3])
                if len(selected_extra_logs) > 3:
                    names += f" (+{len(selected_extra_logs) - 3} more)"
                el_label_var.set(names)

        tk.Button(el_frame, text="Attach Extra Log", font=("Arial", 9), command=browse_extra_logs).pack(side=tk.RIGHT)

        btn_frame = tk.Frame(dialog, bg=BG_COLOR)
        btn_frame.pack(pady=(0, 12))

        def on_send():
            subject = subject_var.get().strip() or "problem"
            user_msg = msg_text.get("1.0", tk.END).strip()
            dialog.destroy()
            self.backend.run_in_thread(self._send_bug_report, minecraft_path, subject, user_msg, crash_files or [], username, list(selected_screenshots), list(selected_extra_logs))

        tk.Button(btn_frame, text="Send Report", bg="#c06060", fg="white", font=FONT_TEXT, width=14, height=1, command=on_send).pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="Cancel", font=FONT_TEXT, width=14, height=1, command=dialog.destroy).pack(side=tk.LEFT, padx=8)

    def _send_bug_report(self, minecraft_path, subject, user_message, crash_files, username="Unknown", screenshots=None, extra_logs=None):
        if DISCORD_BUG_WEBHOOK_URL == "YOUR_WEBHOOK_URL_HERE":
            self.frontend.console_print("Bug reporting not configured (no webhook URL).", "orange")
            return

        def _truncate_log(raw: bytes, budget: int, head: int = 32 * 1024) -> bytes:
            if len(raw) <= budget:
                return raw
            tail_size = budget - head
            sep = b"\n\n[...truncated, showing first %d KB then last %d KB...]\n\n" % (head // 1024, tail_size // 1024)
            return raw[:head] + sep + raw[-tail_size:]

        minecraft_path = Path(minecraft_path)
        log_path = minecraft_path / "logs" / "latest.log"

        try:
            LOG_BUDGET = 7 * 1024 * 1024        # 7 MB for latest.log
            EXTRA_LOG_BUDGET = int(7.9 * 1024 * 1024)  # ~7.9 MB per extra log

            log_content = b""
            if log_path.exists():
                with open(log_path, "rb") as f:
                    log_content = _truncate_log(f.read(), LOG_BUDGET)

            embed = {
                "title": subject,
                "description": user_message if user_message else "*(no message provided)*",
                "color": 0xcc4444,
                "fields": [
                    {"name": "Player", "value": username, "inline": True},
                    {"name": "OS", "value": get_current_os(), "inline": True},
                    {"name": "Launcher", "value": f"v{VERSION_NUMBER}", "inline": True},
                ],
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            }

            LAUNCHER_LOG_BUDGET = 1 * 1024 * 1024  # 1 MB — launcher stdout is small

            MAX_FILES = 10
            fi = 0
            files = {"payload_json": (None, json.dumps({"embeds": [embed]}), "application/json")}
            files[f"files[{fi}]"] = ("latest.log", log_content, "text/plain"); fi += 1
            if LAUNCHER_LOG_PATH.exists() and fi < MAX_FILES:
                launcher_log_content = _truncate_log(LAUNCHER_LOG_PATH.read_bytes(), LAUNCHER_LOG_BUDGET)
                files[f"files[{fi}]"] = ("launcher_log.log", launcher_log_content, "text/plain"); fi += 1
            if crash_files and fi < MAX_FILES:
                files[f"files[{fi}]"] = (crash_files[0].name, crash_files[0].read_bytes(), "text/plain"); fi += 1
            for el in (extra_logs or []):
                if fi >= MAX_FILES:
                    break
                el_path = Path(el)
                el_content = _truncate_log(el_path.read_bytes(), EXTRA_LOG_BUDGET)
                files[f"files[{fi}]"] = (el_path.name, el_content, "text/plain"); fi += 1
            for ss in (screenshots or []):
                if fi >= MAX_FILES:
                    break
                files[f"files[{fi}]"] = (Path(ss).name, Path(ss).read_bytes(), "image/png"); fi += 1

            resp = requests.post(DISCORD_BUG_WEBHOOK_URL, files=files)
            if resp.status_code in (200, 204):
                self.frontend.console_print("Bug report sent! Thank you.", "lime")
            else:
                self.frontend.console_print(f"Failed to send bug report (HTTP {resp.status_code}).", "red")
        except Exception as e:
            self.frontend.console_print(f"Error sending bug report: {e}", "red")

    def blind_launch_task(self):
        path = Path(self.frontend.path_var.get())
        self.frontend.console_print("Running blind launch..", "yellow")
        self.frontend.console_print("Checking for tracked install..", "yellow")
        self.frontend.simulate_progress_bar(0.22)
        repo = self.backend.check_repo(path)
        if repo:
            try:
                branch = repo.active_branch.name
                repo.remotes.origin.fetch()
                local = repo.head.commit
                remote = repo.remotes.origin.refs[branch].commit
                self.frontend.console_print("Got an install! Checking if up to date:", "lime")
                if local != remote:
                    self.frontend.console_print("Looks like there's an update -- stopping and connecting", "orange")
                    self.update_dropdown()
                    self.set_state(STATE_CONNECTED)
                    return
                self.frontend.console_print("Up to date.", "lime")
            except Exception:
                self.frontend.console_print("Couldn't reach remote, trying launch anyway!", "orange")
        else:
            self.frontend.console_print("Couldn't verify install, trying launch anyway!", "orange")
        self.launch_task()

    def control_launch(self):
        if self.get_state() == STATE_UNCONNECTED:
            self.backend.run_in_thread(self.blind_launch_task)
        else:
            self.backend.run_in_thread(self.launch_task)






# Create the Tkinter app
if __name__ == "__main__":
    try:
        LAUNCHER_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _log_fh = open(LAUNCHER_LOG_PATH, "a", buffering=1, encoding="utf-8")
        sys.stdout = _log_fh
        sys.stderr = _log_fh
        print(f"\n{'='*60}")
        print(f"Frontier Launcher v{VERSION_NUMBER} — {datetime.datetime.now().isoformat()}")
        print(f"{'='*60}")
    except Exception as e:
        pass  # don't prevent startup if log file can't be opened

    control = Controller(tk.Tk())
    control.run_app()
    