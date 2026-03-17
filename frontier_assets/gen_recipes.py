"""
Generates TACZ gun/ammo/attachment crafting recipes for all gunpacks.

Usage:
    python frontier_assets/gen_recipes.py               # write balanced recipes
    python frontier_assets/gen_recipes.py --uncraftable # every recipe costs 1 bedrock

Run from repo root.

Key format note:
    IE items MUST use {"item": "immersiveengineering:..."} not {"tag": "..."}.
    Forge-standard tags (forge:ingots/copper, minecraft:logs, etc.) work fine as tags.
"""

import argparse
import json
import os

# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--uncraftable", action="store_true",
                    help="Set every recipe to require 1 bedrock (disables all crafting)")
args = parser.parse_args()

UNCRAFTABLE = args.uncraftable

# ---------------------------------------------------------------------------
# Material constructors
# ---------------------------------------------------------------------------

def by_item(item_id, count=1):
    """Specific item by registry ID. Required for IE/Create items."""
    return {"item": {"item": item_id}, "count": count}

def by_tag(tag_name, count=1):
    """Items matching a forge/vanilla tag. Works for forge-standard tags."""
    return {"item": {"tag": tag_name}, "count": count}

# Uncraftable sentinel
def BEDROCK(n=1): return by_item("minecraft:bedrock", n)

# ------ IE items (must use by_item) ------
def STEEL_PLATE(n):   return by_item("immersiveengineering:plate_steel", n)
def IRON_PLATE(n):    return by_item("immersiveengineering:plate_iron", n)
def ALUM_PLATE(n):    return by_item("immersiveengineering:plate_aluminum", n)
def GOLD_PLATE(n):    return by_item("immersiveengineering:plate_gold", n)
def STEEL_ROD(n):     return by_item("immersiveengineering:stick_steel", n)
def IRON_COMP(n):     return by_item("immersiveengineering:component_iron", n)
def STEEL_COMP(n):    return by_item("immersiveengineering:component_steel", n)

# ------ Create items (must use by_item) ------
def ANDESITE(n):      return by_item("create:andesite_alloy", n)   # early structural metal
def BRASS(n):         return by_item("create:brass_ingot", n)      # precision parts, revolvers

# ------ Forge/vanilla tags (by_tag works fine) ------
def URANIUM(n=1):     return by_tag("forge:ingots/uranium", n)     # IE uranium — end-game gate
def LOGS(n):          return by_tag("minecraft:logs", n)           # wood stocks
def CLAY(n):          return by_tag("minecraft:clay", n)           # polymer frame stand-in
def GLASS(n):         return by_tag("forge:glass", n)              # optics
def COPPER(n):        return by_tag("forge:ingots/copper", n)      # ammo casings
def IRON_NUGGET(n):   return by_tag("forge:nuggets/iron", n)       # bullet material
def GUNPOWDER(n):     return by_tag("forge:gunpowder", n)          # propellant
def BLAZE_ROD(n):     return by_tag("forge:rods/blaze", n)         # incendiary / exotic rounds
def LAPIS(n):         return by_tag("forge:gems/lapis", n)         # propellant additive
def REDSTONE(n):      return by_tag("forge:dusts/redstone", n)     # electronics
def LEATHER(n):       return by_tag("forge:leather", n)            # grips
def ANVIL(n=1):       return by_tag("minecraft:anvil", n)          # heavy machining
def LEVER(n=1):       return by_item("minecraft:lever", n)         # trigger mechanism
def PAPER(n):         return by_item("minecraft:paper", n)         # paper cartridge
def FLINT(n):         return by_item("minecraft:flint", n)         # flintlock / wadding

# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _write(filepath, result, materials):
    mats = [BEDROCK()] if UNCRAFTABLE else materials
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    recipe = {
        "materials": mats,
        "result": result,
        "type": "tacz:gun_smith_table_crafting"
    }
    with open(filepath, "w") as f:
        json.dump(recipe, f, indent=2)

def write_gun(base_dir, namespace, gun_id, materials):
    path = os.path.join(base_dir, "gun", f"{gun_id}.json")
    _write(path, {"type": "gun", "id": f"{namespace}:{gun_id}"}, materials)

def write_ammo(base_dir, namespace, ammo_id, materials, yield_count):
    path = os.path.join(base_dir, "ammo", f"{ammo_id}.json")
    _write(path, {"type": "ammo", "id": f"{namespace}:{ammo_id}", "count": yield_count}, materials)

def write_attachment(base_dir, namespace, attach_id, materials):
    path = os.path.join(base_dir, "attachments", f"{attach_id}.json")
    _write(path, {"type": "attachment", "id": f"{namespace}:{attach_id}"}, materials)


# ===========================================================================
# PACK 1 — GunpowderRevolution  (hamster namespace)
# Historical firearms 1840s–1945. Cheapest guns — the entry point.
# Progression: primitive → early cartridge → bolt-action → WWI → WWII
# ===========================================================================

HAMSTER = "tacz/GunpowderRevolution_gunpack v1/data/hamster/recipes"

print("=== GunpowderRevolution (hamster) ===")

# --- Guns ---

