"""
Shared constants for the recipe toolchain (gen_recipes.py, balance_recipes.py).

Add new materials here. Both scripts import from this module,
so they stay in sync automatically.

Key format note:
    IE/Create items MUST use {"item": "mod:item_id"} — never {"tag": "..."}.
    Forge-standard tags (forge:ingots/copper, minecraft:logs, etc.) work fine as tags.
"""

# ---------------------------------------------------------------------------
# Material registry
# Maps CSV column name → function(count) → TACZ material dict.
# The key order here determines column order in recipes.csv.
# ---------------------------------------------------------------------------

MATERIAL_DEFS = {
    # IE plates / rods / components (must be item refs)
    "steel_plate":  lambda n: {"item": {"item": "immersiveengineering:plate_steel"},    "count": n},
    "iron_plate":   lambda n: {"item": {"item": "immersiveengineering:plate_iron"},     "count": n},
    "alum_plate":   lambda n: {"item": {"item": "immersiveengineering:plate_aluminum"}, "count": n},
    "gold_plate":   lambda n: {"item": {"item": "immersiveengineering:plate_gold"},     "count": n},
    "steel_rod":    lambda n: {"item": {"item": "immersiveengineering:stick_steel"},    "count": n},
    "iron_comp":    lambda n: {"item": {"item": "immersiveengineering:component_iron"}, "count": n},
    "steel_comp":   lambda n: {"item": {"item": "immersiveengineering:component_steel"},"count": n},
    # Create items (must be item refs)
    "andesite":     lambda n: {"item": {"item": "create:andesite_alloy"},       "count": n},
    "brass":        lambda n: {"item": {"item": "create:brass_ingot"},          "count": n},
    "pmech":        lambda n: {"item": {"item": "create:precision_mechanism"},  "count": n},
    # TFMG
    "plastic":      lambda n: {"item": {"item": "tfmg:plastic_sheet"},         "count": n},
    # Forge / vanilla tags
    "lead":         lambda n: {"item": {"tag": "forge:ingots/lead"},      "count": n},
    "uranium":      lambda n: {"item": {"tag": "forge:ingots/uranium"},    "count": n},
    "logs":         lambda n: {"item": {"tag": "minecraft:logs"},          "count": n},
    "clay":         lambda n: {"item": {"tag": "minecraft:clay"},          "count": n},
    "glass":        lambda n: {"item": {"tag": "forge:glass"},             "count": n},
    "copper":       lambda n: {"item": {"tag": "forge:ingots/copper"},     "count": n},
    "iron_nugget":  lambda n: {"item": {"tag": "forge:nuggets/iron"},      "count": n},
    "gunpowder":    lambda n: {"item": {"tag": "forge:gunpowder"},         "count": n},
    "blaze_rod":    lambda n: {"item": {"tag": "forge:rods/blaze"},        "count": n},
    "lapis":        lambda n: {"item": {"tag": "forge:gems/lapis"},        "count": n},
    "redstone":     lambda n: {"item": {"tag": "forge:dusts/redstone"},    "count": n},
    "leather":      lambda n: {"item": {"tag": "forge:leather"},           "count": n},
    "anvil":        lambda n: {"item": {"tag": "minecraft:anvil"},         "count": n},
    # Specific vanilla items
    "tnt":          lambda n: {"item": {"item": "minecraft:tnt"},          "count": n},
    "lever":        lambda n: {"item": {"item": "minecraft:lever"},        "count": n},
    "paper":        lambda n: {"item": {"item": "minecraft:paper"},        "count": n},
    "flint":        lambda n: {"item": {"item": "minecraft:flint"},        "count": n},
}

# Derived — column order for CSV files
MATERIAL_COLS = list(MATERIAL_DEFS.keys())

# Shared field list for recipes.csv (used by balance_recipes.py and ammo_recipes.py)
RECIPES_FIELDS = ["pack", "type", "id", "yield"] + MATERIAL_COLS + ["notes"]

# ---------------------------------------------------------------------------
# Pack paths — maps pack name → recipe output directory
# ---------------------------------------------------------------------------

PACK_PATHS = {
    "hamster": "tacz/GunpowderRevolution_gunpack v1/data/hamster/recipes",
    "tacz":    "tacz/tacz_default_gun/data/tacz/recipes",
    "suffuse": "tacz/Suffuse-GunSmoke-Pack1/data/suffuse/recipes",
}

# ---------------------------------------------------------------------------
# Pack data directories — maps pack name → gun stats directory
# ---------------------------------------------------------------------------

PACK_DATA_DIRS = {
    "hamster": "tacz/GunpowderRevolution_gunpack v1/data/hamster/data/guns",
    "tacz":    "tacz/tacz_default_gun/data/tacz/data/guns",
    "suffuse": "tacz/Suffuse-GunSmoke-Pack1/data/suffuse/data/guns",
}
