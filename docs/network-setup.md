# Router: GL.iNet AX1800 (Flint) einrichten

Ziel: ein **isoliertes LAN** ohne Internet, in dem der Pi eine feste IP hat und der Laptop ihn erreicht. Der Drucker hängt per USB am Pi, **nicht** am Router.

## 1. Erstverbindung

1. Router einstecken. LEDs abwarten.
2. Mit dem Laptop das WLAN `GL-AX1800-xxx` verbinden (Standard-Passwort auf der Unterseite).
   Alternativ: Laptop per LAN an einen der LAN-Ports anschließen.
3. Browser → `http://192.168.8.1` (Standard-Gateway von GL.iNet).
4. Admin-Passwort setzen. Sprache = Deutsch falls gewünscht.

## 2. Internet-Uplink bewusst nicht konfigurieren

Im Setup-Wizard die Frage nach dem WAN/Repeater überspringen. Der WAN-Port bleibt frei. Damit ist das Netz dauerhaft offline – gut für Ausfallsicherheit und Datenschutz.

## 3. LAN-Grundeinstellungen

Menü → **Netzwerk → LAN** (Pfad kann je nach Firmware leicht abweichen):

- LAN-IP: `192.168.8.1`
- Subnetzmaske: `255.255.255.0`
- DHCP-Server: aktiviert
- DHCP-Bereich: `192.168.8.100` – `192.168.8.199`
  → Damit bleiben `192.168.8.2`–`192.168.8.99` frei für **statische Reservierungen**.

Speichern & Übernehmen.

## 4. DHCP-Reservierung für den Pi

Es reicht **eine einzige** Reservierung: der Raspberry Pi. Der Drucker braucht keine, weil er kein Netzwerkgerät ist.

Wenn der Pi das erste Mal am Router hängt, erscheint er unter **Clients**. Dort per „Adresse reservieren“ (oder „Bind“) fixieren:

| Gerät | MAC | Reservierte IP | Hostname |
|---|---|---|---|
| Raspberry Pi 5 | `<MAC des eth0>` | `192.168.8.10` | `bonsystem-pi` |

MAC des Pi ermitteln: `ip link show eth0` → Feld `link/ether`.

Nach dem Eintragen den Pi einmal neu starten, damit er die reservierte IP bekommt.

## 5. WLAN fürs Event

- SSID z. B. `bonsystem` (2,4 GHz reicht für ein paar Clients, stabiler in Hallen mit vielen Geräten).
- WPA2-PSK, starkes Passwort.
- Gast-/Offen-Netz deaktivieren.

## 6. Sanity-Checks

Vom Laptop (im Router-WLAN):

```bash
ping 192.168.8.1        # Router
ping 192.168.8.10       # Pi (nach RPi-Setup)
curl http://192.168.8.10:8080/api/health   # App erreichbar?
```

## 7. Firewall / Isolation (optional)

Default reicht. Wenn später doch mal ein WAN angeschlossen wird:

- **Client-Isolation aus** – sonst sieht der Laptop den Pi nicht.
- **WAN-Zugriff für den Pi deaktivieren**, falls der Pi keine Updates aus dem Internet ziehen soll.