hamster_guns = {
    # Tier 1: Muzzle-loader / Percussion cap (1840s–1860s)
    # Simplest guns. Steel + iron plates + wood. No components yet.
    "flaregun":               [STEEL_PLATE(20), IRON_PLATE(8),  LOGS(6)],
    "one_barrel":             [STEEL_PLATE(25), IRON_PLATE(10), LOGS(8),  STEEL_ROD(2)],
    "coltm1851":              [STEEL_PLATE(30), IRON_PLATE(12), LOGS(4),  STEEL_ROD(2),  BRASS(8)],
    "coltm1851_chain":        [STEEL_PLATE(40), IRON_PLATE(14), LOGS(4),  STEEL_ROD(3),  BRASS(10)],
    "sharps":                 [STEEL_PLATE(35), IRON_PLATE(14), LOGS(12), STEEL_ROD(2)],
    "martinihenry":           [STEEL_PLATE(40), IRON_PLATE(16), LOGS(14), STEEL_ROD(3)],

    # Tier 2: Early cartridge (1865–1885)
    "gras1874":               [STEEL_PLATE(50), IRON_PLATE(20), LOGS(16), STEEL_ROD(4)],
    "colt1873":               [STEEL_PLATE(48), IRON_COMP(6),   LOGS(6),  STEEL_ROD(3),  BRASS(12)],
    "colt1873_lb":            [STEEL_PLATE(56), IRON_COMP(8),   LOGS(8),  STEEL_ROD(4),  BRASS(12)],
    "win1873":                [STEEL_PLATE(60), IRON_COMP(8),   LOGS(16), STEEL_ROD(4)],
    "m1879revolver":          [STEEL_PLATE(44), IRON_COMP(6),   LOGS(5),  STEEL_ROD(3),  BRASS(10)],
    "sw_mk2":                 [STEEL_PLATE(46), IRON_COMP(7),   LOGS(5),  STEEL_ROD(3),  BRASS(10)],

    # Tier 3: Military bolt-action / repeater (1880s–1900s)
    # Steel components appear — more complex mechanisms.
    "berthier":               [STEEL_PLATE(75),  IRON_COMP(8),  LOGS(16), STEEL_ROD(4)],
    "krag":                   [STEEL_PLATE(80),  IRON_COMP(8),  LOGS(14), STEEL_ROD(4)],
    "lebel1886":              [STEEL_PLATE(78),  IRON_COMP(8),  LOGS(16), STEEL_ROD(4)],
    "lebel1886_07c":          [STEEL_PLATE(85),  IRON_COMP(10), LOGS(16), STEEL_ROD(5)],
    "smle_mk3":               [STEEL_PLATE(90),  IRON_COMP(10), LOGS(16), STEEL_ROD(5)],
    "gew98":                  [STEEL_PLATE(95),  IRON_COMP(12), LOGS(18), STEEL_ROD(5)],
    "nagantm1895":            [STEEL_PLATE(60),  IRON_COMP(8),  LOGS(5),  STEEL_ROD(4),  BRASS(12)],
    "nagantcarbine":          [STEEL_PLATE(72),  IRON_COMP(10), LOGS(12), STEEL_ROD(4),  BRASS(10)],
    "coltm1892":              [STEEL_PLATE(58),  IRON_COMP(8),  LOGS(5),  STEEL_ROD(4),  BRASS(12)],
    "coltm1892pair":          [STEEL_PLATE(116), IRON_COMP(16), LOGS(10), STEEL_ROD(8),  BRASS(24)],
    "win1894":                [STEEL_PLATE(78),  IRON_COMP(10), LOGS(16), STEEL_ROD(5)],
    "m1887":                  [STEEL_PLATE(80),  IRON_COMP(10), LOGS(20), STEEL_ROD(5)],
    "m1887_hc":               [STEEL_PLATE(88),  IRON_COMP(12), LOGS(20), STEEL_ROD(5)],
    "webley":                 [STEEL_PLATE(64),  IRON_COMP(9),  LOGS(5),  STEEL_ROD(4),  BRASS(14)],

    # Tier 4: WWI era (1900–1918)
    # Steel components required. Aluminum plates for semi/full-auto.
    "luger1906":              [STEEL_PLATE(85),  IRON_COMP(12), LOGS(4),  STEEL_ROD(5),  BRASS(16)],
    "lugerp08":               [STEEL_PLATE(90),  IRON_COMP(12), LOGS(4),  STEEL_ROD(5),  BRASS(16)],
    "lugerp08_artillerie":    [STEEL_PLATE(100), IRON_COMP(14), LOGS(8),  STEEL_ROD(6),  BRASS(18)],
    "auto5":                  [STEEL_PLATE(110), STEEL_COMP(14),LOGS(18), STEEL_ROD(6),  ALUM_PLATE(16)],
    "mp18":                   [STEEL_PLATE(130), STEEL_COMP(20),LOGS(12), STEEL_ROD(8)],
    "madsen":                 [STEEL_PLATE(180), STEEL_COMP(32),LOGS(14), STEEL_ROD(10), ALUM_PLATE(24)],
    "mg1417":                 [STEEL_PLATE(220), STEEL_COMP(40),LOGS(14), STEEL_ROD(12), ALUM_PLATE(32)],

    # Tier 5: Interwar / WWII (1919–1945)
    # Semi-auto service rifles. Aluminum everywhere.
    "m1903":                  [STEEL_PLATE(110), STEEL_COMP(16), LOGS(16), STEEL_ROD(6),  ALUM_PLATE(20)],
    "mosin91":                [STEEL_PLATE(100), STEEL_COMP(14), LOGS(16), STEEL_ROD(6)],
    "mosin9130":              [STEEL_PLATE(110), STEEL_COMP(16), LOGS(16), STEEL_ROD(6)],
    "type99":                 [STEEL_PLATE(115), STEEL_COMP(18), LOGS(16), STEEL_ROD(6),  ALUM_PLATE(16)],
    "makarov":                [STEEL_PLATE(80),  STEEL_COMP(10), LOGS(4),  STEEL_ROD(5),  BRASS(12)],
    "m1garand":               [STEEL_PLATE(150), STEEL_COMP(24), LOGS(14), STEEL_ROD(8),  ALUM_PLATE(28)],
    "sks":                    [STEEL_PLATE(140), STEEL_COMP(20), LOGS(12), STEEL_ROD(7),  ALUM_PLATE(20)],
    "uppercut":               [STEEL_PLATE(130), STEEL_COMP(18), LOGS(12), STEEL_ROD(7),  ALUM_PLATE(20)],
}

for gid, mats in hamster_guns.items():
    write_gun(HAMSTER, "hamster", gid, mats)

# --- Ammo ---
# compact = pistol/revolver, medium = rifle, long = large rifle
hamster_ammo = {
    "compact_ammo": ([COPPER(12), GUNPOWDER(2)],                         50),
    "medium_ammo":  ([COPPER(16), GUNPOWDER(3)],                         48),
    "long_ammo":    ([COPPER(22), GUNPOWDER(5), LAPIS(1)],               36),
    "flares_ammo":  ([COPPER(8),  GUNPOWDER(2), REDSTONE(4)],            6),
    "12g":          ([COPPER(14), GUNPOWDER(3), IRON_NUGGET(9)],         24),
}

for aid, (mats, count) in hamster_ammo.items():
    write_ammo(HAMSTER, "hamster", aid, mats, count)

