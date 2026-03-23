"""
Attachment recipe generator for TACZ gunpacks.

Computes attachment crafting recipes from category base costs, material
profiles, and global tuning knobs, then updates attachment rows in
recipes.csv. Gun and ammo rows are preserved untouched.

Usage:
    python frontier_assets/attachment_recipes.py             # compute and write
    python frontier_assets/attachment_recipes.py --preview   # show breakdown

Run from repo root.

Tuning guide:
    - ATTACH_SCALE / ATTACH_EXPONENT control overall material cost curve.
    - Category base_cost sets the relative expense of each attachment type.
    - Per-entry mult/offset tweak individual attachments.
    - Per-entry extras add special materials on top.
"""

import argparse
import csv
import os

from recipe_common import MATERIAL_COLS, RECIPES_FIELDS

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
RECIPES_CSV = os.path.join(SCRIPT_DIR, "recipes.csv")

# ---------------------------------------------------------------------------
# Global tuning knobs
# ---------------------------------------------------------------------------

ATTACH_SCALE    = 100.0   # Multiplier on material budget
ATTACH_EXPONENT = 0.65   # Range compression (< 1 compresses cheap/expensive gap)

# ---------------------------------------------------------------------------
# Attachment category profiles
#
# Each category has:
#   base_cost  — relative expense (1.0 = baseline red dot sight)
#   materials  — weight distribution (must sum to 1.0)
# ---------------------------------------------------------------------------

ATTACH_PROFILES = {
    "sight": {
        "base_cost": 1.0,
        "materials": {"steel_plate": 0.30, "glass": 0.30, "electron_tube": 0.20, "redstone": 0.20},
    },
    "scope_low": {
        "base_cost": 1.8,
        "materials": {"steel_plate": 0.25, "glass": 0.35, "steel_comp": 0.20, "electron_tube": 0.20},
    },
    "scope_high": {
        "base_cost": 2.8,
        "materials": {"steel_plate": 0.20, "glass": 0.30, "steel_comp": 0.25, "electron_tube": 0.25},
    },
    "scope_historical": {
        "base_cost": 1.5,
        "materials": {"steel_plate": 0.25, "glass": 0.40, "steel_comp": 0.20, "brass": 0.15},
    },
    "grip_polymer": {
        "base_cost": 0.8,
        "materials": {"plastic": 0.50, "steel_rod": 0.30, "steel_plate": 0.20},
    },
    "grip_metal": {
        "base_cost": 0.8,
        "materials": {"steel_plate": 0.40, "steel_rod": 0.30, "logs": 0.30},
    },
    "stock_polymer": {
        "base_cost": 1.2,
        "materials": {"plastic": 0.50, "steel_rod": 0.20, "steel_plate": 0.30},
    },
    "stock_wood": {
        "base_cost": 1.0,
        "materials": {"logs": 0.50, "steel_plate": 0.30, "steel_rod": 0.20},
    },
    "magazine_light": {
        "base_cost": 1.2,
        "materials": {"steel_plate": 0.60, "steel_rod": 0.25, "andesite": 0.15},
    },
    "magazine_heavy": {
        "base_cost": 2.0,
        "materials": {"steel_plate": 0.55, "steel_rod": 0.25, "steel_comp": 0.20},
    },
    "muzzle_brake": {
        "base_cost": 1.0,
        "materials": {"steel_plate": 0.60, "steel_rod": 0.40},
    },
    "silencer": {
        "base_cost": 2.5,
        "materials": {"steel_plate": 0.35, "alum_plate": 0.25, "steel_rod": 0.20, "steel_comp": 0.20},
    },
    "laser": {
        "base_cost": 1.5,
        "materials": {"electron_tube": 0.30, "redstone": 0.30, "gold_plate": 0.20, "glass": 0.20},
    },
    "bayonet": {
        "base_cost": 1.5,
        "materials": {"steel_plate": 0.65, "steel_rod": 0.20, "leather": 0.15},
    },
    "ammo_mod": {
        "base_cost": 1.0,
        "materials": {"copper": 0.40, "lead": 0.30, "gunpowder": 0.30},
    },
    "bipod": {
        "base_cost": 1.0,
        "materials": {"steel_rod": 0.50, "steel_plate": 0.30, "iron_plate": 0.20},
    },
    "misc_metal": {
        "base_cost": 1.0,
        "materials": {"steel_plate": 0.50, "steel_rod": 0.30, "iron_plate": 0.20},
    },
    "launcher_attachment": {
        "base_cost": 5.0,
        "materials": {"steel_plate": 0.40, "steel_comp": 0.30, "steel_rod": 0.20, "iron_plate": 0.10},
    },
}

