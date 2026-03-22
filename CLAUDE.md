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

## TACZ Recipe Generation System

Generates balanced crafting recipes for all TACZ gunpack weapons, ammo, and attachments. Lives in `frontier_assets/`.

### Architecture

Four Python files:

- **`recipe_common.py`** — Shared config: material definitions (CSV column → TACZ JSON), pack paths, CSV field lists. Both balance scripts import from here.
- **`balance_recipes.py`** — **Gun** recipe balancer. Reads gun `_data.json` stats, computes power scores, applies material profiles, writes gun rows to `recipes.csv`.
- **`ammo_recipes.py`** — **Ammo** recipe balancer. Caliber power table + global knobs → computes ammo material costs and yields, writes ammo rows to `recipes.csv`.
- **`gen_recipes.py`** — Final stage. Reads `recipes.csv` and writes the actual JSON recipe files into each gunpack's directory.

### Pipeline

```
# Guns: scan stats → edit balance.csv → compute recipes
python3 frontier_assets/balance_recipes.py --scan     # discover guns, populate balance.csv
# (edit balance.csv — assign profiles, tweak mult/offset/extras)
python3 frontier_assets/balance_recipes.py            # compute gun recipes → recipes.csv

# Ammo: all config is in ammo_recipes.py (no CSV input)
python3 frontier_assets/ammo_recipes.py               # compute ammo recipes → recipes.csv

# Write JSON files from recipes.csv
python3 frontier_assets/gen_recipes.py                # write JSON to tacz/*/recipes/
```

### Gun balance flow

1. `--scan` reads `*_data.json` files, computes power scores (geometric mean of sustained DPS × alpha damage), writes `balance.csv`
2. User edits `balance.csv`: assigns material profiles (`old_wood`, `modern_steel`, etc.), tunes per-gun `mult`/`offset`/`extras`
3. Default mode reads `balance.csv`, computes `budget = GLOBAL_SCALE * expensive_score ^ GLOBAL_EXPONENT`, distributes across profile materials

### Ammo balance flow

All config lives as Python globals in `ammo_recipes.py`:
- **`CALIBERS`** dict — base power per caliber (9mm=1.0 baseline), shared across packs
- **`AMMO_PROFILES`** — material distributions: `brass` (copper+gunpowder), `shotshell` (iron_nugget+gunpowder+paper), `explosive` (iron_plate+gunpowder+steel_rod)
- **`AMMO_ENTRIES`** — registry mapping (pack, ammo_id) → caliber + profile + per-entry mult/offset/yield_override/extras
- **Global knobs**: `AMMO_SCALE`, `AMMO_EXPONENT` (cost curve), `YIELD_BASE`, `YIELD_EXPONENT` (rounds per craft curve)

Preview without writing: `python3 frontier_assets/ammo_recipes.py --preview`

### Other useful modes

- `balance_recipes.py --scores` — print ranked power scores for all guns
- `balance_recipes.py --preview` — show full gun breakdown without writing
- `gen_recipes.py --uncraftable` — set every recipe to 1 bedrock (testing)

### Key data files

- `frontier_assets/balance.csv` — gun balance tuning (profiles, mult, offset, extras)
- `frontier_assets/recipes.csv` — intermediate: all recipes in flat CSV, read by gen_recipes.py
- `tacz/*/data/*/recipes/{gun,ammo,attachments}/*.json` — output JSON recipes

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