# --- Attachments ---
hamster_attachments = {
    # Bayonets
    "bayonet9805":     [STEEL_PLATE(32), STEEL_ROD(4)],
    "bayonetm1886":    [STEEL_PLATE(32), STEEL_ROD(4)],
    "bayonetp1903":    [STEEL_PLATE(32), STEEL_ROD(4)],
    "bayonettype30":   [STEEL_PLATE(32), STEEL_ROD(4)],
    "m9130_bayonet":   [STEEL_PLATE(32), STEEL_ROD(4)],
    "sks_bayonet":     [STEEL_PLATE(28), STEEL_ROD(4)],
    # Scopes / sights
    "aperture_sight":  [STEEL_PLATE(12), GLASS(2)],
    "deadeye_scope":   [STEEL_PLATE(20), GLASS(6),  STEEL_COMP(4)],
    "gew98_scope":     [STEEL_PLATE(18), GLASS(6),  IRON_COMP(4)],
    "lebel_scope":     [STEEL_PLATE(18), GLASS(6),  IRON_COMP(4)],
    "ppco_scope":      [STEEL_PLATE(22), GLASS(8),  STEEL_COMP(4)],
    "puscope":         [STEEL_PLATE(20), GLASS(6),  STEEL_COMP(4)],
    "unertl_scope":    [STEEL_PLATE(28), GLASS(10), STEEL_COMP(6)],
    # Magazines
    "drum_mag":        [STEEL_PLATE(40), STEEL_ROD(8)],
    "trench_mag":      [STEEL_PLATE(32), STEEL_ROD(6)],
    "loading_pipe":    [STEEL_ROD(6),    IRON_PLATE(4)],
    # Accessories
    "rifle_bipod":     [STEEL_ROD(8),    IRON_PLATE(6)],
    "rifle_grip":      [STEEL_PLATE(12), LOGS(4)],
    "gas_tube":        [STEEL_ROD(4),    IRON_PLATE(4)],
    "speedloader":     [STEEL_PLATE(16), BRASS(8)],
    "whip":            [STEEL_ROD(2),    LEATHER(4)],
}

for aid, mats in hamster_attachments.items():
    write_attachment(HAMSTER, "hamster", aid, mats)


# ===========================================================================
# PACK 2 — tacz_default_gun  (tacz namespace)
# Modern military firearms. Significantly more expensive than historicals.
# Uranium gates the most capable weapons.
# ===========================================================================

TACZ = "tacz/tacz_default_gun/data/tacz/recipes"

print("=== tacz_default_gun (tacz) ===")

# --- Guns ---
tacz_guns = {
    # Shotguns
    "db_short":         [LOGS(80),  STEEL_PLATE(120), IRON_COMP(8),  STEEL_ROD(4)],
    "db_long":          [LOGS(90),  STEEL_PLATE(130), IRON_COMP(8),  STEEL_ROD(6)],
    "m870":             [STEEL_PLATE(160), IRON_COMP(24),  STEEL_ROD(6),  ALUM_PLATE(32)],
    "m1014":            [STEEL_PLATE(190), STEEL_COMP(32), STEEL_ROD(8),  ALUM_PLATE(48)],
    "spas_12":          [STEEL_PLATE(210), STEEL_COMP(36), STEEL_ROD(8),  ALUM_PLATE(48), CLAY(48)],
    "aa12":             [URANIUM(),  STEEL_PLATE(280), STEEL_COMP(64), STEEL_ROD(12), ALUM_PLATE(48), CLAY(48)],
    # Pistols
    "glock_17":         [STEEL_PLATE(80),  IRON_COMP(6),  STEEL_ROD(2),  CLAY(32)],
    "m1911":            [STEEL_PLATE(90),  IRON_COMP(8),  STEEL_ROD(3),  BRASS(16)],
    "cz75":             [STEEL_PLATE(95),  IRON_COMP(12), STEEL_COMP(8), STEEL_ROD(2)],
    "deagle":           [STEEL_PLATE(130), STEEL_COMP(18),STEEL_ROD(3),  ALUM_PLATE(24)],
    "deagle_golden":    [STEEL_PLATE(130), STEEL_COMP(18),STEEL_ROD(3),  GOLD_PLATE(120)],
    "p320":             [URANIUM(),  STEEL_PLATE(100), IRON_COMP(10), STEEL_ROD(2),  CLAY(48)],
    "b93r":             [STEEL_PLATE(110), STEEL_COMP(14),STEEL_ROD(3),  ALUM_PLATE(16), BRASS(16)],
    "timeless50":       [STEEL_PLATE(130), STEEL_COMP(18),STEEL_ROD(4),  ALUM_PLATE(32), BRASS(20)],
    # SMGs
    "hk_mp5a5":         [URANIUM(), STEEL_PLATE(160), STEEL_COMP(36), STEEL_ROD(4), ALUM_PLATE(96), CLAY(48)],
    "ump45":            [URANIUM(), STEEL_PLATE(180), STEEL_COMP(36), STEEL_ROD(4), ALUM_PLATE(96), CLAY(48)],
    "uzi":              [URANIUM(), STEEL_PLATE(175), STEEL_COMP(36), STEEL_ROD(3), ALUM_PLATE(96)],
    "vector45":         [URANIUM(), STEEL_PLATE(220), STEEL_COMP(54), STEEL_ROD(4), ALUM_PLATE(96), CLAY(48)],
    "p90":              [URANIUM(), STEEL_PLATE(170), STEEL_COMP(33), STEEL_ROD(4), ALUM_PLATE(96), CLAY(48)],
    # Assault Rifles
    "ak47":             [LOGS(48),  STEEL_PLATE(256), IRON_COMP(48), STEEL_ROD(6)],
    "rpk":              [LOGS(64),  STEEL_PLATE(300), IRON_COMP(48), STEEL_ROD(12)],
    "type_81":          [LOGS(36),  STEEL_PLATE(275), IRON_COMP(42), STEEL_ROD(6)],
    "m16a1":            [STEEL_PLATE(200), STEEL_COMP(48), STEEL_ROD(5), ALUM_PLATE(96)],
    "m16a4":            [STEEL_PLATE(210), STEEL_COMP(53), STEEL_ROD(5), ALUM_PLATE(96)],
    "m4a1":             [URANIUM(), STEEL_PLATE(200), STEEL_COMP(33), STEEL_ROD(5), ALUM_PLATE(64)],
    "hk416d":           [URANIUM(), STEEL_PLATE(230), STEEL_COMP(60), STEEL_ROD(5), ALUM_PLATE(96), IRON_PLATE(36)],
    "aug":              [STEEL_PLATE(220), STEEL_COMP(48), STEEL_ROD(6), ALUM_PLATE(48), GLASS(16), CLAY(48)],
    "hk_g3":            [URANIUM(), STEEL_PLATE(240), IRON_COMP(18),  STEEL_ROD(3)],
    "scar_l":           [URANIUM(), STEEL_PLATE(220), STEEL_COMP(66), STEEL_ROD(5), ALUM_PLATE(96)],
    "scar_h":           [URANIUM(), STEEL_PLATE(290), STEEL_COMP(66), STEEL_ROD(8), ALUM_PLATE(150)],
    "g36k":             [URANIUM(), STEEL_PLATE(230), STEEL_COMP(54), STEEL_ROD(5), ALUM_PLATE(72), GLASS(10)],
    "fn_fal":           [URANIUM(), STEEL_PLATE(260), STEEL_COMP(60), STEEL_ROD(6), ALUM_PLATE(72), IRON_PLATE(24)],
    "qbz_95":           [URANIUM(), STEEL_PLATE(210), STEEL_COMP(45), STEEL_ROD(5), ALUM_PLATE(72), CLAY(36)],
    "qbz_191":          [URANIUM(), STEEL_PLATE(230), STEEL_COMP(53), STEEL_ROD(6), ALUM_PLATE(72)],
    # DMRs / Battle Rifles
    "mk14":             [URANIUM(), STEEL_PLATE(280), STEEL_COMP(38), STEEL_ROD(6), ALUM_PLATE(64)],
    "sks_tactical":     [URANIUM(), STEEL_PLATE(280), IRON_COMP(18),  STEEL_ROD(8)],
    "m320":             [STEEL_PLATE(150), STEEL_COMP(48), STEEL_ROD(4)],
    "spr15hb":          [URANIUM(), STEEL_PLATE(290), STEEL_COMP(45), STEEL_ROD(8), ALUM_PLATE(72)],
    "fn_evolys":        [URANIUM(), STEEL_PLATE(360), STEEL_COMP(105),STEEL_ROD(18), ALUM_PLATE(96), IRON_PLATE(36)],
    # LMGs
    "m249":             [URANIUM(),   STEEL_PLATE(440), STEEL_COMP(135), STEEL_ROD(24), ALUM_PLATE(96), IRON_PLATE(36)],
    "minigun":          [URANIUM(3),  STEEL_PLATE(700), STEEL_COMP(240), STEEL_ROD(48), ALUM_PLATE(192), IRON_PLATE(96)],
    # Bolt-action / Sniper
    "m700":             [STEEL_PLATE(300), STEEL_COMP(45), STEEL_ROD(9),  ALUM_PLATE(48), ANVIL()],
    "ai_awp":           [STEEL_PLATE(400), STEEL_COMP(72), STEEL_ROD(4),  ANVIL(),   LEVER()],
    "m95":              [STEEL_PLATE(500), STEEL_COMP(100),STEEL_ROD(24), ANVIL(5),  LEVER()],
    "m107":             [URANIUM(), STEEL_PLATE(480), STEEL_COMP(90), STEEL_ROD(20), ALUM_PLATE(64), ANVIL(3)],
    # Launchers / Other
    "rpg7":             [LOGS(96), STEEL_PLATE(350), STEEL_ROD(48)],
    "springfield1873":  [LOGS(64), STEEL_PLATE(100), IRON_COMP(12), STEEL_ROD(4)],
}

