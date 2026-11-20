"""Übersetzt das CI in konkrete Einstellungen für die native LinkedIn Business Card.

LinkedIn bietet dafür keine API. Die Karte wird nur in der LinkedIn-App gestaltet;
dieser Text ist eine Klick-Anleitung mit passenden Auswahlen.
Faktenquelle: references/linkedin-native-card.md (Stand 20.11.2026).
"""
from __future__ import annotations

from common import hue_family_de, normalize_hex

FACT_DATE = "20.11.2026"
HELP_URL = "https://www.linkedin.com/help/linkedin/answer/a16648713"
NEWS_URL = "https://news.linkedin.com/2026/new-ways-to-build-meaningful-connections"

FONT_ADVICE = {
    "sans": "eine schlichte, serifenlose Schrift (Sans)",
    "serif": "eine Schrift mit Serifen (Serif) – wirkt klassisch und hochwertig",
    "mono": "eine technische Schrift mit gleicher Zeichenbreite (Mono), falls angeboten – sonst Sans",
    "script": "eine handschriftliche Schrift nur für Akzente; für gute Lesbarkeit eher Sans",
}

PATTERN_ADVICE = {
    "none": "kein Muster – das Logo und die Farbe tragen die Karte",
    "dots": "ein Punkt- oder Rastermuster",
    "grid": "ein feines Linien- oder Rastermuster",
    "diagonal": "ein Muster mit diagonalen Linien oder Streifen",
    "waves": "ein Muster mit Wellen oder weichen, runden Formen",
    "rings": "ein Muster mit Kreisen oder Ringen",
    "circuit": "ein technisches, geometrisches Muster (Linien/Knoten)",
    "chevron": "ein Zickzack- oder Winkelmuster",
}

LAYOUT_ADVICE = {
    "classic": "ein ruhiges Layout mit linksbündigem Text",
    "split": "ein Layout mit großem Profilfoto auf einer Seite",
    "centered": "ein zentriertes Layout mit Foto oben",
    "diagonal": "ein dynamisches Layout mit Foto auf der Farbfläche",
    "minimal": "das schlichteste Layout mit viel Weißraum",
    "profile": "ein Layout mit Foto auf einem farbigen Band, ähnlich dem Profilkopf",
}


def _font_style(brand, report) -> str:
    style = (brand or {}).get("font_style")
    if style in FONT_ADVICE:
        return style
    try:
        from extract_ci import classify_font

        return classify_font((report.get("fonts") or {}).get("heading", ""))
    except Exception:  # pragma: no cover - Fallback ohne extract_ci
        return "sans"


