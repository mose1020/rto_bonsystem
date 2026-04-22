from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify, request

from ..services.menu_service import load_menu
from ..services.order_service import build_order, persist_order
from ..services.printer_service import PrinterError, print_order


log = logging.getLogger(__name__)

bp = Blueprint("orders", __name__, url_prefix="/api/orders")


@bp.post("")
def create_order():
    payload = request.get_json(silent=True) or {}
    items = payload.get("items") or []
    note = (payload.get("note") or "").strip()

    if not items:
        return jsonify({"error": "Keine Artikel in der Bestellung."}), 400

    menu = load_menu(current_app.config["MENU_PATH"])
    try:
        order = build_order(menu, items, note=note)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    persist_order(current_app.config["ORDERS_PATH"], order)

    try:
        print_order(order, device=current_app.config["PRINTER_DEVICE"])
    except PrinterError as exc:
        log.exception("Druckfehler")
        return jsonify({"order": order, "print_error": str(exc)}), 502

    return jsonify({"order": order}), 201
