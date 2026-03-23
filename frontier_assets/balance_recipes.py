"""
Recipe balancer for TACZ gunpacks.

Reads gun stats from _data.json files, computes power scores,
applies material profiles from balance.csv, and updates recipes.csv.

Pipeline:
    1. balance_recipes.py --scan       # discover guns, create/update balance.csv
    2. (edit balance.csv in spreadsheet — assign profiles, tweak mult/offset/extras)
    3. balance_recipes.py              # compute recipes and update recipes.csv
    4. gen_recipes.py                  # write JSON recipe files from recipes.csv

Other modes:
    balance_recipes.py --scores        # print ranked power scores for all guns
    balance_recipes.py --preview       # show full breakdown without writing

Run from repo root.

Power score heuristic:
    Uses geometric mean of sustained DPS and per-shot alpha damage,
    modified by auto-fire capability and magazine capacity.
    Shotgun pellets use sqrt(bullet_amount) to model spread.
    Launcher explosions use damage * (1 + radius * 0.5).

Expensive score:
    expensive = mult * power_score + offset
    (mult defaults to 1.0, offset to 0 — per-gun tuning knobs in balance.csv)

Total budget:
    budget = GLOBAL_SCALE * expensive ^ GLOBAL_EXPONENT
    Distributed across profile materials by weight. Extras added on top.
"""

import argparse
import csv
import glob
import json
import math
import os
import re

from recipe_common import MATERIAL_COLS, RECIPES_FIELDS, PACK_DATA_DIRS

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BALANCE_CSV = os.path.join(SCRIPT_DIR, "balance.csv")
RECIPES_CSV = os.path.join(SCRIPT_DIR, "recipes.csv")

# ---------------------------------------------------------------------------
# Global tuning knobs
# Adjust these to shift the overall economy up/down or compress the range.
# ---------------------------------------------------------------------------

GLOBAL_SCALE    = 66.0    # Multiplier on budget (higher = everything costs more)
GLOBAL_EXPONENT = 0.51    # Range compression (< 1 compresses the cheap/expensive gap)
GLOBAL_OFFSET   = 2       # Added to every expensive_score before budget computation

# ---------------------------------------------------------------------------
# Power score tuning knobs
# ---------------------------------------------------------------------------

DPS_WEIGHT      = 0.7     # How much sustained DPS matters (vs alpha)
ALPHA_WEIGHT    = 0.3     # How much one-shot damage matters (vs DPS)
SEMI_RPM_CAP    = 360     # Max effective RPM for semi-auto (~6 clicks/sec)
MAG_REFERENCE   = 30      # Magazine size that gives factor = 1.0
MAG_WEIGHT      = 0.35    # Exponent on magazine factor (lower = gentler curve)
PELLET_EXP      = 0.3     # Exponent on bullet_amount for shotguns (lower = less credit)
ARMOR_WEIGHT    = 0.3     # How much armor_ignore contributes (situational advantage)
HS_WEIGHT       = 0.3     # How much headshot multiplier contributes (situational)
PIERCE_BONUS    = 0.2     # Per pierce level, applied via log2 (sublinear)

# ---------------------------------------------------------------------------
# Pack configuration — default profile per pack
# Data directories come from recipe_common.PACK_DATA_DIRS.
# ---------------------------------------------------------------------------

PACK_DEFAULTS = {
    "hamster": "old_wood",
    "tacz":    "modern_steel",
    "suffuse": "modern_steel",
}

# ---------------------------------------------------------------------------
# Material profiles
# Keys are material column names from recipe_common.
# Weights MUST sum to 1.0. Validated at startup.
# ---------------------------------------------------------------------------

# Profile multipliers and exponents — applied to the budget before distributing materials.
# adjusted = mult * budget ^ exponent
# Use mult to shift eras cheaper/more expensive, exponent to control how steeply cost scales.
PROFILE_MULT = {
    "old_wood":       0.52,
    "old_brass":      0.62,
    "mid_wood":       1.0,
    "mid_steel":      1.0,
    "modern_steel":   1.5,
    "modern_polymer": 1.72,
    "heavy_steel":    1.5,
    "launcher":       1.5,
}
PROFILE_EXPONENT = {
    "old_wood":       1.0,
    "old_brass":      1.0,
    "mid_wood":       1.0,
    "mid_steel":      1.0,
    "modern_steel":   0.99,
    "modern_polymer": 0.98,
    "heavy_steel":    1.0,
    "launcher":       1.0,
}

