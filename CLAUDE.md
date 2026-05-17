# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projekt in einem Satz

Flask-Bonsystem, das offline auf einem Raspberry Pi 5 läuft: Ein Laptop oder Tablet ruft im LAN die Flask-Weboberfläche auf, gibt Bestellungen ein, und die App druckt Token-Bons (einer pro Stück, mit Partial Cut zwischen den Bons) über einen oder mehrere per USB am Pi angeschlossene Munbyn-Thermodrucker.

## Hardware-Kontext (wichtig, nicht aus dem Code ableitbar)

| Gerät | Rolle | Verbindung |
|---|---|---|
| GL.iNet AX1800 (Flint) | Isoliertes LAN + DHCP (**keine Internetverbindung**) | Standard-Gateway `192.168.8.1` |
| Raspberry Pi 5 (8 GB) | Flask-Server + Drucker-Host | LAN-Kabel an Router, DHCP-Reservierung `192.168.8.10`; **USB → Drucker** |
| Munbyn ITPP047P (1–n) | Thermodrucker (80 mm) | **USB-B direkt am Pi** (kein LAN-Port); Kernel-Device `/dev/usb/lp0`, `lp1` …; rohes ESC/POS |
| Hamtysan 7″ | HDMI-Monitor am Pi | Zur Status-/Admin-Anzeige, optional Kiosk |
| Laptop / Tablet | Bedienoberfläche | WLAN oder LAN am Router, Browser öffnet `http://192.168.8.10:8080` |

**Kein Internet** im gesamten Setup. Alle Abhängigkeiten müssen vorab heruntergeladen werden (z. B. über Laptop-Hotspot beim Erst-Setup oder per `pip wheel --no-deps`-Mirror). CDNs im Frontend sind tabu – Assets liegen unter `app/static/`.

Details pro Gerät:
- [docs/network-setup.md](docs/network-setup.md) – Router konfigurieren, DHCP-Reservierungen
- [docs/raspberry-pi-setup.md](docs/raspberry-pi-setup.md) – Pi-OS, Autostart via systemd, Kiosk
- [docs/printer-setup.md](docs/printer-setup.md) – Munbyn ITPP047P USB, udev, Testdruck
- [docs/hardware-setup.md](docs/hardware-setup.md) – Verkabelung und Reihenfolge des Hochfahrens

Offene Aufgaben und Backlog: [docs/backlog.md](docs/backlog.md).

## Architektur

```
Laptop / Tablet (Browser)
   │   HTTP :8080
   ▼
Raspberry Pi 5  ──── Flask (app/)
   │                   │
   │                   ├─ routes/
   │                   │   ├─ menu       /  · /uebersicht · /api/menu · PATCH /api/menu/items/<id>
   │                   │   ├─ orders     POST /api/orders
   │                   │   ├─ printers   GET  /api/printers
   │                   │   ├─ health     GET  /api/health · /api/health/printer[/<id>]
   │                   │   ├─ reports    GET  /api/reports/{orders,summary,inventory,days}
   │                   │   └─ admin      POST /api/admin/reset  (passwortgeschützt)
   │                   ├─ services/
   │                   │   ├─ menu_service     load_menu, find_item, update_item_limits
   │                   │   ├─ order_service    build_order, persist_order (orders.json)
   │                   │   ├─ printer_service  print_order, load_printers, find_printer
   │                   │   └─ db               SQLite-Wrapper, init_db, insert_order,
   │                   │                       list_orders, summary, items_sold,
   │                   │                       available_days, reset_orders,
   │                   │                       maybe_migrate_orders_json
   │                   ├─ templates/  order.html · overview.html · base.html
   │                   └─ static/     css/app.css · js/app.js · js/overview.js · img/
   │
   │   write() auf /dev/usb/lp{0,1,...}  (rohes ESC/POS via Kernel-usblp)
   ▼
Munbyn ITPP047P × n  (USB)
```

Leitlinien, die aus dem Code nicht sofort ersichtlich sind:

