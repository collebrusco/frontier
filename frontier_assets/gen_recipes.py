"""
Generates TACZ gun/ammo/attachment crafting recipes for all gunpacks.

Usage:
    python frontier_assets/gen_recipes.py               # write recipes from CSV
    python frontier_assets/gen_recipes.py --uncraftable # every recipe costs 1 bedrock
    python frontier_assets/gen_recipes.py --export-csv  # write frontier_assets/recipes.csv from built-in defaults

Run from repo root.

CSV format (frontier_assets/recipes.csv):
    One row per recipe. Columns: pack, type, id, yield, <material>...
    - pack:    hamster | tacz | suffuse
    - type:    gun | ammo | attachment
    - id:      registry ID without namespace (e.g. "flaregun", "9mm")
    - yield:   ammo only — how many rounds per craft (leave blank for guns/attachments)
    - materials: one column per ingredient, value = count (blank or 0 = not used)
    - notes:   optional, ignored by script — use for tier labels, comments, etc.
    Lines where pack starts with # are skipped (section headers in the sheet).

Key format note:
    IE items MUST use {"item": "immersiveengineering:..."} not {"tag": "..."}.
    Forge-standard tags (forge:ingots/copper, minecraft:logs, etc.) work fine as tags.
"""

import argparse
import csv
import json
import os

from recipe_common import MATERIAL_DEFS, MATERIAL_COLS, PACK_PATHS

# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--uncraftable", action="store_true",
                    help="Set every recipe to require 1 bedrock (disables all crafting)")
parser.add_argument("--export-csv", action="store_true",
                    help="Write the built-in default recipes to frontier_assets/recipes.csv then exit")
args = parser.parse_args()

UNCRAFTABLE  = args.uncraftable
EXPORT_CSV   = args.export_csv

CSV_PATH = os.path.join(os.path.dirname(__file__), "recipes.csv")

# ---------------------------------------------------------------------------
# Recipe writing
# ---------------------------------------------------------------------------

def _row_to_materials(row):
    mats = []
    for col in MATERIAL_COLS:
        val = row.get(col, "").strip()
        if val and val != "0":
            mats.append(MATERIAL_DEFS[col](int(val)))
    return mats