# ---------------------------------------------------------------------------
# Attachment registry
#
# (pack, id, category, mult, offset, extras)
#
#   category — key into ATTACH_PROFILES
#   mult/offset — per-entry tuning: effective = base_cost * mult + offset
#   extras — "material:count,..." added on top
# ---------------------------------------------------------------------------

ATTACH_ENTRIES = [
    # ===== HAMSTER (GunpowderRevolution) =====
    # Bayonets
    ("hamster", "bayonet9805",      "bayonet",          1.0, 0, ""),
    ("hamster", "bayonetm1886",     "bayonet",          1.0, 0, ""),
    ("hamster", "bayonetp1903",     "bayonet",          1.0, 0, ""),
    ("hamster", "bayonettype30",    "bayonet",          1.0, 0, ""),
    ("hamster", "m9130_bayonet",    "bayonet",          1.0, 0, ""),
    ("hamster", "sks_bayonet",      "bayonet",          0.9, 0, ""),
    # Sights / scopes
    ("hamster", "aperture_sight",   "sight",            0.8, 0, ""),
    ("hamster", "deadeye_scope",    "scope_historical", 1.2, 0, ""),
    ("hamster", "gew98_scope",      "scope_historical", 1.0, 0, ""),
    ("hamster", "lebel_scope",      "scope_historical", 1.0, 0, ""),
    ("hamster", "ppco_scope",       "scope_historical", 1.3, 0, ""),
    ("hamster", "puscope",          "scope_historical", 1.1, 0, ""),
    ("hamster", "unertl_scope",     "scope_historical", 1.5, 0, ""),
    # Magazines
    ("hamster", "drum_mag",         "magazine_heavy",   1.2, 0, ""),
    ("hamster", "trench_mag",       "magazine_light",   1.2, 0, ""),
    # Misc
    ("hamster", "loading_pipe",     "misc_metal",       0.6, 0, ""),
    ("hamster", "rifle_bipod",      "bipod",            1.0, 0, ""),
    ("hamster", "rifle_grip",       "grip_metal",       1.0, 0, ""),
    ("hamster", "gas_tube",         "misc_metal",       0.5, 0, ""),
    ("hamster", "speedloader",      "misc_metal",       1.0, 0, "brass:4"),
    ("hamster", "whip",             "misc_metal",       0.5, 0, "leather:4"),

    # ===== TACZ (tacz_default_gun) =====
    # Sights — red dots / reflex / holo
    ("tacz", "sight_552",               "sight",  1.0, 0, ""),
    ("tacz", "sight_acro_pistol",       "sight",  0.8, 0, ""),
    ("tacz", "sight_acro_rifle",        "sight",  0.9, 0, ""),
    ("tacz", "sight_coyote",            "sight",  0.9, 0, ""),
    ("tacz", "sight_deltapoint_pistol", "sight",  0.8, 0, ""),
    ("tacz", "sight_deltapoint_rifle",  "sight",  0.9, 0, ""),
    ("tacz", "sight_exp3",              "sight",  1.0, 0, ""),
    ("tacz", "sight_fastfire_pistol",   "sight",  0.8, 0, ""),
    ("tacz", "sight_fastfire_rifle",    "sight",  0.9, 0, ""),
    ("tacz", "sight_okp7",              "sight",  0.9, 0, ""),
    ("tacz", "sight_pk06_pistol",       "sight",  0.8, 0, ""),
    ("tacz", "sight_pk06_rifle",        "sight",  0.9, 0, ""),
    ("tacz", "sight_rmr_dot",           "sight",  0.8, 0, ""),
    ("tacz", "sight_sro_dot",           "sight",  0.9, 0, ""),
    ("tacz", "sight_srs_02",            "sight",  1.0, 0, ""),
    ("tacz", "sight_t1",                "sight",  0.9, 0, ""),
    ("tacz", "sight_t2",                "sight",  1.0, 0, ""),
    ("tacz", "sight_uh1",               "sight",  1.1, 0, ""),
    # Scopes — low magnification
    ("tacz", "scope_retro_2x",          "scope_low",  0.8, 0, ""),
    ("tacz", "scope_acog_ta31",         "scope_low",  1.0, 0, ""),
    ("tacz", "scope_elcan_4x",          "scope_low",  1.0, 0, ""),
    ("tacz", "scope_hamr",              "scope_low",  1.1, 0, ""),
    ("tacz", "scope_lpvo_1_6",          "scope_low",  1.0, 0, ""),
    ("tacz", "scope_contender",         "scope_low",  0.9, 0, ""),
    ("tacz", "scope_vudu",              "scope_low",  1.1, 0, ""),
    ("tacz", "scope_qmk152",            "scope_low",  1.0, 0, ""),
    ("tacz", "scope_1873_6x",           "scope_historical", 1.0, 0, ""),
    # Scopes — high magnification
    ("tacz", "scope_standard_8x",       "scope_high", 1.0, 0, ""),
    ("tacz", "scope_mk5hd",             "scope_high", 1.2, 0, ""),
    # Grips
    ("tacz", "grip_cobra",              "grip_polymer", 1.0, 0, ""),
    ("tacz", "grip_magpul_afg_2",       "grip_polymer", 1.0, 0, ""),
    ("tacz", "grip_osovets_black",      "grip_polymer", 0.9, 0, ""),
    ("tacz", "grip_rk0",                "grip_polymer", 0.9, 0, ""),
    ("tacz", "grip_rk1_b25u",           "grip_polymer", 1.0, 0, ""),
    ("tacz", "grip_rk6",                "grip_polymer", 0.9, 0, ""),
    ("tacz", "grip_se_5",               "grip_polymer", 1.0, 0, ""),
    ("tacz", "grip_td",                 "grip_polymer", 1.0, 0, ""),
    ("tacz", "grip_vertical_military",  "grip_polymer", 0.9, 0, ""),
    ("tacz", "grip_vertical_ranger",    "grip_polymer", 0.9, 0, ""),
    ("tacz", "grip_vertical_talon",     "grip_polymer", 0.9, 0, ""),
    # Stocks
    ("tacz", "stock_ak12",              "stock_polymer", 1.0, 0, ""),
    ("tacz", "stock_carbon_bone_c5",    "stock_polymer", 1.1, 0, ""),
    ("tacz", "stock_heavy_spas_12",     "stock_polymer", 1.2, 0, ""),
    ("tacz", "stock_hk_slim_line",      "stock_polymer", 0.9, 0, ""),
    ("tacz", "stock_m4ss",              "stock_polymer", 1.0, 0, ""),
    ("tacz", "stock_militech_b5",       "stock_polymer", 1.0, 0, ""),
    ("tacz", "stock_moe",               "stock_polymer", 0.9, 0, ""),
    ("tacz", "stock_ripstock",          "stock_polymer", 0.9, 0, ""),
    ("tacz", "stock_sba3",              "stock_polymer", 0.8, 0, ""),
    ("tacz", "stock_tactical_ar",       "stock_polymer", 1.0, 0, ""),
    ("tacz", "stock_tactical_spas_12",  "stock_polymer", 1.1, 0, ""),
    ("tacz", "oem_stock_light",         "stock_polymer", 0.7, 0, ""),
    ("tacz", "oem_stock_tactical",      "stock_polymer", 0.9, 0, ""),
    ("tacz", "oem_stock_heavy",         "stock_polymer", 1.1, 0, ""),
    # Magazines — light (pistol / SMG)
    ("tacz", "light_extended_mag_1",    "magazine_light", 0.8, 0, ""),
    ("tacz", "light_extended_mag_2",    "magazine_light", 1.0, 0, ""),
    ("tacz", "light_extended_mag_3",    "magazine_light", 1.3, 0, ""),
    # Magazines — standard (rifle)
    ("tacz", "extended_mag_1",          "magazine_light", 1.0, 0, ""),
    ("tacz", "extended_mag_2",          "magazine_light", 1.3, 0, ""),
    ("tacz", "extended_mag_3",          "magazine_heavy", 1.0, 0, ""),
    # Magazines — sniper
    ("tacz", "sniper_extended_mag_1",   "magazine_light", 0.8, 0, ""),
    ("tacz", "sniper_extended_mag_2",   "magazine_light", 1.0, 0, ""),
    ("tacz", "sniper_extended_mag_3",   "magazine_heavy", 0.9, 0, ""),
    # Magazines — shotgun
    ("tacz", "shotgun_extended_mag_1",  "magazine_light", 0.8, 0, ""),
    ("tacz", "shotgun_extended_mag_2",  "magazine_light", 1.0, 0, ""),
    ("tacz", "shotgun_extended_mag_3",  "magazine_heavy", 0.9, 0, ""),
    # Muzzle brakes / compensators
    ("tacz", "muzzle_brake_cthulhu",        "muzzle_brake", 1.1, 0, ""),
    ("tacz", "muzzle_brake_cyclone_d2",     "muzzle_brake", 1.0, 0, ""),
    ("tacz", "muzzle_brake_mastiff_sg",     "muzzle_brake", 1.0, 0, ""),
    ("tacz", "muzzle_brake_pioneer",        "muzzle_brake", 1.0, 0, ""),
    ("tacz", "muzzle_brake_timeless50",     "muzzle_brake", 1.1, 0, ""),
    ("tacz", "muzzle_brake_trex",           "muzzle_brake", 1.0, 0, ""),
    ("tacz", "muzzle_choke_sg",             "muzzle_brake", 0.8, 0, ""),
    ("tacz", "muzzle_compensator_trident",  "muzzle_brake", 1.0, 0, ""),
    # Silencers
    ("tacz", "muzzle_silencer_knight_qd",   "silencer", 1.0, 0, ""),
    ("tacz", "muzzle_silencer_mirage",      "silencer", 0.9, 0, ""),
    ("tacz", "muzzle_silencer_phantom_s1",  "silencer", 1.0, 0, ""),
    ("tacz", "muzzle_silencer_ptilopsis",   "silencer", 0.9, 0, ""),
    ("tacz", "muzzle_silencer_sg",          "silencer", 1.1, 0, ""),
    ("tacz", "muzzle_silencer_ursus",       "silencer", 0.95, 0, ""),
    ("tacz", "muzzle_silencer_vulture",     "silencer", 1.0, 0, ""),
    # Lasers
    ("tacz", "laser_compact",       "laser", 0.8, 0, ""),
    ("tacz", "laser_lopro",         "laser", 0.8, 0, ""),
    ("tacz", "laser_nightstick",    "laser", 1.0, 0, ""),
    # Bayonets
    ("tacz", "bayonet_6h3",         "bayonet", 1.0, 0, ""),
    ("tacz", "bayonet_m9",          "bayonet", 1.0, 0, ""),
    # Special
    ("tacz", "deagle_golden_long_barrel", "muzzle_brake", 1.5, 0, "gold_plate:48"),
    # Ammo mods
    ("tacz", "ammo_mod_fmj",    "ammo_mod", 1.0, 0, "copper:8"),
    ("tacz", "ammo_mod_he",     "ammo_mod", 1.2, 0, "gunpowder:4"),
    ("tacz", "ammo_mod_hp",     "ammo_mod", 0.8, 0, "copper:12"),
    ("tacz", "ammo_mod_i",      "ammo_mod", 1.0, 0, "blaze_rod:2"),
    ("tacz", "ammo_mod_slug",   "ammo_mod", 1.0, 0, "iron_plate:4"),

    # ===== SUFFUSE (GunSmoke) =====
    # Grips
    ("suffuse", "grip_td",             "grip_polymer", 1.0, 0, ""),
    ("suffuse", "grip_td_black",       "grip_polymer", 1.0, 0, ""),
    ("suffuse", "grip_td_blue_grey",   "grip_polymer", 1.0, 0, ""),
    ("suffuse", "grip_td_green",       "grip_polymer", 1.0, 0, ""),
    ("suffuse", "grip_flashlight",     "grip_polymer", 1.0, 0, "electron_tube:1,glass:1"),
    ("suffuse", "grip_m203",           "launcher_attachment", 1.0, 0, ""),
    # Stocks
    ("suffuse", "stock_n4",                 "stock_polymer", 0.9, 0, ""),
    ("suffuse", "stock_bcm_mod2_sopmod",    "stock_polymer", 1.1, 0, ""),
    ("suffuse", "stock_colt",               "stock_wood",    1.0, 0, ""),
    ("suffuse", "stock_colt_plus",          "stock_wood",    1.1, 0, ""),
    ("suffuse", "stock_elf_ultralight",     "stock_polymer", 0.8, 0, ""),
    ("suffuse", "stock_sig_black",          "stock_polymer", 1.1, 0, ""),
    ("suffuse", "stock_sig_blue_grey",      "stock_polymer", 1.1, 0, ""),
    ("suffuse", "stock_sig_desert",         "stock_polymer", 1.1, 0, ""),
    ("suffuse", "stock_vltor_emod_black",   "stock_polymer", 1.2, 0, ""),
    ("suffuse", "stock_vltor_emod_desert",  "stock_polymer", 1.2, 0, ""),
    ("suffuse", "stock_vltor_emod_green",   "stock_polymer", 1.2, 0, ""),
    # Lasers
    ("suffuse", "laser_an_peq_2a",  "laser", 1.1, 0, ""),
    ("suffuse", "laser_dbala2",     "laser", 1.1, 0, ""),
    ("suffuse", "laser_pistol",     "laser", 0.7, 0, ""),
    ("suffuse", "pistollaser",      "laser", 0.7, 0, ""),
    # Sights
    ("suffuse", "sight_cobra_ekp_818", "sight",  1.0, 0, ""),
    ("suffuse", "sight_dbala2",        "sight",  1.0, 0, ""),
    # Scopes
    ("suffuse", "scope_compm4",             "scope_low",  0.8, 0, ""),
    ("suffuse", "scope_ks23m",              "scope_low",  0.9, 0, ""),
    ("suffuse", "scope_qlu11s",             "scope_high", 1.0, 0, ""),
    ("suffuse", "scope_sig_tango_msr_1_6",  "scope_high", 1.1, 0, ""),
    # Silencers
    ("suffuse", "m7_silencer",      "silencer", 0.9, 0, ""),
    ("suffuse", "rm277_silencer",   "silencer", 1.0, 0, ""),
]

# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------

def _validate():
    for name, prof in ATTACH_PROFILES.items():
        total = sum(prof["materials"].values())
        if abs(total - 1.0) > 0.001:
            print(f"ERROR: profile '{name}' weights sum to {total}, expected 1.0")
            raise SystemExit(1)
        for mat in prof["materials"]:
            if mat not in MATERIAL_COLS:
                print(f"ERROR: profile '{name}' uses unknown material '{mat}'")
                raise SystemExit(1)
    for entry in ATTACH_ENTRIES:
        _, _, category, _, _, _ = entry
        if category not in ATTACH_PROFILES:
            print(f"ERROR: unknown category '{category}' in attachment registry")
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

def compute_budget(base_cost, mult=1.0, offset=0):
    """Category base cost → total material budget."""
    effective = base_cost * mult + offset
    return int(ATTACH_SCALE * (max(effective, 0.01) ** ATTACH_EXPONENT))

def compute_materials(category, budget, extras_str=""):
    """Distribute budget across category materials, add extras on top."""
    profile = ATTACH_PROFILES[category]["materials"]
    mats = {}
    for mat, weight in profile.items():
        count = int(budget * weight)
        if count > 0:
            mats[mat] = count
    for mat, count in _parse_extras(extras_str).items():
        mats[mat] = mats.get(mat, 0) + count
    return mats