for gid, mats in tacz_guns.items():
    write_gun(TACZ, "tacz", gid, mats)

# --- Ammo ---
# Caliber-appropriate cost: bigger/rarer rounds cost more copper + powder, yield less
tacz_ammo = {
    # Pistol calibers
    "9mm":       ([COPPER(12), GUNPOWDER(2)],                           50),
    "45acp":     ([COPPER(14), GUNPOWDER(3)],                           50),
    "357mag":    ([COPPER(16), GUNPOWDER(4)],                           50),
    "50ae":      ([COPPER(30), GUNPOWDER(7), LAPIS(1)],                 30),
    "762x25":    ([COPPER(14), GUNPOWDER(3)],                           50),
    # Intermediate / rifle
    "545x39":    ([COPPER(18), GUNPOWDER(5)],                           50),
    "556x45":    ([COPPER(18), GUNPOWDER(5)],                           50),
    "762x39":    ([COPPER(20), GUNPOWDER(5)],                           50),
    "46x30":     ([COPPER(14), GUNPOWDER(3)],                           50),
    "57x28":     ([COPPER(15), GUNPOWDER(4)],                           50),
    "6x35mm":    ([COPPER(15), GUNPOWDER(4)],                           50),
    # Full-power rifle
    "308":       ([COPPER(22), GUNPOWDER(6), LAPIS(1)],                 48),
    "30_06":     ([COPPER(24), GUNPOWDER(6)],                           48),
    "762x54":    ([COPPER(20), GUNPOWDER(6)],                           48),
    "58x42":     ([COPPER(28), GUNPOWDER(8)],                           30),
    "68x51fury": ([COPPER(24), GUNPOWDER(7)],                           40),
    # Sniper / heavy
    "338":       ([COPPER(26), GUNPOWDER(7), LAPIS(1)],                 36),
    "45_70":     ([COPPER(28), GUNPOWDER(8)],                           30),
    "50bmg":     ([COPPER(50), GUNPOWDER(10), LAPIS(4), BLAZE_ROD(1)], 24),
    # Shotgun
    "12g":       ([COPPER(15), GUNPOWDER(4), IRON_NUGGET(9)],           24),
    # Specialty
    "40mm":      ([COPPER(24), GUNPOWDER(8), IRON_PLATE(4)],            4),
    "rpg_rocket":([IRON_PLATE(48), GUNPOWDER(16), STEEL_ROD(4)],        1),
}

for aid, (mats, count) in tacz_ammo.items():
    write_ammo(TACZ, "tacz", aid, mats, count)

# --- Attachments ---