# Profile material distributions — weights MUST sum to 1.0. Validated at startup.
PROFILES = {
    # Historical (pre-WWI, WWI, WWII)
    "old_wood":       {"steel_plate": 0.50, "iron_plate": 0.15, "logs": 0.25, "steel_rod": 0.10},
    "old_brass":      {"steel_plate": 0.35, "iron_plate": 0.10, "logs": 0.15, "steel_rod": 0.10,
                       "brass": 0.20, "iron_comp": 0.10},
    # Mid era (Cold War, early modern)
    "mid_wood":       {"steel_plate": 0.40, "iron_comp": 0.15, "logs": 0.20, "steel_rod": 0.10,
                       "alum_plate": 0.15},
    "mid_steel":      {"steel_plate": 0.40, "steel_comp": 0.20, "steel_rod": 0.10,
                       "alum_plate": 0.15, "iron_comp": 0.15},
    # Modern
    "modern_steel":   {"steel_plate": 0.35, "steel_comp": 0.25, "steel_rod": 0.10,
                       "alum_plate": 0.20, "iron_plate": 0.08, "pmech": 0.02},
    "modern_polymer": {"steel_plate": 0.24, "steel_comp": 0.20, "steel_rod": 0.10,
                       "alum_plate": 0.15, "plastic": 0.28, "pmech": 0.03},
    # Special
    "heavy_steel":    {"steel_plate": 0.35, "steel_comp": 0.20, "steel_rod": 0.10,
                       "alum_plate": 0.15, "iron_plate": 0.20},
    "launcher":       {"steel_plate": 0.30, "steel_rod": 0.25, "iron_plate": 0.25,
                       "steel_comp": 0.20},
}

BALANCE_FIELDS = [
    "pack", "type", "id", "profile", "mult", "offset", "extras",
    "power_score", "notes",
]

## RECIPES_FIELDS imported from recipe_common

# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------

def _validate_profiles():
    for name, weights in PROFILES.items():
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            print(f"ERROR: profile '{name}' weights sum to {total}, expected 1.0")
            raise SystemExit(1)
        for mat in weights:
            if mat not in MATERIAL_COLS:
                print(f"ERROR: profile '{name}' uses unknown material '{mat}'")
                raise SystemExit(1)

_validate_profiles()

# ---------------------------------------------------------------------------
# Power scoring heuristic
# ---------------------------------------------------------------------------

def compute_power_score(data):
    """Compute a composite power score from gun _data.json fields.

    Weighted geometric mean of DPS and per-shot alpha, so damage and fire rate
    contribute independently (no double-counting). Semi-auto RPM is capped to
    model human click speed. Magazine factor uses a gentle log curve.
    """
    bullet = data.get("bullet", {})
    damage = bullet.get("damage", 1)
    bullet_amount = bullet.get("bullet_amount", 1)
    pierce = bullet.get("pierce", 1)

    extra = bullet.get("extra_damage", {})
    armor_ignore = extra.get("armor_ignore", 0)
    headshot = extra.get("head_shot_multiplier", 1.5)

    # Handle explosions (launchers, grenade launchers)
    explosion = bullet.get("explosion", {})
    if explosion.get("explode"):
        expl_damage = explosion.get("damage", 0)
        expl_radius = explosion.get("radius", 0)
        expl_value = expl_damage * (1 + expl_radius * 0.5)
        damage = max(damage, expl_value)
        bullet_amount = 1  # don't double-count pellets for launchers

    rpm   = data.get("rpm", 60)
    ammo  = data.get("ammo_amount", 100)  # default 100 for inventory-based (minigun)
    modes = data.get("fire_mode", ["semi"])

    # Shotgun pellets: bullet_amount^PELLET_EXP (less generous than sqrt)
    pellet_factor = bullet_amount ** PELLET_EXP if bullet_amount > 1 else 1.0

    # Per-shot effective damage
    # Armor ignore and headshot are situational — diminished contribution
    base_damage = damage * pellet_factor
    armor_bonus = 1 + ARMOR_WEIGHT * armor_ignore
    hs_bonus = 1 + HS_WEIGHT * max(0, headshot / 1.5 - 1)
    shot_damage = base_damage * armor_bonus * hs_bonus

    # Effective RPM: semi-auto capped by human click speed, auto uses full RPM
    effective_rpm = rpm if "auto" in modes else min(rpm, SEMI_RPM_CAP)

    # DPS — damage and fire rate contribute equally here
    dps = shot_damage * effective_rpm / 60.0

    # Alpha — per-shot lethality, pierce bonus grows sublinearly
    pierce_factor = 1 + PIERCE_BONUS * math.log2(max(pierce, 1))
    alpha = shot_damage * pierce_factor

    # Weighted geometric mean — DPS and alpha as independent axes
    # (avoids double-counting damage, unlike sqrt(dps * alpha))
    combined = (max(dps, 0.01) ** DPS_WEIGHT) * (max(alpha, 0.01) ** ALPHA_WEIGHT)

    # Magazine factor — gentle log curve, MAG_REFERENCE rounds = 1.0
    mag_factor = (math.log(max(ammo, 1) + 1) / math.log(MAG_REFERENCE + 1)) ** MAG_WEIGHT

    return round(combined * mag_factor, 2)

