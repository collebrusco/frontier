# Frontier - Modded Minecraft Client

This repo is the **client-side** `.minecraft` directory for the Frontier modded Minecraft server (Java 1.20.1 + Forge). It is version-controlled so the server owner can push mod/config/shader updates and players can pull them. Most of the repo is standard Minecraft launcher files, mods, configs, and settings — not custom code.

## How it works

- The owner pushes updates (new mods, config tweaks, shader packs, etc.) to `main`
- Players use the Frontier Launcher (or plain `git pull`) to stay up to date
- The `.gitignore` uses a whitelist pattern (`*` then `!*/`) so only explicitly tracked files are committed

## `frontier_assets/` — Custom Tools

This is where the actual custom-built tooling lives. Everything else in the repo is Minecraft/Forge infrastructure.

### Frontier Launcher (`frontier_assets/frontier_launcher.py`)

A tkinter GUI app (~970 lines, single file) that wraps git operations so non-technical players can install and update the modpack. Built with an MVC-ish pattern:

- **`GitBackend`** — All git operations via GitPython (`import git`). Handles:
  - `install_repo()` — clones the repo into the user's `.minecraft` path
  - `install_remote_at()` — for users with an existing `.minecraft`: inits a repo, adds the remote, fetches, and checks out `main` (with force-overwrite prompt if conflicts)
  - `update_modpack()` — fetches + pulls the selected branch, with dirty-repo warnings and `--hard` reset if needed
  - `check_repo()` — validates the directory is a git repo with the correct remote URL
  - `print_status_update()` — shows branch, commit hash, dirty state, and whether remote is ahead
  - Thread safety via a semaphore (one git operation at a time)

- **`FrontEnd`** — tkinter UI with:
  - Path field (defaults to OS-appropriate `.minecraft` location)
  - Console output (dark terminal style, colored messages)
  - Progress bar (driven by git operation callbacks + a simulated fill for short tasks)
  - Branch dropdown, Install/Update/Status/Launch/Open Dir buttons
  - State machine controlling which buttons are enabled: `Unconnected -> NoInstall/NonManagedInstall -> Connected`

- **`Controller`** — Wires frontend callbacks to backend operations. Key flows:
  - **Confirm path**: checks if dir exists, validates git repo, handles non-git existing installs
  - **Install**: clones or init+fetch+checkout depending on existing directory state
  - **Update**: fetch + pull on selected branch
  - **Launch**: finds/caches the Minecraft launcher executable path, launches it, then quits the updater

- **Git bootstrapping** — On startup, detects if git is installed. On Windows, offers to silently download and install Git for Windows. On Mac/Linux, opens the download page. Sets `GIT_PYTHON_GIT_EXECUTABLE` env var.

- **Cross-platform** — Supports Windows, macOS, and Linux paths and behaviors.

- **Build** — `Makefile` uses PyInstaller to produce `FrontierLauncher.exe` (single-file, no console window). The built exe lives at the repo root for easy download.

## Key paths

- `mods/` — All mod JARs (force-added to git)
- `config/` — Mod configuration files
- `shaderpacks/` — Shader packs
- `resourcepacks/` — Resource packs
- `options.txt` — Minecraft client settings (tracked so defaults ship with the pack)
- `frontier_assets/frontier_launcher.py` — The launcher/updater source
- `frontier_assets/Makefile` — PyInstaller build recipe
- `FrontierLauncher.exe` — Built launcher binary at repo root
- `README.md` — Player-facing install instructions
