# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projekt in einem Satz

Flask-Bonsystem, das offline auf einem Raspberry Pi 5 läuft: Ein Laptop ruft im LAN die Flask-Weboberfläche auf, gibt Bestellungen ein, und die App druckt den Bon über einen per USB am Pi angeschlossenen Munbyn-Thermodrucker.

## Hardware-Kontext (wichtig, nicht aus dem Code ableitbar)

| Gerät | Rolle | Verbindung |
|---|---|---|
| GL.iNet AX1800 (Flint) | Isoliertes LAN + DHCP (**keine Internetverbindung**) | Standard-Gateway `192.168.8.1` |
| Raspberry Pi 5 (8 GB) | Flask-Server + Drucker-Host | LAN-Kabel an Router, DHCP-Reservierung `192.168.8.10`; **USB → Drucker** |
| Munbyn ITPP047P | Thermodrucker (80 mm) | **USB-B direkt am Pi** (kein LAN-Port vorhanden); Kernel-Device `/dev/usb/lp0`, rohes ESC/POS |
| Hamtysan 7″ | HDMI-Monitor am Pi | Zur Status-/Admin-Anzeige, optional Kiosk |
| Laptop | Bedienoberfläche | WLAN oder LAN am Router, Browser öffnet `http://192.168.8.10:8080` |

**Kein Internet** im gesamten Setup. Alle Abhängigkeiten müssen vorab heruntergeladen werden (z. B. über Laptop-Hotspot beim Erst-Setup oder per `pip wheel --no-deps`-Mirror). CDNs im Frontend sind tabu – Assets liegen unter `app/static/`.

Details pro Gerät:
- [docs/network-setup.md](docs/network-setup.md) – Router konfigurieren, DHCP-Reservierungen
- [docs/raspberry-pi-setup.md](docs/raspberry-pi-setup.md) – Pi-OS, Autostart via systemd, Kiosk
- [docs/printer-setup.md](docs/printer-setup.md) – Munbyn ITPP047P Selbsttest, IP, Testdruck
- [docs/hardware-setup.md](docs/hardware-setup.md) – Verkabelung und Reihenfolge des Hochfahrens

## Architektur

```
Laptop (Browser)
   │   HTTP :8080
   ▼
Raspberry Pi 5  ──── Flask (app/)
   │                   │
   │                   ├─ routes/       Blueprints: menu, orders, health
   │                   ├─ services/     menu_service, order_service, printer_service
   │                   └─ templates/    Server-seitiges HTML, kein JS-Framework
   │
   │   write() auf /dev/usb/lp0  (rohes ESC/POS via Kernel-usblp)
   ▼
Munbyn ITPP047P (USB)
```

Leitlinien, die aus dem Code nicht sofort ersichtlich sind:

- **Persistenz heute = JSON-Dateien.** `data/menu.json` ist die Quelle der Speisekarte, `data/orders.json` wird beim ersten Bestellen angelegt. Kein SQL, keine ORM-Schicht. Wenn Reporting/Multi-User-Auswertungen nötig werden: auf SQLite umstellen – Einstiegspunkte sind `app/services/order_service.py` und `app/services/menu_service.py`.
- **Druckaufträge sind synchron.** `POST /api/orders` baut, persistiert, druckt und antwortet. Wenn der Drucker offline ist, bekommt der Client HTTP 502 zurück mit `print_error`, die Bestellung ist aber in `orders.json` bereits gespeichert. **Wichtig:** Kein Queue/Retry. Wenn der Druck fehlschlägt, muss manuell neu gedruckt werden (Feature „Nachdruck“ ist noch nicht vorhanden).
- **ESC/POS direkt ans Kernel-Device.** `python-escpos`'s `File`-Klasse öffnet `/dev/usb/lp0` und schreibt die ESC/POS-Bytes roh hinein. Kein CUPS-Spooler, keine Treiber-Installation. Voraussetzungen auf dem Pi: Kernel-Modul `usblp` (Standard in Raspberry Pi OS) und der Service-User in der Gruppe `lp`. Wenn CUPS installiert ist und sich das Device greift, `sudo systemctl disable --now cups`.
- **Frontend ist serverseitig gerendert + Vanilla-JS.** Kein React/Vue, kein Build-Step. Ein einziges `app.js` manipuliert den Warenkorb im Browser und `fetch`-t `/api/orders`. So bleibt das Deployment trivial und funktioniert offline ohne Node-Toolchain.
- **Design folgt `docs/style-guide.md`.** Touch-Targets ≥ 56 px, deutsche UI-Sprache, Farbsystem in CSS-Custom-Properties. Keine Icon-Fonts / CDN-Frameworks.