def recommend_native(profile: dict, brand: dict, report: dict) -> str:
    colors = (brand or {}).get("colors") or {}
    primary = colors.get("primary")
    secondary = colors.get("secondary")
    style = _font_style(brand, report)
    head = profile.get("headline", "") or ""
    lines = [
        f"# LinkedIn Business Card einstellen – {profile.get('name', '')}",
        "",
        f"Stand der Fakten: {FACT_DATE}. Die Funktion gibt es laut LinkedIn-Hilfe nur in der LinkedIn-App "
        "(englische Oberfläche) und sie wird schrittweise ausgerollt. Falls dir Menüs fehlen: App aktualisieren "
        "oder später erneut prüfen. Quelle: " + HELP_URL,
        "",
        "Die Karte lässt sich nicht automatisch befüllen – LinkedIn bietet dafür keine Schnittstelle. "
        "Diese Anleitung sagt dir, was du in der App antippst, damit sie zu deinem CI passt.",
        "",
        "## 1. Karte öffnen",
        "",
        "1. In der LinkedIn-App oben links auf dein **Profilfoto** tippen.",
        "2. Oben im Profil auf den **QR-Code** tippen. Die Karte erscheint; wischen zeigt Vorder- und Rückseite.",
        "3. Auf das **Edit**-Symbol tippen. Unten erscheinen die Optionen.",
        "",
        "## 2. Optionen wählen",
        "",
    ]
    # Info
    info = "**Info:** Headline prüfen"
    if len(head) > 70:
        info += (f" – deine Headline hat {len(head)} Zeichen. Für die Karte auf etwa 40–70 Zeichen kürzen, "
                 "z. B. Rolle + Nutzen in einem Satz.")
    else:
        info += f" („{head}“ passt)." if head else " (eine kurze Rolle + Nutzen, 40–70 Zeichen)."
    lines.append(f"- {info} Häkchen bei **Company or school**"
                 + (f" ({profile['company']})" if profile.get("company") else "")
                 + " und **Location** setzen, wenn beides auf die Karte soll.")
    lines.append(f"- **Layout:** {LAYOUT_ADVICE.get(report.get('layout'), LAYOUT_ADVICE['classic'])}. "
                 f"Fotostil passend zu deiner Karte: **{report.get('photo_shape', 'circle')}** "
                 "(circle = Kreis, rounded = abgerundet, square = eckig, hexagon = Sechseck – das nächstliegende wählen).")
    lines.append(f"- **Font:** {FONT_ADVICE[style]}. Deine Markenschrift ist "
                 f"„{(report.get('fonts') or {}).get('heading', '–')}“ ({style.capitalize() if style != 'sans' else 'Sans'}). "
                 "LinkedIn bietet eine feste Auswahl; nimm die ähnlichste.")
    if primary:
        p = normalize_hex(primary)
        line = (f"- **Colors:** Vorderseite das Farbfeld aus der Familie **{hue_family_de(p)}**, das {p} am nächsten kommt.")
        if secondary:
            s = normalize_hex(secondary)
            line += (f" Dann **doppelt auf die Farbauswahl tippen**, um zur Rückseite zu wechseln, und dort "
                     f"**{hue_family_de(s)}** (nah an {s}) wählen – oder dieselbe Farbe für einen ruhigen Auftritt.")
        else:
            line += " Doppeltippen auf die Farbauswahl wechselt zur Rückseite; dort dieselbe Familie oder Weiß/Grau wählen."
        line += " Eigene Hex-Werte sind laut Hilfe nicht vorgesehen."
        lines.append(line)
    else:
        lines.append("- **Colors:** Keine Markenfarbe bekannt – wähle eine ruhige, dunkle Farbe (Blau, Grau, Grün). "
                     "Doppeltippen auf die Farbauswahl wechselt zwischen Vorder- und Rückseite.")
    lines.append(f"- **Pattern:** {PATTERN_ADVICE.get(report.get('pattern'), PATTERN_ADVICE['none'])}. "
                 "Im Zweifel dezent: Name und QR-Code müssen gut lesbar bleiben.")
    lines.append("- **Stickers and Doodle** (nur Rückseite): Tipp fürs CI – ein Foto deines **Logos** als "
                 "*cutout* einfügen; optional die **Unterschrift** als Doodle. Sparsam einsetzen: "
                 "höchstens ein bis zwei Elemente.")
    lines += [
        "",
        "Wischen, um beide Seiten zu prüfen, dann **Save** tippen.",
        "",
        "## 3. Ins Wallet legen und teilen",
        "",
        "- **Add to Wallet** antippen und den Anweisungen folgen (Apple Wallet oder Google Wallet).",
        "- Auf Events: Karte zeigen, Gegenüber scannt den QR-Code. Optional in den Share settings "
        "**Auto-swap when you scan** aktivieren – dann tauscht ihr beim Scannen gegenseitig die Karten.",
        "- Wichtig: Ein Kartentausch schickt **keine** Kontaktanfrage. Danach gezielt vernetzen und kurz nachfassen.",
        "- Gesammelte Karten: My Network → Manage My Network → Business Cards.",
        "",
        "## 4. Passend zur gedruckten Karte",
        "",
        f"Die gedruckte bzw. digitale Karte aus diesem Skill nutzt Layout **{report.get('layout')}**, "
        f"Muster **{report.get('pattern')}** und Farbschema **{report.get('theme')}**. Ihr QR-Code führt direkt zu "
        f"{(report.get('qr') or {}).get('url', profile.get('linkedin_url', ''))} – so passen Papier, Bild und App zusammen.",
        "",
        f"Quellen: LinkedIn-Hilfe {HELP_URL} · LinkedIn-Newsroom vom 15.10.2026 {NEWS_URL}",
        "",
        "Hinweis: Dieses Projekt ist nicht mit LinkedIn verbunden. LinkedIn ist eine Marke der LinkedIn Corporation.",
        "",
    ]
    return "\n".join(lines)