- **Zwei parallele Persistenz-Pfade.** Bestellungen werden bei jedem `POST /api/orders` **doppelt** geschrieben: in `data/bonsystem.db` (SQLite, primäre Quelle für Reports/Übersicht) und in `data/orders.json` (Append-Log, Safety-Net falls DB ausfällt). DB-Schreibfehler sind nicht fatal — die Bestellung wird trotzdem gedruckt. Beim ersten Start mit leerer DB importiert die App `orders.json` automatisch in die DB.
- **Multi-Drucker via `data/printers.json`.** Jeder Drucker hat `id`, `name`, `device` (z. B. `/dev/usb/lp0`). UI hat ein Dropdown in der Topbar, der gewählte Drucker wird in `localStorage["bonsystem.printerId"]` gespeichert. Bei unbekannter ID im Payload greift der Default. Wenn `printers.json` fehlt, fällt der Service auf `PRINTER_DEVICE` aus der `.env` zurück.
- **Druckaufträge sind synchron.** `POST /api/orders` baut, persistiert (JSON + DB), druckt und antwortet. Wenn der Drucker offline ist, bekommt der Client HTTP 502 zurück mit `print_error`, die Bestellung ist aber schon persistiert. **Kein Queue/Retry.** Wenn der Druck fehlschlägt, muss aktuell manuell neu gedruckt werden (Storno/Nachdruck steht noch im Backlog).
- **Ein Bon = ein Stück.** `printer_service._render_receipt` expandiert die Items mengenweise (`_expand_tokens`) und druckt pro Stück einen separaten Token-Bon mit Partial Cut (`cut(mode="PART")`) dazwischen, am Ende Full Cut. So kann der Kunde 3× Bier als 3 abreißbare Bons bekommen.
- **ESC/POS direkt ans Kernel-Device.** `python-escpos`'s `File`-Klasse öffnet `/dev/usb/lpN` und schreibt die ESC/POS-Bytes roh hinein. Kein CUPS-Spooler, keine Treiber-Installation. Voraussetzungen auf dem Pi: Kernel-Modul `usblp` (Standard in Raspberry Pi OS) und der Service-User in der Gruppe `lp`. Wenn CUPS installiert ist und sich das Device greift, `sudo systemctl disable --now cups`.
- **Frontend ist serverseitig gerendert + Vanilla-JS.** Kein React/Vue, kein Build-Step. `app.js` macht den Warenkorb auf der Bestellseite + Drucker-Status + Live-Bestand-Polling. `overview.js` macht die Übersichtsseite (Stats, Inventory-Liste, Bestellungstabelle, Limits-Editor, Reset-Dialog).
- **Design folgt `docs/style-guide.md`.** Schwarz/Lauf-Grün-Farbschema, kompakt für Tablet-Bedienung, deutsche UI-Sprache, Farbsystem in CSS-Custom-Properties. Keine Icon-Fonts / CDN-Frameworks. Eine einzige `app.css` für beide Seiten.

## Datenmodell

### `data/menu.json` (Speisekarte + Bestands-Limits)

```jsonc
{
  "version": 4,
  "currency": "EUR",
  "event": { "name": "...", "organizer": "...", "logo": "laufnacht-logo.png" },
  "categories": [
    {
      "id": "getraenke",
      "name": "Getränke",
      "items": [
        // price = Verkaufspreis; deposit = optionaler Pfand (zählt in line_total und total)
        // critical = absolute Obergrenze, ab dem die Karte ORANGE wird (Druck bleibt möglich)
        // warn = Restbestand-Schwelle; ab diesem Punkt wird die Karte GELB
        { "id": "...", "name": "...", "price": 3.00, "deposit": 2.00, "critical": 50, "warn": 12 }
      ]
    }
  ]
}
```

`event.logo` wird relativ zu `app/static/img/` aufgelöst und auf jeden Token-Bon gedruckt (siehe `printer_service._resolve_logo_path`). Gratis-Artikel (Sponsoren-Bons) haben `price: 0` und keinen `deposit` — der Bon zeigt dann „GRATIS" statt eines Preises.

