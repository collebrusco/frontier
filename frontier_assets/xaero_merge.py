"""
Xaero's World Map data merger.

Merges map data from one player's .minecraft directory into another's.

Merge strategy per region zip:
  - Region only in incoming  → copy it wholesale
  - Region in both           → take the larger file (heuristic: more explored = larger)

TODO: proper pixel-level merge
    The region.xaero format stores 512x512 pixels as variable-length entries.
    Each pixel starts with a 4-byte pixelParams int; if pixelParams == 0xFFFFFFFF
    the pixel is unexplored (tile-absent sentinel).  A correct merge would:
      1. Read both region.xaero files out of their zips
      2. Parse the header (format version in first few bytes)
      3. For each chunk/tile entry: if one side has the tile absent and the other
         doesn't, take the present side's tile bytes verbatim
      4. For tiles present in both: walk pixel-by-pixel, keeping any non-0xFFFFFFFF
         pixel (with incoming winning ties so newer exploration wins)
      5. Repack into a new zip
    See frontier_assets/xaero-format.md for the full format spec.
"""

import shutil
from pathlib import Path

_XAERO_WM_SUBDIR = Path("xaero") / "world-map"
_CACHE_ENTRIES = [
    ("cache/1", ".xwmc"),
    ("cache_1", ".xwmc.outdated"),
]


def _log(cb, msg, color="white"):
    if cb:
        cb(msg, color)
    else:
        print(msg)


def _invalidate_region_cache(region_zip: Path):
    """Delete cached render tiles for a region so Xaero regenerates them on next load."""
    stem = region_zip.stem
    parent = region_zip.parent
    for subdir, ext in _CACHE_ENTRIES:
        cache_file = parent / subdir / (stem + ext)
        if cache_file.exists():
            try:
                cache_file.unlink()
            except OSError:
                pass


def _merge_region(base_zip: Path, incoming_zip: Path) -> str:
    """
    Merge incoming_zip into base_zip in-place.
    Returns 'replaced' if base was updated, 'kept' otherwise.

    TODO: replace with proper pixel-level merge (see module docstring).
    """
    if incoming_zip.stat().st_size > base_zip.stat().st_size:
        shutil.copy2(str(incoming_zip), str(base_zip))
        _invalidate_region_cache(base_zip)
        return "replaced"
    return "kept"


def merge_xaero_world_maps(base_minecraft: str, incoming_minecraft: str, log_cb=None) -> dict:
    """
    Merge Xaero world map data from incoming_minecraft into base_minecraft.

    Both arguments are paths to .minecraft directories.  Writes changes into
    base_minecraft in-place.  Returns a stats dict:
        {'copied': int, 'replaced': int, 'kept': int, 'errors': int}
    """
    stats = {"copied": 0, "replaced": 0, "kept": 0, "errors": 0}

    base_wm = Path(base_minecraft) / _XAERO_WM_SUBDIR
    incoming_wm = Path(incoming_minecraft) / _XAERO_WM_SUBDIR

    if not base_wm.exists():
        _log(log_cb, f"No Xaero world map found at base: {base_wm}", "red")
        return stats
    if not incoming_wm.exists():
        _log(log_cb, f"No Xaero world map found in incoming: {incoming_wm}", "red")
        return stats

    base_servers = {d.name for d in base_wm.iterdir() if d.is_dir()}
    incoming_servers = {d.name for d in incoming_wm.iterdir() if d.is_dir()}

    # Servers only in incoming: copy entire folder tree
    for server in incoming_servers - base_servers:
        _log(log_cb, f"Copying new server folder: {server}", "cyan")
        try:
            shutil.copytree(str(incoming_wm / server), str(base_wm / server))
            stats["copied"] += sum(1 for _ in (incoming_wm / server).rglob("*.zip"))
        except Exception as e:
            _log(log_cb, f"  Error copying {server}: {e}", "red")
            stats["errors"] += 1

    # Servers in both: merge region by region
    for server in base_servers & incoming_servers:
        _log(log_cb, f"Merging server: {server}", "yellow")
        base_server = base_wm / server
        incoming_server = incoming_wm / server

        for incoming_zip in incoming_server.rglob("*.zip"):
            rel = incoming_zip.relative_to(incoming_server)
            base_zip = base_server / rel

            try:
                if not base_zip.exists():
                    base_zip.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(incoming_zip), str(base_zip))
                    _invalidate_region_cache(base_zip)
                    _log(log_cb, f"  Copied new region: {rel}", "lime")
                    stats["copied"] += 1
                else:
                    result = _merge_region(base_zip, incoming_zip)
                    if result == "replaced":
                        _log(log_cb, f"  Updated region (incoming larger): {rel}", "cyan")
                        stats["replaced"] += 1
                    else:
                        stats["kept"] += 1
            except Exception as e:
                _log(log_cb, f"  Error merging {rel}: {e}", "red")
                stats["errors"] += 1

    _log(
        log_cb,
        f"Merge complete — "
        f"{stats['copied']} new, {stats['replaced']} updated, "
        f"{stats['kept']} unchanged, {stats['errors']} errors",
        "lime" if stats["errors"] == 0 else "orange",
    )
    return stats