def _write_recipe(base_dir, rec_type, namespace, item_id, materials, yield_count=None):
    if rec_type == "gun":
        subdir = "gun"
        result = {"type": "gun", "id": f"{namespace}:{item_id}"}
    elif rec_type == "ammo":
        subdir = "ammo"
        result = {"type": "ammo", "id": f"{namespace}:{item_id}", "count": yield_count or 1}
    elif rec_type == "attachment":
        subdir = "attachments"
        result = {"type": "attachment", "id": f"{namespace}:{item_id}"}
    else:
        raise ValueError(f"Unknown type: {rec_type}")

    mats = [{"item": {"item": "minecraft:bedrock"}, "count": 1}] if UNCRAFTABLE else materials
    path = os.path.join(base_dir, subdir, f"{item_id}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"materials": mats, "result": result, "type": "tacz:gun_smith_table_crafting"}, f, indent=2)

# ---------------------------------------------------------------------------
# CSV reading — main mode
# ---------------------------------------------------------------------------

def run_from_csv():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found. Run with --export-csv to generate it first.")
        raise SystemExit(1)

    counts = {}
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pack = row.get("pack", "").strip()
            if not pack or pack.startswith("#"):
                continue
            rec_type    = row.get("type", "").strip()
            item_id     = row.get("id",   "").strip()
            yield_str   = row.get("yield","").strip()
            yield_count = int(yield_str) if yield_str else None

            base_dir = PACK_PATHS.get(pack)
            if not base_dir:
                print(f"  WARNING: unknown pack '{pack}', skipping '{item_id}'")
                continue

            materials = _row_to_materials(row)
            if not materials:
                print(f"  WARNING: no materials for {pack}:{item_id}, skipping")
                continue

            _write_recipe(base_dir, rec_type, pack, item_id, materials, yield_count)
            counts[rec_type] = counts.get(rec_type, 0) + 1

    mode = " (UNCRAFTABLE)" if UNCRAFTABLE else ""
    g, a, t = counts.get("gun", 0), counts.get("ammo", 0), counts.get("attachment", 0)
    print(f"Done{mode}: {g} guns, {a} ammo, {t} attachments ({g+a+t} total)")

# ===========================================================================
# Bootstrap data — used only by --export-csv
# Edit frontier_assets/recipes.csv instead of this section.
# ===========================================================================

def _bootstrap_data():
    """Returns list of (pack, type, id, yield_count, materials_dict) tuples."""
    rows = []

    def g(pack, gun_id, mats):
        rows.append((pack, "gun", gun_id, None, mats))
    def a(pack, ammo_id, mats, yld):
        rows.append((pack, "ammo", ammo_id, yld, mats))
    def t(pack, att_id, mats):
        rows.append((pack, "attachment", att_id, None, mats))

    # -----------------------------------------------------------------------
    # PACK 1 — GunpowderRevolution  (hamster)
    # Historical firearms 1840s–1945
    # -----------------------------------------------------------------------

    # Guns — Tier 1: Muzzle-loader / Percussion cap (1840s–1860s)
    g("hamster", "flaregun",            dict(steel_plate=20, iron_plate=8,  logs=6))
    g("hamster", "one_barrel",          dict(steel_plate=25, iron_plate=10, logs=8,  steel_rod=2))
    g("hamster", "coltm1851",           dict(steel_plate=30, iron_plate=12, logs=4,  steel_rod=2,  brass=8))
    g("hamster", "coltm1851_chain",     dict(steel_plate=40, iron_plate=14, logs=4,  steel_rod=3,  brass=10))
    g("hamster", "sharps",              dict(steel_plate=35, iron_plate=14, logs=12, steel_rod=2))
    g("hamster", "martinihenry",        dict(steel_plate=40, iron_plate=16, logs=14, steel_rod=3))
    # Guns — Tier 2: Early cartridge (1865–1885)
    g("hamster", "gras1874",            dict(steel_plate=50, iron_plate=20, logs=16, steel_rod=4))
    g("hamster", "colt1873",            dict(steel_plate=48, iron_comp=6,   logs=6,  steel_rod=3,  brass=12))
    g("hamster", "colt1873_lb",         dict(steel_plate=56, iron_comp=8,   logs=8,  steel_rod=4,  brass=12))
    g("hamster", "win1873",             dict(steel_plate=60, iron_comp=8,   logs=16, steel_rod=4))
    g("hamster", "m1879revolver",       dict(steel_plate=44, iron_comp=6,   logs=5,  steel_rod=3,  brass=10))
    g("hamster", "sw_mk2",              dict(steel_plate=46, iron_comp=7,   logs=5,  steel_rod=3,  brass=10))
    # Guns — Tier 3: Military bolt-action / repeater (1880s–1900s)
    g("hamster", "berthier",            dict(steel_plate=75,  iron_comp=8,  logs=16, steel_rod=4))
    g("hamster", "krag",                dict(steel_plate=80,  iron_comp=8,  logs=14, steel_rod=4))
    g("hamster", "lebel1886",           dict(steel_plate=78,  iron_comp=8,  logs=16, steel_rod=4))
    g("hamster", "lebel1886_07c",       dict(steel_plate=85,  iron_comp=10, logs=16, steel_rod=5))
    g("hamster", "smle_mk3",            dict(steel_plate=90,  iron_comp=10, logs=16, steel_rod=5))
    g("hamster", "gew98",               dict(steel_plate=95,  iron_comp=12, logs=18, steel_rod=5))
    g("hamster", "nagantm1895",         dict(steel_plate=60,  iron_comp=8,  logs=5,  steel_rod=4,  brass=12))
    g("hamster", "nagantcarbine",       dict(steel_plate=72,  iron_comp=10, logs=12, steel_rod=4,  brass=10))
    g("hamster", "coltm1892",          dict(steel_plate=58,  iron_comp=8,  logs=5,  steel_rod=4,  brass=12))
    g("hamster", "coltm1892pair",       dict(steel_plate=116, iron_comp=16, logs=10, steel_rod=8,  brass=24))
    g("hamster", "win1894",             dict(steel_plate=78,  iron_comp=10, logs=16, steel_rod=5))
    g("hamster", "m1887",               dict(steel_plate=80,  iron_comp=10, logs=20, steel_rod=5))
    g("hamster", "m1887_hc",            dict(steel_plate=88,  iron_comp=12, logs=20, steel_rod=5))
    g("hamster", "webley",              dict(steel_plate=64,  iron_comp=9,  logs=5,  steel_rod=4,  brass=14))
    # Guns — Tier 4: WWI era (1900–1918)
    g("hamster", "luger1906",           dict(steel_plate=85,  iron_comp=12, logs=4,  steel_rod=5,  brass=16))
    g("hamster", "lugerp08",            dict(steel_plate=90,  iron_comp=12, logs=4,  steel_rod=5,  brass=16))
    g("hamster", "lugerp08_artillerie", dict(steel_plate=100, iron_comp=14, logs=8,  steel_rod=6,  brass=18))
    g("hamster", "auto5",               dict(steel_plate=110, steel_comp=14, logs=18, steel_rod=6, alum_plate=16))
    g("hamster", "mp18",                dict(steel_plate=130, steel_comp=20, logs=12, steel_rod=8))
    g("hamster", "madsen",              dict(steel_plate=180, steel_comp=32, logs=14, steel_rod=10, alum_plate=24))
    g("hamster", "mg1417",              dict(steel_plate=220, steel_comp=40, logs=14, steel_rod=12, alum_plate=32))
    # Guns — Tier 5: Interwar / WWII (1919–1945)
    g("hamster", "m1903",               dict(steel_plate=110, steel_comp=16, logs=16, steel_rod=6,  alum_plate=20))
    g("hamster", "mosin91",             dict(steel_plate=100, steel_comp=14, logs=16, steel_rod=6))
    g("hamster", "mosin9130",           dict(steel_plate=110, steel_comp=16, logs=16, steel_rod=6))
    g("hamster", "type99",              dict(steel_plate=115, steel_comp=18, logs=16, steel_rod=6,  alum_plate=16))
    g("hamster", "makarov",             dict(steel_plate=80,  steel_comp=10, logs=4,  steel_rod=5,  brass=12))
    g("hamster", "m1garand",            dict(steel_plate=150, steel_comp=24, logs=14, steel_rod=8,  alum_plate=28))
    g("hamster", "sks",                 dict(steel_plate=140, steel_comp=20, logs=12, steel_rod=7,  alum_plate=20))
    g("hamster", "uppercut",            dict(steel_plate=130, steel_comp=18, logs=12, steel_rod=7,  alum_plate=20))

    # Ammo
    a("hamster", "compact_ammo", dict(copper=12, gunpowder=2),                         50)
    a("hamster", "medium_ammo",  dict(copper=16, gunpowder=3),                         48)
    a("hamster", "long_ammo",    dict(copper=22, gunpowder=5, lapis=1),                36)
    a("hamster", "flares_ammo",  dict(copper=8,  gunpowder=2, redstone=4),             6)
    a("hamster", "12g",          dict(copper=14, gunpowder=3, iron_nugget=9),          24)

    # Attachments — bayonets
    t("hamster", "bayonet9805",   dict(steel_plate=32, steel_rod=4))
    t("hamster", "bayonetm1886",  dict(steel_plate=32, steel_rod=4))
    t("hamster", "bayonetp1903",  dict(steel_plate=32, steel_rod=4))
    t("hamster", "bayonettype30", dict(steel_plate=32, steel_rod=4))
    t("hamster", "m9130_bayonet", dict(steel_plate=32, steel_rod=4))
    t("hamster", "sks_bayonet",   dict(steel_plate=28, steel_rod=4))
    # Attachments — optics
    t("hamster", "aperture_sight", dict(steel_plate=12, glass=2))
    t("hamster", "deadeye_scope",  dict(steel_plate=20, glass=6,  steel_comp=4))
    t("hamster", "gew98_scope",    dict(steel_plate=18, glass=6,  iron_comp=4))
    t("hamster", "lebel_scope",    dict(steel_plate=18, glass=6,  iron_comp=4))
    t("hamster", "ppco_scope",     dict(steel_plate=22, glass=8,  steel_comp=4))
    t("hamster", "puscope",        dict(steel_plate=20, glass=6,  steel_comp=4))
    t("hamster", "unertl_scope",   dict(steel_plate=28, glass=10, steel_comp=6))
    # Attachments — magazines
    t("hamster", "drum_mag",      dict(steel_plate=40, steel_rod=8))
    t("hamster", "trench_mag",    dict(steel_plate=32, steel_rod=6))
    t("hamster", "loading_pipe",  dict(steel_rod=6, iron_plate=4))
    # Attachments — accessories
    t("hamster", "rifle_bipod",   dict(steel_rod=8,  iron_plate=6))
    t("hamster", "rifle_grip",    dict(steel_plate=12, logs=4))
    t("hamster", "gas_tube",      dict(steel_rod=4,  iron_plate=4))
    t("hamster", "speedloader",   dict(steel_plate=16, brass=8))
    t("hamster", "whip",          dict(steel_rod=2,  leather=4))

    # -----------------------------------------------------------------------
    # PACK 2 — tacz_default_gun  (tacz)
    # Modern military firearms
    # -----------------------------------------------------------------------

    # Guns — Shotguns
    g("tacz", "db_short",   dict(logs=80,  steel_plate=120, iron_comp=8,  steel_rod=4))
    g("tacz", "db_long",    dict(logs=90,  steel_plate=130, iron_comp=8,  steel_rod=6))
    g("tacz", "m870",       dict(steel_plate=160, iron_comp=24,  steel_rod=6,  alum_plate=32))
    g("tacz", "m1014",      dict(steel_plate=190, steel_comp=32, steel_rod=8,  alum_plate=48))
    g("tacz", "spas_12",    dict(steel_plate=210, steel_comp=36, steel_rod=8,  alum_plate=48, clay=48))
    g("tacz", "aa12",       dict(uranium=1, steel_plate=280, steel_comp=64, steel_rod=12, alum_plate=48, clay=48))
    # Guns — Pistols
    g("tacz", "glock_17",      dict(steel_plate=80,  iron_comp=6,  steel_rod=2,  clay=32))
    g("tacz", "m1911",         dict(steel_plate=90,  iron_comp=8,  steel_rod=3,  brass=16))
    g("tacz", "cz75",          dict(steel_plate=95,  iron_comp=12, steel_comp=8, steel_rod=2))
    g("tacz", "deagle",        dict(steel_plate=130, steel_comp=18, steel_rod=3, alum_plate=24))
    g("tacz", "deagle_golden", dict(steel_plate=130, steel_comp=18, steel_rod=3, gold_plate=120))
    g("tacz", "p320",          dict(uranium=1, steel_plate=100, iron_comp=10, steel_rod=2, clay=48))
    g("tacz", "b93r",          dict(steel_plate=110, steel_comp=14, steel_rod=3, alum_plate=16, brass=16))
    g("tacz", "timeless50",    dict(steel_plate=130, steel_comp=18, steel_rod=4, alum_plate=32, brass=20))
    # Guns — SMGs
    g("tacz", "hk_mp5a5", dict(uranium=1, steel_plate=160, steel_comp=36, steel_rod=4, alum_plate=96, clay=48))
    g("tacz", "ump45",    dict(uranium=1, steel_plate=180, steel_comp=36, steel_rod=4, alum_plate=96, clay=48))
    g("tacz", "uzi",      dict(uranium=1, steel_plate=175, steel_comp=36, steel_rod=3, alum_plate=96))
    g("tacz", "vector45", dict(uranium=1, steel_plate=220, steel_comp=54, steel_rod=4, alum_plate=96, clay=48))
    g("tacz", "p90",      dict(uranium=1, steel_plate=170, steel_comp=33, steel_rod=4, alum_plate=96, clay=48))
    # Guns — Assault Rifles
    g("tacz", "ak47",     dict(logs=48,  steel_plate=256, iron_comp=48, steel_rod=6))
    g("tacz", "rpk",      dict(logs=64,  steel_plate=300, iron_comp=48, steel_rod=12))
    g("tacz", "type_81",  dict(logs=36,  steel_plate=275, iron_comp=42, steel_rod=6))
    g("tacz", "m16a1",    dict(steel_plate=200, steel_comp=48, steel_rod=5, alum_plate=96))
    g("tacz", "m16a4",    dict(steel_plate=210, steel_comp=53, steel_rod=5, alum_plate=96))
    g("tacz", "m4a1",     dict(uranium=1, steel_plate=200, steel_comp=33, steel_rod=5, alum_plate=64))
    g("tacz", "hk416d",   dict(uranium=1, steel_plate=230, steel_comp=60, steel_rod=5, alum_plate=96, iron_plate=36))
    g("tacz", "aug",      dict(steel_plate=220, steel_comp=48, steel_rod=6, alum_plate=48, glass=16, clay=48))
    g("tacz", "hk_g3",    dict(uranium=1, steel_plate=240, iron_comp=18,  steel_rod=3))
    g("tacz", "scar_l",   dict(uranium=1, steel_plate=220, steel_comp=66, steel_rod=5, alum_plate=96))
    g("tacz", "scar_h",   dict(uranium=1, steel_plate=290, steel_comp=66, steel_rod=8, alum_plate=150))
    g("tacz", "g36k",     dict(uranium=1, steel_plate=230, steel_comp=54, steel_rod=5, alum_plate=72, glass=10))
    g("tacz", "fn_fal",   dict(uranium=1, steel_plate=260, steel_comp=60, steel_rod=6, alum_plate=72, iron_plate=24))
    g("tacz", "qbz_95",   dict(uranium=1, steel_plate=210, steel_comp=45, steel_rod=5, alum_plate=72, clay=36))
    g("tacz", "qbz_191",  dict(uranium=1, steel_plate=230, steel_comp=53, steel_rod=6, alum_plate=72))
    # Guns — DMRs / Battle Rifles
    g("tacz", "mk14",        dict(uranium=1, steel_plate=280, steel_comp=38, steel_rod=6, alum_plate=64))
    g("tacz", "sks_tactical",dict(uranium=1, steel_plate=280, iron_comp=18,  steel_rod=8))
    g("tacz", "m320",        dict(steel_plate=150, steel_comp=48, steel_rod=4))
    g("tacz", "spr15hb",     dict(uranium=1, steel_plate=290, steel_comp=45, steel_rod=8, alum_plate=72))
    g("tacz", "fn_evolys",   dict(uranium=1, steel_plate=360, steel_comp=105, steel_rod=18, alum_plate=96, iron_plate=36))
    # Guns — LMGs
    g("tacz", "m249",   dict(uranium=1, steel_plate=440, steel_comp=135, steel_rod=24, alum_plate=96,  iron_plate=36))
    g("tacz", "minigun",dict(uranium=3, steel_plate=700, steel_comp=240, steel_rod=48, alum_plate=192, iron_plate=96))
    # Guns — Bolt-action / Sniper
    g("tacz", "m700",   dict(steel_plate=300, steel_comp=45,  steel_rod=9,  alum_plate=48, anvil=1))
    g("tacz", "ai_awp", dict(steel_plate=400, steel_comp=72,  steel_rod=4,  anvil=1, lever=1))
    g("tacz", "m95",    dict(steel_plate=500, steel_comp=100, steel_rod=24, anvil=5, lever=1))
    g("tacz", "m107",   dict(uranium=1, steel_plate=480, steel_comp=90, steel_rod=20, alum_plate=64, anvil=3))
    # Guns — Launchers / Other
    g("tacz", "rpg7",           dict(logs=96,  steel_plate=350, steel_rod=48))
    g("tacz", "springfield1873",dict(logs=64,  steel_plate=100, iron_comp=12, steel_rod=4))

    # Ammo — Pistol calibers
    a("tacz", "9mm",      dict(copper=12, gunpowder=2),                          50)
    a("tacz", "45acp",    dict(copper=14, gunpowder=3),                          50)
    a("tacz", "357mag",   dict(copper=16, gunpowder=4),                          50)
    a("tacz", "50ae",     dict(copper=30, gunpowder=7, lapis=1),                 30)
    a("tacz", "762x25",   dict(copper=14, gunpowder=3),                          50)
    # Ammo — Intermediate / rifle
    a("tacz", "545x39",   dict(copper=18, gunpowder=5),                          50)
    a("tacz", "556x45",   dict(copper=18, gunpowder=5),                          50)
    a("tacz", "762x39",   dict(copper=20, gunpowder=5),                          50)
    a("tacz", "46x30",    dict(copper=14, gunpowder=3),                          50)
    a("tacz", "57x28",    dict(copper=15, gunpowder=4),                          50)
    a("tacz", "6x35mm",   dict(copper=15, gunpowder=4),                          50)
    # Ammo — Full-power rifle
    a("tacz", "308",      dict(copper=22, gunpowder=6, lapis=1),                 48)
    a("tacz", "30_06",    dict(copper=24, gunpowder=6),                          48)
    a("tacz", "762x54",   dict(copper=20, gunpowder=6),                          48)
    a("tacz", "58x42",    dict(copper=28, gunpowder=8),                          30)
    a("tacz", "68x51fury",dict(copper=24, gunpowder=7),                          40)
    # Ammo — Sniper / heavy
    a("tacz", "338",      dict(copper=26, gunpowder=7, lapis=1),                 36)
    a("tacz", "45_70",    dict(copper=28, gunpowder=8),                          30)
    a("tacz", "50bmg",    dict(copper=50, gunpowder=10, lapis=4, blaze_rod=1),   24)
    # Ammo — Shotgun / Specialty
    a("tacz", "12g",      dict(copper=15, gunpowder=4, iron_nugget=9),           24)
    a("tacz", "40mm",     dict(copper=24, gunpowder=8, iron_plate=4),            4)
    a("tacz", "rpg_rocket",dict(iron_plate=48, gunpowder=16, steel_rod=4),       1)

    # Attachments — Sights (red dots / holos)
    t("tacz", "sight_t1",                dict(steel_plate=6,  glass=4, redstone=4))
    t("tacz", "sight_t2",                dict(steel_plate=6,  glass=4, redstone=4))
    t("tacz", "sight_552",               dict(steel_plate=8,  glass=4, redstone=4))
    t("tacz", "sight_coyote",            dict(steel_plate=8,  glass=4, redstone=4))
    t("tacz", "sight_exp3",              dict(steel_plate=10, glass=6, redstone=4))
    t("tacz", "sight_uh1",               dict(steel_plate=10, glass=6, redstone=4))
    t("tacz", "sight_acro_pistol",       dict(steel_plate=6,  glass=4, redstone=4))
    t("tacz", "sight_acro_rifle",        dict(steel_plate=8,  glass=4, redstone=4))
    t("tacz", "sight_deltapoint_pistol", dict(steel_plate=6,  glass=4, redstone=4))
    t("tacz", "sight_deltapoint_rifle",  dict(steel_plate=8,  glass=4, redstone=4))
    t("tacz", "sight_fastfire_pistol",   dict(steel_plate=6,  glass=4, redstone=4))
    t("tacz", "sight_fastfire_rifle",    dict(steel_plate=8,  glass=4, redstone=4))
    t("tacz", "sight_rmr_dot",           dict(steel_plate=6,  glass=4, redstone=4))
    t("tacz", "sight_sro_dot",           dict(steel_plate=6,  glass=4, redstone=4))
    t("tacz", "sight_srs_02",            dict(steel_plate=8,  glass=6, redstone=4))
    t("tacz", "sight_okp7",              dict(steel_plate=8,  glass=4, redstone=4))
    t("tacz", "sight_pk06_pistol",       dict(steel_plate=6,  glass=4, redstone=4))
    t("tacz", "sight_pk06_rifle",        dict(steel_plate=8,  glass=4, redstone=4))
    # Attachments — Scopes
    t("tacz", "scope_retro_2x",   dict(steel_plate=12, glass=6,  redstone=4))
    t("tacz", "scope_1873_6x",    dict(steel_plate=16, glass=8,  iron_comp=4))
    t("tacz", "scope_hamr",       dict(steel_plate=14, glass=6,  steel_comp=4, redstone=4))
    t("tacz", "scope_acog_ta31",  dict(steel_plate=14, glass=6,  steel_comp=4, redstone=4))
    t("tacz", "scope_elcan_4x",   dict(steel_plate=18, glass=8,  steel_comp=4, redstone=4))
    t("tacz", "scope_lpvo_1_6",   dict(steel_plate=20, glass=8,  steel_comp=6, redstone=4))
    t("tacz", "scope_qmk152",     dict(steel_plate=22, glass=10, steel_comp=6, redstone=4))
    t("tacz", "scope_mk5hd",      dict(steel_plate=24, glass=10, steel_comp=6, redstone=4))
    t("tacz", "scope_standard_8x",dict(steel_plate=22, glass=10, steel_comp=6, redstone=4))
    t("tacz", "scope_contender",  dict(steel_plate=26, glass=12, steel_comp=8, redstone=4))
    t("tacz", "scope_vudu",       dict(steel_plate=26, glass=12, steel_comp=8, redstone=4))
    # Attachments — Grips
    t("tacz", "grip_cobra",             dict(steel_plate=12, logs=4))
    t("tacz", "grip_magpul_afg_2",      dict(steel_plate=14, logs=4, steel_rod=2))
    t("tacz", "grip_osovets_black",     dict(steel_plate=12, logs=4))
    t("tacz", "grip_rk0",               dict(steel_plate=12, logs=4))
    t("tacz", "grip_rk1_b25u",          dict(steel_plate=14, logs=4))
    t("tacz", "grip_rk6",               dict(steel_plate=14, logs=4))
    t("tacz", "grip_se_5",              dict(steel_plate=12, logs=4))
    t("tacz", "grip_td",                dict(steel_plate=12, logs=4, leather=4))
    t("tacz", "grip_vertical_military", dict(steel_plate=14, logs=4, steel_rod=2))
    t("tacz", "grip_vertical_ranger",   dict(steel_plate=14, logs=4, steel_rod=2))
    t("tacz", "grip_vertical_talon",    dict(steel_plate=14, logs=4, steel_rod=2))
    # Attachments — Stocks
    t("tacz", "oem_stock_light",        dict(steel_plate=16, logs=6))
    t("tacz", "oem_stock_heavy",        dict(steel_plate=24, logs=6, steel_rod=2))
    t("tacz", "oem_stock_tactical",     dict(steel_plate=20, clay=16, steel_rod=2))
    t("tacz", "stock_ak12",             dict(steel_plate=20, logs=6,  steel_rod=2))
    t("tacz", "stock_carbon_bone_c5",   dict(steel_plate=24, clay=16, steel_rod=2))
    t("tacz", "stock_heavy_spas_12",    dict(steel_plate=28, logs=6,  steel_rod=4))
    t("tacz", "stock_tactical_spas_12", dict(steel_plate=24, clay=16, steel_rod=4))
    t("tacz", "stock_hk_slim_line",     dict(steel_plate=20, clay=16, steel_rod=2))
    t("tacz", "stock_m4ss",             dict(steel_plate=20, clay=16, steel_rod=2))
    t("tacz", "stock_militech_b5",      dict(steel_plate=22, clay=16, steel_rod=2))
    t("tacz", "stock_moe",              dict(steel_plate=20, logs=6))
    t("tacz", "stock_ripstock",         dict(steel_plate=20, clay=16, steel_rod=2))
    t("tacz", "stock_sba3",             dict(steel_plate=18, clay=12, steel_rod=2))
    t("tacz", "stock_tactical_ar",      dict(steel_plate=22, clay=16, steel_rod=2))
    # Attachments — Extended magazines
    t("tacz", "extended_mag_1",        dict(steel_plate=20, steel_rod=4))
    t("tacz", "extended_mag_2",        dict(steel_plate=32, steel_rod=6))
    t("tacz", "extended_mag_3",        dict(steel_plate=48, steel_rod=8))
    t("tacz", "light_extended_mag_1",  dict(steel_plate=16, steel_rod=4))
    t("tacz", "light_extended_mag_2",  dict(steel_plate=24, steel_rod=6))
    t("tacz", "light_extended_mag_3",  dict(steel_plate=36, steel_rod=8))
    t("tacz", "sniper_extended_mag_1", dict(steel_plate=20, steel_rod=4))
    t("tacz", "sniper_extended_mag_2", dict(steel_plate=32, steel_rod=6))
    t("tacz", "sniper_extended_mag_3", dict(steel_plate=48, steel_rod=8))
    t("tacz", "shotgun_extended_mag_1",dict(steel_plate=20, steel_rod=4))
    t("tacz", "shotgun_extended_mag_2",dict(steel_plate=32, steel_rod=6))
    t("tacz", "shotgun_extended_mag_3",dict(steel_plate=48, steel_rod=8))
    # Attachments — Muzzle devices
    t("tacz", "muzzle_brake_cthulhu",      dict(steel_plate=18, steel_rod=3))
    t("tacz", "muzzle_brake_cyclone_d2",   dict(steel_plate=16, steel_rod=3))
    t("tacz", "muzzle_brake_mastiff_sg",   dict(steel_plate=16, steel_rod=3))
    t("tacz", "muzzle_brake_pioneer",      dict(steel_plate=16, steel_rod=3))
    t("tacz", "muzzle_brake_timeless50",   dict(steel_plate=18, steel_rod=3))
    t("tacz", "muzzle_brake_trex",         dict(steel_plate=16, steel_rod=3))
    t("tacz", "muzzle_choke_sg",           dict(steel_plate=14, steel_rod=2))
    t("tacz", "muzzle_compensator_trident",dict(steel_plate=16, steel_rod=3))
    t("tacz", "muzzle_silencer_knight_qd", dict(steel_plate=40, steel_rod=8, steel_comp=4))
    t("tacz", "muzzle_silencer_mirage",    dict(steel_plate=36, steel_rod=6, steel_comp=4))
    t("tacz", "muzzle_silencer_phantom_s1",dict(steel_plate=40, steel_rod=8, steel_comp=4))
    t("tacz", "muzzle_silencer_ptilopsis", dict(steel_plate=36, steel_rod=6, steel_comp=4))
    t("tacz", "muzzle_silencer_sg",        dict(steel_plate=44, steel_rod=8, steel_comp=4))
    t("tacz", "muzzle_silencer_ursus",     dict(steel_plate=38, steel_rod=7, steel_comp=4))
    t("tacz", "muzzle_silencer_vulture",   dict(steel_plate=40, steel_rod=8, steel_comp=4))
    # Attachments — Lasers
    t("tacz", "laser_compact",   dict(redstone=6, gold_plate=6, glass=2))
    t("tacz", "laser_lopro",     dict(redstone=6, gold_plate=6, glass=2))
    t("tacz", "laser_nightstick",dict(redstone=8, gold_plate=8, glass=4))
    # Attachments — Bayonets
    t("tacz", "bayonet_6h3", dict(steel_plate=32, steel_rod=4))
    t("tacz", "bayonet_m9",  dict(steel_plate=32, steel_rod=4))
    # Attachments — Special barrel
    t("tacz", "deagle_golden_long_barrel", dict(gold_plate=48, steel_plate=24, steel_rod=3))
    # Attachments — Ammo modifications
    t("tacz", "ammo_mod_fmj",  dict(steel_plate=8,  copper=16))
    t("tacz", "ammo_mod_he",   dict(steel_plate=8,  gunpowder=8))
    t("tacz", "ammo_mod_hp",   dict(copper=24,      iron_plate=4))
    t("tacz", "ammo_mod_i",    dict(blaze_rod=4,    steel_plate=8))
    t("tacz", "ammo_mod_slug", dict(iron_plate=8,   steel_plate=8))

    # -----------------------------------------------------------------------
    # PACK 3 — Suffuse GunSmoke  (suffuse)
    # Contemporary / cutting-edge
    # -----------------------------------------------------------------------

    # Guns — Pistols
    g("suffuse", "tt33",        dict(steel_plate=60,  iron_comp=10, steel_rod=3, brass=12))
    g("suffuse", "m1895",       dict(steel_plate=70,  iron_comp=12, steel_rod=3, brass=14, logs=8))
    g("suffuse", "lifecard",    dict(steel_plate=45,  iron_comp=8,  steel_rod=2, brass=8))
    g("suffuse", "tec9",        dict(steel_plate=80,  iron_comp=14, steel_rod=3, alum_plate=16))
    g("suffuse", "python",      dict(steel_plate=90,  steel_comp=14, steel_rod=4, brass=20))
    g("suffuse", "viper2011",   dict(steel_plate=100, steel_comp=16, steel_rod=4, brass=18))
    g("suffuse", "tti2011",     dict(steel_plate=110, steel_comp=18, steel_rod=4, brass=22, alum_plate=16))
    g("suffuse", "usp45",       dict(steel_plate=105, steel_comp=16, steel_rod=4, alum_plate=18, clay=24))
    g("suffuse", "usp45_black", dict(steel_plate=105, steel_comp=16, steel_rod=4, alum_plate=18, clay=24))
    g("suffuse", "webley1913",  dict(steel_plate=95,  steel_comp=14, steel_rod=4, brass=20, logs=6))
    # Guns — SMGs
    g("suffuse", "ump45",    dict(uranium=1, steel_plate=195, steel_comp=39, steel_rod=5, alum_plate=96, clay=48))
    g("suffuse", "pp19",     dict(steel_plate=170, steel_comp=30, steel_rod=6, alum_plate=48, clay=24))
    g("suffuse", "mas38",    dict(steel_plate=150, steel_comp=27, steel_rod=6, andesite=32, logs=16))
    g("suffuse", "mpdr",     dict(steel_plate=180, steel_comp=33, steel_rod=6, alum_plate=48, brass=18))
    g("suffuse", "kacpdw",   dict(uranium=1, steel_plate=210, steel_comp=42, steel_rod=6, alum_plate=72, clay=36))
    g("suffuse", "gepardpdw",dict(uranium=1, steel_plate=195, steel_comp=36, steel_rod=6, alum_plate=72))
    g("suffuse", "n4",       dict(steel_plate=145, steel_comp=27, steel_rod=6, alum_plate=36, brass=18))
    # Guns — Shotguns / Launchers
    g("suffuse", "trapper50cal", dict(steel_plate=50,  iron_plate=8,  logs=14, steel_rod=6))
    g("suffuse", "spas12",       dict(steel_plate=240, steel_comp=45, steel_rod=10, alum_plate=48, clay=48))
    g("suffuse", "ks23m",        dict(steel_plate=260, steel_comp=48, steel_rod=12, alum_plate=72, clay=48))
    g("suffuse", "m79",          dict(steel_plate=180, steel_comp=36, steel_rod=8,  brass=24))
    # Guns — Assault Rifles
    g("suffuse", "an94",      dict(uranium=1, steel_plate=245, steel_comp=57, steel_rod=6, alum_plate=72))
    g("suffuse", "qbz951",    dict(uranium=1, steel_plate=220, steel_comp=48, steel_rod=6, alum_plate=72, clay=30))
    g("suffuse", "qbz951s",   dict(uranium=1, steel_plate=230, steel_comp=51, steel_rod=6, alum_plate=72, clay=30))
    g("suffuse", "qbz191",    dict(uranium=1, steel_plate=240, steel_comp=54, steel_rod=6, alum_plate=96))
    g("suffuse", "qbz192",    dict(uranium=1, steel_plate=225, steel_comp=48, steel_rod=6, alum_plate=72))
    g("suffuse", "qbu191",    dict(uranium=1, steel_plate=260, steel_comp=60, steel_rod=8, alum_plate=96))
    g("suffuse", "xm7",       dict(uranium=1, steel_plate=275, steel_comp=63, steel_rod=8, alum_plate=96))
    g("suffuse", "ar57",      dict(uranium=1, steel_plate=215, steel_comp=45, steel_rod=6, alum_plate=72))
    g("suffuse", "rm277",     dict(uranium=1, steel_plate=290, steel_comp=66, steel_rod=8, alum_plate=96))
    g("suffuse", "saddam_golden_ak", dict(gold_plate=180, steel_plate=270, iron_comp=48, steel_rod=6, logs=36))
    g("suffuse", "aks74u",    dict(steel_plate=190, steel_comp=33, steel_rod=6, alum_plate=36, andesite=32))
    # Guns — Battle Rifles / DMRs
    g("suffuse", "ash12", dict(uranium=1, steel_plate=300, steel_comp=66, steel_rod=9,  alum_plate=72, iron_plate=24))
    g("suffuse", "svd",   dict(steel_plate=300, steel_comp=57, steel_rod=10, alum_plate=48, logs=12, anvil=1))
    g("suffuse", "dvl10", dict(uranium=1, steel_plate=340, steel_comp=66, steel_rod=12, alum_plate=72, anvil=2))
    g("suffuse", "np762", dict(uranium=1, steel_plate=330, steel_comp=63, steel_rod=12, alum_plate=48, anvil=2))
    g("suffuse", "m203",  dict(steel_plate=195, steel_comp=42, steel_rod=8, alum_plate=36))
    # Guns — LMGs
    g("suffuse", "pkp",  dict(uranium=1, steel_plate=410, steel_comp=120, steel_rod=21, alum_plate=96,  iron_plate=48))
    g("suffuse", "qlu11",dict(uranium=1, steel_plate=385, steel_comp=105, steel_rod=18, alum_plate=72,  iron_plate=36))
    # Guns — Snipers / Anti-Material
    g("suffuse", "m200", dict(uranium=1,  steel_plate=450, steel_comp=108, steel_rod=18, alum_plate=96,  anvil=3))
    g("suffuse", "aw50", dict(uranium=2,  steel_plate=520, steel_comp=135, steel_rod=21, alum_plate=120, anvil=3))
    g("suffuse", "gm6",  dict(uranium=2,  steel_plate=600, steel_comp=165, steel_rod=24, alum_plate=150, anvil=5))
    g("suffuse", "axmc", dict(uranium=2,  steel_plate=560, steel_comp=143, steel_rod=21, alum_plate=120, anvil=4))
    g("suffuse", "axsr", dict(uranium=2,  steel_plate=580, steel_comp=150, steel_rod=22, alum_plate=120, anvil=4))
    # Guns — Special / Heavy
    g("suffuse", "aiyasinrpg", dict(steel_plate=420, steel_comp=90,  steel_rod=30, iron_plate=48))
    g("suffuse", "pf98a",      dict(uranium=1, steel_plate=450, steel_comp=98,  steel_rod=36, iron_plate=72))
    g("suffuse", "ags30",      dict(uranium=1, steel_plate=500, steel_comp=135, steel_rod=30, alum_plate=96, iron_plate=72))

    # Ammo
    a("suffuse", "7.65x20mm",    dict(copper=10, gunpowder=2),                            60)
    a("suffuse", "6x35mm",       dict(copper=15, gunpowder=4),                            50)
    a("suffuse", "35x32mm",      dict(copper=30, gunpowder=6),                            20)
    a("suffuse", "545x39",       dict(copper=18, gunpowder=5),                            50)
    a("suffuse", "6.8tvcm",      dict(copper=22, gunpowder=6),                            40)
    a("suffuse", "12.7x55",      dict(copper=40, gunpowder=8, lapis=1),                   20)
    a("suffuse", "23mm",         dict(copper=48, gunpowder=10, iron_plate=4),             12)
    a("suffuse", "120mm",        dict(iron_plate=64, gunpowder=16, steel_plate=16),        1)
    a("suffuse", "boomstickshot",dict(paper=3, gunpowder=9, flint=9),                      6)
    a("suffuse", ".22lr",        dict(copper=6,  gunpowder=3),                            64)
    a("suffuse", ".22wmr",       dict(copper=8,  gunpowder=4),                            60)
    a("suffuse", ".408ct",       dict(copper=80, gunpowder=14, lapis=2),                  30)
    a("suffuse", ".600ne",       dict(copper=96, gunpowder=18, lapis=4, blaze_rod=1),     12)

    # Attachments — Grips
    t("suffuse", "grip_td",             dict(steel_plate=12, logs=4, leather=4))
    t("suffuse", "grip_td_black",       dict(steel_plate=12, logs=4, leather=4))
    t("suffuse", "grip_td_blue_grey",   dict(steel_plate=12, logs=4, leather=4))
    t("suffuse", "grip_td_green",       dict(steel_plate=12, logs=4, leather=4))
    t("suffuse", "grip_flashlight",     dict(steel_plate=14, logs=4, redstone=4, glass=2))
    t("suffuse", "grip_m203",           dict(steel_plate=120, steel_comp=20, steel_rod=6))
    # Attachments — Stocks
    t("suffuse", "stock_n4",              dict(steel_plate=18, clay=12, steel_rod=2))
    t("suffuse", "stock_bcm_mod2_sopmod", dict(steel_plate=22, clay=16, steel_rod=2))
    t("suffuse", "stock_colt",            dict(steel_plate=18, logs=6))
    t("suffuse", "stock_colt_plus",       dict(steel_plate=20, logs=6,  steel_rod=2))
    t("suffuse", "stock_elf_ultralight",  dict(steel_plate=16, clay=12, steel_rod=2))
    t("suffuse", "stock_sig_black",       dict(steel_plate=22, clay=16, steel_rod=2))
    t("suffuse", "stock_sig_blue_grey",   dict(steel_plate=22, clay=16, steel_rod=2))
    t("suffuse", "stock_sig_desert",      dict(steel_plate=22, clay=16, steel_rod=2))
    t("suffuse", "stock_vltor_emod_black", dict(steel_plate=24, clay=16, steel_rod=2))
    t("suffuse", "stock_vltor_emod_desert",dict(steel_plate=24, clay=16, steel_rod=2))
    t("suffuse", "stock_vltor_emod_green", dict(steel_plate=24, clay=16, steel_rod=2))
    # Attachments — Lasers
    t("suffuse", "laser_an_peq_2a", dict(redstone=8, gold_plate=8, glass=4))
    t("suffuse", "laser_dbala2",    dict(redstone=8, gold_plate=8, glass=4))
    t("suffuse", "laser_pistol",    dict(redstone=6, gold_plate=6, glass=2))
    t("suffuse", "pistollaser",     dict(redstone=6, gold_plate=6, glass=2))
    # Attachments — Sights / Scopes
    t("suffuse", "sight_cobra_ekp_818",       dict(steel_plate=8,  glass=4, redstone=4))
    t("suffuse", "sight_dbala2",              dict(steel_plate=8,  glass=4, redstone=4))
    t("suffuse", "scope_compm4",              dict(steel_plate=10, glass=6, redstone=4))
    t("suffuse", "scope_ks23m",               dict(steel_plate=14, glass=6, steel_comp=4))
    t("suffuse", "scope_qlu11s",              dict(steel_plate=20, glass=8, steel_comp=6, redstone=4))
    t("suffuse", "scope_sig_tango_msr_1_6",   dict(steel_plate=22, glass=10, steel_comp=6, redstone=4))
    # Attachments — Silencers
    t("suffuse", "m7_silencer",   dict(steel_plate=36, steel_rod=6, steel_comp=4))
    t("suffuse", "rm277_silencer",dict(steel_plate=40, steel_rod=8, steel_comp=4))

    return rows

# ---------------------------------------------------------------------------
# --export-csv mode
# ---------------------------------------------------------------------------

def export_csv():
    rows = _bootstrap_data()
    fieldnames = ["pack", "type", "id", "yield"] + MATERIAL_COLS + ["notes"]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        current_pack = None
        for (pack, rec_type, item_id, yield_count, mats_dict) in rows:
            if pack != current_pack:
                # Section header row — pack starts with #, rest blank
                writer.writerow({"pack": f"# --- {pack.upper()} ---"})
                current_pack = pack
            row = {"pack": pack, "type": rec_type, "id": item_id, "yield": yield_count or ""}
            for col in MATERIAL_COLS:
                row[col] = mats_dict.get(col, "")
            row["notes"] = ""
            writer.writerow(row)
    print(f"Exported {len(rows)} recipes to {CSV_PATH}")
    print("Open in Excel/LibreOffice Calc and edit freely. Blank cells = 0 (ingredient not used).")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if EXPORT_CSV:
    export_csv()
else:
    run_from_csv()
