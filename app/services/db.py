"""SQLite-Persistierung für Bestellungen.

Schema:
- orders        Bestell-Header (1 Zeile pro Bon-Submit)
- order_items   Positionen (n Zeilen pro Bestellung)

Bewusst kein ORM (siehe docs/backlog.md): handgeschriebenes SQL über die
Standard-Library reicht und vermeidet eine zusätzliche Abhängigkeit.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from pathlib import Path

log = logging.getLogger(__name__)

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id              TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    currency        TEXT NOT NULL,
    subtotal        REAL NOT NULL,
    deposit_total   REAL NOT NULL,
    total           REAL NOT NULL,
    tendered        REAL,
    change_due      REAL,
    printer_id      TEXT,
    printer_name    TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        TEXT NOT NULL,
    item_id         TEXT NOT NULL,
    name            TEXT NOT NULL,
    unit_price      REAL NOT NULL,
    deposit         REAL NOT NULL,
    quantity        INTEGER NOT NULL,
    line_total      REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items (order_id);
"""


def _connect(path: Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(path: Path) -> None:
    """Legt Tabellen + Indizes an, falls noch nicht vorhanden. Idempotent."""
    with _lock:
        with _connect(path) as conn:
            conn.executescript(SCHEMA)


def insert_order(path: Path, order: dict) -> None:
    """Schreibt eine vollständige Bestellung (Header + Items) in einer Transaktion."""
    printer = order.get("printer") or {}
    with _lock:
        with _connect(path) as conn:
            conn.execute(
                """INSERT INTO orders
                   (id, created_at, currency, subtotal, deposit_total, total,
                    tendered, change_due, printer_id, printer_name)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    order["id"],
                    order["created_at"],
                    order["currency"],
                    order["subtotal"],
                    order["deposit_total"],
                    order["total"],
                    order.get("tendered"),
                    order.get("change"),
                    printer.get("id"),
                    printer.get("name"),
                ),
            )
            for item in order["items"]:
                conn.execute(
                    """INSERT INTO order_items
                       (order_id, item_id, name, unit_price, deposit, quantity, line_total)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        order["id"],
                        item["id"],
                        item["name"],
                        item["unit_price"],
                        item["deposit"],
                        item["quantity"],
                        item["line_total"],
                    ),
                )


def maybe_migrate_orders_json(db_path: Path, json_path: Path) -> int:
    """Importiert orders.json einmalig in die DB, falls die DB leer ist und
    die JSON-Datei existiert. Gibt Anzahl importierter Bestellungen zurück."""
    json_path = Path(json_path)
    if not json_path.is_file():
        return 0
    with _connect(db_path) as conn:
        existing = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    if existing > 0:
        return 0

    try:
        with open(json_path, "r", encoding="utf-8") as fh:
            orders = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("orders.json konnte nicht gelesen werden: %s", exc)
        return 0

    imported = 0
    for order in orders:
        try:
            insert_order(db_path, order)
            imported += 1
        except sqlite3.IntegrityError:
            # bereits importiert (id-Konflikt)
            continue
        except Exception as exc:
            log.warning("Migration: Order %s übersprungen: %s", order.get("id"), exc)
    if imported:
        log.info("Migration: %d Bestellungen aus orders.json in DB importiert", imported)
    return imported


def _day_bounds(day: str | None) -> tuple[str | None, str | None]:
    """YYYY-MM-DD -> (start, end) ISO-Strings. None bei fehlendem Argument."""
    if not day or len(day) != 10:
        return (None, None)
    return (f"{day}T00:00:00", f"{day}T23:59:59")