## Häufige Befehle

Alle Befehle laufen aus dem Repo-Root.

```bash
# Erst-Setup auf dem Raspberry Pi
./scripts/install-pi.sh

# Lokal (Entwickler-Laptop) entwickeln
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env      # ohne Drucker läuft die App; /api/orders gibt 502 zurück
python -m app.wsgi        # http://localhost:8080

# Flask-Debug-Modus
FLASK_APP=app.wsgi:app FLASK_DEBUG=1 flask run -h 0.0.0.0 -p 8080

# Tests
pytest                    # alle Tests
pytest tests/test_order_service.py::test_build_order_sums_correctly  # einzelner Test

# Lint
ruff check .
ruff format .

# Drucker-Sanity-Check (druckt einen Testbon, nur am Pi mit angeschlossenem Drucker)
python scripts/print_test.py
PRINTER_DEVICE=/dev/usb/lp1 python scripts/print_test.py    # falls anderes Device

# Druckererreichbarkeit prüfen, ohne zu drucken
curl http://192.168.8.10:8080/api/health/printer

# Welches USB-Device ist der Drucker?
lsusb
ls -l /dev/usb/
```

## Deployment auf dem Pi (systemd)

```bash
sudo cp scripts/bonsystem.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bonsystem
sudo systemctl status bonsystem
journalctl -u bonsystem -f
```

Die Unit geht davon aus, dass das Repo unter `/home/pi/rto_bonsystem` liegt und das Venv unter `.venv/` existiert. Beim Verschieben: `scripts/bonsystem.service` anpassen. Die Unit nutzt `SupplementaryGroups=lp`, damit der Service-User Schreibzugriff auf `/dev/usb/lp0` bekommt, ohne root zu sein.

## Konfiguration

Einstellungen kommen ausschließlich aus Umgebungsvariablen (siehe `.env.example`). `app/config.py` ist der einzige Ort, an dem Umgebungsvariablen gelesen werden – neue Konfigwerte dort ergänzen, nicht verstreut `os.environ` einführen.

## Offene Design-Entscheidungen

Diese Punkte sind bewusst noch nicht festgelegt. Wenn die Arbeit in diese Richtung geht, vorher mit dem Nutzer abstimmen:

1. **Touchbedienung auf dem Pi-Monitor** – aktuell nur Laptop als Client. Falls der Hamtysan-Monitor Touch unterstützt und am Pi direkt bedient werden soll, wird Chromium-Kiosk-Mode nötig (siehe `docs/raspberry-pi-setup.md`).
2. **Küchen-/Theken-Trennung** – ein Drucker, ein Bon. Falls später zwei Drucker (z. B. Küche vs. Bar) nötig werden: `printer_service.print_order` muss Kategorien splitten.
3. **Authentifizierung** – keine. LAN ist physisch isoliert. Wenn mehrere Bediener sichtbar sein sollen: Sitzung/Login erst dann einführen.
4. **Stornos / Nachdruck** – nicht implementiert. Orders sind append-only in JSON.

## Arbeits-Konventionen für dieses Repo

- **Sprache des UI und der Bons: Deutsch.** Quellcode-Identifier bleiben englisch.
- **Abhängigkeiten minimal halten.** Pi hat offline kein `pip install`. Jede neue Dependency = Aufwand beim Deployen. Vor dem Hinzufügen fragen.
- **Keine CDN-Links in Templates.** Assets immer unter `app/static/`.
- **Der Drucker ist die einzige externe Integration.** Fehler von dort werden nicht geschluckt – sie müssen der Bedienung angezeigt werden.
