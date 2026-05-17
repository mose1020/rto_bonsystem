from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template, request

from ..services.menu_service import load_menu, update_item_limits
from ..services.printer_service import load_printers


bp = Blueprint("menu", __name__)


@bp.get("/")
def index():
    menu = load_menu(current_app.config["MENU_PATH"])
    printers_cfg = load_printers(
        current_app.config["PRINTERS_PATH"],
        fallback_device=current_app.config.get("PRINTER_DEVICE"),
    )
    printers = [
        {"id": p["id"], "name": p.get("name", p["id"])}
        for p in printers_cfg["printers"]
    ]
    return render_template(
        "order.html",
        menu=menu,
        printers=printers,
        default_printer_id=printers_cfg["default"],
    )


@bp.get("/api/menu")
def api_menu():
    return load_menu(current_app.config["MENU_PATH"])


@bp.get("/uebersicht")
def overview():
    menu = load_menu(current_app.config["MENU_PATH"])
    return render_template("overview.html", menu=menu)


@bp.patch("/api/menu/items/<item_id>")
def patch_item_limits(item_id: str):
    """Aktualisiert kritischen Wert und/oder Warnwert für einen Artikel.

    Erwartet Body: { "critical": int, "warn": int } (beide optional).
    """
    payload = request.get_json(silent=True) or {}
    critical = payload.get("critical")
    warn = payload.get("warn")
    if critical is None and warn is None:
        return jsonify({"error": "Keine Werte zum Aktualisieren"}), 400

    def _coerce(name, value):
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return f"_invalid:{name}"

    crit = _coerce("critical", critical)
    wrn = _coerce("warn", warn)
    for v, n in [(crit, "critical"), (wrn, "warn")]:
        if isinstance(v, str) and v.startswith("_invalid"):
            return jsonify({"error": f"Ungültiger Wert für {n}"}), 400

    try:
        updated = update_item_limits(
            current_app.config["MENU_PATH"], item_id, crit, wrn
        )
    except ValueError as exc:
        msg = str(exc)
        status = 404 if "Unbekannt" in msg else 400
        return jsonify({"error": msg}), status
    return jsonify({"item": updated})
