# Gestaltung: Formen, Farben, Muster

Diese Datei beschreibt, **wie** der Agent aus einem CI eine Karte wählt. Alle Optionen gibt `uv run scripts/make_card.py --list` aus.

## Entscheidungsweg in 5 Schritten

1. **Farbschema (`--theme`).** Das Schema der Website übernehmen:
   - Website hell → `light`
   - Website dunkel → `dark`
   - Marke lebt von einer kräftigen Vollfarbe (z. B. Sparkasse-Rot) → `brand`
2. **Layout (`--layout`).** Nach Persönlichkeit und Inhalt wählen, siehe Tabelle unten.
3. **Muster (`--pattern`).** Branche und Formensprache der Website spiegeln. Bei unruhigem Logo oder viel Text `none` oder `--intensity subtle` wählen.
4. **Formen.**
   - `--corners` nach den Rundungen der Website:
     - `suggest.corners` aus `brand.json` übernehmen
     - Pill-Buttons → `round`
     - eckige Website → `sharp`
   - `--photo-shape` passend dazu:
     - `circle` als Standard, wirkt wie LinkedIn
     - `rounded` passt zu weichen Marken
     - `square` passt zu Architektur und Editorial
     - `hexagon` passt zu Tech
5. **Galerie prüfen.** Mit `--gallery` alle Layouts rendern, die zwei besten ansehen und eines festlegen. Nicht raten: Die Bilder wirklich anschauen.

## Layouts

| Layout | Wirkung | Passt zu | Vermeiden bei |
| --- | --- | --- | --- |
| `classic` | seriös, ruhig, Akzentbalken | Beratung, Recht, Finanzen, Mittelstand | sehr langen Namen ohne Muster (dann `none`) |
| `split` | persönlich, Foto oder Monogramm groß | Coaches, Selbstständige, Personal Brand | Firmen-Accounts ohne Person |
| `centered` | formell, symmetrisch, edel | Kanzleien, Hotellerie, Kultur | sehr langen Headlines (wird gekürzt) |
| `diagonal` | dynamisch, modern | Sales, Sport, Start-ups, Events | konservativen Branchen |
| `minimal` | Designer-Look, viel Weißraum | Agenturen, Architektur, Kreative | kleinem Logo ohne Kontrast |
| `profile` | erinnert an den LinkedIn-Profilkopf | Recruiting, Netzwerk-Events, Teams | – (Allrounder) |

## Muster

| Muster | Wirkung | Typische Branchen |
| --- | --- | --- |
| `none` | ruhig, das Logo trägt | Luxus, Recht, starke Logos |
| `dots` | freundlich, leicht | Bildung, Gesundheit, Soziales |
| `grid` | präzise, technisch | Ingenieure, Architektur, Daten |
| `diagonal` | Bewegung | Logistik, Sport, Vertrieb |
| `waves` | weich, organisch | Wellness, Natur, Kreativ |
| `rings` | Fokus, Wirkung | Beratung, Coaching, Marketing |
| `circuit` | Tech, KI | Software, KI, IT-Dienstleister |
| `chevron` | Energie, Handel | Retail, Fitness, Events |

Muster sind Ton in Ton, damit sie den Kontrast nie senken. Ist die Fläche mittelhell und die Schrift weiß, wird das Muster automatisch dunkler gezeichnet.

## Farben: Regeln, die das Skript erzwingt

- **Haupttext** auf hellem oder dunklem Grund mindestens **7:1** (WCAG AAA). Auf Markenfläche mindestens **4,5:1** (AA), damit die Markenfarbe unverfälscht bleibt.
- **Nebentext** (Headline, Firma, Kontakte) mindestens 4,5:1, geprüft auch gegen den Mustergrund.
- Reicht der Kontrast nicht, ändert sich **nur die Helligkeit**, der Farbton bleibt erhalten.
- **QR-Code:** immer dunkle Module auf weißer Kachel, Kontrast ≥ 7:1, Ruhezone 4 Module, Fehlerkorrektur M. Nie invertieren, kein Logo in den Code.
- `report.json` → `min_text_contrast` zeigt den tatsächlich schlechtesten Wert.

## Typografie

- Überschrift = Markenschrift (`fonts.heading`), Fließtext = `fonts.body`.
- Ist die Schrift nicht installiert, warnt der Bericht. Dann gibt es zwei Wege:
  - Google-Font installieren.
  - Eine ähnliche, installierte Schrift eintragen. Proprietäre Hausschriften (z. B. „sparkasseHead“) gibt es meist nicht frei; dann die nächstliegende freie Schrift wählen: Inter, Manrope oder Sora für Sans, Source Serif oder Playfair Display für Serif.
- Mindestgrößen im Druck: 2,0 mm (≈ 5,7 pt) für Kleintext, Name ≥ 2,9 mm. Lange Namen brechen um, Bindestrich-Namen am Bindestrich. Lange E-Mails brechen am @ um und werden nicht abgeschnitten.

## Formate

| `--format` | Größe | Beschnitt | Zweck |
| --- | --- | --- | --- |
| `eu` | 85 × 55 mm | 3 mm | Druck (DACH/EU) |
| `us` | 3,5 × 2 in | 1/8 in | Druck (USA) |
| `wallet` | 85,6 × 53,98 mm | – | digital, Scheckkartenformat |
| `share` | 1200 × 627 px | – | Bild für Posts, Mail-Signatur, Events |

**Druck:**
- Für die Druckerei `card-print.pdf` mit 2 Seiten nehmen, Beschnitt ist enthalten.
- Abgerundete Ecken als „Eckenabrundung“ bestellen; die Druckdatei selbst bleibt rechteckig.
- Den QR-Code vor dem Druck mit zwei Handys testen, er muss mindestens 18 mm groß sein.
