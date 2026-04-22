# rto_bonsystem

Offline-Bonsystem für Vereins-/Event-Ausschank. Flask-App auf Raspberry Pi 5, druckt Bons auf einen Munbyn ITPP047P, bedient via Laptop im LAN des GL.iNet AX1800.

## Schnellstart (Entwicklung auf dem Laptop)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python -m app.wsgi
```

→ http://localhost:8080

## Deployment auf dem Pi

Siehe [docs/hardware-setup.md](docs/hardware-setup.md) für die Gesamt-Reihenfolge. Die einzelnen Geräte-Anleitungen:

- [docs/network-setup.md](docs/network-setup.md) – GL.iNet AX1800
- [docs/raspberry-pi-setup.md](docs/raspberry-pi-setup.md) – Pi-OS, systemd, Kiosk
- [docs/printer-setup.md](docs/printer-setup.md) – Munbyn ITPP047P
- [docs/style-guide.md](docs/style-guide.md) – UI-Design-Regeln

Architektur-Überblick und Befehlsreferenz: [CLAUDE.md](CLAUDE.md).

## Lizenz

TBD.