# Helper groups for attachments that share the same recipe
def red_dot_small():  return [STEEL_PLATE(6),  GLASS(4), REDSTONE(4)]
def red_dot_medium(): return [STEEL_PLATE(8),  GLASS(4), REDSTONE(4)]
def red_dot_large():  return [STEEL_PLATE(10), GLASS(6), REDSTONE(4)]
def scope_low():      return [STEEL_PLATE(12), GLASS(6), REDSTONE(4)]
def scope_mid():      return [STEEL_PLATE(18), GLASS(8), STEEL_COMP(4), REDSTONE(4)]
def scope_high():     return [STEEL_PLATE(24), GLASS(10), STEEL_COMP(6), REDSTONE(4)]
def grip_simple():    return [STEEL_PLATE(12), LOGS(4)]
def grip_tactical():  return [STEEL_PLATE(16), LOGS(4), STEEL_ROD(2)]
def stock_light():    return [STEEL_PLATE(16), LOGS(6)]
def stock_heavy():    return [STEEL_PLATE(24), LOGS(6), STEEL_ROD(2)]
def stock_polymer():  return [STEEL_PLATE(20), CLAY(16), STEEL_ROD(2)]
def mag_small():      return [STEEL_PLATE(20), STEEL_ROD(4)]
def mag_medium():     return [STEEL_PLATE(32), STEEL_ROD(6)]
def mag_large():      return [STEEL_PLATE(48), STEEL_ROD(8)]
def silencer():       return [STEEL_PLATE(36), STEEL_ROD(6), STEEL_COMP(4)]
def muzzle_brake():   return [STEEL_PLATE(16), STEEL_ROD(3)]
def laser_small():    return [REDSTONE(6), GOLD_PLATE(6), GLASS(2)]
def laser_large():    return [REDSTONE(8), GOLD_PLATE(8), GLASS(4)]

