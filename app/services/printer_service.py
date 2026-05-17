from __future__ import annotations

import logging
import textwrap
from datetime import datetime
from pathlib import Path

from escpos.printer import File


log = logging.getLogger(__name__)

WIDTH = 32  # Zeichen pro Zeile bei 80mm, normaler Schrift


class PrinterError(RuntimeError):
    """Raised when a receipt cannot be printed."""


def print_order(order: dict, *, device: str, event: dict | None = None) -> None:
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
        _render_receipt(printer, order, event or {})
    except Exception as exc:
        raise PrinterError(f"Fehler beim Drucken: {exc}") from exc
    finally:
        try:
            printer.close()
        except Exception:
            log.debug("printer.close() failed", exc_info=True)


def _render_receipt(printer, order: dict, event: dict) -> None:
    currency = order.get("currency", "EUR")
    tokens = _expand_tokens(order["items"])
    total_tokens = len(tokens)

    for idx, token in enumerate(tokens, start=1):
        _render_token(printer, order, event, token, idx, total_tokens, currency)
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


def _format_created_at(created_at: str) -> str:
    """ISO 'YYYY-MM-DDTHH:MM:SS' -> 'DD.MM.YYYY  HH:MM'."""
    try:
        dt = datetime.fromisoformat(created_at)
        return dt.strftime("%d.%m.%Y  %H:%M")
    except (TypeError, ValueError):
        return created_at


def _render_token(printer, order: dict, event: dict, token: dict,
                  idx: int, total: int, currency: str) -> None:
    event_name = (event.get("name") or "BESTELLUNG").upper()
    organizer = event.get("organizer") or ""
    logo_path = _resolve_logo_path(event.get("logo"))

    # ── Kopf: Logo (Fallback: Text) + Organizer ────────────────────────
    if logo_path is not None:
        try:
            printer.set(align="center")
            printer.image(str(logo_path), center=True, impl="bitImageRaster")
        except Exception:
            log.warning("Logo-Druck fehlgeschlagen, fallback auf Text", exc_info=True)
            _print_text_event_name(printer, event_name)
    else:
        _print_text_event_name(printer, event_name)
    if organizer:
        printer.set(align="center", bold=False, double_height=False, double_width=False)
        printer.text(f"{organizer}\n")

    # ── Pos i/N nur bei Mehr-Token-Bestellungen ─────────────────────────
    if total > 1:
        printer.set(align="center", bold=False)
        printer.text(f"Pos {idx}/{total}\n")

    printer.text("\n")

    # ── Artikelname (größte Schrift: doppelt hoch + doppelt breit) ─────
    printer.set(align="center", bold=True, double_height=True, double_width=True)
    name_width = WIDTH // 2  # double_width halbiert die Zeichen pro Zeile
    for line in textwrap.wrap(token["name"], width=name_width, break_long_words=False) or [token["name"]]:
        printer.text(line + "\n")
    printer.set(align="center", bold=False, double_height=False, double_width=False)

    # ── Preisblock (einheitlich, zweispaltig wenn Pfand) ───────────────
    printer.text("\n")

    if token["deposit"] > 0:
        # Aufschlüsselung in der gleichen Schriftgröße wie der Endwert (doppelt hoch).
        printer.set(align="left", bold=False, double_height=True, double_width=False)
        printer.text(_two_col("Preis", f"{token['unit_price']:.2f} {currency}") + "\n")
        printer.text(_two_col("Pfand", f"+{token['deposit']:.2f} {currency}") + "\n")
        printer.set(align="right", bold=False, double_height=False, double_width=False)
        printer.text("-" * 14 + "\n")

    # Hauptwert: rechtsbündig, doppelt hoch, fett (gleich groß wie Aufschlüsselung).
    total_for_token = token["unit_price"] + token["deposit"]
    printer.set(align="right", bold=True, double_height=True, double_width=False)
    if total_for_token == 0:
        printer.text("GRATIS\n")
    else:
        printer.text(f"{total_for_token:.2f} {currency}\n")
    printer.set(align="left", bold=False, double_height=False, double_width=False)


def _resolve_logo_path(logo_filename: str | None) -> Path | None:
    """Logo liegt unter app/static/img/<filename>. Gibt None zurück wenn Datei fehlt."""
    if not logo_filename:
        return None
    candidate = Path(__file__).resolve().parent.parent / "static" / "img" / logo_filename
    return candidate if candidate.is_file() else None


def _print_text_event_name(printer, event_name: str) -> None:
    printer.set(align="center", bold=True, double_height=True, double_width=True)
    printer.text(f"{event_name}\n")
    printer.set(align="center", bold=False, double_height=False, double_width=False)


def _two_col(left: str, right: str, width: int = WIDTH) -> str:
    """Linker Text links, rechter Text rechtsbündig, abgeschnitten falls zu lang."""
    space = width - len(left) - len(right)
    if space < 1:
        # Im Notfall rechts kürzen
        left = left[: max(0, width - len(right) - 1)]
        space = width - len(left) - len(right)
    return f"{left}{' ' * max(1, space)}{right}"
