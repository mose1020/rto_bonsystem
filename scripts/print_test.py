#!/usr/bin/env python3
"""Druckt einen Testbon an den Munbyn ITPP047P über USB.

Benutzung:
    python scripts/print_test.py
    PRINTER_DEVICE=/dev/usb/lp1 python scripts/print_test.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from escpos.printer import File


def main() -> int:
    device = os.environ.get("PRINTER_DEVICE", "/dev/usb/lp0")

    if not Path(device).exists():
        print(f"Fehler: {device} existiert nicht.", file=sys.stderr)
        print("Prüfen: Drucker eingeschaltet? USB-Kabel am Pi? 'ls /dev/usb/'", file=sys.stderr)
        return 1

    print(f"Drucke auf {device} …")
    printer = File(device)
    try:
        printer.set(align="center", bold=True, double_height=True, double_width=True)
        printer.text("TESTBON\n")
        printer.set(bold=False, double_height=False, double_width=False)
        printer.text("Drucker erreichbar.\n")
        printer.text("\n\n")
        printer.cut()
    finally:
        printer.close()
    print("Fertig.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