tacz_attachments = {
    # Sights — red dots / holos
    "sight_t1":                [STEEL_PLATE(6),  GLASS(4), REDSTONE(4)],
    "sight_t2":                [STEEL_PLATE(6),  GLASS(4), REDSTONE(4)],
    "sight_552":               [STEEL_PLATE(8),  GLASS(4), REDSTONE(4)],
    "sight_coyote":            [STEEL_PLATE(8),  GLASS(4), REDSTONE(4)],
    "sight_exp3":              [STEEL_PLATE(10), GLASS(6), REDSTONE(4)],
    "sight_uh1":               [STEEL_PLATE(10), GLASS(6), REDSTONE(4)],
    "sight_acro_pistol":       [STEEL_PLATE(6),  GLASS(4), REDSTONE(4)],
    "sight_acro_rifle":        [STEEL_PLATE(8),  GLASS(4), REDSTONE(4)],
    "sight_deltapoint_pistol": [STEEL_PLATE(6),  GLASS(4), REDSTONE(4)],
    "sight_deltapoint_rifle":  [STEEL_PLATE(8),  GLASS(4), REDSTONE(4)],
    "sight_fastfire_pistol":   [STEEL_PLATE(6),  GLASS(4), REDSTONE(4)],
    "sight_fastfire_rifle":    [STEEL_PLATE(8),  GLASS(4), REDSTONE(4)],
    "sight_rmr_dot":           [STEEL_PLATE(6),  GLASS(4), REDSTONE(4)],
    "sight_sro_dot":           [STEEL_PLATE(6),  GLASS(4), REDSTONE(4)],
    "sight_srs_02":            [STEEL_PLATE(8),  GLASS(6), REDSTONE(4)],
    "sight_okp7":              [STEEL_PLATE(8),  GLASS(4), REDSTONE(4)],
    "sight_pk06_pistol":       [STEEL_PLATE(6),  GLASS(4), REDSTONE(4)],
    "sight_pk06_rifle":        [STEEL_PLATE(8),  GLASS(4), REDSTONE(4)],
    # Scopes
    "scope_retro_2x":          [STEEL_PLATE(12), GLASS(6),  REDSTONE(4)],
    "scope_1873_6x":           [STEEL_PLATE(16), GLASS(8),  IRON_COMP(4)],
    "scope_hamr":              [STEEL_PLATE(14), GLASS(6),  STEEL_COMP(4), REDSTONE(4)],
    "scope_acog_ta31":         [STEEL_PLATE(14), GLASS(6),  STEEL_COMP(4), REDSTONE(4)],
    "scope_elcan_4x":          [STEEL_PLATE(18), GLASS(8),  STEEL_COMP(4), REDSTONE(4)],
    "scope_lpvo_1_6":          [STEEL_PLATE(20), GLASS(8),  STEEL_COMP(6), REDSTONE(4)],
    "scope_qmk152":            [STEEL_PLATE(22), GLASS(10), STEEL_COMP(6), REDSTONE(4)],
    "scope_mk5hd":             [STEEL_PLATE(24), GLASS(10), STEEL_COMP(6), REDSTONE(4)],
    "scope_standard_8x":       [STEEL_PLATE(22), GLASS(10), STEEL_COMP(6), REDSTONE(4)],
    "scope_contender":         [STEEL_PLATE(26), GLASS(12), STEEL_COMP(8), REDSTONE(4)],
    "scope_vudu":              [STEEL_PLATE(26), GLASS(12), STEEL_COMP(8), REDSTONE(4)],
    # Grips
    "grip_cobra":              [STEEL_PLATE(12), LOGS(4)],
    "grip_magpul_afg_2":       [STEEL_PLATE(14), LOGS(4), STEEL_ROD(2)],
    "grip_osovets_black":      [STEEL_PLATE(12), LOGS(4)],
    "grip_rk0":                [STEEL_PLATE(12), LOGS(4)],
    "grip_rk1_b25u":           [STEEL_PLATE(14), LOGS(4)],
    "grip_rk6":                [STEEL_PLATE(14), LOGS(4)],
    "grip_se_5":               [STEEL_PLATE(12), LOGS(4)],
    "grip_td":                 [STEEL_PLATE(12), LOGS(4), LEATHER(4)],
    "grip_vertical_military":  [STEEL_PLATE(14), LOGS(4), STEEL_ROD(2)],
    "grip_vertical_ranger":    [STEEL_PLATE(14), LOGS(4), STEEL_ROD(2)],
    "grip_vertical_talon":     [STEEL_PLATE(14), LOGS(4), STEEL_ROD(2)],
    # Stocks
    "oem_stock_light":         [STEEL_PLATE(16), LOGS(6)],
    "oem_stock_heavy":         [STEEL_PLATE(24), LOGS(6), STEEL_ROD(2)],
    "oem_stock_tactical":      [STEEL_PLATE(20), CLAY(16), STEEL_ROD(2)],
    "stock_ak12":              [STEEL_PLATE(20), LOGS(6), STEEL_ROD(2)],
    "stock_carbon_bone_c5":    [STEEL_PLATE(24), CLAY(16), STEEL_ROD(2)],
    "stock_heavy_spas_12":     [STEEL_PLATE(28), LOGS(6), STEEL_ROD(4)],
    "stock_tactical_spas_12":  [STEEL_PLATE(24), CLAY(16), STEEL_ROD(4)],
    "stock_hk_slim_line":      [STEEL_PLATE(20), CLAY(16), STEEL_ROD(2)],
    "stock_m4ss":              [STEEL_PLATE(20), CLAY(16), STEEL_ROD(2)],
    "stock_militech_b5":       [STEEL_PLATE(22), CLAY(16), STEEL_ROD(2)],
    "stock_moe":               [STEEL_PLATE(20), LOGS(6)],
    "stock_ripstock":          [STEEL_PLATE(20), CLAY(16), STEEL_ROD(2)],
    "stock_sba3":              [STEEL_PLATE(18), CLAY(12), STEEL_ROD(2)],
    "stock_tactical_ar":       [STEEL_PLATE(22), CLAY(16), STEEL_ROD(2)],
    # Extended magazines
    "extended_mag_1":          [STEEL_PLATE(20), STEEL_ROD(4)],
    "extended_mag_2":          [STEEL_PLATE(32), STEEL_ROD(6)],
    "extended_mag_3":          [STEEL_PLATE(48), STEEL_ROD(8)],
    "light_extended_mag_1":    [STEEL_PLATE(16), STEEL_ROD(4)],
    "light_extended_mag_2":    [STEEL_PLATE(24), STEEL_ROD(6)],
    "light_extended_mag_3":    [STEEL_PLATE(36), STEEL_ROD(8)],
    "sniper_extended_mag_1":   [STEEL_PLATE(20), STEEL_ROD(4)],
    "sniper_extended_mag_2":   [STEEL_PLATE(32), STEEL_ROD(6)],
    "sniper_extended_mag_3":   [STEEL_PLATE(48), STEEL_ROD(8)],
    "shotgun_extended_mag_1":  [STEEL_PLATE(20), STEEL_ROD(4)],
    "shotgun_extended_mag_2":  [STEEL_PLATE(32), STEEL_ROD(6)],
    "shotgun_extended_mag_3":  [STEEL_PLATE(48), STEEL_ROD(8)],
    # Muzzle devices
    "muzzle_brake_cthulhu":    [STEEL_PLATE(18), STEEL_ROD(3)],
    "muzzle_brake_cyclone_d2": [STEEL_PLATE(16), STEEL_ROD(3)],
    "muzzle_brake_mastiff_sg": [STEEL_PLATE(16), STEEL_ROD(3)],
    "muzzle_brake_pioneer":    [STEEL_PLATE(16), STEEL_ROD(3)],
    "muzzle_brake_timeless50": [STEEL_PLATE(18), STEEL_ROD(3)],
    "muzzle_brake_trex":       [STEEL_PLATE(16), STEEL_ROD(3)],
    "muzzle_choke_sg":         [STEEL_PLATE(14), STEEL_ROD(2)],
    "muzzle_compensator_trident": [STEEL_PLATE(16), STEEL_ROD(3)],
    "muzzle_silencer_knight_qd":  [STEEL_PLATE(40), STEEL_ROD(8), STEEL_COMP(4)],
    "muzzle_silencer_mirage":     [STEEL_PLATE(36), STEEL_ROD(6), STEEL_COMP(4)],
    "muzzle_silencer_phantom_s1": [STEEL_PLATE(40), STEEL_ROD(8), STEEL_COMP(4)],
    "muzzle_silencer_ptilopsis":  [STEEL_PLATE(36), STEEL_ROD(6), STEEL_COMP(4)],
    "muzzle_silencer_sg":         [STEEL_PLATE(44), STEEL_ROD(8), STEEL_COMP(4)],
    "muzzle_silencer_ursus":      [STEEL_PLATE(38), STEEL_ROD(7), STEEL_COMP(4)],
    "muzzle_silencer_vulture":    [STEEL_PLATE(40), STEEL_ROD(8), STEEL_COMP(4)],
    # Lasers
    "laser_compact":   [REDSTONE(6), GOLD_PLATE(6),  GLASS(2)],
    "laser_lopro":     [REDSTONE(6), GOLD_PLATE(6),  GLASS(2)],
    "laser_nightstick":[REDSTONE(8), GOLD_PLATE(8),  GLASS(4)],
    # Bayonets
    "bayonet_6h3":     [STEEL_PLATE(32), STEEL_ROD(4)],
    "bayonet_m9":      [STEEL_PLATE(32), STEEL_ROD(4)],
    # Special barrel
    "deagle_golden_long_barrel": [GOLD_PLATE(48), STEEL_PLATE(24), STEEL_ROD(3)],
    # Ammo modifications
    "ammo_mod_fmj":    [STEEL_PLATE(8),  COPPER(16)],
    "ammo_mod_he":     [STEEL_PLATE(8),  GUNPOWDER(8)],
    "ammo_mod_hp":     [COPPER(24),      IRON_PLATE(4)],
    "ammo_mod_i":      [BLAZE_ROD(4),    STEEL_PLATE(8)],
    "ammo_mod_slug":   [IRON_PLATE(8),   STEEL_PLATE(8)],
}

for aid, mats in tacz_attachments.items():
    write_attachment(TACZ, "tacz", aid, mats)


# ===========================================================================
# PACK 3 — Suffuse GunSmoke  (suffuse namespace)
# Contemporary / cutting-edge. Matches or exceeds tacz_default_gun cost.
# ===========================================================================

SUFFUSE = "tacz/Suffuse-GunSmoke-Pack1/data/suffuse/recipes"

print("=== Suffuse GunSmoke (suffuse) ===")

