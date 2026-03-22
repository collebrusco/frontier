"""
Ammo recipe generator for TACZ gunpacks.

Computes ammo crafting recipes from caliber power values and global tuning
knobs, then updates ammo rows in recipes.csv. Gun and attachment rows are
preserved untouched.

Usage:
    python frontier_assets/ammo_recipes.py             # compute and write ammo recipes
    python frontier_assets/ammo_recipes.py --preview   # show breakdown without writing

Run from repo root.

Tuning guide:
    - CALIBERS dict sets base power per caliber (9mm = 1.0 baseline).
    - AMMO_SCALE / AMMO_EXPONENT control overall material cost curve.
    - YIELD_BASE / YIELD_EXPONENT control rounds-per-craft curve.
    - Per-entry mult/offset tweak individual ammo types.
    - Per-entry extras add special materials on top (lapis, blaze_rod, etc.).
    - yield_override (non-None) bypasses the auto yield formula.
"""

import argparse
import csv
import math
import os

from recipe_common import MATERIAL_COLS, RECIPES_FIELDS

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
RECIPES_CSV = os.path.join(SCRIPT_DIR, "recipes.csv")

# ---------------------------------------------------------------------------
# Global tuning knobs
# ---------------------------------------------------------------------------

AMMO_SCALE    = 24.0    # Multiplier on material budget (higher = everything costs more)
AMMO_EXPONENT = 0.6    # Range compression (< 1 compresses cheap/expensive gap)

YIELD_BASE     = 16      # Yield for a power=1.0 round
YIELD_EXPONENT = 0.35    # How steeply yield drops with power (< 1 = gentle slope)

# ---------------------------------------------------------------------------
# Ammo material profiles
# Weights must sum to 1.0.
# ---------------------------------------------------------------------------

AMMO_PROFILES = {
    "pistol":     {"brass": 0.25, "lead": 0.40, "gunpowder": 0.35},
    "rifle":     {"brass": 0.25, "lead": 0.35, "gunpowder": 0.40},
    "shotshell": {"paper": 0.15, "lead": 0.40, "gunpowder": 0.30, "iron_nugget": 0.15},
    "explosive": {"iron_plate": 0.35, "tnt": 0.30, "gunpowder": 0.25, "steel_rod": 0.10},
}

# ---------------------------------------------------------------------------
# Caliber table — base power values
#
# Roughly proportional to bullet mass and cartridge energy.
# 9mm Parabellum = 1.0 baseline.
# ---------------------------------------------------------------------------

CALIBERS = {
    # Rimfire
    ".22lr":      0.4,
    ".22wmr":     0.5,
    # Pistol
    "7.65x20mm":  0.6,
    "9mm":        1.0,
    "45acp":      1.5,
    "762x25":     1.0,
    "357mag":     1.5,
    "50ae":       2.2,
    # PDW
    "46x30":      0.8,
    "57x28":      0.9,
    # Intermediate rifle
    "6x35mm":     1.5,
    "545x39":     1.8,
    "556x45":     1.9,
    "762x39":     2.1,
    "58x42":      2.0,
    "6.8tvcm":    2.3,
    "68x51fury":  2.5,
    # Full-power rifle
    "308":        3.0,
    "30_06":      3.2,
    "762x54":     3.0,
    "45_70":      3.5,
    # Heavy / sniper
    "338":        4.5,
    "12.7x55":    4.0,
    ".408ct":     6.5,
    "50bmg":      7.0,
    ".600ne":     9.0,
    # Shotgun
    "12g":        2.5,
    # Autocannon
    "23mm":       12.0,
    # Grenades / rockets
    "35x32mm":    3.0,
    "40mm":       5.0,
    "rpg":        10.0,
    "120mm":      20.0,
    # Misc
    "flare":      0.3,
    "boomstick":  1.5,
}

# ---------------------------------------------------------------------------
# Ammo registry
#
# Each entry: (pack, id, caliber, profile, mult, offset, yield_override, extras)
#
#   caliber        — key into CALIBERS table
#   profile        — key into AMMO_PROFILES ("pistol", "rifle", "shotshell", "explosive")
#   mult / offset  — per-entry tuning: effective_power = caliber_power * mult + offset
#   yield_override — None = auto-compute, or int to force a specific yield
#   extras         — "material:count,..." added on top of computed materials
# ---------------------------------------------------------------------------

# egs of extras

    # ("suffuse", "12.7x55",       "12.7x55",    "rifle",     1.0, 0, None, "lapis:1"),
    # ("suffuse", "23mm",          "23mm",        "rifle",     1.0, 0, 12,   "iron_plate:4"),

