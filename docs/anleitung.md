# Anleitung: Business Card im eigenen CI

[English version](guide.en.md) · [Zurück zur Übersicht](../README.md)

Diese Anleitung erklärt Schritt für Schritt, wie du mit dem Skill eine Visitenkarte erstellst. Du brauchst etwa 10 Minuten.

## 1. Einmal einrichten

1. Ordner herunterladen und in den Skill-Ordner deines Agenten legen:
   - Claude Code: `~/.claude/skills/linkedin-business-card`
   - Codex: `~/.codex/skills/linkedin-business-card`
2. Im Ordner `uv sync` ausführen. Ohne `uv` geht auch `python3 -m pip install segno==1.6.6`.
3. Für PNG und PDF `rsvg-convert` installieren:
   - macOS: `brew install librsvg`
   - Linux: `apt install librsvg2-bin`

## 2. Das brauchst du

- **Deine LinkedIn-Profil-URL.** Du findest sie in deinem Profil unter *Kontaktinfo*, z. B. `linkedin.com/in/dein-name`.
- **Deine Profildaten**, auf einem dieser Wege:
  - Name, Headline, Firma und Ort einfach in den Chat schreiben.
  - Oder dein Profil als PDF speichern: Profil → *Mehr* → *Als PDF speichern*.
  - Oder den LinkedIn-Datenexport nutzen: *Einstellungen* → *Datenschutz* → *Kopie Ihrer Daten anfordern*.
- **Deine Website**, damit der Skill Farben, Schriften und Logo erkennt. Ohne Website reichen Primärfarbe und Logo-Datei.
- Optional: ein **Foto**, quadratisch, mindestens 600 × 600 Pixel.

## 3. Karte erstellen lassen

Schreib deinem Agenten zum Beispiel:

> Erstelle mir eine Business Card aus meinem LinkedIn-Profil im Stil von https://meine-firma.de. Profil-URL: linkedin.com/in/mein-name. Auf die Karte sollen E-Mail und Website, keine Telefonnummer. Ich brauche eine Druckdatei.

Der Agent macht dann Folgendes:

1. Er liest dein Profil und das CI deiner Website.
2. Er zeigt dir die erkannten Farben, Schriften und das Logo.
3. Er rendert alle Layouts als Galerie und wählt das passendste.
4. Er prüft Lesbarkeit, Textlänge und QR-Code.
5. Er gibt dir die Dateien und die Anleitung für die LinkedIn-App.

## 4. Ergebnis prüfen

- Öffne `preview.html` und schau dir beide Seiten an.
- Scanne den QR-Code mit deinem Handy. Er muss dein LinkedIn-Profil öffnen.
- Lies die Hinweise in `report.json`. Dort steht z. B., ob eine Schrift ersetzt oder ein Text gekürzt wurde.

Gefällt dir etwas nicht, sag es einfach. Zum Beispiel: „Bitte ohne Muster“, „dunkler“, „Foto statt Initialen“ oder „anderes Layout“.

## 5. Drucken

- Schicke `card-print.pdf` an die Druckerei. Das Format ist 85 × 55 mm, 3 mm Beschnitt sind schon enthalten.
- Abgerundete Ecken bei der Druckerei als **Eckenabrundung** bestellen.
- Vorher einen Probedruck machen und den QR-Code testen.

## 6. Die LinkedIn Business Card einstellen

LinkedIn lässt die Karte nur in der App gestalten. Der Skill kann sie nicht für dich ausfüllen. Öffne `linkedin-native-card.md` und folge den Schritten:

1. In der LinkedIn-App oben links auf dein Profilfoto tippen, dann auf den QR-Code.
2. Auf *Edit* tippen und die Optionen *Info*, *Layout*, *Font*, *Colors*, *Pattern* und *Stickers and Doodle* so wählen, wie es die Anleitung empfiehlt.
3. Auf *Save* tippen, dann auf *Add to Wallet*.

Gut zu wissen: Ein Kartentausch per Scan schickt **keine** Kontaktanfrage. Vernetze dich danach gezielt.

## Wenn etwas nicht klappt

| Problem | Lösung |
| --- | --- |
| „Abruf fehlgeschlagen“ oder HTTP 403 | Die Website blockiert automatische Abrufe. Gib Farbe und Logo von Hand an. |
| Falsche Farbe erkannt | Sag dem Agenten deine richtige Markenfarbe (z. B. `#E30613`). |
| Andere Schrift als auf der Website | Deine Hausschrift ist nicht installiert oder nicht frei verfügbar. Installiere sie oder nimm eine ähnliche. |
| Text wurde gekürzt | Kürze deine Headline auf 40–70 Zeichen. |
| Nur SVG, kein PNG/PDF | `rsvg-convert` installieren (siehe Schritt 1). |

## Was der Skill nicht verspricht

- Automatisch erkannte Farben, Schriften und Logos sind Vorschläge. Prüfe sie.
- Es gibt keine Garantie für Druckergebnisse. Mach einen Probedruck.
- Angaben zur LinkedIn-Funktion entsprechen dem Stand vom 20.11.2026 und können sich ändern.
