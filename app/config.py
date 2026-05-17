from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    SECRET_KEY: str = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

    # Thermodrucker: hängt per USB am Pi. Kernel-Treiber usblp legt
    # /dev/usb/lp0 an. Falls mehrere Drucker/USB-Devices existieren,
    # kann es lp1, lp2 ... sein – dann PRINTER_DEVICE in .env setzen.
    PRINTER_DEVICE: str = os.environ.get("PRINTER_DEVICE", "/dev/usb/lp0")

    HTTP_HOST: str = os.environ.get("HTTP_HOST", "0.0.0.0")
    HTTP_PORT: int = int(os.environ.get("HTTP_PORT", "8080"))

    # Passwort für administrative Aktionen (DB-Reset). Wenn leer, ist
    # der Reset-Endpoint deaktiviert.
    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "")

    MENU_PATH: Path = REPO_ROOT / "data" / "menu.json"
    ORDERS_PATH: Path = REPO_ROOT / "data" / "orders.json"
    PRINTERS_PATH: Path = REPO_ROOT / "data" / "printers.json"
    DB_PATH: Path = REPO_ROOT / "data" / "bonsystem.db"
