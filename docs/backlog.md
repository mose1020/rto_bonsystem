# Offene Punkte / Backlog

Lebende Liste mit konkreten Aufgaben, die noch anstehen. Reihenfolge ≈ Priorität.

## Priorität 1 – Blockiert Produktivnutzung

### Bon-Formatierung verbessern
- **Status:** offen, Details folgen in nächster Session
- **Beschreibung:** Das aktuelle Layout passt noch nicht. Konkrete Kritikpunkte kommen vom Nutzer (Foto/Beschreibung).
- **Einstiegspunkt im Code:** `app/services/printer_service.py::_render_receipt`
- **Relevante Regeln:** `docs/style-guide.md` Abschnitt „Bon-Layout (Thermodruck)"
- **Typische Stellschrauben:**
  - Codepage bei Umlauten (`printer.charcode("CP858")` oder `"CP437"` o. ä.)
  - Zeilenbreite (32 Zeichen auf 80 mm)
  - Anordnung Name/Preis (aktuell in zwei Zeilen, evtl. besser in einer)
  - Kopf-/Fußbereich (Größe, Leerzeilen vor Cut)

### Umzug des Pi auf das GL.iNet-Netz
- **Status:** offen – Pi läuft aktuell im Heimnetz (192.168.178.99)
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

## Priorität 2 – Inhaltlich

### Speisekarte auf echte Artikel umstellen
- **Status:** offen – aktuelle `data/menu.json` enthält Beispielartikel (Bier, Bratwurst, …)
- **Datei:** `data/menu.json`
- **Format:** `categories[].items[] = {id, name, price}`, Preise als Dezimalzahl in EUR
- **Bedenken:** `id` ist Schlüssel; wenn eine Bestellung auf eine alte `id` verweist, bleibt sie in `orders.json`. Also besser `id`s stabil halten.

### Deployment/Update-Workflow dokumentieren
- **Status:** ad-hoc noch nicht festgehalten
- **Aktueller Ablauf:**
  1. Änderung in WSL (`/home/smoser/rto_bonsystem`)
  2. `rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='.git' /home/smoser/rto_bonsystem/ pi@<pi-ip>:/home/pi/rto_bonsystem/`
  3. Auf dem Pi: `sudo systemctl restart bonsystem`
- **TODO:** als Shortcut-Skript `scripts/deploy.sh` ablegen (nimmt Ziel-IP als Argument)

### Datenbank statt JSON – Verkaufszahlen mit Zeitstempel tracken
- **Status:** offen – heute werden Bestellungen append-only in `data/orders.json` geschrieben, jeder Eintrag enthält `created_at`.
- **Motivation:** Reports erstellen („Wie viel Bier in welcher Stunde?"), Tages-/Event-Abrechnung, ggf. Live-Dashboard.
- **Vorschlag:** SQLite (eingebaut in Python, keine extra Abhängigkeit, läuft offline), eine Tabelle `orders` (Header) + `order_items` (Positionen) + optional `events` (Datum, Name) zum Gruppieren mehrerer Events.
- **Einstiegspunkte im Code:**
  - `app/services/order_service.py::persist_order` – Schreibpfad
  - `app/services/order_service.py` (neu: `list_orders(from, to)`, Aggregation pro Artikel/Stunde)
  - Neue Route(n) unter `app/routes/reports.py`
  - `app/config.py`: `DB_PATH`
- **Migration:** einmaliger Import von `orders.json` in die DB bevor umgeschaltet wird.
- **Nicht-Ziel:** ORM (SQLAlchemy). Reicht: `sqlite3`-Modul aus der Standard-Library mit handgeschriebenen SQL-Statements.

## Priorität 3 – Nice to have

### Perforiertes / vorperforiertes Thermopapier
- **Status:** offen – zu recherchieren
- **Frage des Nutzers:** Gibt es 80-mm-Thermorollen mit Perforationen zwischen Bons, damit jede Bestellung als einzelnes Ticket abreißbar ist?
- **Kontext:** Der ITPP047P hat bereits einen Auto-Cutter, jeder Druck wird derzeit per `printer.cut()` getrennt. Perforation wäre also Alternativ-/Fallback-Option (z. B. falls Cutter verschleißt oder bei hoher Druckfrequenz nerven soll).
- **Zu klären:**
  - Gibt es 80-mm-Thermopapier **mit Perforationen in regelmäßigen Abständen** (z. B. alle 10 cm) im Handel?
  - Wenn ja: passen die Abstände zur typischen Bon-Länge? Variiert die Bon-Länge stark (je nach Anzahl Artikel)?
  - Alternative: **Partial Cut** statt Full Cut – der Auto-Cutter lässt einen kleinen Steg stehen, sodass Bons sauber abreißen ohne runterzufallen. In `python-escpos` via `printer.cut(mode="PART")` statt `printer.cut()`.
- **Pragma:** Wahrscheinlich reicht **Partial Cut**; echte Perforation im Papier ist bei 80-mm-Rollen für POS-Drucker unüblich.

### Kiosk-Modus auf dem Hamtysan-Monitor
- **Status:** optional, aus `docs/raspberry-pi-setup.md` Abschnitt 6 bekannt
- **Wann relevant:** wenn am Pi direkt bedient werden soll (Touch?) oder Status angezeigt

### Storno / Nachdruck
- **Status:** nicht implementiert
- **Beschreibung:** Falls ein Druck fehlschlägt, ist die Bestellung in `orders.json` persistiert, aber kein UI-Pfad zum erneuten Drucken.
- **Skizze:** neue Route `POST /api/orders/<id>/reprint` die `print_order()` mit persistierter Order nochmal aufruft.

### Küchen-/Theken-Trennung (zweiter Drucker)
- **Status:** nicht geplant solange nur ein Drucker existiert

### Auth / Bediener-Login
- **Status:** bewusst weggelassen, LAN ist isoliert

## Erledigt (Archiv)

- [x] Hardware-Setup (Router, Pi, Drucker) dokumentiert
- [x] Flask-Skeleton mit Bestellung + Druck
- [x] Umstellung Drucker von Netzwerk auf USB (`python-escpos.File`)
- [x] systemd-Autostart
- [x] Erster erfolgreicher Testbon aus der App
