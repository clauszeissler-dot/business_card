"""Übersetzt das CI in konkrete Einstellungen für die native LinkedIn Business Card (Deutsch/Englisch).

LinkedIn bietet dafür keine API. Die Karte wird nur in der LinkedIn-App gestaltet;
dieser Text ist eine Klick-Anleitung mit passenden Auswahlen.
Faktenquelle: references/linkedin-native-card.md (Stand 20.11.2026).
"""
from __future__ import annotations

from common import hue_family_de, normalize_hex

FACT_DATE = {"de": "20.11.2026", "en": "20 November 2026"}
HELP_URL = "https://www.linkedin.com/help/linkedin/answer/a16648713"
NEWS_URL = "https://news.linkedin.com/2026/new-ways-to-build-meaningful-connections"

HUE_EN = {"Rot": "Red", "Orange": "Orange", "Gelb": "Yellow", "Grün": "Green", "Türkis": "Teal", "Blau": "Blue",
          "Violett": "Purple", "Pink": "Pink", "Grau": "Grey", "Schwarz": "Black", "Weiß": "White"}

T = {
    "de": {
        "title": "LinkedIn Business Card einstellen",
        "intro": ("Stand der Fakten: {date}. Die Funktion gibt es laut LinkedIn-Hilfe nur in der LinkedIn-App "
                  "(englische Oberfläche) und sie wird schrittweise ausgerollt. Falls dir Menüs fehlen: App aktualisieren "
                  "oder später erneut prüfen. Quelle: {help}"),
        "noapi": ("Die Karte lässt sich nicht automatisch befüllen – LinkedIn bietet dafür keine Schnittstelle. "
                  "Diese Anleitung sagt dir, was du in der App antippst, damit sie zu deinem CI passt."),
        "h_open": "## 1. Karte öffnen",
        "open": ["In der LinkedIn-App oben links auf dein **Profilfoto** tippen.",
                 "Oben im Profil auf den **QR-Code** tippen. Die Karte erscheint; wischen zeigt Vorder- und Rückseite.",
                 "Auf das **Edit**-Symbol tippen. Unten erscheinen die Optionen."],
        "h_opts": "## 2. Optionen wählen",
        "info": "**Info:** Headline prüfen",
        "info_long": (" – deine Headline hat {n} Zeichen. Für die Karte auf etwa 40–70 Zeichen kürzen, "
                      "z. B. Rolle + Nutzen in einem Satz."),
        "info_ok": " („{h}“ passt).",
        "info_none": " (eine kurze Rolle + Nutzen, 40–70 Zeichen).",
        "info_tail": " Häkchen bei **Company or school**{c} und **Location** setzen, wenn beides auf die Karte soll.",
        "layout": ("**Layout:** {l}. Fotostil passend zu deiner Karte: **{p}** (circle = Kreis, rounded = abgerundet, "
                   "square = eckig, hexagon = Sechseck – das nächstliegende wählen)."),
        "font": "**Font:** {a}. Deine Markenschrift ist „{f}“ ({s}). LinkedIn bietet eine feste Auswahl; nimm die ähnlichste.",
        "colors": "**Colors:** Vorderseite das Farbfeld aus der Familie **{fam}**, das {hex} am nächsten kommt.",
        "colors_back": (" Dann **doppelt auf die Farbauswahl tippen**, um zur Rückseite zu wechseln, und dort "
                        "**{fam}** (nah an {hex}) wählen – oder dieselbe Farbe für einen ruhigen Auftritt."),
        "colors_back_none": " Doppeltippen auf die Farbauswahl wechselt zur Rückseite; dort dieselbe Familie oder Weiß/Grau wählen.",
        "colors_nohex": " Eigene Hex-Werte sind laut Hilfe nicht vorgesehen.",
        "colors_unknown": ("**Colors:** Keine Markenfarbe bekannt – wähle eine ruhige, dunkle Farbe (Blau, Grau, Grün). "
                           "Doppeltippen auf die Farbauswahl wechselt zwischen Vorder- und Rückseite."),
        "pattern": "**Pattern:** {p}. Im Zweifel dezent: Name und QR-Code müssen gut lesbar bleiben.",
        "stickers": ("**Stickers and Doodle** (nur Rückseite): Tipp fürs CI – ein Foto deines **Logos** als *cutout* "
                     "einfügen; optional die **Unterschrift** als Doodle. Sparsam einsetzen: höchstens ein bis zwei Elemente."),
        "save": "Wischen, um beide Seiten zu prüfen, dann **Save** tippen.",
        "h_wallet": "## 3. Ins Wallet legen und teilen",
        "wallet": ["**Add to Wallet** antippen und den Anweisungen folgen (Apple Wallet oder Google Wallet).",
                   "Auf Events: Karte zeigen, Gegenüber scannt den QR-Code. Optional in den Share settings "
                   "**Auto-swap when you scan** aktivieren – dann tauscht ihr beim Scannen gegenseitig die Karten.",
                   "Wichtig: Ein Kartentausch schickt **keine** Kontaktanfrage. Danach gezielt vernetzen und kurz nachfassen.",
                   "Gesammelte Karten: My Network → Manage My Network → Business Cards."],
        "h_match": "## 4. Passend zur gedruckten Karte",
        "match": ("Die gedruckte bzw. digitale Karte aus diesem Skill nutzt Layout **{l}**, Muster **{p}** und Farbschema "
                  "**{t}**. Ihr QR-Code führt direkt zu {u} – so passen Papier, Bild und App zusammen."),
        "sources": "Quellen: LinkedIn-Hilfe {help} · LinkedIn-Newsroom vom 15.10.2026 {news}",
        "disclaimer": "Hinweis: Dieses Projekt ist nicht mit LinkedIn verbunden. LinkedIn ist eine Marke der LinkedIn Corporation.",
        "fonts": {"sans": "eine schlichte, serifenlose Schrift (Sans)",
                  "serif": "eine Schrift mit Serifen (Serif) – wirkt klassisch und hochwertig",
                  "mono": "eine technische Schrift mit gleicher Zeichenbreite (Mono), falls angeboten – sonst Sans",
                  "script": "eine handschriftliche Schrift nur für Akzente; für gute Lesbarkeit eher Sans"},
        "patterns": {"none": "kein Muster – das Logo und die Farbe tragen die Karte",
                     "dots": "ein Punkt- oder Rastermuster", "grid": "ein feines Linien- oder Rastermuster",
                     "diagonal": "ein Muster mit diagonalen Linien oder Streifen",
                     "waves": "ein Muster mit Wellen oder weichen, runden Formen",
                     "rings": "ein Muster mit Kreisen oder Ringen",
                     "circuit": "ein technisches, geometrisches Muster (Linien/Knoten)",
                     "chevron": "ein Zickzack- oder Winkelmuster"},
        "layouts": {"classic": "ein ruhiges Layout mit linksbündigem Text",
                    "split": "ein Layout mit großem Profilfoto auf einer Seite",
                    "centered": "ein zentriertes Layout mit Foto oben",
                    "diagonal": "ein dynamisches Layout mit Foto auf der Farbfläche",
                    "minimal": "das schlichteste Layout mit viel Weißraum",
                    "profile": "ein Layout mit Foto auf einem farbigen Band, ähnlich dem Profilkopf"},
    },
    "en": {
        "title": "Set up your LinkedIn Business Card",
        "intro": ("Facts as of {date}. According to LinkedIn Help, the feature is only available in the LinkedIn mobile "
                  "app (in English) and is rolling out gradually. If menus are missing, update the app or check again "
                  "later. Source: {help}"),
        "noapi": ("The card cannot be filled in automatically – LinkedIn offers no interface for it. "
                  "This guide tells you what to tap in the app so the card matches your brand."),
        "h_open": "## 1. Open your card",
        "open": ["Tap your **profile photo** in the upper-left corner of the LinkedIn app.",
                 "Tap the **QR code** at the top of your profile. Your card opens; swipe to see front and back.",
                 "Tap the **Edit** icon. The options appear at the bottom of the screen."],
        "h_opts": "## 2. Choose the options",
        "info": "**Info:** Check your headline",
        "info_long": (" – your headline has {n} characters. For the card, shorten it to about 40–70 characters, "
                      "e.g. role + value in one sentence."),
        "info_ok": " (“{h}” works).",
        "info_none": " (a short role + value, 40–70 characters).",
        "info_tail": " Tick **Company or school**{c} and **Location** if you want both on the card.",
        "layout": ("**Layout:** {l}. Photo style to match your card: **{p}** (circle, rounded, square, hexagon – "
                   "pick the closest one)."),
        "font": "**Font:** {a}. Your brand font is “{f}” ({s}). LinkedIn offers a fixed set; pick the closest one.",
        "colors": "**Colors:** For the front, pick the swatch from the **{fam}** family that is closest to {hex}.",
        "colors_back": (" Then **double-tap the colour options** to switch to the back and pick **{fam}** (close to {hex}) "
                        "– or the same colour for a calm look."),
        "colors_back_none": " Double-tap the colour options to switch to the back; choose the same family or white/grey there.",
        "colors_nohex": " According to LinkedIn Help, custom hex values are not offered.",
        "colors_unknown": ("**Colors:** No brand colour known – choose a calm, dark colour (blue, grey, green). "
                           "Double-tap the colour options to switch between front and back."),
        "pattern": "**Pattern:** {p}. When in doubt, keep it subtle: your name and the QR code must stay easy to read.",
        "stickers": ("**Stickers and Doodle** (back only): brand tip – add a photo of your **logo** as a *cutout*; "
                     "optionally add your **signature** as a doodle. Use one or two elements at most."),
        "save": "Swipe to check both sides, then tap **Save**.",
        "h_wallet": "## 3. Add to your wallet and share",
        "wallet": ["Tap **Add to Wallet** and follow the on-screen steps (Apple Wallet or Google Wallet).",
                   "At events: show your card and let the other person scan the QR code. Optionally turn on "
                   "**Auto-swap when you scan** in Share settings so you swap cards both ways.",
                   "Important: swapping cards does **not** send a connection request. Connect afterwards and follow up.",
                   "Collected cards: My Network → Manage My Network → Business Cards."],
        "h_match": "## 4. Matching your printed card",
        "match": ("The printed or digital card from this skill uses layout **{l}**, pattern **{p}** and colour theme "
                  "**{t}**. Its QR code links straight to {u} – so paper, image and app work together."),
        "sources": "Sources: LinkedIn Help {help} · LinkedIn Newsroom, 15 Oct 2026 {news}",
        "disclaimer": "Note: This project is not affiliated with LinkedIn. LinkedIn is a trademark of LinkedIn Corporation.",
        "fonts": {"sans": "a clean sans-serif font (Sans)",
                  "serif": "a serif font (Serif) – classic and premium",
                  "mono": "a technical monospaced font (Mono) if available – otherwise Sans",
                  "script": "a handwritten font only for accents; for readability rather Sans"},
        "patterns": {"none": "no pattern – logo and colour carry the card",
                     "dots": "a dot or grid pattern", "grid": "a fine line or grid pattern",
                     "diagonal": "a pattern with diagonal lines or stripes",
                     "waves": "a pattern with waves or soft, round shapes",
                     "rings": "a pattern with circles or rings",
                     "circuit": "a technical, geometric pattern (lines/nodes)",
                     "chevron": "a zigzag or chevron pattern"},
        "layouts": {"classic": "a calm layout with left-aligned text",
                    "split": "a layout with a large profile photo on one side",
                    "centered": "a centred layout with the photo on top",
                    "diagonal": "a dynamic layout with the photo on the colour area",
                    "minimal": "the simplest layout with lots of white space",
                    "profile": "a layout with the photo on a coloured band, similar to the profile header"},
    },
}


