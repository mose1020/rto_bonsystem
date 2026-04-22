# UI Style Guide – Bonsystem

Dieser Guide ist für eine **schnelle, latenzarme Bon-Erfassung** auf Laptop und optional Touch-Display. Alles ist serverseitig gerendert, Styles werden mit CSS-Custom-Properties in `app/static/css/app.css` zentral gehalten.

## 1. Designprinzipien

1. **Schnelligkeit vor Eleganz.** Jede Sekunde an einem Bier-Abend zählt. Klicks so direkt wie möglich – keine Modale, wenn ein Button reicht.
2. **Offline-first.** Keine externen Fonts, keine CDNs, keine Icon-Fonts.
3. **Klare Rückmeldung.** Jede Aktion (Item-Klick, Bon drucken, Druckerfehler) gibt visuelles Feedback innerhalb von 100 ms.
4. **Nur eine Primäraktion pro Screen.** „Bon drucken“ ist die einzige rote Schaltfläche.
5. **Deutsch, vertraut.** Bedienbegriffe aus der Gastro: „Bon“, „Bestellung“, „Summe“, „Notiz“.

## 2. Farben

In `:root` in `app/static/css/app.css`:

| Variable | Hex | Rolle |
|---|---|---|
| `--c-bg` | `#f6f5f1` | Hintergrund (leicht warmes Off-White, weniger grell als reines Weiß in Hallenlicht) |
| `--c-surface` | `#ffffff` | Karten, Eingabeflächen |
| `--c-border` | `#e3e1da` | Trennlinien |
| `--c-ink` | `#1c1c1c` | Primäre Schriftfarbe |
| `--c-ink-muted` | `#5d5d5d` | Sekundäre Schrift, Preise |
| `--c-primary` | `#b8002e` | Primäraktion (Bon drucken). Kontrast AA auf Weiß. |
| `--c-primary-ink` | `#ffffff` | Schrift auf Primär |
| `--c-accent` | `#f2c200` | Akzent (Hervorhebung, z. B. Kategorien-Tag) |
| `--c-success` | `#1f7a3a` | Erfolg („Gedruckt: …“), Drucker-online |
| `--c-danger` | `#b0332c` | Fehler, Drucker-offline |

Regeln:
- **Rot nur** für die Primäraktion und Fehler. Nicht für Dekoration.
- **Gelb sparsam** – maximal eine Fläche sichtbar.
- Text auf farbigen Flächen: immer Kontrast ≥ 4.5:1. Im Zweifel mit dem Browser-Inspector prüfen.

## 3. Typografie

- **Font:** System-UI-Stack (`system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`). Damit kein Laden zur Laufzeit.
- **Basis-Größe:** 18 px. (Deutlich größer als Standard-16px, damit Preise aus der Distanz lesbar bleiben.)
- **Skala:** 0.9 / 1 / 1.05 / 1.2 rem. Keine feineren Stufen.
- **Gewicht:** 400 für Fließtext, 600 für Namen/Beträge, kein 700 (wirkt in Hallenlicht fett-fleckig).

## 4. Abstände, Radien, Schatten

- **Spacing-Skala:** 4 / 8 / 12 / 16 / 24 / 32 px. Kein Freestyle zwischendrin.
- **Border-Radius:** 10 px für Karten, 6 px für Chips/kleine Buttons. Nichts rund, aber auch keine harten Kanten.
- **Schatten:** genau einer (`0 2px 8px rgba(0,0,0,.06)`). Mehr Ebenen brauchen wir nicht.

## 5. Komponenten

### Produktkarte `.product`
- Höhe ≥ 96 px, Breite elastisch via Grid (`minmax(180px, 1fr)`).
- Obere Zeile: Produktname, 600 weight.
- Untere Zeile: Preis in `--c-ink-muted`, 2 Nachkommastellen, Euro-Zeichen.
- Kein Bild. Wenn später Bilder dazu kommen, max. 64×64 px Icon links.

### Warenkorb `.cart`
- Sticky rechts (Desktop), unter Katalog (Mobile unter 900 px).
- Zeilen mit drei Spalten: [− / Name+Preis×Menge / +].
- **Nie scrollt der Bestellen-Button aus dem Bild** – `cart__list` bekommt `max-height: 40vh` und scrollt selbst.

### Buttons
- `.btn` – Basis, Mindesthöhe `--touch-min` = **56 px**.
- `.btn--primary` – rot, „Bon drucken“. Immer unten rechts.
- `.btn--ghost` – transparent mit Rand, „Leeren“.
- Fokus-Outline nicht entfernen. (Keyboard-Navigation ist wertvoll beim Testen.)

### Status-Chip `.status`
- Kompaktes Pill oben rechts.
- Zustände: `status--ok` (grün, „Drucker: bereit“), `status--error` (rot, „Drucker: offline“), `status--unknown` (grau, initial).
- Aktualisiert sich alle 15 s automatisch (`pollPrinter` in `app.js`).

### Feedback-Zeile `.cart__feedback`
- Eine Zeile unter den Aktionen.
- `role="status" aria-live="polite"` – Screenreader-freundlich.
- Inhalt: „Gedruckt: 20260422-203011-3A“ bei Erfolg, Fehlermeldung in Rot sonst.

## 6. Bon-Layout (Thermodruck)

Nicht Web-UI, sondern **der gedruckte Bon**. Layoutregeln, damit Lesbarkeit auf 80 mm (≈ 32 Zeichen) gegeben ist:

```
       BESTELLUNG
    (centered, groß + fett)
   Bon 20260422-203011-3A
      2026-04-22T20:30:11
  --------------------------
   2x Bratwurst mit Brötchen
                      9,00 €
   3x Bier 0,5l
                     12,00 €
  --------------------------
                 Summe: 21,00 €
  (rechtsbündig, fett)

  Notiz:
  ohne Senf
```

Regeln:
- Kopf zweizeilig groß und mittig – spart Rückfragen an der Ausgabe.
- Zeilen pro Position = 2 (Name + Betrag rechtsbündig), nicht kompakt einzeilig.
- Separatorzeilen aus Minuszeichen (32 ×), nicht aus Unicode-Linien (Codepage-Risiko).
- Notiz nur drucken, wenn ausgefüllt.

Der Renderer dazu steht in `app/services/printer_service.py::_render_receipt`. Änderungen am Layout dort – **nicht** in der Route.

## 7. Barrierefreiheit (Grundlagen)

- Kontrastverhältnisse prüfen (alle obigen Paarungen erfüllen mindestens WCAG AA).
- Touch-Targets ≥ 56 px.
- Alle interaktiven Elemente haben `<button>`-Semantik (nicht `<div onclick>`).
- Formularlabel: immer vorhanden (`<label>` umschließt Input in `order.html`).

## 8. Was bewusst weggelassen wird

- **Kein Dark Mode.** Gastro-Umgebung ist hell.
- **Kein CSS-Framework.** Jede neue Abhängigkeit muss offline installierbar sein.
- **Keine Animationen außer `active:scale(.98)`.** Ablenkung beim schnellen Tippen.
- **Keine Modalfenster.** Bestätigung des Drucks passiert inline.
