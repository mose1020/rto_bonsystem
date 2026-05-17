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
    tokens = _expand_tokens(order["items"])
    total_tokens = len(tokens)

    for idx, token in enumerate(tokens, start=1):
        _render_token(printer, order, token, idx, total_tokens, currency)
        if idx < total_tokens:
            printer.cut(mode="PART")
        else:
            printer.cut()


def _expand_tokens(items: list[dict]) -> list[dict]:
    tokens: list[dict] = []
    for line in items:
        qty = int(line["quantity"])
        unit_price = float(line.get("unit_price", line["line_total"] / qty))
        deposit = float(line.get("deposit", 0.0))
        for _ in range(qty):
            tokens.append({
                "name": line["name"],
                "unit_price": unit_price,
                "deposit": deposit,
            })
    return tokens


def _render_token(printer, order: dict, token: dict, idx: int, total: int, currency: str) -> None:
    printer.set(align="center", bold=True, double_height=True, double_width=True)
    printer.text("BESTELLUNG\n")
    printer.set(align="center", bold=False, double_height=False, double_width=False)
    printer.text(f"Bon {order['id']}\n")
    printer.text(f"Pos {idx}/{total}\n")
    printer.text(f"{order['created_at']}\n")
    printer.text("-" * 32 + "\n")

    printer.set(align="center", bold=True, double_height=True, double_width=True)
    printer.text(f"{token['name']}\n")
    printer.set(align="center", bold=False, double_height=False, double_width=False)

    if token["deposit"] > 0:
        printer.text(f"{token['unit_price']:.2f} {currency}\n")
        printer.text(f"+ {token['deposit']:.2f} {currency} Pfand\n")
        printer.text("-" * 16 + "\n")
        printer.set(align="center", bold=True)
        printer.text(f"{token['unit_price'] + token['deposit']:.2f} {currency}\n")
        printer.set(bold=False)
    else:
        printer.text(f"{token['unit_price']:.2f} {currency}\n")

    printer.text("-" * 32 + "\n")
    printer.text("\n\n")
