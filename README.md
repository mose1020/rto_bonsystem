# rto_bonsystem

Offline-Bonsystem für die **Ortenauer Laufnacht** (Running Team Ortenau).
Flask-App auf Raspberry Pi 5, druckt Token-Bons (einer pro Stück, abreißbar via Partial Cut) auf einen oder mehrere Munbyn ITPP047P, bedient via Laptop oder Tablet im LAN des GL.iNet AX1800.

## Features

- **Token-basierter Bondruck**: Pro Stück ein eigener Bon, dazwischen Partial Cut. Bei „2× Pils + 1× Salat" → 3 abreißbare Bons mit Pos 1/3, 2/3, 3/3.
- **Pfand wird sauber ausgewiesen**: Bei pfandpflichtigen Getränken (Ketterer, Aperol) erscheint die Aufschlüsselung Preis / + Pfand / Gesamt auf dem Bon und im Warenkorb.
- **Sponsoren-Bons als Gratis-Artikel**: Eigene Kategorie, druckt „GRATIS" statt eines Preises.
- **Wechselgeld-Hilfe**: Schein-Buttons (5/10/20/50/100 €) + Custom-Input, Rückgeld live im Warenkorb.
- **Multi-Drucker**: Mehrere ESC/POS-Drucker per USB, Dropdown in der Topbar, gewählter Drucker bleibt im Browser gespeichert.
- **SQLite-Persistierung mit Bestands-Übersicht**: Live-Übersichts-Seite zeigt verkaufte Mengen vs. Kritisch-/Warn-Werte, sortiert nach Auslastung. Limits direkt im UI editierbar.
- **DB-Reset** für den Übergang zwischen Veranstaltungen, geschützt mit Passwort aus `.env`.
- **Veranstaltungs-Branding**: Logo der Ortenauer Laufnacht auf jedem Bon, „Running Team Ortenau" als Untertitel.

## Schnellstart (Entwicklung auf dem Laptop)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env       # ADMIN_PASSWORD setzen, falls Reset gewollt
python -m app.wsgi
```

→ http://localhost:8080 (Bestellung) und http://localhost:8080/uebersicht

Ohne Drucker startet die App problemlos; `POST /api/orders` antwortet dann mit HTTP 502 + `print_error`. Die Bestellung wird trotzdem in DB und JSON persistiert.

## Deployment auf den Pi

```bash
./scripts/deploy.sh                  # sync nach pi@192.168.178.10, Service neu starten
./scripts/deploy.sh 192.168.8.10     # ins GL.iNet-Produktivnetz
```

Erst-Installation und Setup-Reihenfolge:

- [docs/hardware-setup.md](docs/hardware-setup.md) – Verkabelung + Reihenfolge des Hochfahrens
- [docs/network-setup.md](docs/network-setup.md) – GL.iNet AX1800 konfigurieren
- [docs/raspberry-pi-setup.md](docs/raspberry-pi-setup.md) – Pi-OS, systemd-Service, optionaler Kiosk
- [docs/printer-setup.md](docs/printer-setup.md) – Munbyn ITPP047P, udev, Testdruck
- [docs/style-guide.md](docs/style-guide.md) – UI-Designregeln (Farben, Spacing, Touch-Targets)

Architekturüberblick, API-Referenz und Befehle: [CLAUDE.md](CLAUDE.md). Offene Punkte: [docs/backlog.md](docs/backlog.md).

## Bedienung am Tablet

1. Browser auf `http://192.168.8.10:8080`.
2. **Bestellung**: Tabs „Bestellung" / „Übersicht" in der Topbar; Drucker rechts oben (wird automatisch gespeichert).
3. Artikel antippen → erscheint im Warenkorb. Wechselgeld optional über die Schein-Buttons.
4. **Bon drucken** löst den Druck aus. Jedes Stück kommt als eigener abreißbarer Bon raus.
5. **Übersicht**: Live-Bestand pro Artikel (sortiert nach Auslastung), Bestellungstabelle rechts, Limits via `✎` editieren.
6. Bei neuem Event: rechts unten **Datenbank zurücksetzen** + Passwort aus `.env`.

## Lizenz

TBD.