### `data/printers.json`

```jsonc
{
  "default": "drucker_1",
  "printers": [
    { "id": "drucker_1", "name": "Drucker_1", "device": "/dev/usb/lp0" }
  ]
}
```

Wenn die Datei fehlt: Fallback auf `PRINTER_DEVICE` aus `.env` (ein einzelner Default-Drucker).

### SQLite-Schema (`data/bonsystem.db`)

```sql
orders(id TEXT PK, created_at TEXT, currency TEXT,
       subtotal REAL, deposit_total REAL, total REAL,
       tendered REAL, change_due REAL,
       printer_id TEXT, printer_name TEXT)

order_items(id INT PK AUTO, order_id TEXT FK→orders.id ON DELETE CASCADE,
            item_id TEXT, name TEXT,
            unit_price REAL, deposit REAL, quantity INT, line_total REAL)

INDEX idx_orders_created_at ON orders(created_at)
INDEX idx_order_items_order_id ON order_items(order_id)
```

Schema-Init bei jedem App-Start in `db.init_db()` (idempotent).

## API-Übersicht

| Method | Pfad | Was |
|---|---|---|
| GET | `/` | Bestellseite (Speisekarte + Warenkorb) |
| GET | `/uebersicht` | Übersichtsseite (Bestand + Bestellungen + Reset) |
| GET | `/api/menu` | Speisekarte als JSON |
| PATCH | `/api/menu/items/<id>` | Limits ändern: Body `{"critical": int, "warn": int}` |
| POST | `/api/orders` | Bestellung anlegen + drucken. Body: `{items, tendered?, printer_id?}` |
| GET | `/api/printers` | Drucker-Liste + Default |
| GET | `/api/health` | App-Health |
| GET | `/api/health/printer[/<id>]` | Drucker-Health (Default oder spezifisch) |
| GET | `/api/reports/orders?limit=&day=` | Bestellungen mit Items |
| GET | `/api/reports/summary?day=` | Gesamtsummen + Top-Artikel |
| GET | `/api/reports/inventory` | Bestand pro Artikel mit Status `ok`/`warn`/`critical` |
| GET | `/api/reports/days` | Tage mit Bestellungen (YYYY-MM-DD) |
| POST | `/api/admin/reset` | DB leeren. Body `{"password": "..."}`. 401 bei Falsch, 503 wenn `ADMIN_PASSWORD` leer |

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
curl http://192.168.8.10:8080/api/health/printer/drucker_2

# Welches USB-Device ist welcher Drucker?
lsusb
ls -l /dev/usb/

# Reports auslesen
curl http://192.168.8.10:8080/api/reports/summary | python3 -m json.tool
curl 'http://192.168.8.10:8080/api/reports/orders?limit=500' > tagesabschluss.json

# DB-Reset (Passwort aus .env)
curl -X POST http://192.168.8.10:8080/api/admin/reset \
     -H 'Content-Type: application/json' \
     -d '{"password":"…"}'