def process_entry(entry):
    """Process one ATTACH_ENTRIES tuple → (pack, id, materials_dict, debug_info)."""
    pack, att_id, category, mult, offset, extras = entry
    base_cost = ATTACH_PROFILES[category]["base_cost"]
    budget = compute_budget(base_cost, mult, offset)
    mats = compute_materials(category, budget, extras)
    debug = {
        "category": category, "base_cost": base_cost,
        "mult": mult, "offset": offset, "budget": budget,
    }
    return pack, att_id, mats, debug

# ---------------------------------------------------------------------------
# CSV I/O — updates attachment rows in recipes.csv, preserves everything else
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

    # Index existing attachment rows by (pack, id)
    attach_index = {}
    for i, row in enumerate(recipes):
        pack  = row.get("pack", "").strip()
        rtype = row.get("type", "").strip()
        rid   = row.get("id", "").strip()
        if rtype == "attachment" and pack and not pack.startswith("#"):
            attach_index[(pack, rid)] = i

    updated = 0
    added = 0

    for entry in ATTACH_ENTRIES:
        pack, att_id, mats, _ = process_entry(entry)

        recipe_row = {"pack": pack, "type": "attachment", "id": att_id, "yield": ""}
        for col in MATERIAL_COLS:
            recipe_row[col] = mats.get(col, "")
        recipe_row["notes"] = ""

        key = (pack, att_id)
        if key in attach_index:
            idx = attach_index[key]
            recipe_row["notes"] = recipes[idx].get("notes", "")
            recipes[idx] = recipe_row
            updated += 1
        else:
            recipes.append(recipe_row)
            added += 1

    write_recipes_csv(recipes)
    print(f"Updated {RECIPES_CSV}: {updated} attachments updated, {added} attachments added")
    print(f"  (gun and ammo rows preserved)")
    print(f"  Knobs: SCALE={ATTACH_SCALE}  EXPONENT={ATTACH_EXPONENT}")

# ---------------------------------------------------------------------------
# --preview: show breakdown without writing
# ---------------------------------------------------------------------------

def preview_mode():
    print(f"{'Pack':<10} {'ID':<35} {'Category':<20} "
          f"{'Base':>5} {'x':>4} {'+':>3} {'Bgt':>5}  Materials")
    print("-" * 120)

    for entry in ATTACH_ENTRIES:
        pack, att_id, mats, dbg = process_entry(entry)
        mat_str = "  ".join(f"{k}={v}" for k, v in sorted(mats.items()) if v > 0)
        print(f"{pack:<10} {att_id:<35} {dbg['category']:<20} "
              f"{dbg['base_cost']:>5.1f} {dbg['mult']:>4.1f} {dbg['offset']:>+3.0f} "
              f"{dbg['budget']:>5}  {mat_str}")

    print(f"\n{len(ATTACH_ENTRIES)} attachment entries  |  "
          f"SCALE={ATTACH_SCALE}  EXPONENT={ATTACH_EXPONENT}")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TACZ attachment recipe generator")
    parser.add_argument("--preview", action="store_true",
                        help="Show breakdown without writing to recipes.csv")
    args = parser.parse_args()

    if args.preview:
        preview_mode()
    else:
        write_mode()
