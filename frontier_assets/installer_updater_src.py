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

# Global Constants for Design Language
BG_COLOR = "#aeaaae"  # Default background color
CONNECTED_BG_COLOR = "#a4fba6"  # Background color when connected
CONSOLE_BG = "#0f0e0f"  # Console background
CONSOLE_FG = "lime"  # Console text color
FONT_FAMILY = "Arial"  # Font family
FONT_TITLE = (FONT_FAMILY, 14, "bold")
FONT_TEXT = (FONT_FAMILY, 12)
FONT_CONSOLE = ("Courier", 12)
BUTTON_HEIGHT = 2
BUTTON_WIDTH = 20

# Global Constants for Paths and Repo
REPO_URL = "https://github.com/collebrusco/frontier.git"

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


class ModpackBackend:
    def __init__(self, ui_callback, ui_root):
        self.ui_callback = ui_callback
        self.ui_root = ui_root
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

    def print_status_update(self, path):
        """Check Git status and print branch, commit hash, date, and update status."""
        try:
            # Ensure it's a valid Git repository
            repo = git.Repo(path)
            branch = repo.active_branch.name
            commit = repo.head.commit

            # Get commit date
            commit_date = datetime.datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d %H:%M:%S")

            # Log branch, commit hash, and date
            status_message = f"Branch: {branch}\ncommit: {commit.hexsha[:7]} <{commit_date}>"
            self.ui_callback(status_message, color="pink")

            # Fetch remote changes
            self.ui_callback("Checking for new remote versions...", color="yellow")
            repo.remotes.origin.fetch()

            # Compare local and remote branch commits
            remote_branch = repo.remotes.origin.refs[branch]
            if commit.hexsha == remote_branch.commit.hexsha:
                self.ui_callback(f"You are up-to-date with version {branch}", color='lime')
            else:
                self.ui_callback(f"A newer version {remote_branch.commit.hexsha[:7]} is available on the remote branch {branch}", color="orange")

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
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()

    def check_repo(self, path):
        """Check if the path is a valid Git repository."""
        try:
            repo = git.Repo(path)
            if repo.remotes.origin.url == REPO_URL:
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
            
    # def perform_backup(self, path):
    #     """Handle directory backup with user choice for admin or manual backup."""
    #     backup_index = 1
    #     backup_path = path.with_name(f"{path.name}_BU{backup_index}")

    #     # Increment index until a unique backup path is found
    #     while os.path.exists('{backup_path}'):
    #         backup_index += 1
    #         backup_path = path.with_name(f"{path.name}_BU{backup_index}")

    #     try:
    #         self.print_status(f"Attempting to rename '{path}' to '{backup_path}'...", "yellow")

    #         # Check for write permissions
    #         if True or not os.access(path, os.W_OK):
    #             self.print_status("Write access denied for the folder. Admin privileges required.", "red")

    #             # Ask user whether to restart as admin or handle it themselves
    #             response = messagebox.askyesnocancel(
    #                 "Admin Privileges Required",
    #                 "I need admin permissions to back this up, or you can re-name or delete the folder yourself.\n"
    #                 "- Yes: Automatic backup (requires permissions)\n"
    #                 "- No: Handle the backup yourself\n"
    #                 "- Cancel: Abort this operation"
    #             )
    #             if response is None:  # User selected Cancel
    #                 self.print_status("Backup operation canceled.", "red")
    #                 return None
    #             elif response:  # User selected Yes
    #                 if run_as_admin():
    #                     self.print_status("got permissions...", "yellow")
    #                 else:
    #                     self.print_status("Failed to get permissions.", "red")
    #                     return None
    #             else:  # User selected No
    #                 self.print_status("re-name your existing install (or delete it if you don't care). i recommend if anything saving your options and saves. re-confirm folder here when finished.", "red")
    #                 self.set_state(STATE_UNCONNECTED)  # Transition back to unconnected state
    #                 return None

    #         # Try to rename the directory
    #         try:
    #             os.rename(str(path), str(backup_path))
    #             self.print_status(f"Backup successful (os.rename): {backup_path}", "cyan")
    #             return backup_path
    #         except OSError as e:
    #             self.print_status(f"os.rename failed: {e}.", "red")

    #         return backup_path
    #     except Exception as e:
    #         self.print_status(f"Backup failed: {e}", "red")
    #         return None

    # def get_unique_backup_path(self, path):
    #     """Generate a unique backup path by appending '_BUx'."""
    #     backup_index = 1
    #     backup_path = path.with_name(f"{path.name}_BU{backup_index}")
    #     while os.path.exists('{backup_path}'):
    #         backup_index += 1
    #         backup_path = path.with_name(f"{path.name}_BU{backup_index}")
    #     return backup_path

    # def confirm_backup(self, path):
    #     """Ask the user to confirm a backup."""
    #     response = messagebox.askyesno("Backup Existing Folder",
    #                                    "An existing folder was found that is not managed by this app. "
    #                                    "Would you like to rename it and proceed?")
    #     if response:
    #         return self.perform_backup(path)
    #     else:
    #         self.print_status("Backup declined by user. Operation aborted.", "red")
    #         return None
        
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
            progress_message = f"{cur_count}/{max_count if max_count else '?'}: {message.strip()}"
            self.print_status(progress_message, "cyan")

        self.print_status(f"Cloning repository into {path}...", "yellow")

        try:
            self.print_status(f"Cloning branch into {path}...", "yellow")
            git.Repo.clone_from(REPO_URL, path, progress=progress_callback)
            self.print_status("Clone successful!", 'lime')
        except Exception as e:
            self.print_status(f"Clone failed: {e}", "red")



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
          
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Frontier Installer/Updater")
        self.root.geometry("600x700")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        # Initialize Backend
        self.backend = ModpackBackend(self.console_print, self.root)

        # Initialize State
        self.current_state = STATE_UNCONNECTED
        self.current_branch = None

        # --- State Display Section ---
        self.setup_state_display(root)

        # --- Path Section ---
        self.setup_path_field(root)

        # --- Console Section ---
        self.setup_console(root, height=200, bg=CONSOLE_BG, fg=CONSOLE_FG, font=FONT_CONSOLE)

        # --- Image Section ---
        self.image_label = self.setup_image(root, image_url="https://raw.githubusercontent.com/collebrusco/frontier/refs/heads/main/frontier_assets/img/icon.png")

        # --- Controls Section ---
        self.setup_controls(root)

        # Update UI
        self.update_ui_for_state()
        


    def setup_state_display(self, root):
        """Display the current application state."""
        self.state_frame = tk.Frame(root, bg=BG_COLOR)
        self.state_frame.pack(pady=10)
        self.state_title_label = tk.Label(self.state_frame, text="Current State:", font=FONT_TEXT, bg=BG_COLOR)
        self.state_title_label.pack(side=tk.LEFT, padx=5)
        self.state_label = tk.Label(self.state_frame, text=self.current_state, font=FONT_TEXT, bg=BG_COLOR, fg="black")
        self.state_label.pack(side=tk.LEFT, padx=5)

    def set_state(self, new_state):
        """Transition to a new application state."""
        self.console_print(f'transitioning from {self.current_state} -> {new_state}\n', "yellow")
        self.current_state = new_state
        self.state_label.config(text=new_state)
        if new_state == STATE_CONNECTED:
            self.root.configure(bg=CONNECTED_BG_COLOR)
            self.state_frame.configure(bg=CONNECTED_BG_COLOR)
            self.path_frame.configure(bg=CONNECTED_BG_COLOR)
            self.controls_frame.configure(bg=CONNECTED_BG_COLOR)
            self.path_buttons_frame.configure(bg=CONNECTED_BG_COLOR)
            self.branch_label.configure(bg=CONNECTED_BG_COLOR)
            self.path_label.configure(bg=CONNECTED_BG_COLOR)
            self.state_title_label.configure(bg=CONNECTED_BG_COLOR)
            self.state_label.configure(bg=CONNECTED_BG_COLOR)

            self.backend.print_status_update(self.path_var.get())
        else:
            self.root.configure(bg=BG_COLOR)
            self.state_frame.configure(bg=BG_COLOR)
            self.path_frame.configure(bg=BG_COLOR)
            self.controls_frame.configure(bg=BG_COLOR)
            self.path_buttons_frame.configure(bg=BG_COLOR)
            self.branch_label.configure(bg=BG_COLOR)
            self.path_label.configure(bg=BG_COLOR)
            self.state_title_label.configure(bg=BG_COLOR)
            self.state_label.configure(bg=BG_COLOR)
        self.update_ui_for_state()

    def update_ui_for_state(self):
        """Update UI elements based on the current state."""
        if self.current_state == STATE_UNCONNECTED:
            self.enable_path_editing(True)
            self.enable_install(False)
            self.enable_update(False)
            self.enable_opendir(True)
        elif self.current_state in (STATE_NON_MANAGED, STATE_NO_INSTALL):
            self.enable_path_editing(True)
            self.enable_update(False)
            self.enable_install(True)
            self.enable_opendir(True)
        elif self.current_state == STATE_CONNECTED:
            self.enable_path_editing(False)
            self.enable_install(False)
            self.enable_update(True)
            self.enable_opendir(True)

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

    def setup_path_field(self, root):
        """Setup the Minecraft path field."""
        self.path_frame = tk.Frame(root, bg=BG_COLOR)
        self.path_frame.pack(pady=10)

        self.path_label = tk.Label(self.path_frame, text="Minecraft Folder Path:", font=FONT_TEXT, bg=BG_COLOR)
        self.path_label.grid(row=0, column=0, padx=5)

        self.path_var = tk.StringVar(value=str(MINECRAFT_DEFAULT_DIR))
        self.path_entry = tk.Entry(self.path_frame, textvariable=self.path_var, width=50)
        self.path_entry.grid(row=0, column=1, padx=5)

        self.path_buttons_frame = tk.Frame(self.path_frame, bg=BG_COLOR)
        self.path_buttons_frame.grid(row=1, column=1, pady=5)

        self.browse_button = tk.Button(self.path_buttons_frame, text="Browse", command=self.browse_path, height=BUTTON_HEIGHT, width=BUTTON_WIDTH)
        self.browse_button.pack(side=tk.LEFT, padx=5)

        self.confirm_button = tk.Button(self.path_buttons_frame, text="Confirm Path", command=self.confirm_path, height=BUTTON_HEIGHT, width=BUTTON_WIDTH, bg="lightblue", fg="black")
        self.confirm_button.pack(side=tk.LEFT, padx=5)

    def browse_path(self):
        """Open a directory selection dialog and update the path field."""
        selected_path = fd.askdirectory(initialdir=str(MINECRAFT_DEFAULT_DIR), title="Select Minecraft Folder")
        if selected_path:
            self.path_var.set(selected_path)

    def setup_controls(self, root):
        """Set up the controls section with buttons and dropdowns."""
        self.controls_frame = tk.Frame(root, bg=BG_COLOR)
        self.controls_frame.pack(pady=10)

        self.branch_label = tk.Label(self.controls_frame, text="Branch:", font=FONT_TEXT, bg=BG_COLOR)
        self.branch_label.grid(row=0, column=0, padx=5)

        self.branch_var = tk.StringVar(value="master")
        self.branch_dropdown = ttk.Combobox(self.controls_frame, textvariable=self.branch_var, state="readonly", width=25)
        self.branch_dropdown.grid(row=0, column=1, padx=5)

        self.update_button = tk.Button(self.controls_frame, text="Update", command=self.update_modpack, height=BUTTON_HEIGHT, width=BUTTON_WIDTH)
        self.update_button.grid(row=0, column=2, padx=10)

        self.install_button = tk.Button(self.controls_frame, text="Install", command=self.install_modpack, height=BUTTON_HEIGHT, width=BUTTON_WIDTH)
        self.install_button.grid(row=1, column=2, padx=10, pady=5)

        self.open_dir_button = tk.Button(self.controls_frame, text="Open Minecraft Dir", command=self.open_dir, height=BUTTON_HEIGHT, width=BUTTON_WIDTH, bg='lightgreen')
        self.open_dir_button.grid(row=1, column=1, padx=10, pady=5)

    def open_dir(self):
        thisos = get_current_os()
        if thisos == OS_WIN:
            os.startfile(self.path_var.get())
        if thisos == OS_MAC:
            subprocess.run(["open", self.path_var.get()], check=True)
        if thisos == OS_LIN:
            subprocess.run(["xdg-open", self.path_var.get()], check=True)

    def setup_console(self, root, height=150, bg=CONSOLE_BG, fg=CONSOLE_FG, font=FONT_CONSOLE):
        """Set up the console for displaying messages."""
        console_frame = tk.Frame(root, bg=bg, height=height)
        console_frame.pack(fill=tk.X, padx=10, pady=5)

        self.console_text = tk.Text(console_frame, bg=bg, fg=fg, wrap=tk.WORD, font=font, height=height // 20)
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console_print("Frontier - Forge Minecraft Server 2025")
        self.console_print("Welcome to the Frontier Client Modpack Installer/Updater")
        self.console_print("Confirm your .minecraft path above to get started")

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

    def update_dropdown(self):
        """Update the dropdown with branches."""
        repo_path = Path(self.path_var.get())
        if not repo_path.exists():
            self.console_print("Invalid repository path.", "red")
            return

        branches = self.backend.fetch_remote_branches(repo_path)
        self.branch_dropdown["values"] = branches
        if branches:
            self.branch_var.set(branches[0])  # Default to first branch

    def _update_modpack(self):
        """Fetch and pull updates for the selected branch."""
        def progress_callback(op_code, cur_count, max_count=None, message=""):
            """Handles progress updates."""
            progress_message = f"{cur_count}/{max_count if max_count else '?'}: {message.strip()}"
            print(progress_message)
            self.console_print(progress_message, "cyan")
        repo_path = Path(self.path_var.get())
        branch = self.branch_var.get()
        try:
            repo = git.Repo(repo_path)
            repo.git.reset('--hard')
            repo.remotes.origin.fetch(progress=progress_callback)
            repo.git.checkout(branch)
            repo.remotes.origin.pull(progress=progress_callback)
            self.console_print(f"Update on {branch} successful", 'lime')
            self.backend.print_status_update(self.path_var.get())
            
        except Exception as e:
            self.console_print(f"Update failed: {e}", "red")

    def update_modpack(self):
        self.backend.run_in_thread(self._update_modpack)

    def confirm_path(self):
        """Confirm the Minecraft folder path and determine the application state."""
        path = Path(self.path_var.get())
        if os.path.exists(f'{path.__str__()}'):
            self.update_dropdown()
            repo = self.backend.check_repo(path)
            if repo:
                self.set_state(STATE_CONNECTED)
            else:
                response = messagebox.showinfo(title="Back up or Remove", message="you have an existing folder here that is not managed by this installer. to avoid me messing up any of your old files, go re-name or move this. or, just delete it if you don't care. you may want to at least back up your options and of course, saves.")
                self.set_state(STATE_UNCONNECTED)
        else:
            self.set_state(STATE_NO_INSTALL)

    def install_modpack_internal(self, path):
        self.backend.check_and_prepare(path)
        self.confirm_path()
    def install_modpack(self):
        """Handler for the Install Modpack button."""
        path = Path(self.path_var.get())
        self.backend.run_in_thread(self.install_modpack_internal, path)


# Create the Tkinter app
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

# import os

# folder = "C:/Users/tedti/AppData/Roaming/.minecraft"
# for item in os.listdir(folder):
#     print(item)
