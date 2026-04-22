from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=4)
def _load_menu_cached(path_str: str, mtime: float) -> dict:
    with open(path_str, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_menu(path: Path) -> dict:
    path = Path(path)
    return _load_menu_cached(str(path), path.stat().st_mtime)


def find_item(menu: dict, item_id: str) -> dict | None:
    for category in menu.get("categories", []):
        for item in category.get("items", []):
            if item.get("id") == item_id:
                return item
    return None