# ---------------------------------------------------------------------------
# Budget and material computation
# ---------------------------------------------------------------------------

def score_to_budget(expensive_score):
    """Convert expensive score → total material budget."""
    shifted = max(expensive_score + GLOBAL_OFFSET, 0.01)
    return int(GLOBAL_SCALE * (shifted ** GLOBAL_EXPONENT))

def parse_extras(extras_str):
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

def compute_materials(profile_name, total_budget, extras_str=""):
    """Distribute total_budget across profile materials by weight, add extras."""
    profile = PROFILES.get(profile_name)
    if not profile:
        return None

    exp = PROFILE_EXPONENT.get(profile_name, 1.0)
    adjusted_budget = PROFILE_MULT.get(profile_name, 1.0) * (total_budget ** exp)
    mats = {}
    for mat, weight in profile.items():
        count = int(adjusted_budget * weight)
        if count > 0:
            mats[mat] = count

    for mat, count in parse_extras(extras_str).items():
        mats[mat] = mats.get(mat, 0) + count

    return mats

# ---------------------------------------------------------------------------
# Gun data discovery
# ---------------------------------------------------------------------------

def _load_commented_json(filepath):
    """Load a JSON file that may contain // and /* */ comments and trailing commas."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    # Strip block comments /* ... */
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Strip line comments // ...
    text = re.sub(r'//[^\n]*', '', text)
    # Strip trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return json.loads(text)

def discover_guns():
    """Find all gun _data.json files. Returns {(pack, gun_id): parsed_data}."""
    guns = {}
    for pack_name, data_dir in PACK_DATA_DIRS.items():
        if not os.path.isdir(data_dir):
            print(f"  WARNING: data dir not found: {data_dir}")
            continue
        pattern = os.path.join(data_dir, "*_data.json")
        for filepath in sorted(glob.glob(pattern)):
            filename = os.path.basename(filepath)
            gun_id = filename.replace("_data.json", "")
            try:
                data = _load_commented_json(filepath)
            except (json.JSONDecodeError, OSError) as e:
                print(f"  WARNING: {filepath}: {e}")
                continue
            guns[(pack_name, gun_id)] = data
    return guns

# ---------------------------------------------------------------------------
# CSV I/O
# ---------------------------------------------------------------------------

def read_balance_csv():
    if not os.path.exists(BALANCE_CSV):
        return []
    with open(BALANCE_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_balance_csv(rows):
    with open(BALANCE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=BALANCE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

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

# ---------------------------------------------------------------------------
# --scan: discover guns, create/update balance.csv
# ---------------------------------------------------------------------------

def scan_mode():
    guns = discover_guns()
    existing = read_balance_csv()

    # Index existing by (pack, id) — preserve user edits
    existing_index = {}
    for row in existing:
        pack = row.get("pack", "").strip()
        rid  = row.get("id", "").strip()
        if pack and not pack.startswith("#") and rid:
            existing_index[(pack, rid)] = row

    new_rows = []
    new_count = 0
    for (pack, gun_id), data in sorted(guns.items()):
        score = compute_power_score(data)
        key = (pack, gun_id)

        if key in existing_index:
            # Preserve user edits (profile, mult, offset, extras, notes)
            row = dict(existing_index[key])
            row["power_score"] = score
        else:
            # New gun — defaults
            row = {
                "pack": pack, "type": "gun", "id": gun_id,
                "profile": PACK_DEFAULTS.get(pack, "modern_steel"),
                "mult": "1", "offset": "0", "extras": "",
                "power_score": score,
                "notes": "",
            }
            new_count += 1
        new_rows.append(row)

    # Preserve any non-gun rows (future ammo/attachment support)
    for row in existing:
        rtype = row.get("type", "").strip()
        pack  = row.get("pack", "").strip()
        if pack.startswith("#") or rtype != "gun":
            new_rows.append(row)

    write_balance_csv(new_rows)
    print(f"Scanned {len(guns)} guns → {BALANCE_CSV}")
    print(f"  New: {new_count} | Updated: {len(guns) - new_count}")

# ---------------------------------------------------------------------------
# --scores: print ranked power scores
# ---------------------------------------------------------------------------

def scores_mode():
    guns = discover_guns()
    scored = [(compute_power_score(data), pack, gid) for (pack, gid), data in guns.items()]
    scored.sort(reverse=True)

    print(f"{'Score':>8}  {'Budget':>7}  {'Pack':<10} {'Gun ID'}")
    print("-" * 55)
    for score, pack, gun_id in scored:
        budget = score_to_budget(score)
        print(f"{score:>8.1f}  {budget:>7}  {pack:<10} {gun_id}")
    print(f"\n{len(scored)} guns total  |  SCALE={GLOBAL_SCALE}  EXPONENT={GLOBAL_EXPONENT}  OFFSET={GLOBAL_OFFSET}")

# ---------------------------------------------------------------------------
# --preview: show full breakdown without writing
# ---------------------------------------------------------------------------

def preview_mode():
    balance = read_balance_csv()
    guns = discover_guns()

    if not balance:
        print("No balance.csv found. Run --scan first.")
        return

    print(f"{'Pack':<10} {'ID':<25} {'Profile':<16} {'Power':>7} {'x':>5} {'+':>5} {'Exp':>7} {'Budget':>7}  Materials")
    print("-" * 130)

    for row in balance:
        pack = row.get("pack", "").strip()
        if not pack or pack.startswith("#"):
            continue
        gun_id  = row.get("id", "").strip()
        profile = row.get("profile", "").strip()
        mult    = float(row.get("mult", 1) or 1)
        offset  = float(row.get("offset", 0) or 0)
        extras  = row.get("extras", "")

        key = (pack, gun_id)
        score = compute_power_score(guns[key]) if key in guns else float(row.get("power_score", 0) or 0)
        expensive = mult * score + offset
        budget = score_to_budget(expensive)

        mats = compute_materials(profile, budget, extras)
        if mats:
            mat_str = "  ".join(f"{k}={v}" for k, v in sorted(mats.items()) if v > 0)
        else:
            mat_str = f"(unknown profile: {profile})"

        print(f"{pack:<10} {gun_id:<25} {profile:<16} {score:>7.1f} {mult:>5.1f} {offset:>+5.0f} {expensive:>7.1f} {budget:>7}  {mat_str}")

# ---------------------------------------------------------------------------
# Default mode: compute recipes and update recipes.csv
# ---------------------------------------------------------------------------

def balance_mode():
    balance = read_balance_csv()
    guns = discover_guns()
    recipes = read_recipes_csv()

    if not balance:
        print("No balance.csv found. Run --scan first.")
        return

    # Index existing recipes by (pack, type, id)
    recipe_index = {}
    for i, row in enumerate(recipes):
        pack  = row.get("pack", "").strip()
        rtype = row.get("type", "").strip()
        rid   = row.get("id", "").strip()
        if pack and not pack.startswith("#"):
            recipe_index[(pack, rtype, rid)] = i

    updated = 0
    added = 0

    for brow in balance:
        pack    = brow.get("pack", "").strip()
        if not pack or pack.startswith("#"):
            continue
        gun_id  = brow.get("id", "").strip()
        profile = brow.get("profile", "").strip()
        mult    = float(brow.get("mult", 1) or 1)
        offset  = float(brow.get("offset", 0) or 0)
        extras  = brow.get("extras", "")

        if not profile or profile == "manual":
            continue  # user owns this row, skip

        key = (pack, gun_id)
        if key not in guns:
            print(f"  WARNING: no data file for {pack}:{gun_id}, skipping")
            continue

        score     = compute_power_score(guns[key])
        expensive = mult * score + offset
        budget    = score_to_budget(expensive)
        mats      = compute_materials(profile, budget, extras)

        if mats is None:
            print(f"  WARNING: unknown profile '{profile}' for {pack}:{gun_id}")
            continue

        # Build recipe row
        recipe_row = {"pack": pack, "type": "gun", "id": gun_id, "yield": ""}
        for col in MATERIAL_COLS:
            recipe_row[col] = mats.get(col, "")
        recipe_row["notes"] = ""

        # Update existing or append
        rkey = (pack, "gun", gun_id)
        if rkey in recipe_index:
            idx = recipe_index[rkey]
            recipe_row["notes"] = recipes[idx].get("notes", "")
            recipes[idx] = recipe_row
            updated += 1
        else:
            recipes.append(recipe_row)
            added += 1

    write_recipes_csv(recipes)
    print(f"Updated {RECIPES_CSV}: {updated} updated, {added} added")
    print(f"  (ammo, attachment, and profile=manual rows preserved)")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def graph_mode():
    """Write graph.csv with all scalar scores for easy graphing."""
    balance = read_balance_csv()
    guns = discover_guns()

    if not balance:
        print("No balance.csv found. Run --scan first.")
        return

    graph_path = os.path.join(SCRIPT_DIR, "graph.csv")
    fields = ["pack", "id", "profile", "mult", "offset",
              "power_score", "expensive_score", "total_budget", "profile_mult", "profile_exp", "adjusted_budget"]

    rows = []
    for row in balance:
        pack = row.get("pack", "").strip()
        if not pack or pack.startswith("#"):
            continue
        gun_id  = row.get("id", "").strip()
        profile = row.get("profile", "").strip()
        mult    = float(row.get("mult", 1) or 1)
        offset  = float(row.get("offset", 0) or 0)

        key = (pack, gun_id)
        score = compute_power_score(guns[key]) if key in guns else float(row.get("power_score", 0) or 0)
        expensive = mult * score + offset
        budget = score_to_budget(expensive)
        pmult = PROFILE_MULT.get(profile, 1.0)
        pexp = PROFILE_EXPONENT.get(profile, 1.0)
        adjusted = int(pmult * (budget ** pexp))

        rows.append({
            "pack": pack, "id": gun_id, "profile": profile,
            "mult": mult, "offset": offset,
            "power_score": round(score, 2),
            "expensive_score": round(expensive, 2),
            "total_budget": budget,
            "profile_mult": pmult,
            "profile_exp": pexp,
            "adjusted_budget": adjusted,
        })

    rows.sort(key=lambda r: r["power_score"], reverse=True)

    with open(graph_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Wrote {len(rows)} rows to {graph_path}")
    print(f"  Columns: {', '.join(fields)}")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TACZ recipe balancer")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--scan",    action="store_true", help="Discover guns, create/update balance.csv")
    group.add_argument("--scores",  action="store_true", help="Print ranked power scores")
    group.add_argument("--preview", action="store_true", help="Show breakdown without writing")
    group.add_argument("--graph",   action="store_true", help="Write graph.csv with all scores for graphing")
    args = parser.parse_args()

    if args.scan:
        scan_mode()
    elif args.scores:
        scores_mode()
    elif args.preview:
        preview_mode()
    elif args.graph:
        graph_mode()
    else:
        balance_mode()
