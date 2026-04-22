# Raspberry Pi 5 einrichten

Ziel: Der Pi startet automatisch den Flask-Bonsystem-Server, zeigt auf dem Hamtysan-Monitor optional einen Kiosk-Browser, und hängt per LAN am Router.

## 1. SD-Karte flashen

Auf dem **Laptop mit Internet** (einmalig):

1. [Raspberry Pi Imager](https://www.raspberrypi.com/software/) installieren.
2. SD-Karte einlegen, Imager starten.
3. „Raspberry Pi OS (64-bit) Full“ (Bookworm) wählen. „Full“ nur, wenn du Chromium direkt für den Kiosk willst; sonst „Lite“ + später Chromium.
4. **Vor dem Schreiben** das Zahnrad für erweiterte Optionen öffnen:
   - Hostname: `bonsystem-pi`
   - SSH aktiviert, User `pi` + eigenes Passwort
   - WLAN-Zugangsdaten **leer lassen** (wir wollen LAN ohne Internet)
   - Locale: `de_DE.UTF-8`, Zeitzone `Europe/Berlin`
5. Schreiben.

## 2. Erstes Booten

1. SD-Karte in den Pi, HDMI in den Hamtysan, LAN ins Router, Strom an.
2. Nach Bootvorgang am Monitor einloggen (falls Desktop) oder per SSH:

   ```bash
   ssh pi@192.168.8.<vom Router vergebene IP>
   ```

3. Router-Clientliste öffnen → MAC des Pi → IP auf `192.168.8.10` reservieren (siehe [network-setup.md](network-setup.md)), dann `sudo reboot`.

## 3. Projekt kopieren

Da der Pi offline ist, muss der Code irgendwie auf ihn drauf. Zwei Wege:

**a) Einmalig Internet geben** (Laptop-Hotspot an Pi):
```bash
git clone <repo-url> /home/pi/rto_bonsystem
cd /home/pi/rto_bonsystem
./scripts/install-pi.sh
```

**b) Offline über USB-Stick / scp:**
```bash
# Vom Laptop aus
scp -r rto_bonsystem/ pi@192.168.8.10:/home/pi/
# Dann auf dem Pi:
cd /home/pi/rto_bonsystem
./scripts/install-pi.sh
```

Für das Venv braucht `install-pi.sh` Internet (pip). Dafür den Pi **einmalig** ins Internet hängen (mobiler Hotspot am Laptop, oder WAN-Port des GL.iNet temporär benutzen). Danach wieder offline.

## 4. Autostart via systemd

```bash
sudo cp scripts/bonsystem.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bonsystem
sudo systemctl status bonsystem
```

Die Unit startet `python -m app.wsgi` im Venv unter `/home/pi/rto_bonsystem/.venv`. Läuft auf `0.0.0.0:8080`.

Logs anschauen:
```bash
journalctl -u bonsystem -f
```

## 5. Firewall (optional)

Standardmäßig ist der Pi offen im LAN – passt, weil das Netz isoliert ist. Wenn du paranoider sein willst:

```bash
sudo apt-get install -y ufw
sudo ufw allow from 192.168.8.0/24 to any port 8080 proto tcp
sudo ufw allow from 192.168.8.0/24 to any port 22 proto tcp
sudo ufw --force enable
```

## 6. Kiosk-Modus auf dem Hamtysan-Monitor (optional)

Wenn du am Pi-Monitor eine Statusansicht oder Touch-Bedienung haben willst, kann Chromium im Vollbild starten.

```bash
sudo apt-get install -y chromium-browser unclutter
```

Datei `~/.config/autostart/bonsystem-kiosk.desktop` (nach erstem Desktop-Login):

```ini
[Desktop Entry]
Type=Application
Name=Bonsystem Kiosk
Exec=/bin/bash -lc "sleep 10 && chromium-browser --kiosk --incognito --noerrdialogs --disable-translate --no-first-run http://127.0.0.1:8080"
X-GNOME-Autostart-enabled=true
```

Bildschirm-Standby im Raspberry-Pi-Desktop unter „Einstellungen → Screen Blanking“ abschalten, damit der Kiosk nicht in den Bildschirmschoner läuft.

> **Hinweis:** Laut Projektbeschreibung erfolgt die Bedienung primär über den Laptop. Kiosk-Mode ist also optional für Statusanzeige. Touch-Bedienung auf dem Hamtysan ist nur sinnvoll, wenn der Monitor Touch unterstützt.

## 7. Updates / Upgrades

Offline gibt es keine Updates. Wenn du das Gerät periodisch online bringst:

```bash
sudo apt-get update && sudo apt-get upgrade -y
cd /home/pi/rto_bonsystem
source .venv/bin/activate
pip install -U -r requirements.txt
sudo systemctl restart bonsystem
```
