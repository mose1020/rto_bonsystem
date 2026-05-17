# Offene Punkte / Backlog

Lebende Liste mit konkreten Aufgaben, die noch anstehen. Reihenfolge ≈ Priorität.

## Priorität 1 – Blockiert Produktivnutzung

### Umzug des Pi auf das GL.iNet-Netz
- **Status:** offen – Pi läuft aktuell im Heimnetz (192.168.178.10)
- **Schritte:**
  1. Pi herunterfahren, LAN-Kabel vom Heimrouter ziehen und in den GL.iNet-Router (LAN-Port, nicht WAN).
  2. Pi einschalten.
  3. Laptop ins GL.iNet-WLAN wechseln.
  4. GL.iNet-Admin (`http://192.168.8.1`) → Clients → `bonsystem-pi` → Adresse reservieren auf `192.168.8.10`.
  5. Pi rebooten (`sudo reboot`), Verifikation: `ssh pi@192.168.8.10`, `hostname -I` → `192.168.8.10`.
  6. Browser vom Laptop: `http://192.168.8.10:8080`.

### WAN am GL.iNet trennen
- **Status:** offen – WAN hängt aktuell am Heimrouter, damit der Pi beim Setup Internet hatte
- **Beschreibung:** Nach erfolgreichem Umzug + installiertem System Kabel aus dem WAN-Port des GL.iNet ziehen, damit das Produktiv-Netz wirklich offline ist.
- **Wiederherstellen:** Wenn später Updates nötig sind, einfach wieder einstecken, `sudo apt upgrade && pip install -U -r requirements.txt`, dann wieder abziehen.

### `ADMIN_PASSWORD` auf dem Pi setzen
- **Status:** offen – `.env` wird vom `deploy.sh` nicht überschrieben, muss manuell auf dem Pi gepflegt werden.
- **Befehl:**
  ```bash
  ssh pi@192.168.178.10
  # in /home/pi/rto_bonsystem/.env das Feld ADMIN_PASSWORD setzen
  sudo systemctl restart bonsystem
  ```
- **Bemerkung:** Solange leer, ist der DB-Reset-Button auf der Übersichtsseite deaktiviert (`/api/admin/reset` antwortet 503).

## Priorität 2 – Inhaltlich

### Maximalwerte für die echte Veranstaltung anpassen
- **Status:** offen – `data/menu.json` hat Default-Werte für `critical`/`warn` pro Artikel.
- **Vorgehen:**
  - direkt auf der Übersichtsseite via `✎`-Button pro Artikel (speichert per `PATCH /api/menu/items/<id>`)
  - oder `data/menu.json` editieren + `./scripts/deploy.sh`

### Stabile USB-Device-Namen via udev (bei Multi-Drucker)
- **Status:** offen – Linux nummeriert `/dev/usb/lp0`, `lp1` … in Anschluss-Reihenfolge, nicht stabil über Reboots.
- **Lösung:** udev-Rule legen, die abhängig von USB-Seriennummer einen symbolischen Link unter `/dev/bonsystem/drucker_1`, `drucker_2` … erzeugt. Diese Symlinks dann in `data/printers.json::device`.
- **Erst nötig wenn der zweite Drucker physisch angeschlossen ist** – mit nur einem Drucker bleibt `lp0` stabil.

### Auto-Split nach Kategorie auf mehrere Drucker
- **Status:** nicht implementiert. Multi-Drucker existiert, aber `print_order` druckt aktuell den ganzen Auftrag auf den gewählten Drucker.
- **Skizze:** in `printer_service.print_order` Token-Liste nach `category` partitionieren und pro Kategorie einen Drucker wählen (Mapping in `printers.json`).

### Storno / Nachdruck
- **Status:** nicht implementiert
- **Beschreibung:** Falls ein Druck fehlschlägt, ist die Bestellung in DB + `orders.json` persistiert, aber kein UI-Pfad zum erneuten Drucken.
- **Skizze:** neue Route `POST /api/orders/<id>/reprint` die `print_order()` mit persistierter Order nochmal aufruft. UI-Button in der Bestellungstabelle auf der Übersichtsseite.

## Priorität 3 – Nice to have

### Perforiertes / vorperforiertes Thermopapier
- **Status:** im Code teilweise umgesetzt
- **Was implementiert ist:** Partial Cut (`printer.cut(mode="PART")`) zwischen den Token-Bons, Full Cut am Ende. Damit hängen die Bons zusammen und lassen sich abreißen.
- **Offen:** Testen ob der Munbyn-Auto-Cutter zuverlässig partial cuttet, bei hoher Druckfrequenz nicht überhitzt.

### Kiosk-Modus auf dem Hamtysan-Monitor
- **Status:** optional, aus `docs/raspberry-pi-setup.md` Abschnitt 6 bekannt
- **Wann relevant:** wenn am Pi direkt bedient werden soll (Touch?) oder Status angezeigt

### Auth / Bediener-Login
- **Status:** bewusst weggelassen, LAN ist isoliert
- **Aktueller Stand:** Nur das Admin-Passwort schützt den DB-Reset. Alles andere ist offen für jeden im LAN.

### Tages-Reports / Export
- **Status:** API existiert (`/api/reports/orders`, `/api/reports/summary`), aber kein UI für Filter nach Zeitraum oder CSV-Export.
- **Skizze:** Übersichtsseite um „Export"-Button erweitern, der `/api/reports/orders?limit=…&day=…` aufruft und CSV anbietet.

## Erledigt (Archiv)

- [x] Hardware-Setup (Router, Pi, Drucker) dokumentiert
- [x] Flask-Skeleton mit Bestellung + Druck
- [x] Umstellung Drucker von Netzwerk auf USB (`python-escpos.File`)
- [x] systemd-Autostart
- [x] Erster erfolgreicher Testbon aus der App
- [x] `scripts/deploy.sh` für Sync + Service-Restart
- [x] Bon-Formatierung mit Logo (Ortenauer Laufnacht), Token-Druck pro Stück, Footer mit Bestellnummer + Datum, einheitlicher Preisblock für ohne/mit Pfand/gratis
- [x] Echte Speisekarte aus `Speisekarte_2026.pdf` eingebaut, inkl. Aperol-Volumen-Korrektur und Bunter Salatteller
- [x] Sponsoren-Bons als Gratis-Kategorie (Essen / Getränk / Kaffee oder Kuchen)
- [x] Pfand wird sauber ausgewiesen (in Cart, Order, Bon, DB)
- [x] „Gegeben"-Block mit Schein-Buttons + Custom-Input + Rückgeld-Berechnung statt der Notiz-Textarea
- [x] SQLite-Persistierung (`data/bonsystem.db`) mit automatischer Migration aus `orders.json` beim ersten Start
- [x] Reports-API (`/api/reports/orders`, `/summary`, `/inventory`)
- [x] Übersichtsseite mit Stats, Bestand (sortiert nach Auslastung), letzte Bestellungen
- [x] Bestands-Limits (`critical`, `warn`) pro Artikel, inline-Editor in der UI
- [x] Multi-Drucker-Konfiguration über `data/printers.json`, Drucker-Dropdown in der Topbar mit localStorage-Persistierung
- [x] DB-Reset auf der Übersichtsseite, passwortgeschützt über `ADMIN_PASSWORD` aus `.env`
