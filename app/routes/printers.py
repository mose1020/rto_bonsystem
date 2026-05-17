from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from ..services.printer_service import load_printers


bp = Blueprint("printers", __name__, url_prefix="/api/printers")


@bp.get("")
def list_printers():
    cfg = load_printers(
        current_app.config["PRINTERS_PATH"],
        fallback_device=current_app.config.get("PRINTER_DEVICE"),
    )
    return jsonify({
        "default": cfg["default"],
        "printers": [{"id": p["id"], "name": p.get("name", p["id"])} for p in cfg["printers"]],
    })
