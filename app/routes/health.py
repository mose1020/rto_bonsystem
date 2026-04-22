from __future__ import annotations

import os
from pathlib import Path

from flask import Blueprint, current_app, jsonify


bp = Blueprint("health", __name__, url_prefix="/api/health")


@bp.get("")
def health():
    return jsonify({"status": "ok"})


@bp.get("/printer")
def printer_health():
    device = current_app.config["PRINTER_DEVICE"]
    path = Path(device)
    if not path.exists():
        return jsonify({
            "status": "missing",
            "device": device,
            "error": "Gerät nicht gefunden (Drucker aus oder nicht verbunden?)",
        }), 503
    if not os.access(device, os.W_OK):
        return jsonify({
            "status": "permission_denied",
            "device": device,
            "error": "Kein Schreibzugriff (User in Gruppe 'lp'?)",
        }), 503
    return jsonify({"status": "ok", "device": device})