def _font_style(brand, report) -> str:
    style = (brand or {}).get("font_style")
    if style in T["de"]["fonts"]:
        return style
    try:
        from extract_ci import classify_font

        return classify_font((report.get("fonts") or {}).get("heading", ""))
    except Exception:  # pragma: no cover - Fallback ohne extract_ci
        return "sans"


def _family(hexcolor, lang):
    fam = hue_family_de(hexcolor)
    return HUE_EN[fam] if lang == "en" else fam


def recommend_native(profile: dict, brand: dict, report: dict, lang: str | None = None) -> str:
    lang = lang or report.get("lang") or "de"
    t = T["en" if lang == "en" else "de"]
    lang = "en" if lang == "en" else "de"
    colors = (brand or {}).get("colors") or {}
    primary, secondary = colors.get("primary"), colors.get("secondary")
    style = _font_style(brand, report)
    head = profile.get("headline", "") or ""
    out = [f"# {t['title']} – {profile.get('name', '')}", "",
           t["intro"].format(date=FACT_DATE[lang], help=HELP_URL), "", t["noapi"], "", t["h_open"], ""]
    out += [f"{i}. {line}" for i, line in enumerate(t["open"], 1)]
    out += ["", t["h_opts"], ""]
    info = t["info"]
    if len(head) > 70:
        info += t["info_long"].format(n=len(head))
    else:
        info += t["info_ok"].format(h=head) if head else t["info_none"]
    company = f" ({profile['company']})" if profile.get("company") else ""
    out.append("- " + info + t["info_tail"].format(c=company))
    out.append("- " + t["layout"].format(l=t["layouts"].get(report.get("layout"), t["layouts"]["classic"]),
                                          p=report.get("photo_shape", "circle")))
    style_label = {"sans": "Sans", "serif": "Serif", "mono": "Mono", "script": "Script"}[style]
    out.append("- " + t["font"].format(a=t["fonts"][style], f=(report.get("fonts") or {}).get("heading", "–"),
                                        s=style_label))
    if primary:
        p = normalize_hex(primary)
        line = t["colors"].format(fam=_family(p, lang), hex=p)
        if secondary:
            s = normalize_hex(secondary)
            line += t["colors_back"].format(fam=_family(s, lang), hex=s)
        else:
            line += t["colors_back_none"]
        out.append("- " + line + t["colors_nohex"])
    else:
        out.append("- " + t["colors_unknown"])
    out.append("- " + t["pattern"].format(p=t["patterns"].get(report.get("pattern"), t["patterns"]["none"])))
    out.append("- " + t["stickers"])
    out += ["", t["save"], "", t["h_wallet"], ""]
    out += [f"- {line}" for line in t["wallet"]]
    out += ["", t["h_match"], "",
            t["match"].format(l=report.get("layout"), p=report.get("pattern"), t=report.get("theme"),
                              u=(report.get("qr") or {}).get("url", profile.get("linkedin_url", ""))),
            "", t["sources"].format(help=HELP_URL, news=NEWS_URL), "", t["disclaimer"], ""]
    return "\n".join(out)
