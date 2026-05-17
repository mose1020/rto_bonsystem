from __future__ import annotations

import hmac
import logging
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from ..services.db import reset_orders


log = logging.getLogger(__name__)

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.post("/reset")
def reset_database():
    """Setzt die Bestellungen-DB zurück. Erfordert Passwort aus .env."""
    expected = (current_app.config.get("ADMIN_PASSWORD") or "").strip()
    if not expected:
        return jsonify({
            "error": "Reset ist nicht aktiviert (ADMIN_PASSWORD in .env fehlt)."
        }), 503

    payload = request.get_json(silent=True) or {}
    provided = str(payload.get("password") or "")
    # konstant-zeitiger Vergleich
    if not hmac.compare_digest(expected, provided):
        return jsonify({"error": "Falsches Passwort."}), 401

    db_path = current_app.config["DB_PATH"]
    stats = reset_orders(db_path)

    # orders.json sicherheitshalber als Backup wegrotieren, damit der
    # automatische Re-Import beim nächsten App-Start nicht alles wieder einliest.
    orders_json = Path(current_app.config["ORDERS_PATH"])
    if orders_json.is_file():
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = orders_json.with_suffix(orders_json.suffix + f".bak.{ts}")
        try:
            orders_json.rename(backup)
            stats["orders_json_backup"] = backup.name
        except OSError as exc:
            log.warning("orders.json konnte nicht archiviert werden: %s", exc)

    log.info("DB-Reset durch Admin: %s", stats)
    return jsonify({"status": "ok", **stats})