# --- Guns ---
suffuse_guns = {
    # Pistols
    "tt33":             [STEEL_PLATE(60),  IRON_COMP(10), STEEL_ROD(3),  BRASS(12)],
    "m1895":            [STEEL_PLATE(70),  IRON_COMP(12), STEEL_ROD(3),  BRASS(14), LOGS(8)],
    "lifecard":         [STEEL_PLATE(45),  IRON_COMP(8),  STEEL_ROD(2),  BRASS(8)],
    "tec9":             [STEEL_PLATE(80),  IRON_COMP(14), STEEL_ROD(3),  ALUM_PLATE(16)],
    "python":           [STEEL_PLATE(90),  STEEL_COMP(14),STEEL_ROD(4),  BRASS(20)],
    "viper2011":        [STEEL_PLATE(100), STEEL_COMP(16),STEEL_ROD(4),  BRASS(18)],
    "tti2011":          [STEEL_PLATE(110), STEEL_COMP(18),STEEL_ROD(4),  BRASS(22), ALUM_PLATE(16)],
    "usp45":            [STEEL_PLATE(105), STEEL_COMP(16),STEEL_ROD(4),  ALUM_PLATE(18), CLAY(24)],
    "usp45_black":      [STEEL_PLATE(105), STEEL_COMP(16),STEEL_ROD(4),  ALUM_PLATE(18), CLAY(24)],
    "webley1913":       [STEEL_PLATE(95),  STEEL_COMP(14),STEEL_ROD(4),  BRASS(20), LOGS(6)],
    # SMGs
    "ump45":            [URANIUM(), STEEL_PLATE(195), STEEL_COMP(39), STEEL_ROD(5), ALUM_PLATE(96), CLAY(48)],
    "pp19":             [STEEL_PLATE(170), STEEL_COMP(30), STEEL_ROD(6), ALUM_PLATE(48), CLAY(24)],
    "mas38":            [STEEL_PLATE(150), STEEL_COMP(27), STEEL_ROD(6), ANDESITE(32), LOGS(16)],
    "mpdr":             [STEEL_PLATE(180), STEEL_COMP(33), STEEL_ROD(6), ALUM_PLATE(48), BRASS(18)],
    "kacpdw":           [URANIUM(), STEEL_PLATE(210), STEEL_COMP(42), STEEL_ROD(6), ALUM_PLATE(72), CLAY(36)],
    "gepardpdw":        [URANIUM(), STEEL_PLATE(195), STEEL_COMP(36), STEEL_ROD(6), ALUM_PLATE(72)],
    "n4":               [STEEL_PLATE(145), STEEL_COMP(27), STEEL_ROD(6), ALUM_PLATE(36), BRASS(18)],
    # Shotguns / Launchers
    "trapper50cal":     [STEEL_PLATE(50),  IRON_PLATE(8),  LOGS(14), STEEL_ROD(6)],
    "spas12":           [STEEL_PLATE(240), STEEL_COMP(45), STEEL_ROD(10), ALUM_PLATE(48), CLAY(48)],
    "ks23m":            [STEEL_PLATE(260), STEEL_COMP(48), STEEL_ROD(12), ALUM_PLATE(72), CLAY(48)],
    "m79":              [STEEL_PLATE(180), STEEL_COMP(36), STEEL_ROD(8),  BRASS(24)],
    # Assault Rifles
    "an94":             [URANIUM(), STEEL_PLATE(245), STEEL_COMP(57), STEEL_ROD(6),  ALUM_PLATE(72)],
    "qbz951":           [URANIUM(), STEEL_PLATE(220), STEEL_COMP(48), STEEL_ROD(6),  ALUM_PLATE(72), CLAY(30)],
    "qbz951s":          [URANIUM(), STEEL_PLATE(230), STEEL_COMP(51), STEEL_ROD(6),  ALUM_PLATE(72), CLAY(30)],
    "qbz191":           [URANIUM(), STEEL_PLATE(240), STEEL_COMP(54), STEEL_ROD(6),  ALUM_PLATE(96)],
    "qbz192":           [URANIUM(), STEEL_PLATE(225), STEEL_COMP(48), STEEL_ROD(6),  ALUM_PLATE(72)],
    "qbu191":           [URANIUM(), STEEL_PLATE(260), STEEL_COMP(60), STEEL_ROD(8),  ALUM_PLATE(96)],
    "xm7":              [URANIUM(), STEEL_PLATE(275), STEEL_COMP(63), STEEL_ROD(8),  ALUM_PLATE(96)],
    "ar57":             [URANIUM(), STEEL_PLATE(215), STEEL_COMP(45), STEEL_ROD(6),  ALUM_PLATE(72)],
    "rm277":            [URANIUM(), STEEL_PLATE(290), STEEL_COMP(66), STEEL_ROD(8),  ALUM_PLATE(96)],
    "saddam_golden_ak": [GOLD_PLATE(180), STEEL_PLATE(270), IRON_COMP(48), STEEL_ROD(6), LOGS(36)],
    "aks74u":           [STEEL_PLATE(190), STEEL_COMP(33), STEEL_ROD(6),  ALUM_PLATE(36), ANDESITE(32)],
    # Battle Rifles / DMRs
    "ash12":            [URANIUM(), STEEL_PLATE(300), STEEL_COMP(66), STEEL_ROD(9),  ALUM_PLATE(72), IRON_PLATE(24)],
    "svd":              [STEEL_PLATE(300), STEEL_COMP(57), STEEL_ROD(10), ALUM_PLATE(48), LOGS(12), ANVIL()],
    "dvl10":            [URANIUM(), STEEL_PLATE(340), STEEL_COMP(66), STEEL_ROD(12), ALUM_PLATE(72), ANVIL(2)],
    "np762":            [URANIUM(), STEEL_PLATE(330), STEEL_COMP(63), STEEL_ROD(12), ALUM_PLATE(48), ANVIL(2)],
    "m203":             [STEEL_PLATE(195), STEEL_COMP(42), STEEL_ROD(8),  ALUM_PLATE(36)],
    # LMGs
    "pkp":              [URANIUM(), STEEL_PLATE(410), STEEL_COMP(120), STEEL_ROD(21), ALUM_PLATE(96), IRON_PLATE(48)],
    "qlu11":            [URANIUM(), STEEL_PLATE(385), STEEL_COMP(105), STEEL_ROD(18), ALUM_PLATE(72), IRON_PLATE(36)],
    # Snipers / Anti-Material
    "m200":             [URANIUM(),   STEEL_PLATE(450), STEEL_COMP(108), STEEL_ROD(18), ALUM_PLATE(96), ANVIL(3)],
    "aw50":             [URANIUM(2),  STEEL_PLATE(520), STEEL_COMP(135), STEEL_ROD(21), ALUM_PLATE(120), ANVIL(3)],
    "gm6":              [URANIUM(2),  STEEL_PLATE(600), STEEL_COMP(165), STEEL_ROD(24), ALUM_PLATE(150), ANVIL(5)],
    "axmc":             [URANIUM(2),  STEEL_PLATE(560), STEEL_COMP(143), STEEL_ROD(21), ALUM_PLATE(120), ANVIL(4)],
    "axsr":             [URANIUM(2),  STEEL_PLATE(580), STEEL_COMP(150), STEEL_ROD(22), ALUM_PLATE(120), ANVIL(4)],
    # Special / Heavy
    "aiyasinrpg":       [STEEL_PLATE(420), STEEL_COMP(90),  STEEL_ROD(30), IRON_PLATE(48)],
    "pf98a":            [URANIUM(), STEEL_PLATE(450), STEEL_COMP(98),  STEEL_ROD(36), IRON_PLATE(72)],
    "ags30":            [URANIUM(), STEEL_PLATE(500), STEEL_COMP(135), STEEL_ROD(30), ALUM_PLATE(96), IRON_PLATE(72)],
}

