from __future__ import annotations

import json
import secrets
import threading
from datetime import datetime
from pathlib import Path

from .menu_service import find_item


_write_lock = threading.Lock()


def build_order(menu: dict, items: list[dict], tendered: float | None = None) -> dict:
    resolved_items: list[dict] = []
    subtotal = 0.0
    deposit_total = 0.0
    for entry in items:
        item_id = entry.get("id")
        quantity = int(entry.get("quantity", 1))
        if quantity <= 0:
            continue
        item = find_item(menu, item_id)
        if item is None:
            raise ValueError(f"Unbekannter Artikel: {item_id}")
        unit_price = float(item["price"])
        deposit = float(item.get("deposit", 0.0))
        line_subtotal = round(unit_price * quantity, 2)
        line_deposit = round(deposit * quantity, 2)
        line_total = round(line_subtotal + line_deposit, 2)
        subtotal = round(subtotal + line_subtotal, 2)
        deposit_total = round(deposit_total + line_deposit, 2)
        resolved_items.append({
            "id": item["id"],
            "name": item["name"],
            "unit_price": unit_price,
            "deposit": deposit,
            "quantity": quantity,
            "line_total": line_total,
        })

    if not resolved_items:
        raise ValueError("Bestellung ist leer.")

    total = round(subtotal + deposit_total, 2)

    tendered_value: float | None = None
    change: float | None = None
    if tendered is not None:
        tendered_value = round(float(tendered), 2)
        change = round(tendered_value - total, 2)

    return {
        "id": _generate_order_id(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "currency": menu.get("currency", "EUR"),
        "items": resolved_items,
        "subtotal": subtotal,
        "deposit_total": deposit_total,
        "total": total,
        "tendered": tendered_value,
        "change": change,
    }


def persist_order(path: Path, order: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _write_lock:
        orders = []
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    orders = json.load(fh)
            except json.JSONDecodeError:
                orders = []
        orders.append(order)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(orders, fh, ensure_ascii=False, indent=2)
        tmp.replace(path)


def _generate_order_id() -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{secrets.token_hex(2).upper()}"
