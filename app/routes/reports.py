from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from ..services.db import available_days, items_sold, list_orders, summary
from ..services.menu_service import load_menu


bp = Blueprint("reports", __name__, url_prefix="/api/reports")


def _day_arg() -> str | None:
    """Holt ?day=YYYY-MM-DD aus Query oder None."""
    day = request.args.get("day")
    if day and len(day) == 10:
        return day
    return None


@bp.get("/days")
def get_days():
    """Liste der Tage (YYYY-MM-DD), an denen es Bestellungen gab."""
    return jsonify({"days": available_days(current_app.config["DB_PATH"])})


@bp.get("/orders")
def get_orders():
    try:
        limit = max(1, min(int(request.args.get("limit", 100)), 1000))
    except ValueError:
        limit = 100
    orders = list_orders(
        current_app.config["DB_PATH"], limit=limit, day=_day_arg()
    )
    return jsonify({"orders": orders, "count": len(orders)})


@bp.get("/summary")
def get_summary():
    return jsonify(summary(current_app.config["DB_PATH"], day=_day_arg()))


@bp.get("/inventory")
def get_inventory():
    """Pro Artikel: verkaufte Menge, kritischer/Warn-Wert, Status.

    status:
      'ok'        — alles im grünen Bereich (oder kein critical gesetzt)
      'warn'      — Restbestand ≤ warn (gelb)
      'critical'  — verkauft ≥ critical (orange)
    """
    menu = load_menu(current_app.config["MENU_PATH"])
    sold = items_sold(current_app.config["DB_PATH"], day=_day_arg())
    categories = []
    for cat in menu.get("categories", []):
        items = []
        for it in cat.get("items", []):
            sold_qty = sold.get(it["id"], 0)
            critical = it.get("critical")
            warn = it.get("warn")
            remaining = (critical - sold_qty) if isinstance(critical, (int, float)) else None

            status = "ok"
            if isinstance(critical, (int, float)):
                if sold_qty >= critical:
                    status = "critical"
                elif isinstance(warn, (int, float)) and remaining is not None and remaining <= warn:
                    status = "warn"

            items.append({
                "id": it["id"],
                "name": it["name"],
                "sold": sold_qty,
                "critical": critical,
                "warn": warn,
                "remaining": remaining,
                "status": status,
            })
        categories.append({"id": cat["id"], "name": cat["name"], "items": items})
    return jsonify({"categories": categories, "currency": menu.get("currency", "EUR")})
