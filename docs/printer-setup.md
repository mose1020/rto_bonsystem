# Drucker: Munbyn ITPP047P über USB einrichten

Der ITPP047P spricht **ESC/POS über USB**. Wir nutzen **nicht** CUPS oder den Windows-Treiber, sondern den Kernel-Treiber `usblp`, der den Drucker als rohes Zeichengerät unter `/dev/usb/lp0` bereitstellt. Python schreibt die ESC/POS-Bytes direkt in dieses Device.

## 1. Auspacken und Verkabeln

1. Papierrolle einlegen (thermosensible Seite zeigt zum Druckkopf; Deckel schließt nur korrekt, wenn die Rolle richtig liegt).
2. Netzkabel anschließen. Drucker **noch nicht einschalten**.
3. USB-Kabel (USB-A → USB-B) vom Drucker an einen **USB-Port des Raspberry Pi**.
   - **Nicht** an den Router, nicht an den Laptop.
   - USB-3-Port (blau) am Pi ist stabiler als USB-2 bei längeren Drucken.
4. Drucker einschalten.

## 2. Prüfen, dass der Pi den Drucker sieht

Auf dem Pi (per SSH oder direkt am Hamtysan-Monitor):

```bash
lsusb
```

Du solltest eine Zeile sehen mit einem Hersteller wie `Winbond`, `Prolific`, oder einer generischen „USB Printer“-Bezeichnung. Notiere die **Vendor:Product-ID** (Form `xxxx:yyyy`) – gut zu wissen, falls später `/dev/usb/lp0` nicht automatisch angelegt wird.

```bash
ls -l /dev/usb/
```

Erwartet: Eintrag `lp0`. Wenn `/dev/usb/lp0` **nicht** existiert:
- Prüfe `dmesg | tail -30` – dort steht, warum der `usblp`-Treiber nicht zugegriffen hat.
- Manchmal „schnappt“ sich `cups` das Device und blockiert `usblp`. Dann: `sudo systemctl disable --now cups` und Drucker ab- und wieder anstecken.

## 3. Zugriff für den App-User

Das Device `/dev/usb/lp0` gehört der Gruppe `lp`. Damit die App ohne `sudo` schreiben darf, muss der Benutzer in der `lp`-Gruppe sein:

```bash
sudo usermod -a -G lp "$USER"
# einmal aus- und wieder einloggen (oder Neustart), danach:
groups         # muss 'lp' enthalten
```

`scripts/install-pi.sh` erledigt das automatisch, aber das erneute Einloggen muss manuell passieren.

## 4. Testbon aus Python

```bash
cd /home/pi/rto_bonsystem
source .venv/bin/activate
python scripts/print_test.py
```

Erwartet: ein kleiner Bon mit `TESTBON` wird ausgedruckt und abgeschnitten.

Falls andere Device-Nummer:
```bash
PRINTER_DEVICE=/dev/usb/lp1 python scripts/print_test.py
```

## 5. Aus der Flask-App drucken

```bash
curl http://192.168.8.10:8080/api/health/printer
# -> {"status":"ok","device":"/dev/usb/lp0","printer":{"id":"drucker_1","name":"Drucker_1"}}
```

In der Weboberfläche Artikel anklicken und „Bon drucken“.

## 5a. Mehrere Drucker einrichten

Wenn ein zweiter (oder dritter) Munbyn angeschlossen wird, taucht er als `/dev/usb/lp1`, `lp2`, … auf. Konfiguration läuft über `data/printers.json`:

```json
{
  "default": "drucker_1",
  "printers": [
    {"id": "drucker_1", "name": "Drucker_1", "device": "/dev/usb/lp0"},
    {"id": "drucker_2", "name": "Drucker_2", "device": "/dev/usb/lp1"}
  ]
}
```

Per Health-Check pro Drucker prüfen:
```bash
curl http://192.168.8.10:8080/api/health/printer/drucker_2
```

