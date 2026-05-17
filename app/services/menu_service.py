from __future__ import annotations

import json
import threading
from functools import lru_cache
from pathlib import Path


_write_lock = threading.Lock()


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


def update_item_limits(path: Path, item_id: str,
                        critical: int | None, warn: int | None) -> dict:
    """Aktualisiert `critical` und/oder `warn` für einen Artikel in menu.json.

    Atomar via temp-File. Wirft ValueError wenn Item unbekannt oder
    Werte ungültig (warn >= critical, oder negative Werte).
    """
    with _write_lock:
        path = Path(path)
        with open(path, "r", encoding="utf-8") as fh:
            menu = json.load(fh)

        target = None
        for cat in menu.get("categories", []):
            for it in cat.get("items", []):
                if it.get("id") == item_id:
                    target = it
                    break
            if target:
                break
        if target is None:
            raise ValueError(f"Unbekannter Artikel: {item_id}")

        new_critical = target.get("critical") if critical is None else int(critical)
        new_warn = target.get("warn") if warn is None else int(warn)

        if new_critical is not None and new_critical < 0:
            raise ValueError("kritischer Wert muss ≥ 0 sein")
        if new_warn is not None and new_warn < 0:
            raise ValueError("Warnwert muss ≥ 0 sein")
        if (new_critical is not None and new_warn is not None
                and new_warn >= new_critical):
            raise ValueError("Warnwert muss kleiner sein als der kritische Wert")

        if critical is not None:
            target["critical"] = new_critical
        if warn is not None:
            target["warn"] = new_warn

        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(menu, fh, ensure_ascii=False, indent=2)
        tmp.replace(path)

    # Cache leeren, damit die nächste load_menu()-Call frische Daten holt
    _load_menu_cached.cache_clear()
    return target