AMMO_ENTRIES = [
    # --- HAMSTER (GunpowderRevolution) ---
    # Abstract names: compact=pistol, medium=intermediate, long=rifle
    ("hamster", "compact_ammo",  "9mm",       "pistol",    1.0, 0, None, ""),
    ("hamster", "medium_ammo",   "45acp",     "pistol",    1.0, 0, None, ""),
    ("hamster", "long_ammo",     "308",       "rifle",     1.0, 0, None, ""),
    ("hamster", "flares_ammo",   "flare",     "pistol",    1.0, 0, None,  ""),
    ("hamster", "12g",           "12g",       "shotshell", 1.0, 0, None, ""),

    # --- TACZ (tacz_default_gun) ---
    # Pistol calibers
    ("tacz", "9mm",        "9mm",       "pistol", 1.0, 0, None, ""),
    ("tacz", "45acp",      "45acp",     "pistol", 1.0, 0, None, ""),
    ("tacz", "357mag",     "357mag",    "pistol", 1.0, 0, None, ""),
    ("tacz", "50ae",       "50ae",      "pistol", 1.0, 0, None, ""),
    ("tacz", "762x25",     "762x25",    "pistol", 1.0, 0, None, ""),
    # PDW
    ("tacz", "46x30",      "46x30",     "pistol", 1.0, 0, None, ""),
    ("tacz", "57x28",      "57x28",     "pistol", 1.0, 0, None, ""),
    # Intermediate
    ("tacz", "545x39",     "545x39",    "rifle",  1.0, 0, None, ""),
    ("tacz", "556x45",     "556x45",    "rifle",  1.0, 0, None, ""),
    ("tacz", "762x39",     "762x39",    "rifle",  1.0, 0, None, ""),
    ("tacz", "6x35mm",     "6x35mm",    "rifle",  1.0, 0, None, ""),
    # Full-power rifle
    ("tacz", "308",        "308",       "rifle",  1.0, 0, None, ""),
    ("tacz", "30_06",      "30_06",     "rifle",  1.0, 0, None, ""),
    ("tacz", "762x54",     "762x54",    "rifle",  1.0, 0, None, ""),
    ("tacz", "58x42",      "58x42",     "rifle",  1.0, 0, None, ""),
    ("tacz", "68x51fury",  "68x51fury", "rifle",  1.0, 0, None, ""),
    # Heavy / sniper
    ("tacz", "338",        "338",       "rifle",  1.0, 0, None, ""),
    ("tacz", "45_70",      "45_70",     "rifle",  1.0, 0, None, ""),
    ("tacz", "50bmg",      "50bmg",     "rifle",  1.0, 0, None, ""),
    # Shotgun
    ("tacz", "12g",        "12g",       "shotshell", 1.0, 0, None, ""),
    # Explosive / launcher
    ("tacz", "40mm",       "40mm",      "explosive", 1.0, 0, None,  ""),
    ("tacz", "rpg_rocket", "rpg",       "explosive", 1.0, 0, 3,  ""),

    # --- SUFFUSE (GunSmoke) ---
    ("suffuse", "7.65x20mm",     "7.65x20mm",  "pistol",    1.0, 0, None, ""),
    ("suffuse", "6x35mm",        "6x35mm",     "rifle",     1.0, 0, None, ""),
    ("suffuse", "35x32mm",       "35x32mm",    "explosive", 1.0, 0, 10,   ""),
    ("suffuse", "545x39",        "545x39",     "rifle",     1.0, 0, None, ""),
    ("suffuse", "6.8tvcm",       "6.8tvcm",    "rifle",     1.0, 0, None, ""),
    ("suffuse", "12.7x55",       "12.7x55",    "rifle",     1.0, 0, None, ""),
    ("suffuse", "23mm",          "23mm",        "rifle",     1.0, 0, 12,   ""),
    ("suffuse", "120mm",         "120mm",       "explosive", 1.0, 0, 1,    ""),
    ("suffuse", "boomstickshot", "boomstick",   "shotshell", 1.0, 0, 6,    ""),
    ("suffuse", ".22lr",         ".22lr",       "pistol",    1.0, 0, None, ""),
    ("suffuse", ".22wmr",        ".22wmr",      "pistol",    1.0, 0, None, ""),
    ("suffuse", ".408ct",        ".408ct",      "rifle",     1.0, 0, None, ""),
    ("suffuse", ".600ne",        ".600ne",      "rifle",     1.0, 0, None, ""),
]

# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------

def _validate():
    for name, weights in AMMO_PROFILES.items():
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            print(f"ERROR: ammo profile '{name}' weights sum to {total}, expected 1.0")
            raise SystemExit(1)
        for mat in weights:
            if mat not in MATERIAL_COLS:
                print(f"ERROR: ammo profile '{name}' uses unknown material '{mat}'")
                raise SystemExit(1)
    for entry in AMMO_ENTRIES:
        _, _, caliber, profile, _, _, _, _ = entry
        if caliber not in CALIBERS:
            print(f"ERROR: unknown caliber '{caliber}' in ammo registry")
            raise SystemExit(1)
        if profile not in AMMO_PROFILES:
            print(f"ERROR: unknown profile '{profile}' in ammo registry")
            raise SystemExit(1)

_validate()

# ---------------------------------------------------------------------------
# Computation
# ---------------------------------------------------------------------------

