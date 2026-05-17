from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify, request

from ..services.db import insert_order as db_insert_order
from ..services.menu_service import load_menu
from ..services.order_service import build_order, persist_order
from ..services.printer_service import (
    PrinterError,
    find_printer,
    load_printers,
    print_order,
)


log = logging.getLogger(__name__)

bp = Blueprint("orders", __name__, url_prefix="/api/orders")


@bp.post("")
def create_order():
    payload = request.get_json(silent=True) or {}
    items = payload.get("items") or []
    printer_id = payload.get("printer_id")
    tendered_raw = payload.get("tendered")
    tendered: float | None = None
    if tendered_raw is not None and tendered_raw != "":
        try:
            tendered = float(tendered_raw)
        except (TypeError, ValueError):
            return jsonify({"error": "Ungültiger Wert für 'gegeben'."}), 400

    if not items:
        return jsonify({"error": "Keine Artikel in der Bestellung."}), 400

    menu = load_menu(current_app.config["MENU_PATH"])
    try:
        order = build_order(menu, items, tendered=tendered)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    printers_cfg = load_printers(
        current_app.config["PRINTERS_PATH"],
        fallback_device=current_app.config.get("PRINTER_DEVICE"),
    )
    printer = find_printer(printers_cfg, printer_id)
    order["printer"] = {"id": printer["id"], "name": printer.get("name", printer["id"])}

    persist_order(current_app.config["ORDERS_PATH"], order)
    try:
        db_insert_order(current_app.config["DB_PATH"], order)
    except Exception:
        # JSON-Backup ist bereits geschrieben; DB-Fehler nicht fatal,
        # damit die Bestellung trotzdem gedruckt werden kann.
        log.exception("DB-Insert fehlgeschlagen (JSON-Backup vorhanden)")

    try:
        print_order(order, device=printer["device"], event=menu.get("event"))
    except PrinterError as exc:
        log.exception("Druckfehler")
        return jsonify({"order": order, "print_error": str(exc)}), 502

    return jsonify({"order": order}), 201