def list_orders(path: Path, limit: int = 100, day: str | None = None) -> list[dict]:
    """Gibt Bestellungen inkl. Items als Liste von Dicts zurück (neueste zuerst).

    Wenn `day` (YYYY-MM-DD) gesetzt ist, werden nur Bestellungen dieses Tages
    zurückgeliefert.
    """
    since, until = _day_bounds(day)
    with _connect(path) as conn:
        if since:
            cur = conn.execute(
                """SELECT * FROM orders
                   WHERE created_at >= ? AND created_at <= ?
                   ORDER BY created_at DESC LIMIT ?""",
                (since, until, limit),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        orders = [dict(r) for r in cur.fetchall()]
        for o in orders:
            cur2 = conn.execute(
                "SELECT item_id, name, unit_price, deposit, quantity, line_total "
                "FROM order_items WHERE order_id = ? ORDER BY id",
                (o["id"],),
            )
            o["items"] = [dict(r) for r in cur2.fetchall()]
    return orders


def items_sold(path: Path, day: str | None = None) -> dict[str, int]:
    """Mapping item_id -> verkaufte Stückzahl. Optionaler Tagesfilter."""
    since, until = _day_bounds(day)
    with _connect(path) as conn:
        if since:
            rows = conn.execute(
                """SELECT oi.item_id, SUM(oi.quantity) AS qty
                   FROM order_items oi JOIN orders o ON o.id = oi.order_id
                   WHERE o.created_at >= ? AND o.created_at <= ?
                   GROUP BY oi.item_id""",
                (since, until),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT item_id, SUM(quantity) AS qty FROM order_items GROUP BY item_id"
            ).fetchall()
    return {r["item_id"]: int(r["qty"] or 0) for r in rows}


def reset_orders(path: Path) -> dict:
    """Löscht alle Bestellungen + Items aus der DB. Gibt Statistik zurück."""
    with _lock:
        with _connect(path) as conn:
            before = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            conn.execute("DELETE FROM order_items")
            conn.execute("DELETE FROM orders")
    return {"deleted_orders": before}


def available_days(path: Path) -> list[str]:
    """Liste aller Tage (YYYY-MM-DD) an denen mindestens eine Bestellung war,
    neueste zuerst."""
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(created_at, 1, 10) AS day FROM orders "
            "ORDER BY day DESC"
        ).fetchall()
    return [r["day"] for r in rows]


def summary(path: Path, day: str | None = None) -> dict:
    """Aggregierte Auswertung: Gesamtsummen + Top-Artikel. Optional pro Tag."""
    since, until = _day_bounds(day)
    with _connect(path) as conn:
        if since:
            totals_row = conn.execute(
                """SELECT COUNT(*) AS order_count,
                          COALESCE(SUM(subtotal), 0) AS subtotal_sum,
                          COALESCE(SUM(deposit_total), 0) AS deposit_sum,
                          COALESCE(SUM(total), 0) AS total_sum
                   FROM orders WHERE created_at >= ? AND created_at <= ?""",
                (since, until),
            ).fetchone()
            items_rows = conn.execute(
                """SELECT oi.item_id, oi.name,
                          SUM(oi.quantity) AS qty_sum,
                          SUM(oi.line_total) AS revenue
                   FROM order_items oi JOIN orders o ON o.id = oi.order_id
                   WHERE o.created_at >= ? AND o.created_at <= ?
                   GROUP BY oi.item_id, oi.name
                   ORDER BY qty_sum DESC""",
                (since, until),
            ).fetchall()
        else:
            totals_row = conn.execute(
                """SELECT COUNT(*) AS order_count,
                          COALESCE(SUM(subtotal), 0) AS subtotal_sum,
                          COALESCE(SUM(deposit_total), 0) AS deposit_sum,
                          COALESCE(SUM(total), 0) AS total_sum
                   FROM orders"""
            ).fetchone()
            items_rows = conn.execute(
                """SELECT item_id, name,
                          SUM(quantity) AS qty_sum,
                          SUM(line_total) AS revenue
                   FROM order_items
                   GROUP BY item_id, name
                   ORDER BY qty_sum DESC"""
            ).fetchall()
    return {
        "totals": dict(totals_row),
        "items": [dict(r) for r in items_rows],
    }