```

## Deployment

### Vom Laptop auf den Pi syncen + Service neu starten

```bash
./scripts/deploy.sh                  # Default-Ziel pi@192.168.178.10 (Heimnetz)
./scripts/deploy.sh 192.168.8.10     # Produktiv-Pi im GL.iNet
SKIP_RESTART=1 ./scripts/deploy.sh   # nur syncen
```

Der `rsync` excludet `.venv/`, `.git/`, `__pycache__/`, `data/orders.json`, `.env` und `*.db*`. Heißt: lokale Daten (DB, Backup-JSONs, Env-Konfiguration) am Pi bleiben unberührt.

### Erst-Installation am Pi

```bash
sudo cp scripts/bonsystem.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bonsystem
sudo systemctl status bonsystem
journalctl -u bonsystem -f
```

Die Unit geht davon aus, dass das Repo unter `/home/pi/rto_bonsystem` liegt und das Venv unter `.venv/` existiert. Sie nutzt `SupplementaryGroups=lp`, damit der Service-User Schreibzugriff auf `/dev/usb/lp*` bekommt, ohne root zu sein. Außerdem braucht der Pi-User eine passwortfreie sudo-Regel für `systemctl restart bonsystem`, damit `deploy.sh` ohne Passwortfrage durchläuft — siehe `docs/raspberry-pi-setup.md`.

## Konfiguration

Einstellungen kommen ausschließlich aus Umgebungsvariablen (siehe `.env.example`). `app/config.py` ist der einzige Ort, an dem Umgebungsvariablen gelesen werden – neue Konfigwerte dort ergänzen, nicht verstreut `os.environ` einführen.

Aktuelle Variablen:
| Variable | Default | Zweck |
|---|---|---|
| `FLASK_SECRET_KEY` | `dev-secret-change-me` | Flask-Session-Schlüssel |
| `PRINTER_DEVICE` | `/dev/usb/lp0` | Fallback wenn `printers.json` fehlt |
| `HTTP_HOST` | `0.0.0.0` | Bind-Adresse |
| `HTTP_PORT` | `8080` | Port |
| `ADMIN_PASSWORD` | `""` (leer) | Passwort für DB-Reset; leer = Reset-Endpoint deaktiviert |

Datendateien (in `data/`):
| Datei | Zweck | Gitignored |
|---|---|---|
| `menu.json` | Speisekarte + Limits | nein (Quelldatei) |
| `printers.json` | Drucker-Konfiguration | nein |
| `orders.json` | Append-Log aller Bestellungen | **ja** |
| `bonsystem.db` | SQLite-Persistierung | **ja** (`*.db`) |
| `orders.json.bak.*` | Backup nach Reset | **ja** |

## Offene Design-Entscheidungen

Diese Punkte sind bewusst noch nicht festgelegt. Wenn die Arbeit in diese Richtung geht, vorher mit dem Nutzer abstimmen:

1. **Touchbedienung auf dem Pi-Monitor** – aktuell Tablet oder Laptop als Client. Falls der Hamtysan-Monitor Touch unterstützt und am Pi direkt bedient werden soll, wird Chromium-Kiosk-Mode nötig (siehe `docs/raspberry-pi-setup.md`).
2. **Auto-Split nach Kategorie auf mehrere Drucker** – Multi-Drucker existiert technisch, aber `print_order` druckt aktuell immer den ganzen Auftrag auf den einen ausgewählten Drucker. Wenn Küche-vs-Theke-Trennung gewünscht: per Kategorie filtern und auf zwei verschiedene Drucker schicken.
3. **Authentifizierung** – außer dem Admin-Passwort für den Reset keine. LAN ist physisch isoliert. Wenn mehrere Bediener mit eigener Identität sichtbar sein sollen: Sitzung/Login erst dann einführen.
4. **Stornos / Nachdruck** – nicht implementiert. Orders sind unveränderlich in DB + JSON. Skizze: neue Route `POST /api/orders/<id>/reprint`, die per ID nochmal `print_order()` aufruft.

## Arbeits-Konventionen für dieses Repo

- **Sprache des UI und der Bons: Deutsch.** Quellcode-Identifier bleiben englisch.
- **Abhängigkeiten minimal halten.** Pi hat offline kein `pip install`. Jede neue Dependency = Aufwand beim Deployen. Vor dem Hinzufügen fragen.
- **Keine CDN-Links in Templates.** Assets immer unter `app/static/`.
- **Der Drucker ist die einzige externe Integration.** Fehler von dort werden nicht geschluckt – sie müssen der Bedienung angezeigt werden.
- **DB-Schreiben darf den Druck nicht blockieren.** Wenn die SQLite-DB schreibfehler hat, wird das nur geloggt; `orders.json` ist das Safety-Net.
- **Limits sind Information, kein Block.** `critical`/`warn` färben die UI, verhindern aber **nicht** den Druck — auch Bestellungen über dem kritischen Wert gehen durch.
