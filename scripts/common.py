"""Gemeinsame Helfer: Farben, Kontrast, Paletten, Text, URL-Prüfung.

Nur Standardbibliothek. Alle Funktionen sind ohne Netzwerk nutzbar.
"""
from __future__ import annotations

import colorsys
import re
from xml.sax.saxutils import escape as _xml_escape

# ---------------------------------------------------------------------------
# Farben
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def normalize_hex(value: str) -> str:
    """'#abc' / 'abc' / '#AABBCC' -> '#AABBCC'. Wirft ValueError bei ungültigen Werten."""
    if not isinstance(value, str):
        raise ValueError(f"Keine Farbe: {value!r}")
    m = _HEX_RE.match(value.strip())
    if not m:
        raise ValueError(f"Ungültige Hex-Farbe: {value!r}")
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.upper()


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    h = normalize_hex(value)[1:]
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(rgb) -> str:
    r, g, b = (max(0, min(255, round(c))) for c in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def relative_luminance(value: str) -> float:
    def channel(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = hex_to_rgb(value)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(a: str, b: str) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def mix(a: str, b: str, t: float) -> str:
    """t=0 -> a, t=1 -> b."""
    ra, rb = hex_to_rgb(a), hex_to_rgb(b)
    return rgb_to_hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def _hls(value: str):
    r, g, b = (c / 255 for c in hex_to_rgb(value))
    return colorsys.rgb_to_hls(r, g, b)


def _from_hls(h, l, s) -> str:  # noqa: E741
    r, g, b = colorsys.hls_to_rgb(h, max(0.0, min(1.0, l)), max(0.0, min(1.0, s)))
    return rgb_to_hex((r * 255, g * 255, b * 255))


def with_lightness(value: str, lightness: float) -> str:
    h, _, s = _hls(value)
    return _from_hls(h, lightness, s)


def is_light(value: str) -> bool:
    return relative_luminance(value) > 0.4


def ensure_contrast(color: str, against: str, target: float) -> str:
    """Verschiebt nur die Helligkeit von `color`, bis der Kontrast zu `against` reicht.

    Der Farbton bleibt erhalten. Reicht keine Richtung, wird Schwarz/Weiß geliefert.
    """
    color = normalize_hex(color)
    if contrast_ratio(color, against) >= target:
        return color
    h, l, s = _hls(color)  # noqa: E741
    direction = -1 if is_light(against) else 1
    for d in (direction, -direction):
        ll = l
        for _ in range(100):
            ll += d * 0.01
            if ll < 0 or ll > 1:
                break
            candidate = _from_hls(h, ll, s)
            if contrast_ratio(candidate, against) >= target:
                return candidate
    return "#000000" if contrast_ratio("#000000", against) >= contrast_ratio("#FFFFFF", against) else "#FFFFFF"


def best_on(background: str, candidates=("#FFFFFF", "#0B0F19")) -> str:
    return max(candidates, key=lambda c: contrast_ratio(c, background))


def hue_family_de(value: str) -> str:
    """Grobe deutsche Farbfamilie für Anleitungen ("wähle ein Feld aus der Familie …")."""
    h, l, s = _hls(value)  # noqa: E741
    if l < 0.12:
        return "Schwarz"
    if l > 0.94:
        return "Weiß"
    if s < 0.12:
        return "Grau"
    deg = h * 360
    if deg < 15 or deg >= 345:
        return "Rot"
    if deg < 42:
        return "Orange"
    if deg < 65:
        return "Gelb"
    if deg < 160:
        return "Grün"
    if deg < 195:
        return "Türkis"
    if deg < 255:
        return "Blau"
    if deg < 290:
        return "Violett"
    return "Pink"


def build_palette(brand: dict, theme: str = "light") -> dict:
    """Leitet aus den Markenfarben eine lesbare Kartenpalette ab.

    Garantien (getestet): Text >= 7:1, Nebentext >= 4,5:1, Text auf Primärfläche
    >= 4,5:1, Akzenttext >= 4,5:1, QR-Code dunkel auf hell >= 7:1.
    """
    if theme not in ("light", "dark", "brand"):
        raise ValueError(f"Unbekanntes Farbschema: {theme!r} (light, dark, brand)")
    colors = (brand or {}).get("colors") or {}
    primary = normalize_hex(colors.get("primary") or "#0A66C2")
    secondary = normalize_hex(colors.get("secondary") or primary)
    brand_bg = colors.get("background")
    brand_text = colors.get("text")

    # Primärfläche: muss eine lesbare Schrift tragen können.
    on_primary = best_on(primary)
    if contrast_ratio(on_primary, primary) < 4.5:
        primary_fill = ensure_contrast(primary, on_primary, 4.5)
    else:
        primary_fill = primary

    if theme == "light":
        bg = normalize_hex(brand_bg) if brand_bg and relative_luminance(brand_bg) > 0.8 else "#FFFFFF"
        text_base = brand_text if brand_text and not is_light(brand_text) else "#111827"
    elif theme == "dark":
        if brand_bg and relative_luminance(brand_bg) < 0.03:
            bg = normalize_hex(brand_bg)
        else:
            h, _, s = _hls(primary)
            bg = _from_hls(h, 0.09, min(s, 0.55))
        text_base = "#F8FAFC"
    else:  # brand
        bg = primary_fill
        text_base = on_primary

    text = ensure_contrast(text_base, bg, 4.5 if theme == "brand" else 7.0)
    muted = None
    for t in (0.42, 0.36, 0.30, 0.24, 0.18, 0.12, 0.06, 0.0):
        candidate = mix(text, bg, t)
        if contrast_ratio(candidate, bg) >= 4.5:
            muted = candidate
            break
    if theme == "brand":
        # Zweitfarbe nur, wenn sie von sich aus lesbar ist; sonst Text in Grundfarbe statt verfälschter Farbe.
        accent_text = secondary if contrast_ratio(secondary, bg) >= 4.5 else text
    else:
        accent_text = ensure_contrast(primary, bg, 4.5)

    # QR: immer dunkle Module auf weißer Kachel.
    qr_light = "#FFFFFF"
    qr_dark = min((text, primary, "#0B0F19"), key=relative_luminance)
    qr_dark = ensure_contrast(qr_dark, qr_light, 7.0)

    pattern_color = on_primary if theme == "brand" else (primary if theme == "light" else with_lightness(primary, 0.7))
    return {
        "theme": theme,
        "bg": bg,
        "text": text,
        "muted": muted,
        "primary": primary_fill,
        "primary_raw": primary,
        "secondary": secondary,
        "on_primary": on_primary,
        "accent_text": accent_text,
        "qr_dark": qr_dark,
        "qr_light": qr_light,
        "pattern": pattern_color,
    }


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_NARROW = set("iljtfr.,:;!|'()[]{} ")
_WIDE = set("mwMW@%")


def text_width(text: str, size: float, bold: bool = False) -> float:
    """Konservative Breitenschätzung ohne Fontdatei (eher zu breit als zu schmal)."""
    w = 0.0
    for ch in text:
        if ch in _NARROW:
            w += 0.32
        elif ch in _WIDE:
            w += 0.88
        elif ch.isupper():
            w += 0.69
        elif ch.isdigit():
            w += 0.58
        else:
            w += 0.56
    return w * size * (1.07 if bold else 1.0) * 1.04


def fit_text(text: str, max_width: float, size: float, min_size: float, max_lines: int = 1, bold: bool = False):
    """Verkleinert, bricht um und kürzt notfalls mit '…'.

    Rückgabe: (zeilen, schriftgröße, gekürzt: bool). Die Zeilen passen immer in max_width.
    """
    text = " ".join((text or "").split())
    if not text:
        return [], size, False
    step = max(size * 0.04, 0.01)
    s = size
    while s >= min_size - 1e-9:
        lines = _wrap(text, max_width, s, max_lines, bold)
        if lines is not None:
            return lines, s, False
        s -= step
    s = min_size
    lines = _wrap_truncate(text, max_width, s, max_lines, bold)
    return lines, s, True


def _tokens(text):
    """Wörter; Bindestrich-Komposita dürfen nach dem Bindestrich umbrechen."""
    out = []
    for word in text.split(" "):
        parts = re.findall(r"[^-]+-|[^-]+$|-", word)
        out.extend(parts or [word])
        out.append(" ")
    return [t for t in out[:-1]]


def _join(current, token):
    if token == " ":
        return current
    if not current:
        return token
    return current + token if current.endswith("-") else f"{current} {token}"


def _wrap(text, max_width, size, max_lines, bold):
    words = [t for t in _tokens(text) if t != " "]
    lines, current = [], ""
    for word in words:
        trial = _join(current, word)
        if text_width(trial, size, bold) <= max_width:
            current = trial
            continue
        if not current:  # einzelnes Wort zu lang
            return None
        lines.append(current)
        current = word
        if text_width(current, size, bold) > max_width:
            return None
    if current:
        lines.append(current)
    return lines if len(lines) <= max_lines else None


def _wrap_truncate(text, max_width, size, max_lines, bold):
    words = [t for t in _tokens(text) if t != " "]
    lines, current = [], ""
    i = 0
    while i < len(words) and len(lines) < max_lines:
        trial = _join(current, words[i])
        if text_width(trial, size, bold) <= max_width:
            current = trial
            i += 1
        else:
            if not current:
                current = words[i]
                while current and text_width(current + "…", size, bold) > max_width:
                    current = current[:-1]
                current += "…"
                i += 1
                lines.append(current)
                current = ""
                if i >= len(words):
                    return lines
                continue
            lines.append(current)
            current = ""
    if current and len(lines) < max_lines:
        lines.append(current)
    if i < len(words) or not lines:
        last = lines[-1] if lines else ""
        while last and text_width(last + " …", size, bold) > max_width:
            last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
        lines = lines[:-1] + [(last.rstrip(" ,;:–-") + " …").strip()]
    return lines


def esc(text) -> str:
    return _xml_escape(str(text), {'"': "&quot;", "'": "&apos;"})


def initials(name: str) -> str:
    parts = [p for p in re.split(r"[\s\-]+", name or "") if p and p[0].isalpha()]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


# ---------------------------------------------------------------------------
# LinkedIn-URL
# ---------------------------------------------------------------------------

_LI_RE = re.compile(
    r"^(?:https?://)?(?:[a-z]{2,3}\.|www\.)?linkedin\.com/in/([A-Za-z0-9\-_%]{2,100})/?(?:[?#].*)?$",
    re.IGNORECASE,
)


def validate_linkedin_url(url) -> str:
    """Normalisiert eine öffentliche Profil-URL auf https://www.linkedin.com/in/<slug>/."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("LinkedIn-Profil-URL fehlt (Format: https://www.linkedin.com/in/<name>/).")
    m = _LI_RE.match(url.strip())
    if not m:
        raise ValueError(f"Keine gültige LinkedIn-Profil-URL: {url!r} (erwartet: https://www.linkedin.com/in/<name>/)")
    return f"https://www.linkedin.com/in/{m.group(1)}/"
