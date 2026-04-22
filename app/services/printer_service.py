from __future__ import annotations

import logging
from pathlib import Path

from escpos.printer import File


log = logging.getLogger(__name__)


class PrinterError(RuntimeError):
    """Raised when a receipt cannot be printed."""


def print_order(order: dict, *, device: str) -> None:
    """Schreibt den Bon als rohes ESC/POS an das Kernel-Device (/dev/usb/lp0)."""
    if not Path(device).exists():
        raise PrinterError(
            f"Drucker-Gerät {device} nicht vorhanden. "
            "Ist der Drucker per USB angeschlossen und eingeschaltet?"
        )

    try:
        printer = File(device)
    except Exception as exc:
        raise PrinterError(f"Drucker-Gerät konnte nicht geöffnet werden ({device}): {exc}") from exc

    try:
        _render_receipt(printer, order)
    except Exception as exc:
        raise PrinterError(f"Fehler beim Drucken: {exc}") from exc
    finally:
        try:
            printer.close()
        except Exception:
            log.debug("printer.close() failed", exc_info=True)


def _render_receipt(printer, order: dict) -> None:
    currency = order.get("currency", "EUR")

    printer.set(align="center", bold=True, double_height=True, double_width=True)
    printer.text("BESTELLUNG\n")
    printer.set(align="center", bold=False, double_height=False, double_width=False)
    printer.text(f"Bon {order['id']}\n")
    printer.text(f"{order['created_at']}\n")
    printer.text("-" * 32 + "\n")

    printer.set(align="left")
    for line in order["items"]:
        qty = line["quantity"]
        name = line["name"]
        line_total = f"{line['line_total']:.2f} {currency}"
        printer.text(f"{qty:>2}x {name}\n")
        printer.text(f"     {line_total:>26}\n")

    printer.text("-" * 32 + "\n")
    printer.set(align="right", bold=True)
    printer.text(f"Summe: {order['total']:.2f} {currency}\n")

    if order.get("note"):
        printer.set(align="left", bold=False)
        printer.text("\nNotiz:\n")
        printer.text(order["note"] + "\n")

    printer.text("\n\n")
    printer.cut()