def _parse_extras(extras_str):
    """Parse 'uranium:1,brass:4' → {'uranium': 1, 'brass': 4}."""
    if not extras_str or not extras_str.strip():
        return {}
    result = {}
    for pair in extras_str.split(","):
        pair = pair.strip()
        if ":" not in pair:
            continue
        key, val = pair.split(":", 1)
        key, val = key.strip(), val.strip()
        if key and val:
            result[key] = int(val)
    return result

def compute_budget(power, mult=1.0, offset=0):
    """Caliber power → total material budget."""
    effective = power * mult + offset
    return int(AMMO_SCALE * (max(effective, 0.01) ** AMMO_EXPONENT))

def compute_yield(power, mult=1.0, offset=0):
    """Caliber power → rounds per craft."""
    effective = power * mult + offset
    return max(1, int(YIELD_BASE / (max(effective, 0.01) ** YIELD_EXPONENT)))

def compute_materials(profile_name, budget, extras_str=""):
    """Distribute budget across profile materials, add extras on top."""
    profile = AMMO_PROFILES[profile_name]
    mats = {}
    for mat, weight in profile.items():
        count = int(budget * weight)
        if count > 0:
            mats[mat] = count
    for mat, count in _parse_extras(extras_str).items():
        mats[mat] = mats.get(mat, 0) + count
    return mats

def process_entry(entry):
    """Process one AMMO_ENTRIES tuple → (pack, id, yield, materials_dict, debug_info)."""
    pack, ammo_id, caliber, profile, mult, offset, yield_override, extras = entry
    power = CALIBERS[caliber]
    budget = compute_budget(power, mult, offset)
    yld = yield_override if yield_override is not None else compute_yield(power, mult, offset)
    mats = compute_materials(profile, budget, extras)
    debug = {
        "caliber": caliber, "profile": profile,
        "power": power, "mult": mult, "offset": offset,
        "budget": budget, "yield": yld,
    }
    return pack, ammo_id, yld, mats, debug

# ---------------------------------------------------------------------------
# CSV I/O — updates ammo rows in recipes.csv, preserves everything else
# ---------------------------------------------------------------------------

def read_recipes_csv():
    if not os.path.exists(RECIPES_CSV):
        return []
    with open(RECIPES_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_recipes_csv(rows):
    with open(RECIPES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RECIPES_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def write_mode():
    recipes = read_recipes_csv()

    # Index existing ammo rows by (pack, id)
    ammo_index = {}
    for i, row in enumerate(recipes):
        pack  = row.get("pack", "").strip()
        rtype = row.get("type", "").strip()
        rid   = row.get("id", "").strip()
        if rtype == "ammo" and pack and not pack.startswith("#"):
            ammo_index[(pack, rid)] = i

    updated = 0
    added = 0

    for entry in AMMO_ENTRIES:
        pack, ammo_id, yld, mats, _ = process_entry(entry)

        recipe_row = {"pack": pack, "type": "ammo", "id": ammo_id, "yield": yld}
        for col in MATERIAL_COLS:
            recipe_row[col] = mats.get(col, "")
        recipe_row["notes"] = ""

        key = (pack, ammo_id)
        if key in ammo_index:
            idx = ammo_index[key]
            recipe_row["notes"] = recipes[idx].get("notes", "")
            recipes[idx] = recipe_row
            updated += 1
        else:
            recipes.append(recipe_row)
            added += 1

    write_recipes_csv(recipes)
    print(f"Updated {RECIPES_CSV}: {updated} ammo updated, {added} ammo added")
    print(f"  (gun and attachment rows preserved)")
    print(f"  Knobs: SCALE={AMMO_SCALE}  EXPONENT={AMMO_EXPONENT}  "
          f"YIELD_BASE={YIELD_BASE}  YIELD_EXP={YIELD_EXPONENT}")

# ---------------------------------------------------------------------------
# --preview: show breakdown without writing
# ---------------------------------------------------------------------------

def preview_mode():
    print(f"{'Pack':<10} {'ID':<20} {'Cal':<12} {'Prof':<10} "
          f"{'Pwr':>5} {'x':>4} {'+':>3} {'Bgt':>5} {'Yld':>4}  Materials")
    print("-" * 110)

    for entry in AMMO_ENTRIES:
        pack, ammo_id, yld, mats, dbg = process_entry(entry)
        mat_str = "  ".join(f"{k}={v}" for k, v in sorted(mats.items()) if v > 0)
        print(f"{pack:<10} {ammo_id:<20} {dbg['caliber']:<12} {dbg['profile']:<10} "
              f"{dbg['power']:>5.1f} {dbg['mult']:>4.1f} {dbg['offset']:>+3.0f} "
              f"{dbg['budget']:>5} {yld:>4}  {mat_str}")

    print(f"\n{len(AMMO_ENTRIES)} ammo entries  |  "
          f"SCALE={AMMO_SCALE}  EXPONENT={AMMO_EXPONENT}  "
          f"YIELD_BASE={YIELD_BASE}  YIELD_EXP={YIELD_EXPONENT}")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TACZ ammo recipe generator")
    parser.add_argument("--preview", action="store_true",
                        help="Show breakdown without writing to recipes.csv")
    args = parser.parse_args()

    if args.preview:
        preview_mode()
    else:
        write_mode()