In der UI erscheint dann ein Dropdown rechts oben in der Topbar; der gewählte Drucker bleibt im Browser (localStorage) gespeichert und wird mit jeder Bestellung mitgeschickt (Payload-Feld `printer_id`).

**Wichtig: stabile Device-Pfade.** Linux nummeriert die `lp*`-Devices nach Anschluss-Reihenfolge — nach einem Reboot kann `lp0` und `lp1` getauscht sein. Für den Produktivbetrieb mit mehreren Druckern empfiehlt sich eine udev-Rule, die anhand der USB-Seriennummer einen stabilen Symlink anlegt:

```bash
# Seriennummer ermitteln (Drucker per USB anschließen, dann)
udevadm info -a -n /dev/usb/lp0 | grep -E 'idVendor|idProduct|serial'

# /etc/udev/rules.d/99-bonsystem-printers.rules
SUBSYSTEM=="usb", ATTRS{idVendor}=="04b8", ATTRS{idProduct}=="0e20", ATTRS{serial}=="SERIENNR1", SYMLINK+="bonsystem/drucker_1"
SUBSYSTEM=="usb", ATTRS{idVendor}=="04b8", ATTRS{idProduct}=="0e20", ATTRS{serial}=="SERIENNR2", SYMLINK+="bonsystem/drucker_2"

sudo udevadm control --reload && sudo udevadm trigger
```

In `printers.json` dann `"device": "/dev/bonsystem/drucker_1"` statt `/dev/usb/lp0`.

## 6. Typische Probleme

| Symptom | Ursache | Fix |
|---|---|---|
| `/dev/usb/lp0` existiert nicht | `usblp`-Treiber nicht geladen, oder CUPS hat das Gerät belegt | `sudo modprobe usblp`; ggf. `sudo systemctl disable --now cups` und Drucker neu einstecken |
| `Permission denied` beim Öffnen | User nicht in Gruppe `lp` | `sudo usermod -a -G lp "$USER"`, dann neu einloggen |
| Druck kommt nur teilweise | Buffer-Problem bei Folgeaufträgen | Der Service schließt das Device nach jedem Druck – sollte nicht auftreten. Wenn doch: zwischen zwei Drucken ~200 ms warten. |
| Umlaute kaputt (ä → Sonderzeichen) | Codepage falsch | In `app/services/printer_service.py` vor dem `text()` eine Codepage setzen: `printer.charcode("CP858")`. Alternativ `"CP437"`. |
| Cutter schneidet nicht | Cutter im Menü des Druckers deaktiviert, oder Modell ohne Cutter | Drucker-Webmenü/-DIP-Schalter prüfen. Als Workaround `printer.cut()` durch `printer.text("\n\n\n")` ersetzen. |
| `lsusb` listet nichts | USB-Kabel, USB-Port oder Drucker-Netzteil | Anderes Kabel/Port probieren, Netz-LED am Drucker prüfen |

## 7. Warum nicht CUPS?

CUPS wäre ein zweiter Layer zwischen App und Drucker – mehr Fehlerquellen, langsamere Fehlermeldungen. Da wir `python-escpos` ohnehin nutzen, um Layouts zu erzeugen, schreiben wir die Rohbytes direkt. Vorteile:
- Keine Druckertreiber-Installation.
- Keine Warteschlange, die sich verhakt.
- Fehler sind sofort sichtbar in der App (HTTP 502 + Meldung), nicht in `/var/log/cups`.

## 8. ESC/POS-Referenz

Der ITPP047 implementiert das Epson-ESC/POS-Kommandoset. Im MUNBYN-Support-Center gibt es einen Artikel „ITPP047 esc/pos (HEX) command“, der alle unterstützten Hex-Sequenzen listet. Für unser Projekt reichen die Abstraktionen aus `python-escpos` (`text`, `set`, `cut`, `charcode`).
