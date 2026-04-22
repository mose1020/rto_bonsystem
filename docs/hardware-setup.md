# Hardware-Setup – Überblick

Dieses Dokument zeigt, **in welcher Reihenfolge** die Geräte aufgebaut werden, damit später alles zusammen funktioniert. Details zu einzelnen Geräten in den verlinkten Anleitungen.

## Komponenten

| # | Gerät | Kabel | Ziel |
|---|---|---|---|
| 1 | GL.iNet AX1800 (Flint) | Netzstecker | WLAN + LAN bereitstellen |
| 2 | Raspberry Pi 5 (8 GB) | USB-C Netzteil, HDMI → Monitor, LAN → Router, **USB → Drucker** | Flask-Server |
| 3 | Hamtysan 7″ Monitor | HDMI ← Pi, Netzstecker | Status / Kiosk |
| 4 | Munbyn ITPP047P | **USB → Pi**, Netzstecker, Papierrolle | Bon-Drucker |
| 5 | Laptop | WLAN oder LAN → Router | Bedienung |

Wichtig: **Kein Internet-Uplink.** Der WAN-Port des Routers bleibt leer.

## Aufbau-Reihenfolge

1. **Router aufstellen, einschalten.** Erst alleine booten lassen (30 s).
2. **Router konfigurieren** (Admin-Passwort, DHCP-Range, siehe [network-setup.md](network-setup.md)). Einmalig.
3. **Raspberry Pi vorbereiten:** SD-Karte flashen, Erst-Setup, Pi per LAN an den Router, Abhängigkeiten installieren. Siehe [raspberry-pi-setup.md](raspberry-pi-setup.md). DHCP-Reservierung z. B. `192.168.8.10`.
4. **Drucker anschließen:** Papierrolle einlegen, Strom an, **USB-Kabel vom Drucker direkt an einen USB-Port des Pi**. Siehe [printer-setup.md](printer-setup.md).
5. **Testbon** vom Pi: `python scripts/print_test.py`.
6. **Laptop verbinden** (WLAN des Routers). `http://192.168.8.10:8080` öffnen.
7. **Testbon aus der App** über „Bon drucken“.

## Netzplan

```
       ┌───────────────────────────┐
       │    GL.iNet AX1800 Flint   │
       │    LAN: 192.168.8.1/24    │
       │    WAN: unbelegt          │
       └─────────────┬─────────────┘
                     │
       ┌─────────────┴─────────────┐
       │                           │
     (LAN)                       (WLAN)
       │                           │
┌──────┴──────┐               ┌────┴─────┐
│ Raspberry   │               │ Laptop   │
│ Pi 5        │               │ (Browser)│
│ 192.168.8.10│               │ DHCP     │
└──────┬──────┘               └──────────┘
       │
     (USB)
       │
┌──────┴──────┐
│ Munbyn      │
│ ITPP047P    │
│ /dev/usb/lp0│
└─────────────┘
```

Der Drucker hat **keine eigene IP**. Er ist ein USB-Gerät am Pi. Der Pi fungiert als einziger Netzwerk-Endpunkt für die App und spricht den Drucker lokal über `/dev/usb/lp0` an.

## Nach dem Event – Herunterfahren

1. Browser am Laptop schließen.
2. Auf dem Pi: `sudo systemctl stop bonsystem` oder sauber `sudo shutdown now`, dann Netz trennen.
3. Drucker ausschalten (Paper-Feed nicht bei ausgeschaltetem Drucker ziehen – kann Walze verbiegen).
4. Router ausstecken.
