import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import os
import git
import threading
from pathlib import Path
import tkinter.filedialog as fd
import subprocess
import ctypes
import sys
import datetime
import time
import random

# Global Constants for Design Language
BG_COLOR = "#c0c0c0"  # Default background color
CONNECTED_BG_COLOR = "#a4fba6"  # Background color when connected
CONSOLE_BG = "#0f0e0f"  # Console background
CONSOLE_FG = "lime"  # Console text color
FONT_FAMILY = "Arial"  # Font family
FONT_TITLE = (FONT_FAMILY, 14, "bold")
FONT_TEXT = (FONT_FAMILY, 12)
FONT_CONSOLE = ("Courier", 12)
BUTTON_HEIGHT = 2
BUTTON_WIDTH = 20

MAIN_BRANCH_NAME = 'main'

# Global Constants for Paths and Repo
REPO_URL = "https://github.com/collebrusco/frontier.git"
REPO_URL_SSH = "git@github.com:collebrusco/frontier.git"

# Application States
STATE_UNCONNECTED = "Unconnected"
STATE_NON_MANAGED = "NonManagedInstall"
STATE_NO_INSTALL = "NoInstall"
STATE_CONNECTED = "Connected"
import platform

# OS Enum
OS_WIN = "Windows"
OS_MAC = "Darwin"
OS_LIN = "Linux"

def get_current_os():
    """Detect the current operating system."""
    system = platform.system()
    if system not in [OS_LIN, OS_MAC, OS_WIN]:
        raise RuntimeError(f"Unsupported operating system: {system}")
    return system

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

class GitBackend:
    def __init__(self, ui_callback, ui_bar_callback):
        self.ui_callback = ui_callback
        self.ui_bar_callback = ui_bar_callback
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
            status_message = f">> status: on branch '{branch}'\n>> commit: {commit.hexsha[:7]} ({'dirty' if len(repo.index.diff(None))!=0 else 'clean'}) <{commit_date}>"

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

    def update_modpack(self, repo_path, branch):
        """Fetch and pull updates for the selected branch."""
        def progress_callback(op_code, cur_count, max_count=None, message=""):
            """Handles progress updates."""
            progress_message = format_progress(cur_count, max_count, message)
            print(progress_message)
            self.ui_callback(progress_message, "cyan")
            repo_path = Path(repo_path)
        try:
            repo = git.Repo(repo_path)
            if repo.is_dirty():
                result = messagebox.askokcancel('Warning', 'You have modifications to tracked files that will be reset. The installer does not track anything like saves or options, so this is likely random timestamps or something that dont matter. Ill try to remove these from being tracked if I can eventually. For now,\nrun status to see what they are if you are worried, or press ok to proceed.')
                if not result:
                    raise UserWarning("user cancelled to check modifications")
                if not repo.head.is_detached:
                    # Repository is NOT in detached HEAD state
                    tracking_branch = repo.active_branch.tracking_branch()
                    if tracking_branch:
                        self.ui_callback(f"Tracking branch: {tracking_branch}", "green")
                        repo.git.reset('--hard')
                        repo.remotes.origin.fetch(progress=progress_callback)
            repo.git.checkout(branch)
            repo.remotes.origin.pull(progress=progress_callback)
            self.ui_callback(f"Update on {branch} successful", 'lime')
            self.print_status_update(repo_path)
            
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
            self.enable_launch(False)
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

    def setup_callbacks(self, browse_cb, confirm_cb, update_cb, install_cb, open_cb, status_cb, launch_cb):
        self.browse_button.config(command=browse_cb)

        self.confirm_button.config(command=confirm_cb)

        self.update_button.config(command=update_cb)

        self.install_button.config(command=install_cb)

        self.open_dir_button.config(command=open_cb)

        self.status_button.config(command=status_cb)

        self.launch_button.config(command=launch_cb)

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
        self.update_button = tk.Button(self.controls_frame, text="Update", command=None, height=BUTTON_HEIGHT, width=BUTTON_WIDTH, bg='lightblue')
        self.update_button.pack(pady=5)

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
            self.control_launch
        )

        self.backend = GitBackend(self.frontend.console_print, self.frontend.update_progress_bar)
        self.set_state(STATE_UNCONNECTED, False)

    def bootup_seq(self):
        self.frontend.console_print("Frontier - Forge Minecraft Server 2025")
        self.frontend.simulate_progress_bar(0.1)
        self.frontend.update_progress_bar(0,1)
        self.frontend.console_print("Welcome to the Frontier Client Modpack Installer/Updater")
        time.sleep(0.1)
        self.frontend.console_print("Confirm your .minecraft path above to get started")

    def run_app(self):
        self.backend.run_in_thread(self.bootup_seq)
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
        self.backend.run_in_thread(self.backend.update_modpack, repo_path, branch)
    
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


    def control_launch(self):
        self.backend.run_in_thread(self.launch_task)






# Create the Tkinter app
if __name__ == "__main__":
    control = Controller(tk.Tk())
    control.run_app()
    

# import os

# folder = "C:/Users/tedti/AppData/Roaming/.minecraft"
# for item in os.listdir(folder):
#     print(item)
