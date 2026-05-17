#!/usr/bin/env bash
# Update-Skript: synchronisiert das Repo auf den Pi und startet den Dienst neu.
#
# Benutzung:
#   scripts/deploy.sh                  # Default-Pi: 192.168.178.10 (Heimnetz)
#   scripts/deploy.sh 192.168.8.10     # Produktiv-Pi im GL.iNet
#   scripts/deploy.sh bonsystem-pi     # Hostname statt IP geht auch
#
# Optionen (per Umgebungsvariablen):
#   PI_USER=pi          SSH-User auf dem Pi
#   PI_PATH=/home/pi/rto_bonsystem    Zielpfad auf dem Pi
#   SKIP_RESTART=1      Nur syncen, Dienst nicht neu starten

set -euo pipefail

PI_HOST="${1:-192.168.178.10}"
PI_USER="${PI_USER:-pi}"
PI_PATH="${PI_PATH:-/home/pi/rto_bonsystem}"
SKIP_RESTART="${SKIP_RESTART:-0}"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${PI_USER}@${PI_HOST}"

echo "→ Quelle:  ${REPO_DIR}/"
echo "→ Ziel:    ${TARGET}:${PI_PATH}/"
echo

# Erreichbarkeit kurz testen, damit man nicht ewig auf rsync-Timeout wartet.
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "${TARGET}" 'true' 2>/dev/null; then
    echo "✗ ${TARGET} nicht erreichbar (SSH-Timeout / kein Key)." >&2
    echo "  Prüfen: ping ${PI_HOST}; ssh ${TARGET}" >&2
    exit 1
fi

echo "→ Synchronisiere Code …"
rsync -az --delete \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='.pytest_cache/' \
    --exclude='.ruff_cache/' \
    --exclude='node_modules/' \
    --exclude='/data/orders.json' \
    --exclude='/.env' \
    --info=stats2,name0 \
    "${REPO_DIR}/" "${TARGET}:${PI_PATH}/"

if [[ "${SKIP_RESTART}" == "1" ]]; then
    echo
    echo "✓ Sync fertig (Dienst nicht neu gestartet, SKIP_RESTART=1)."
    exit 0
fi

echo
echo "→ Starte bonsystem.service neu …"
ssh "${TARGET}" 'sudo systemctl restart bonsystem'

echo
echo "→ Status:"
ssh "${TARGET}" 'systemctl --no-pager --lines=5 status bonsystem' || true

echo
echo "✓ Deployment fertig. App erreichbar unter http://${PI_HOST}:8080"
