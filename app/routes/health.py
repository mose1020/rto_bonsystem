from __future__ import annotations

import os
from pathlib import Path

from flask import Blueprint, current_app, jsonify

from ..services.printer_service import load_printers, find_printer


bp = Blueprint("health", __name__, url_prefix="/api/health")


@bp.get("")
def health():
    return jsonify({"status": "ok"})


def _check_device(device: str) -> tuple[dict, int]:
    path = Path(device)
    if not path.exists():
        return {
            "status": "missing",
            "device": device,
            "error": "Gerät nicht gefunden (Drucker aus oder nicht verbunden?)",
        }, 503
    if not os.access(device, os.W_OK):
        return {
            "status": "permission_denied",
            "device": device,
            "error": "Kein Schreibzugriff (User in Gruppe 'lp'?)",
        }, 503
    return {"status": "ok", "device": device}, 200


@bp.get("/printer")
def printer_health_default():
    """Health-Check des Default-Druckers (Rückwärtskompatibilität)."""
    cfg = load_printers(
        current_app.config["PRINTERS_PATH"],
        fallback_device=current_app.config.get("PRINTER_DEVICE"),
    )
    p = find_printer(cfg, None)
    body, status = _check_device(p["device"])
    body["printer"] = {"id": p["id"], "name": p.get("name", p["id"])}
    return jsonify(body), status


@bp.get("/printer/<printer_id>")
def printer_health_specific(printer_id: str):
    cfg = load_printers(
        current_app.config["PRINTERS_PATH"],
        fallback_device=current_app.config.get("PRINTER_DEVICE"),
    )
    if not any(p.get("id") == printer_id for p in cfg["printers"]):
        return jsonify({
            "status": "unknown_printer",
            "error": f"Unbekannter Drucker: {printer_id}",
        }), 404
    p = find_printer(cfg, printer_id)
    body, status = _check_device(p["device"])
    body["printer"] = {"id": p["id"], "name": p.get("name", p["id"])}
    return jsonify(body), status