for gid, mats in suffuse_guns.items():
    write_gun(SUFFUSE, "suffuse", gid, mats)

# --- Ammo ---
suffuse_ammo = {
    "7.65x20mm":  ([COPPER(10), GUNPOWDER(2)],                           60),  # MAS38 pistol round
    "6x35mm":     ([COPPER(15), GUNPOWDER(4)],                           50),
    "35x32mm":    ([COPPER(30), GUNPOWDER(6)],                           20),
    "545x39":     ([COPPER(18), GUNPOWDER(5)],                           50),
    "6.8tvcm":    ([COPPER(22), GUNPOWDER(6)],                           40),
    "12.7x55":    ([COPPER(40), GUNPOWDER(8), LAPIS(1)],                 20),  # Russian antimat
    "23mm":       ([COPPER(48), GUNPOWDER(10), IRON_PLATE(4)],           12),
    "120mm":      ([IRON_PLATE(64), GUNPOWDER(16), STEEL_PLATE(16)],     1),   # tank round
    "boomstickshot": ([PAPER(3), GUNPOWDER(9), FLINT(9)],               6),   # keep original feel
}

for aid, (mats, count) in suffuse_ammo.items():
    write_ammo(SUFFUSE, "suffuse", aid, mats, count)

# --- Attachments ---
suffuse_attachments = {
    # Grips
    "grip_td":              [STEEL_PLATE(12), LOGS(4), LEATHER(4)],
    "grip_td_black":        [STEEL_PLATE(12), LOGS(4), LEATHER(4)],
    "grip_td_blue_grey":    [STEEL_PLATE(12), LOGS(4), LEATHER(4)],
    "grip_td_green":        [STEEL_PLATE(12), LOGS(4), LEATHER(4)],
    "grip_flashlight":      [STEEL_PLATE(14), LOGS(4), REDSTONE(4), GLASS(2)],
    "grip_m203":            [STEEL_PLATE(120), STEEL_COMP(20), STEEL_ROD(6)],  # underbarrel GL
    # Stocks
    "stock_n4":             [STEEL_PLATE(18), CLAY(12), STEEL_ROD(2)],
    "stock_bcm_mod2_sopmod":[STEEL_PLATE(22), CLAY(16), STEEL_ROD(2)],
    "stock_colt":           [STEEL_PLATE(18), LOGS(6)],
    "stock_colt_plus":      [STEEL_PLATE(20), LOGS(6),  STEEL_ROD(2)],
    "stock_elf_ultralight": [STEEL_PLATE(16), CLAY(12), STEEL_ROD(2)],
    "stock_sig_black":      [STEEL_PLATE(22), CLAY(16), STEEL_ROD(2)],
    "stock_sig_blue_grey":  [STEEL_PLATE(22), CLAY(16), STEEL_ROD(2)],
    "stock_sig_desert":     [STEEL_PLATE(22), CLAY(16), STEEL_ROD(2)],
    "stock_vltor_emod_black":  [STEEL_PLATE(24), CLAY(16), STEEL_ROD(2)],
    "stock_vltor_emod_desert": [STEEL_PLATE(24), CLAY(16), STEEL_ROD(2)],
    "stock_vltor_emod_green":  [STEEL_PLATE(24), CLAY(16), STEEL_ROD(2)],
    # Lasers
    "laser_an_peq_2a":      [REDSTONE(8), GOLD_PLATE(8), GLASS(4)],
    "laser_dbala2":         [REDSTONE(8), GOLD_PLATE(8), GLASS(4)],
    "laser_pistol":         [REDSTONE(6), GOLD_PLATE(6), GLASS(2)],
    "pistollaser":          [REDSTONE(6), GOLD_PLATE(6), GLASS(2)],
    # Sights / Scopes
    "sight_cobra_ekp_818":  [STEEL_PLATE(8),  GLASS(4), REDSTONE(4)],
    "sight_dbala2":         [STEEL_PLATE(8),  GLASS(4), REDSTONE(4)],
    "scope_compm4":         [STEEL_PLATE(10), GLASS(6), REDSTONE(4)],
    "scope_ks23m":          [STEEL_PLATE(14), GLASS(6), STEEL_COMP(4)],
    "scope_qlu11s":         [STEEL_PLATE(20), GLASS(8), STEEL_COMP(6), REDSTONE(4)],
    "scope_sig_tango_msr_1_6": [STEEL_PLATE(22), GLASS(10), STEEL_COMP(6), REDSTONE(4)],
    # Silencers
    "m7_silencer":          [STEEL_PLATE(36), STEEL_ROD(6), STEEL_COMP(4)],
    "rm277_silencer":       [STEEL_PLATE(40), STEEL_ROD(8), STEEL_COMP(4)],
}

for aid, mats in suffuse_attachments.items():
    write_attachment(SUFFUSE, "suffuse", aid, mats)


print(f"\nDone. {'(UNCRAFTABLE MODE)' if UNCRAFTABLE else ''}")
