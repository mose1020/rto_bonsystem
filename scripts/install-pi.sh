#!/usr/bin/env bash
# Installiert Systempakete + Python-Abhängigkeiten auf dem Raspberry Pi.
# Für Raspberry Pi OS (Bookworm).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo ">> System-Pakete"
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git

echo ">> Benutzer in Gruppe 'lp' (Zugriff auf /dev/usb/lp0)"
sudo usermod -a -G lp "$USER"

echo ">> Virtualenv anlegen"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo ">> Python-Abhängigkeiten"
pip install --upgrade pip
pip install -r requirements.txt

echo ">> .env anlegen (falls nicht vorhanden)"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "   -> .env erstellt. Standard: PRINTER_DEVICE=/dev/usb/lp0"
fi

echo
echo ">> Fertig."
echo "   WICHTIG: einmalig aus-/einloggen (oder 'newgrp lp'), damit die Gruppe greift."
echo "   Start: source .venv/bin/activate && python -m app.wsgi"
