#!/usr/bin/env python3
"""Erzeugt eine Business Card (Vorder- und Rückseite) im CI einer Marke.

Ausgabe: SVG (Master), optional PNG und PDF über rsvg-convert, preview.html,
report.json und linkedin-native-card.md (Einstellungsanleitung für die
native LinkedIn Business Card).

Beispiel:
    uv run scripts/make_card.py --profile profile.json --brand brand.json \
        --layout split --pattern circuit --theme light --format eu --out out/
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

import segno

sys.path.insert(0, str(Path(__file__).resolve().parent))  # auch mit python -I lauffähig
from common import (  # noqa: E402
    build_palette,
    contrast_ratio,
    ensure_contrast,
    esc,
    fit_text,
    initials,
    is_light,
    mix,
    relative_luminance,
    validate_linkedin_url,
)

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "assets" / "icons" / "lucide"

FORMATS = {
    "eu": {"w": 85.0, "h": 55.0, "unit": "mm", "bleed": 3.0, "print": True, "label": "Visitenkarte EU 85 × 55 mm"},
    "us": {"w": 88.9, "h": 50.8, "unit": "mm", "bleed": 3.175, "print": True, "label": "Business Card US 3,5 × 2 in"},
    "wallet": {"w": 85.6, "h": 53.98, "unit": "mm", "bleed": 0.0, "print": False, "label": "Scheckkarte ISO/IEC 7810 ID-1 (digital)"},
    "share": {"w": 1200.0, "h": 627.0, "unit": "px", "bleed": 0.0, "print": False, "label": "Teilen-Bild 1200 × 627 px (LinkedIn-Link-Format)"},
}

LAYOUTS = {
    "classic": "Klassisch: Akzentbalken links, Logo oben, Name unten links",
    "split": "Geteilt: farbige Seitenfläche mit Foto/Monogramm, Text rechts",
    "centered": "Zentriert: Foto oben mittig, Text zentriert, ruhig und formell",
    "diagonal": "Diagonal: schräge Farbfläche, dynamisch, Foto in der Fläche",
    "minimal": "Minimal: viel Weißraum, großer Name, Muster nur als Eckmotiv",
    "profile": "Profil: Farbband oben, Foto auf der Bandkante (nah an LinkedIn)",
}

PATTERNS = {
    "none": "Kein Muster",
    "dots": "Punktraster – freundlich, ruhig",
    "grid": "Linienraster – technisch, präzise",
    "diagonal": "Diagonale Linien – Bewegung, Dynamik",
    "waves": "Wellen – weich, kreativ, Gesundheit/Natur",
    "rings": "Konzentrische Ringe – Fokus, Beratung",
    "circuit": "Leiterbahnen – Tech, KI, Software",
    "chevron": "Zickzack – Energie, Handel, Sport",
}

CORNERS = {"sharp": 0.0, "soft": 1.5, "round": 3.5}
PHOTO_SHAPES = ("circle", "rounded", "square", "hexagon")
THEMES = ("light", "dark", "brand")
INTENSITY = {"subtle": 0.07, "normal": 0.12, "strong": 0.2}

MAX_IMAGE_BYTES = 1024 * 1024
ICONS = {"email": "mail", "phone": "phone", "website": "globe", "location": "map-pin", "company": "building-2"}

LABELS = {
    "de": {"qr": "Scannen & vernetzen", "card": "Business Card"},
    "en": {"qr": "Scan to connect", "card": "Business card"},
}


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------

def _fmt(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


def _safe_font(name, fallback):
    name = re.sub(r"[^A-Za-z0-9 \-]", "", str(name or "")).strip()
    return name or fallback


def _load_image(path, warnings, label, allow_svg=True):
    """Liest ein lokales Bild als data:-URI. Nie inline als Markup."""
    if not path:
        return None
    p = Path(path).expanduser()
    if not p.is_file():
        warnings.append(f"{label} nicht gefunden: {p.name}")
        return None
    size = p.stat().st_size
    if size > MAX_IMAGE_BYTES:
        warnings.append(f"{label} ignoriert: größer als 1 MB ({size // 1024} KB). Bitte verkleinern.")
        return None
    data = p.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif data[:3] == b"\xff\xd8\xff":
        mime = "image/jpeg"
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        mime = "image/webp"
    elif data[:6] in (b"GIF87a", b"GIF89a"):
        mime = "image/gif"
    elif allow_svg and b"<svg" in data[:4096].lower():
        mime = "image/svg+xml"
    else:
        warnings.append(f"{label} ignoriert: Format nicht erkannt (PNG, JPEG, WebP, GIF{', SVG' if allow_svg else ''}).")
        return None
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


_ICON_CACHE: dict[str, str] = {}


def _icon_inner(name):
    if name not in _ICON_CACHE:
        raw = (ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
        raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
        start = raw.index(">", raw.index("<svg")) + 1
        end = raw.rindex("</svg>")
        _ICON_CACHE[name] = " ".join(raw[start:end].split())
    return _ICON_CACHE[name]


class Canvas:
    def __init__(self, fmt_key, side, uid):
        f = FORMATS[fmt_key]
        self.f = f
        self.b = f["bleed"]
        self.w, self.h = f["w"], f["h"]
        self.cw, self.ch = self.w + 2 * self.b, self.h + 2 * self.b
        self.s = self.h / 55.0
        self.m = 4.5 * self.s
        self.defs: list[str] = []
        self.body: list[str] = []
        self.uid = f"{uid}-{side}"
        self._n = 0
        self.min_contrast = 99.0
        self.fits = True
        self.truncated: list[str] = []
        self.surfaces: dict[str, tuple[str, float]] = {}

    # Inhaltsbereich (Trim minus Sicherheitsabstand)
    @property
    def x0(self):
        return self.b + self.m

    @property
    def y0(self):
        return self.b + self.m

    @property
    def x1(self):
        return self.b + self.w - self.m

    @property
    def y1(self):
        return self.b + self.h - self.m

    def id(self, prefix):
        self._n += 1
        return f"{prefix}-{self.uid}-{self._n}"

    def add(self, s):
        self.body.append(s)

    def rect(self, x, y, w, h, fill, rx=0, extra=""):
        r = f' rx="{_fmt(rx)}"' if rx else ""
        self.add(f'<rect x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(w)}" height="{_fmt(h)}"{r} fill="{fill}"{extra}/>')

    def text_lines(self, x, y_top, lines, size, color, family, weight=400, anchor="start", lh=1.2, surface=None,
                   min_ratio=4.5):
        """Zeichnet Zeilen ab Oberkante y_top. Liefert die Unterkante."""
        if surface:
            worst = surface
            if surface in self.surfaces:
                pc, op = self.surfaces[surface]
                worst = mix(surface, pc, op)
            color = ensure_contrast(color, worst, min_ratio)
            self.min_contrast = min(self.min_contrast, contrast_ratio(color, surface), contrast_ratio(color, worst))
        y = y_top
        for line in lines:
            y += size * 0.86
            self.add(
                f'<text x="{_fmt(x)}" y="{_fmt(y)}" font-family="{family}" font-size="{_fmt(size)}" '
                f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{esc(line)}</text>'
            )
            y += size * (lh - 0.86)
        return y

    def svg(self, title, corners_r):
        unit = self.f["unit"]
        wattr = f"{_fmt(self.cw)}{unit if unit == 'mm' else ''}"
        hattr = f"{_fmt(self.ch)}{unit if unit == 'mm' else ''}"
        body = "".join(self.body)
        if corners_r and not self.f["print"]:
            cid = self.id("card")
            self.defs.append(
                f'<clipPath id="{cid}"><rect width="{_fmt(self.cw)}" height="{_fmt(self.ch)}" rx="{_fmt(corners_r)}"/></clipPath>'
            )
            body = f'<g clip-path="url(#{cid})">{body}</g>'
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{wattr}" height="{hattr}" '
            f'viewBox="0 0 {_fmt(self.cw)} {_fmt(self.ch)}" role="img" aria-label="{esc(title)}">'
            f"<title>{esc(title)}</title><defs>{''.join(self.defs)}</defs>{body}</svg>"
        )


# ---------------------------------------------------------------------------
# Muster
# ---------------------------------------------------------------------------

def _pattern_def(c: Canvas, kind, color, opacity):
    """Definiert ein Muster und liefert fill-Wert (url(#…)) oder None."""
    if kind == "none":
        return None
    s = c.s
    pid = c.id("pat")
    sw = 0.22 * s
    common = f'stroke="{color}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="round"'
    if kind == "dots":
        t = 3.2 * s
        inner = f'<circle cx="{_fmt(t / 2)}" cy="{_fmt(t / 2)}" r="{_fmt(0.5 * s)}" fill="{color}"/>'
        size = (t, t)
    elif kind == "grid":
        t = 4.0 * s
        inner = f'<path d="M{_fmt(t)} 0V{_fmt(t)}M0 {_fmt(t)}H{_fmt(t)}" {common}/>'
        size = (t, t)
    elif kind == "diagonal":
        t = 2.8 * s
        size = (2 * t, 2 * t)
        inner = f'<path d="M0 {_fmt(2 * t)}L{_fmt(2 * t)} 0M{_fmt(-t)} {_fmt(t)}L{_fmt(t)} {_fmt(-t)}M{_fmt(t)} {_fmt(3 * t)}L{_fmt(3 * t)} {_fmt(t)}" {common}/>'
    elif kind == "waves":
        tw, th = 8.0 * s, 3.2 * s
        a = 0.9 * s
        y = th / 2
        inner = (f'<path d="M0 {_fmt(y)} C{_fmt(tw * 0.25)} {_fmt(y - 2 * a)} {_fmt(tw * 0.25)} {_fmt(y + 2 * a)} '
                 f'{_fmt(tw * 0.5)} {_fmt(y)} S{_fmt(tw * 0.75)} {_fmt(y - 2 * a)} {_fmt(tw)} {_fmt(y)}" {common}/>')
        size = (tw, th)
    elif kind == "chevron":
        tw, th = 5.0 * s, 3.0 * s
        inner = f'<path d="M0 {_fmt(th * 0.75)}L{_fmt(tw / 2)} {_fmt(th * 0.25)}L{_fmt(tw)} {_fmt(th * 0.75)}" {common}/>'
        size = (tw, th)
    elif kind == "circuit":
        t = 14.0 * s
        r = 0.7 * s
        p = lambda v: _fmt(v * t)  # noqa: E731
        inner = (
            f'<path d="M0 {p(.2)}H{p(.35)}L{p(.5)} {p(.35)}V{p(.62)}M{p(.5)} {p(.62)}H{p(.82)}'
            f'M{p(.18)} {p(1)}V{p(.75)}L{p(.3)} {p(.63)}M{p(.7)} 0V{p(.18)}L{p(.85)} {p(.33)}H{p(1)}" {common}/>'
            f'<circle cx="{p(.82)}" cy="{p(.62)}" r="{_fmt(r)}" {common}/>'
            f'<circle cx="{p(.3)}" cy="{p(.63)}" r="{_fmt(r)}" {common}/>'
            f'<circle cx="{p(.35)}" cy="{p(.2)}" r="{_fmt(r * .6)}" fill="{color}"/>'
        )
        size = (t, t)
    elif kind == "rings":
        return ("rings", color, opacity)
    else:
        raise ValueError(f"Unbekanntes Muster: {kind!r}")
    c.defs.append(
        f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{_fmt(size[0])}" height="{_fmt(size[1])}">{inner}</pattern>'
    )
    return f"url(#{pid})"


def paint_pattern(c: Canvas, kind, color, opacity, clip_shape, surface, center=None):
    """Malt ein Muster in eine Clip-Form (SVG-Element ohne fill)."""
    if kind == "none":
        return
    base = surface
    # Helles Muster auf mittelheller Fläche würde weißen Text schwächen:
    # dann Ton-in-Ton dunkler zeichnen (erhöht den Kontrast statt ihn zu senken).
    if relative_luminance(color) > relative_luminance(base) and contrast_ratio("#FFFFFF", base) < 10:
        color = mix(base, "#000000", 0.5)
        opacity = min(opacity * 2.2, 0.4)
    c.surfaces[surface] = (color, opacity)
    cid = c.id("clip")
    c.defs.append(f'<clipPath id="{cid}">{clip_shape}</clipPath>')
    fill = _pattern_def(c, kind, color, opacity)
    if isinstance(fill, tuple):  # rings
        cx, cy = center or (c.cw, c.ch)
        sw = 0.25 * c.s
        circles = "".join(
            f'<circle cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(r * 3.6 * c.s)}" fill="none" stroke="{color}" stroke-width="{_fmt(sw)}"/>'
            for r in range(1, 40)
        )
        c.add(f'<g clip-path="url(#{cid})" opacity="{opacity}">{circles}</g>')
        return
    c.add(f'<g clip-path="url(#{cid})" opacity="{opacity}"><rect width="{_fmt(c.cw)}" height="{_fmt(c.ch)}" fill="{fill}"/></g>')


# ---------------------------------------------------------------------------
# Formen: Foto / Monogramm
# ---------------------------------------------------------------------------

def _shape_markup(shape, cx, cy, size):
    r = size / 2
    if shape == "circle":
        return f'<circle cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(r)}"/>'
    if shape == "rounded":
        return f'<rect x="{_fmt(cx - r)}" y="{_fmt(cy - r)}" width="{_fmt(size)}" height="{_fmt(size)}" rx="{_fmt(size * 0.24)}"/>'
    if shape == "square":
        return f'<rect x="{_fmt(cx - r)}" y="{_fmt(cy - r)}" width="{_fmt(size)}" height="{_fmt(size)}"/>'
    if shape == "hexagon":
        pts = " ".join(
            f"{_fmt(cx + r * math.cos(math.radians(60 * i - 90)))},{_fmt(cy + r * math.sin(math.radians(60 * i - 90)))}"
            for i in range(6)
        )
        return f'<polygon points="{pts}"/>'
    raise ValueError(f"Unbekannte Fotoform: {shape!r}")


def avatar(c: Canvas, ctx, cx, cy, size, fill, ink, ring=None, around=None):
    """Foto in Form oder Monogramm (Initialen).

    Hebt sich die Monogrammfläche nicht von der Umgebung ab, werden Fläche und
    Schrift getauscht (z. B. Markenfläche auf Markenhintergrund).
    """
    shape = ctx["photo_shape"]
    if around and contrast_ratio(fill, around) < 1.6:
        fill, ink = ink, fill
    markup = _shape_markup(shape, cx, cy, size)
    if ring:
        ring_markup = _shape_markup(shape, cx, cy, size + 1.6 * c.s)
        c.add(ring_markup.replace("/>", f' fill="{ring}"/>'))
    if ctx["photo"]:
        cid = c.id("photo")
        c.defs.append(f'<clipPath id="{cid}">{markup}</clipPath>')
        r = size / 2
        c.add(
            f'<image href="{ctx["photo"]}" x="{_fmt(cx - r)}" y="{_fmt(cy - r)}" width="{_fmt(size)}" height="{_fmt(size)}" '
            f'preserveAspectRatio="xMidYMid slice" clip-path="url(#{cid})"/>'
        )
        return
    c.add(markup.replace("/>", f' fill="{fill}"/>'))
    letters = initials(ctx["profile"].get("name", ""))
    fs = size * 0.38
    c.min_contrast = min(c.min_contrast, contrast_ratio(ink, fill))
    c.add(
        f'<text x="{_fmt(cx)}" y="{_fmt(cy + fs * 0.35)}" font-family="{ctx["font_h"]}" font-size="{_fmt(fs)}" '
        f'font-weight="700" fill="{ink}" text-anchor="middle" letter-spacing="{_fmt(fs * 0.02)}">{esc(letters)}</text>'
    )


def logo(c: Canvas, ctx, x, y, w, h, align="xMinYMid", on_dark=False):
    href = ctx["logo_dark"] if on_dark else ctx["logo"]
    if not href:
        return False
    c.add(
        f'<image href="{href}" x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(w)}" height="{_fmt(h)}" '
        f'preserveAspectRatio="{align} meet"/>'
    )
    return True


def has_logo(ctx, on_dark=False):
    return bool(ctx["logo_dark"] if on_dark else ctx["logo"])


# ---------------------------------------------------------------------------
# Textstapel
# ---------------------------------------------------------------------------

def text_stack(c: Canvas, ctx, region, items, valign="center", anchor="start", surface=None):
    """Setzt Textelemente (Name, Headline, Meta) passend in eine Region.

    items: dicts mit text, size, min, lines, bold, color, font, gap
    Verkleinert gemeinsam, bis die Höhe passt; kürzt notfalls; lässt zuletzt
    niedrig priorisierte Elemente weg. Ergebnis: nichts ragt aus der Region.
    """
    x, y, w, h = region
    items = [it for it in items if it.get("text") or it.get("rule")]
    factor = 1.0
    for _ in range(40):
        placed, total = [], 0.0
        for it in items:
            if it.get("rule"):
                gh = it["gap"] * factor
                placed.append((it, None, None, False, gh))
                total += gh
                continue
            lines, size, cut = fit_text(it["text"], w, max(it["size"] * factor, it["min"]), it["min"],
                                        it.get("lines", 1), it.get("bold", False))
            block = len(lines) * size * 1.2 + it.get("gap", 0) * factor
            placed.append((it, lines, size, cut, block))
            total += block
        if total <= h:
            break
        if factor > 0.6:
            factor *= 0.95
            continue
        droppable = [it for it in items if it.get("optional")]
        if not droppable:
            break
        items.remove(droppable[-1])
        c.truncated.append(f"{droppable[-1].get('key', 'Feld')} (weggelassen, zu wenig Platz)")
    if total > h + 1e-6:
        c.fits = False
    if valign == "top":
        cy = y
    elif valign == "bottom":
        cy = y + h - total
    else:
        cy = y + (h - total) / 2
    tx = {"start": x, "middle": x + w / 2, "end": x + w}[anchor]
    for it, lines, size, cut, block in placed:
        if it.get("rule"):
            rw = it.get("width", 10) * c.s
            rx = {"start": x, "middle": x + w / 2 - rw / 2, "end": x + w - rw}[anchor]
            c.rect(rx, cy + block / 2 - 0.3 * c.s, rw, 0.6 * c.s, it["color"])
            cy += block
            continue
        if cut:
            c.truncated.append(it.get("key", "Text"))
        cy = c.text_lines(tx, cy, lines, size, it["color"], it.get("font", ctx["font_b"]),
                          700 if it.get("bold") else it.get("weight", 400), anchor, 1.2, surface)
        cy += it.get("gap", 0) * factor
    return cy


def _items(c, ctx, pal_text, pal_muted, pal_accent, big=1.0, center=False, with_rule=False):
    s = c.s
    p = ctx["profile"]
    meta = " · ".join(v for v in (p.get("company"), p.get("location")) if v)
    items = [
        {"key": "Name", "text": p.get("name", ""), "size": 5.4 * s * big, "min": 2.9 * s, "lines": 3, "bold": True,
         "color": pal_text, "font": ctx["font_h"], "gap": 1.2 * s},
    ]
    if with_rule:
        items.append({"rule": True, "gap": 2.2 * s, "color": pal_accent, "width": 9})
    items += [
        {"key": "Headline", "text": p.get("headline", ""), "size": 2.7 * s, "min": 2.1 * s, "lines": 3,
         "color": pal_muted, "gap": 1.4 * s},
        {"key": "Firma/Ort", "text": meta, "size": 2.4 * s, "min": 2.1 * s, "lines": 2, "weight": 600,
         "color": pal_accent, "optional": True},
    ]
    return items


# ---------------------------------------------------------------------------
# Vorderseiten-Layouts
# ---------------------------------------------------------------------------

def front_classic(c, ctx, pal):
    s = c.s
    bg = pal["bg"]
    c.rect(0, 0, c.cw, c.ch, bg)
    px = c.b + c.w * 0.62
    paint_pattern(c, ctx["pattern"], pal["pattern"], ctx["opacity"],
                  f'<rect x="{_fmt(px)}" y="0" width="{_fmt(c.cw - px)}" height="{_fmt(c.ch)}"/>', bg)
    c.rect(0, 0, c.b + 2.2 * s, c.ch, pal["primary"])
    top_h = 9 * s
    right_reserved = 0
    if ctx["photo"] or ctx["photo_on_front"]:
        size = 15 * s
        avatar(c, ctx, c.x1 - size / 2, c.y0 + size / 2, size, pal["primary"], pal["on_primary"], around=bg)
        right_reserved = size + 3 * s
        top_h = max(top_h, size)
    if is_light(bg) and has_logo(ctx):
        logo(c, ctx, c.x0, c.y0, min(30 * s, c.x1 - c.x0 - right_reserved), 9 * s)
    elif not is_light(bg) and has_logo(ctx, on_dark=True):
        logo(c, ctx, c.x0, c.y0, min(30 * s, c.x1 - c.x0 - right_reserved), 9 * s, on_dark=True)
    width = (px - c.x0 - 3 * s) if ctx["pattern"] != "none" else (c.x1 - c.x0)
    region = (c.x0, c.y0 + top_h + 2.5 * s, width, c.y1 - c.y0 - top_h - 2.5 * s)
    text_stack(c, ctx, region, _items(c, ctx, pal["text"], pal["muted"], pal["accent_text"]), "bottom", "start", bg)


def front_split(c, ctx, pal):
    s = c.s
    bg = pal["bg"]
    c.rect(0, 0, c.cw, c.ch, bg)
    pw = c.b + c.w * 0.38
    c.rect(0, 0, pw, c.ch, pal["primary"])
    paint_pattern(c, ctx["pattern"], pal["on_primary"], ctx["opacity"],
                  f'<rect width="{_fmt(pw)}" height="{_fmt(c.ch)}"/>', pal["primary"])
    size = min((pw - c.b) * 0.62, c.h * 0.5)
    avatar(c, ctx, c.b + (pw - c.b) / 2, c.b + c.h / 2, size, pal["on_primary"], pal["primary"])
    left = pw + 5 * s
    bottom = c.y1
    if is_light(bg) and has_logo(ctx):
        logo(c, ctx, c.x1 - 22 * s, c.y1 - 6 * s, 22 * s, 6 * s, "xMaxYMid")
        bottom = c.y1 - 8 * s
    elif not is_light(bg) and has_logo(ctx, True):
        logo(c, ctx, c.x1 - 22 * s, c.y1 - 6 * s, 22 * s, 6 * s, "xMaxYMid", True)
        bottom = c.y1 - 8 * s
    region = (left, c.y0, c.x1 - left, bottom - c.y0)
    text_stack(c, ctx, region, _items(c, ctx, pal["text"], pal["muted"], pal["accent_text"], 0.92), "center", "start", bg)


def front_centered(c, ctx, pal):
    s = c.s
    bg = pal["bg"]
    c.rect(0, 0, c.cw, c.ch, bg)
    paint_pattern(c, ctx["pattern"], pal["pattern"], ctx["opacity"] * 0.8,
                  f'<rect width="{_fmt(c.cw)}" height="{_fmt(c.ch)}"/>', bg)
    top = c.y0
    size = 12 * s
    avatar(c, ctx, c.b + c.w / 2, top + size / 2, size, pal["primary"], pal["on_primary"], around=bg)
    top += size + 2.4 * s
    bottom = c.y1
    on_dark = not is_light(bg)
    if has_logo(ctx, on_dark):
        logo(c, ctx, c.b + c.w / 2 - 12 * s, c.y1 - 5 * s, 24 * s, 5 * s, "xMidYMid", on_dark)
        bottom -= 7 * s
    region = (c.x0 + 4 * s, top, c.x1 - c.x0 - 8 * s, bottom - top)
    text_stack(c, ctx, region, _items(c, ctx, pal["text"], pal["muted"], pal["accent_text"], 0.86, True, True),
               "center", "middle", bg)


def front_diagonal(c, ctx, pal):
    s = c.s
    bg = pal["bg"]
    c.rect(0, 0, c.cw, c.ch, bg)
    a, b2 = c.b + c.w * 0.66, c.b + c.w * 0.50
    poly = f'<polygon points="{_fmt(a)},0 {_fmt(c.cw)},0 {_fmt(c.cw)},{_fmt(c.ch)} {_fmt(b2)},{_fmt(c.ch)}"/>'
    c.add(poly.replace("/>", f' fill="{pal["primary"]}"/>'))
    paint_pattern(c, ctx["pattern"], pal["on_primary"], ctx["opacity"], poly, pal["primary"])
    size = min(c.h * 0.42, c.w * 0.24)
    avatar(c, ctx, c.b + c.w * 0.80, c.b + c.h / 2, size, pal["on_primary"], pal["primary"])
    top = c.y0
    on_dark = not is_light(bg)
    if has_logo(ctx, on_dark):
        logo(c, ctx, c.x0, c.y0, 26 * s, 7 * s, "xMinYMid", on_dark)
        top += 9 * s
    right = c.b + c.w * 0.52 - 2 * s
    region = (c.x0, top, right - c.x0, c.y1 - top)
    text_stack(c, ctx, region, _items(c, ctx, pal["text"], pal["muted"], pal["accent_text"], 0.92), "center", "start", bg)


def front_minimal(c, ctx, pal):
    s = c.s
    bg = pal["bg"]
    c.rect(0, 0, c.cw, c.ch, bg)
    paint_pattern(c, ctx["pattern"], pal["pattern"], ctx["opacity"] * 1.2,
                  f'<circle cx="{_fmt(c.cw)}" cy="{_fmt(c.ch)}" r="{_fmt(c.h * 0.62)}"/>', bg,
                  center=(c.cw, c.ch))
    on_dark = not is_light(bg)
    if has_logo(ctx, on_dark):
        logo(c, ctx, c.x0, c.y0, 24 * s, 6.5 * s, "xMinYMid", on_dark)
    else:
        c.text_lines(c.x0, c.y0, [initials(ctx["profile"].get("name", ""))], 4.2 * s, pal["accent_text"],
                     ctx["font_h"], 700, "start", 1.2, bg)
    c.rect(c.x0, c.y0 + 9 * s, 7 * s, 0.6 * s, pal["accent_text"])
    region = (c.x0, c.y0 + 12 * s, (c.x1 - c.x0) * 0.74, c.y1 - c.y0 - 12 * s)
    text_stack(c, ctx, region, _items(c, ctx, pal["text"], pal["muted"], pal["accent_text"], 1.1), "bottom", "start", bg)


def front_profile(c, ctx, pal):
    s = c.s
    bg = pal["bg"]
    c.rect(0, 0, c.cw, c.ch, bg)
    band = c.b + c.h * 0.36
    band_color = pal["primary"]
    if contrast_ratio(band_color, bg) < 1.3:  # Markenhintergrund: Band dunkler absetzen
        band_color = mix(pal["primary"], "#000000", 0.32)
    band_ink = ensure_contrast(pal["on_primary"], band_color, 4.5)
    c.rect(0, 0, c.cw, band, band_color)
    paint_pattern(c, ctx["pattern"], band_ink, ctx["opacity"],
                  f'<rect width="{_fmt(c.cw)}" height="{_fmt(band)}"/>', band_color)
    size = c.h * 0.36
    cx = c.x0 + size / 2
    avatar(c, ctx, cx, band, size, pal["primary"], pal["on_primary"], ring=bg, around=bg)
    if has_logo(ctx, True):
        logo(c, ctx, c.x1 - 26 * s, c.y0, 26 * s, band - c.y0 - 2.5 * s, "xMaxYMid", True)
    elif ctx["profile"].get("company"):
        lines, size_t, _ = fit_text(ctx["profile"]["company"], (c.x1 - c.x0) * 0.55, 2.4 * s, 2.0 * s, 1, True)
        c.text_lines(c.x1, c.y0, lines, size_t, band_ink, ctx["font_h"], 700, "end", 1.2, band_color)
    left = cx + size / 2 + 3.5 * s
    region = (left, band + 2.0 * s, c.x1 - left, c.y1 - band - 2.0 * s)
    items = _items(c, ctx, pal["text"], pal["muted"], pal["accent_text"], 0.82)
    items[1]["lines"] = 2
    text_stack(c, ctx, region, items, "center", "start", bg)


FRONTS = {
    "classic": front_classic,
    "split": front_split,
    "centered": front_centered,
    "diagonal": front_diagonal,
    "minimal": front_minimal,
    "profile": front_profile,
}


# ---------------------------------------------------------------------------
# Rückseite: QR + Kontakt
# ---------------------------------------------------------------------------

def qr_block(c: Canvas, ctx, pal, x, y, size, surface_text, surface):
    """Weiße Kachel mit QR-Code inkl. 4 Module Ruhezone."""
    qr = ctx["qr"]
    matrix = qr.matrix
    n = len(matrix)
    quiet = 4
    mod = size / (n + 2 * quiet)
    rx = min(ctx["corner_r"] * 0.8, size * 0.06)
    c.rect(x, y, size, size, pal["qr_light"], rx)
    ox, oy = x + quiet * mod, y + quiet * mod
    d = []
    for r, row in enumerate(matrix):
        col = 0
        while col < n:
            if row[col]:
                start = col
                while col < n and row[col]:
                    col += 1
                d.append(f"M{_fmt(ox + start * mod)} {_fmt(oy + r * mod)}h{_fmt((col - start) * mod)}v{_fmt(mod)}h{_fmt(-(col - start) * mod)}z")
            else:
                col += 1
    c.add(f'<path d="{"".join(d)}" fill="{pal["qr_dark"]}" shape-rendering="crispEdges"/>')
    unit = FORMATS[ctx["fmt"]]["unit"]
    mm = size if unit == "mm" else None
    return {"modules": n, "version": qr.designator, "quiet_zone_modules": quiet,
            "size": round(size, 2), "size_mm": round(mm, 1) if mm else None,
            "module_size": round(mod, 3)}


def _break_address(value, width, size, max_lines=3):
    """Bricht E-Mail/URL an @ . - / um (statt zu kürzen). Rückgabe wie fit_text."""
    from common import text_width
    tokens = re.split(r"(?=[@./\-])", value)
    lines, cur = [], ""
    for t in tokens:
        if text_width(cur + t, size) <= width or not cur:
            cur += t
        else:
            lines.append(cur)
            cur = t
    lines.append(cur)
    ok = len(lines) <= max_lines and all(text_width(x, size) <= width for x in lines)
    if ok:
        return lines, size, False
    return fit_text(value, width, size, size, 1)


def icon(c: Canvas, name, x, y, size, color):
    c.add(
        f'<svg x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(size)}" height="{_fmt(size)}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f"{_icon_inner(name)}</svg>"
    )


def sticker_column(c: Canvas, ctx, x, y, w, h):
    """Bis zu drei Begegnungsfotos als Polaroid-Sticker (wie die Sticker der LinkedIn-Karte)."""
    s = c.s
    items = ctx["stickers"][:3]
    n = len(items)
    size = min(w * (0.62 if n == 1 else 0.5 if n == 2 else 0.42), h * (0.62 if n < 3 else 0.46))
    frame, cap_h = size * 0.07, 3.0 * s
    # (x-Anteil, y-Anteil, Winkel); gezeichnet in Listenreihenfolge, spätere liegen oben.
    # Bei drei Fotos liegt das untere zuerst, damit alle Bildunterschriften sichtbar bleiben.
    spots = {1: [(0.5, 0.4, -4)], 2: [(0.0, 0.1, -6), (1.0, 0.75, 5)],
             3: [(0.5, 1.0, 3), (0.0, 0.0, -6), (1.0, 0.08, 5)]}[n]
    order = [0, 1, 2][:n] if n < 3 else [2, 0, 1]  # Foto-Index je Platz: 1. Foto oben links
    angles = [a for _, _, a in spots]
    for slot, i in enumerate(order):
        st = items[i]
        fxr, fyr, _ = spots[slot]
        fx = x + (w - size - 2 * frame) * fxr
        fy = y + (h - size - 2 * frame - cap_h) * fyr
        cx, cy = fx + size / 2 + frame, fy + (size + 2 * frame + cap_h) / 2
        fw, fh = size + 2 * frame, size + 2 * frame + cap_h
        cid = c.id("st")
        c.defs.append(f'<clipPath id="{cid}"><rect x="{_fmt(fx + frame)}" y="{_fmt(fy + frame)}" '
                      f'width="{_fmt(size)}" height="{_fmt(size)}"/></clipPath>')
        lines, fs, _ = fit_text(st.get("caption", ""), size, 2.1 * s, 2.0 * s, 1)
        cap = (f'<text x="{_fmt(cx)}" y="{_fmt(fy + frame + size + cap_h * 0.72)}" font-family="{ctx["font_b"]}" '
               f'font-size="{_fmt(fs)}" font-weight="600" fill="#1F2937" text-anchor="middle">{esc(lines[0])}</text>'
               if lines else "")
        if lines:
            c.min_contrast = min(c.min_contrast, contrast_ratio("#1F2937", "#FFFFFF"))
        c.add(
            f'<g transform="rotate({angles[slot]} {_fmt(cx)} {_fmt(cy)})">'
            f'<rect x="{_fmt(fx + 0.5 * s)}" y="{_fmt(fy + 0.7 * s)}" width="{_fmt(fw)}" height="{_fmt(fh)}" '
            f'rx="{_fmt(0.6 * s)}" fill="#000000" opacity="0.18"/>'
            f'<rect x="{_fmt(fx)}" y="{_fmt(fy)}" width="{_fmt(fw)}" height="{_fmt(fh)}" rx="{_fmt(0.6 * s)}" fill="#FFFFFF"/>'
            f'<image href="{st["href"]}" x="{_fmt(fx + frame)}" y="{_fmt(fy + frame)}" width="{_fmt(size)}" '
            f'height="{_fmt(size)}" preserveAspectRatio="xMidYMid slice" clip-path="url(#{cid})"/>{cap}</g>'
        )


def back(c: Canvas, ctx, pal):
    s = c.s
    p = ctx["profile"]
    if pal["theme"] == "brand":
        surface = ctx["brand_bg_light"] or "#FFFFFF"
        ink = ensure_contrast(pal["primary"], surface, 7.0)
        accent = ink
        pattern_color = pal["primary"]
    else:
        surface = pal["primary"] if pal["theme"] == "light" else pal["bg"]
        ink = pal["on_primary"] if pal["theme"] == "light" else pal["text"]
        pattern_color = pal["on_primary"] if pal["theme"] == "light" else pal["pattern"]
        accent = ink
    ink_muted = ensure_contrast(mix(ink, surface, 0.22), surface, 4.5)
    c.rect(0, 0, c.cw, c.ch, surface)
    paint_pattern(c, ctx["pattern"], pattern_color, ctx["opacity"], f'<rect width="{_fmt(c.cw)}" height="{_fmt(c.ch)}"/>',
                  surface, center=(c.cw, c.ch))

    caption_h = 3.2 * s
    qsize = min(c.h - 2 * c.m - caption_h - 1.5 * s, (c.w - 2 * c.m) * 0.42)
    qr_right = ctx["layout"] in ("minimal", "centered")
    qx = c.x1 - qsize if qr_right else c.x0
    qy = c.y0 + (c.y1 - c.y0 - qsize - caption_h - 1.5 * s) / 2
    qr_info = qr_block(c, ctx, pal, qx, qy, qsize, ink, surface)
    cap = ctx["qr_label"]
    icon(c, "scan-line", qx, qy + qsize + 1.5 * s, 2.6 * s, ink)
    lines, csz, _ = fit_text(cap, qsize - 3.4 * s, 2.3 * s, 2.0 * s, 1, True)
    c.text_lines(qx + 3.4 * s, qy + qsize + 1.45 * s, lines, csz, ink, ctx["font_b"], 700, "start", 1.2, surface)

    # Info-Spalte
    ix0 = c.x0 if qr_right else qx + qsize + 5 * s
    ix1 = qx - 5 * s if qr_right else c.x1
    iw = ix1 - ix0
    on_dark = not is_light(surface)
    if ctx.get("stickers"):
        sticker_column(c, ctx, ix0, c.y0, iw, c.y1 - c.y0)
        return qr_info
    contacts = []
    for key in ("email", "phone", "website", "location"):
        if p.get(key):
            contacts.append((ICONS[key], p[key]))
    row = 4.1 * s
    list_h = row * (len(contacts) + 1)
    block_bottom = qy + qsize + caption_h + 1.5 * s
    logo_h = 10.5 * s if has_logo(ctx, on_dark) else 0
    # Infospalte am QR-Block ausrichten, wenn genug Platz ist; sonst volle Höhe nutzen.
    aligned = (block_bottom - qy - list_h - 2 * s) >= logo_h + 5 * s
    y = qy if aligned else c.y0
    bottom = block_bottom if aligned else c.y1
    first = len(c.body)  # ab hier gehört alles zur Infogruppe (wird vertikal zentriert)
    if logo_h:
        logo(c, ctx, ix0, y, min(iw, 28 * s), 7.5 * s, "xMinYMid", on_dark)
        y += logo_h
    li = ctx["linkedin_url"].replace("https://www.", "").rstrip("/")
    isz = 2.5 * s
    tw = iw - isz - 1.8 * s
    rows = []
    for name, value in contacts:
        lines, fs, cut = fit_text(value, tw, 2.3 * s, 2.0 * s, 1)
        if cut:
            lines, fs, cut = _break_address(value, tw, 2.0 * s)
        if cut:
            c.truncated.append(name)
        rows.append((name, lines, fs))
    extra = sum(len(r[1]) - 1 for r in rows) * 2.7 * s
    gap = 2.6 * s
    head_items = [
        {"key": "Name", "text": p.get("name", ""), "size": 3.6 * s, "min": 2.6 * s, "lines": 3, "bold": True,
         "color": ink, "font": ctx["font_h"], "gap": 0.6 * s},
        {"key": "Firma", "text": p.get("company", "") if not has_logo(ctx, on_dark) else "", "size": 2.3 * s,
         "min": 2.0 * s, "lines": 1, "color": ink_muted, "optional": True},
    ]
    head_region = (ix0, y, iw, max(0.0, bottom - y - list_h - extra - gap))
    ly = text_stack(c, ctx, head_region, head_items, "top", "start", surface) + gap
    for name, lines, fs in rows:
        icon(c, name, ix0, ly + 0.2 * s, isz, accent)
        c.text_lines(ix0 + isz + 1.6 * s, ly, lines, fs, ink, ctx["font_b"], 400, "start", 1.12, surface)
        ly += row + (len(lines) - 1) * 2.7 * s
    lines, fs, _ = fit_text(li, iw, 2.2 * s, 2.0 * s, 1)
    ly = c.text_lines(ix0, ly, lines, fs, ink_muted, ctx["font_b"], 600, "start", 1.2, surface)
    dy = (bottom - ly) / 2
    if dy > 0.5 * s and len(c.body) > first:
        c.body[first:] = [f'<g transform="translate(0 {_fmt(dy)})">' + "".join(c.body[first:]) + "</g>"]
    return qr_info


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------

def render_card(profile: dict, brand: dict, layout="classic", pattern="dots", theme="light", fmt="eu",
                corners="soft", photo_shape="circle", intensity="normal", lang="de", qr_label=None,
                photo_on_front=False, back_style="contact"):
    """Rendert Vorder- und Rückseite. Rückgabe: {'front': svg, 'back': svg, 'report': dict}."""
    for value, allowed, label in ((layout, LAYOUTS, "Layout"), (pattern, PATTERNS, "Muster"),
                                  (theme, THEMES, "Farbschema"), (fmt, FORMATS, "Format"),
                                  (corners, CORNERS, "Ecken"), (photo_shape, PHOTO_SHAPES, "Fotoform"),
                                  (intensity, INTENSITY, "Muster-Intensität"), (lang, LABELS, "Sprache")):
        if value not in allowed:
            raise ValueError(f"Unbekannte Option für {label}: {value!r}. Erlaubt: {', '.join(allowed)}")
    profile = dict(profile or {})
    if not profile.get("name"):
        raise ValueError("Profil braucht mindestens einen Namen.")
    linkedin_url = validate_linkedin_url(profile.get("linkedin_url"))
    brand = dict(brand or {})
    warnings: list[str] = []
    pal = build_palette(brand, theme)
    fonts = brand.get("fonts") or {}
    head = _safe_font(fonts.get("heading"), "Inter")
    body = _safe_font(fonts.get("body"), head)
    sans_stack = "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif"
    serif_stack = "'Source Serif 4', Georgia, 'Times New Roman', serif"
    try:
        from extract_ci import classify_font
    except ImportError:  # pragma: no cover
        classify_font = lambda n: "sans"  # noqa: E731
    stack_h = serif_stack if classify_font(head) == "serif" else sans_stack
    stack_b = serif_stack if classify_font(body) == "serif" else sans_stack
    ctx = {
        "profile": profile,
        "layout": layout,
        "pattern": pattern,
        "fmt": fmt,
        "lang": lang,
        "photo_shape": photo_shape,
        "opacity": INTENSITY[intensity],
        "font_h": f"'{head}', {stack_h}",
        "font_b": f"'{body}', {stack_b}",
        "photo": _load_image(profile.get("photo"), warnings, "Foto", allow_svg=False),
        "photo_on_front": photo_on_front,
        "stickers": [],
        "logo": _load_image(brand.get("logo"), warnings, "Logo"),
        "logo_dark": _load_image(brand.get("logo_on_dark"), warnings, "Logo (dunkel)"),
        "linkedin_url": linkedin_url,
        "qr": segno.make(linkedin_url, error="m", micro=False, boost_error=True),
        "brand_bg_light": None,
    }
    if brand.get("colors", {}).get("background"):
        try:
            bgc = brand["colors"]["background"]
            if is_light(bgc):
                ctx["brand_bg_light"] = bgc.upper() if bgc.startswith("#") else None
        except ValueError:
            pass
    ctx["qr_label"] = " ".join(str(qr_label).split())[:40] if qr_label else LABELS[lang]["qr"]
    f = FORMATS[fmt]
    corner_r = CORNERS[corners] * (f["h"] / 55.0)
    ctx["corner_r"] = corner_r
    uid = re.sub(r"[^a-z0-9]", "", (profile.get("name", "x")).lower())[:12] or "card"
    title = f"{LABELS[lang]['card']} – {profile.get('name')}"

    front_c = Canvas(fmt, "front", uid)
    FRONTS[layout](front_c, ctx, pal)
    back_c = Canvas(fmt, "back", uid)
    if back_style not in ("contact", "stickers"):
        raise ValueError(f"Unbekannte Rückseite: {back_style!r}. Erlaubt: contact, stickers")
    if back_style == "stickers":
        raw = profile.get("stickers") or []
        if len(raw) > 3:
            warnings.append(f"Sticker: nur die ersten 3 von {len(raw)} Fotos passen auf die Rückseite.")
        for st in raw[:3]:
            href = _load_image(st.get("image") if isinstance(st, dict) else st, warnings, "Sticker-Foto", allow_svg=False)
            if href:
                ctx["stickers"].append({"href": href, "caption": (st.get("caption", "") if isinstance(st, dict) else "")})
        if not ctx["stickers"]:
            warnings.append("Sticker-Rückseite gewählt, aber keine Fotos unter profile.stickers – Kontaktrückseite genutzt.")
    qr_info = back(back_c, ctx, pal)

    if f["print"] and corner_r:
        warnings.append(f"Abgerundete Ecken ({CORNERS[corners]} mm) bei der Druckerei als Eckenabrundung bestellen; "
                        "die Druckdatei bleibt rechteckig mit Beschnitt.")
    if qr_info["size_mm"] and qr_info["size_mm"] < 18:
        warnings.append("QR-Code kleiner als 18 mm – beim Druck schwer scanbar.")
    truncated = front_c.truncated + back_c.truncated
    if truncated:
        warnings.append("Gekürzt oder weggelassen: " + ", ".join(dict.fromkeys(truncated)))
    report = {
        "format": fmt,
        "lang": lang,
        "format_label": f["label"],
        "trim_mm": [f["w"], f["h"]] if f["unit"] == "mm" else None,
        "trim_px": [int(f["w"]), int(f["h"])] if f["unit"] == "px" else None,
        "bleed_mm": int(f["bleed"]) if float(f["bleed"]).is_integer() else f["bleed"],
        "layout": layout,
        "pattern": pattern,
        "theme": theme,
        "corners": corners,
        "photo_shape": photo_shape,
        "palette": {k: v for k, v in pal.items() if k != "theme"},
        "fonts": {"heading": head, "body": body},
        "min_text_contrast": round(min(front_c.min_contrast, back_c.min_contrast), 2),
        "qr": dict(qr_info, url=linkedin_url, error_correction="M (boost)", colors=[pal["qr_dark"], pal["qr_light"]],
                   contrast=round(contrast_ratio(pal["qr_dark"], pal["qr_light"]), 2)),
        "text_fits": front_c.fits and back_c.fits,
        "truncated": list(dict.fromkeys(truncated)),
        "warnings": warnings,
    }
    return {"front": front_c.svg(title + " (Vorderseite)", corner_r), "back": back_c.svg(title + " (Rückseite)", corner_r),
            "report": report}


# ---------------------------------------------------------------------------
# Dateien schreiben
# ---------------------------------------------------------------------------

BUNDLED_FONTS = {"inter", "sora", "source serif 4"}


def preview_html(result, profile, brand):
    fonts = brand.get("fonts") or {}
    fams = [f for f in {fonts.get("heading"), fonts.get("body")} if f]
    link = ""
    if fams:
        q = "&".join("family=" + re.sub(r"[^A-Za-z0-9 ]", "", f).replace(" ", "+") + ":wght@400;600;700" for f in fams)
        link = f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{q}&display=swap">'
    name = esc(profile.get("name", ""))
    rep = result["report"]
    en = rep.get("lang") == "en"
    L = {"front": "Front" if en else "Vorderseite", "back": "Back" if en else "Rückseite",
         "notes": "Notes" if en else "Hinweise", "none": "No notes." if en else "Keine Hinweise.",
         "pattern": "pattern" if en else "Muster", "theme": "theme" if en else "Schema",
         "bleed": "The preview includes the bleed area." if en else "Die Vorschau zeigt den Beschnitt mit.",
         "qr": "QR code links to" if en else "QR-Code führt zu",
         "alt_f": "Front of the business card" if en else "Vorderseite der Business Card",
         "alt_b": "Back of the business card with QR code to the LinkedIn profile" if en
         else "Rückseite der Business Card mit QR-Code zum LinkedIn-Profil"}
    warn = "".join(f"<li>{esc(w)}</li>" for w in rep["warnings"]) or f"<li>{L['none']}</li>"
    return f"""<!doctype html>
<html lang="{'en' if en else 'de'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Business Card – {name}</title>{link}
<style>
:root{{--bg:#F3F4F6;--fg:#111827;--muted:#4B5563;--card-shadow:0 18px 40px rgba(0,0,0,.18)}}
@media (prefers-color-scheme: dark){{:root{{--bg:#0B0F19;--fg:#F3F4F6;--muted:#9CA3AF;--card-shadow:0 18px 40px rgba(0,0,0,.6)}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;padding:24px 16px}}
main{{max-width:1100px;margin:0 auto}}
h1{{font-size:1.25rem;margin:0 0 4px}} p{{color:var(--muted);margin:0 0 24px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:28px}}
figure{{margin:0}} figure img{{width:100%;height:auto;border-radius:10px;box-shadow:var(--card-shadow);display:block}}
figcaption{{margin-top:10px;color:var(--muted);font-size:.9rem}}
ul{{color:var(--muted);padding-left:20px}}
</style></head><body><main>
<h1>Business Card – {name}</h1>
<p>{esc(rep['format_label'])} · Layout {esc(rep['layout'])} · {L['pattern']} {esc(rep['pattern'])} · {L['theme']} {esc(rep['theme'])}. {L['bleed']}</p>
<div class="cards">
<figure><img src="front.svg" alt="{L['alt_f']}"><figcaption>{L['front']}</figcaption></figure>
<figure><img src="back.svg" alt="{L['alt_b']}"><figcaption>{L['back']} – {L['qr']} {esc(rep['qr']['url'])}</figcaption></figure>
</div>
<h2 style="font-size:1rem;margin-top:28px">{L['notes']}</h2><ul>{warn}</ul>
</main></body></html>
"""


def font_installed(name):
    """True/False, wenn fontconfig verfügbar ist; None, wenn unbekannt."""
    exe = shutil.which("fc-list")
    if not exe or not name:
        return None
    res = subprocess.run([exe, ":", "family"], capture_output=True, text=True)
    fams = {f.strip().lower() for line in res.stdout.splitlines() for f in line.split(",")}
    return name.lower() in fams


def write_outputs(result, profile, brand, out: Path, png=True, pdf=True):
    from render import svg_to_png, svgs_to_pdf

    out.mkdir(parents=True, exist_ok=True)
    for fam in dict.fromkeys((result["report"]["fonts"] or {}).values()):
        if fam.lower() not in BUNDLED_FONTS and font_installed(fam) is not True:
            result["report"]["warnings"].append(
                f"Schrift „{fam}“ ist hier nicht installiert: PNG/PDF nutzen die mitgelieferte Ersatzschrift "
                "(Inter bzw. Source Serif 4). Schrift installieren oder eine freie Schrift in brand.json eintragen.")
    fmt = result["report"]["format"]
    f = FORMATS[fmt]
    files = {}
    for side in ("front", "back"):
        p = out / f"{side}.svg"
        p.write_text(result[side], encoding="utf-8")
        files[f"{side}.svg"] = p
        if png:
            width = round((f["w"] + 2 * f["bleed"]) / 25.4 * 300) if f["unit"] == "mm" else int(f["w"] * 2)
            files[f"{side}.png"] = svg_to_png(result[side], out / f"{side}.png", width)
    if pdf and f["print"]:
        kind = svgs_to_pdf([result["front"], result["back"]], out / "card-print.pdf", fmt)
        files["card-print.pdf"] = out / "card-print.pdf"
        if kind == "raster":
            result["report"]["warnings"].append(
                "rsvg-convert fehlt: card-print.pdf ist ein Raster-PDF (600 dpi). Für ein Vektor-PDF "
                "librsvg installieren (brew install librsvg bzw. apt install librsvg2-bin).")
    (out / "preview.html").write_text(preview_html(result, profile, brand), encoding="utf-8")
    (out / "report.json").write_text(json.dumps(result["report"], ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        from native import recommend_native

        (out / "linkedin-native-card.md").write_text(
            recommend_native(profile, brand, result["report"]), encoding="utf-8")
    except ImportError:
        pass
    return files


def write_gallery(profile, brand, out: Path, **opts):
    """Alle Layouts nebeneinander zum Auswählen (gallery.html)."""
    out.mkdir(parents=True, exist_ok=True)
    figs = []
    for name, desc in LAYOUTS.items():
        res = render_card(profile, brand, layout=name, **opts)
        (out / f"{name}-front.svg").write_text(res["front"], encoding="utf-8")
        (out / f"{name}-back.svg").write_text(res["back"], encoding="utf-8")
        figs.append(f'<figure><img src="{name}-front.svg" alt="Layout {name}"><figcaption><b>{name}</b> – {esc(desc)}</figcaption></figure>')
    html = ("<!doctype html><html lang=\"de\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>Layout-Galerie</title><style>body{margin:0;padding:24px 16px;background:#F3F4F6;font:15px system-ui;color:#111827}"
            "main{max-width:1200px;margin:auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:24px}"
            "img{width:100%;border-radius:8px;box-shadow:0 10px 24px rgba(0,0,0,.15)}figure{margin:0}figcaption{margin-top:8px}</style>"
            "<main>" + "".join(figs) + "</main></html>")
    (out / "gallery.html").write_text(html, encoding="utf-8")
    return out / "gallery.html"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Business Card im CI erzeugen (Vorder- und Rückseite).")
    ap.add_argument("--profile", help="profile.json (Pflicht außer bei --list)")
    ap.add_argument("--brand", help="brand.json (ohne: neutrale Standardfarben)")
    ap.add_argument("--out", help="Ausgabeordner (Pflicht außer bei --list)")
    ap.add_argument("--layout", default="classic", choices=LAYOUTS)
    ap.add_argument("--pattern", default="dots", choices=PATTERNS)
    ap.add_argument("--theme", default="light", choices=THEMES)
    ap.add_argument("--format", dest="fmt", default="eu", choices=FORMATS)
    ap.add_argument("--corners", default="soft", choices=CORNERS)
    ap.add_argument("--photo-shape", default="circle", choices=PHOTO_SHAPES)
    ap.add_argument("--intensity", default="normal", choices=INTENSITY)
    ap.add_argument("--lang", default="de", choices=["de", "en"])
    ap.add_argument("--qr-label", help="eigener Text unter dem QR-Code (max. 40 Zeichen)")
    ap.add_argument("--back", default="contact", choices=["contact", "stickers"],
                    help="Rückseite: Kontaktdaten oder Begegnungsfotos (profile.stickers)")
    ap.add_argument("--gallery", action="store_true", help="zusätzlich alle Layouts als gallery.html")
    ap.add_argument("--no-png", action="store_true")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--list", action="store_true", help="Optionen mit Beschreibung ausgeben")
    args = ap.parse_args(argv)

    if args.list:
        print(json.dumps({"layouts": LAYOUTS, "patterns": PATTERNS, "corners": CORNERS, "photo_shapes": PHOTO_SHAPES,
                          "themes": THEMES, "formats": {k: v["label"] for k, v in FORMATS.items()}},
                         ensure_ascii=False, indent=2))
        return 0
    if not args.profile or not args.out:
        ap.error("--profile und --out sind Pflicht")
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    brand = json.loads(Path(args.brand).read_text(encoding="utf-8")) if args.brand else {}
    base = Path(args.brand).parent if args.brand else Path.cwd()
    for key in ("logo", "logo_on_dark"):
        if brand.get(key) and not Path(brand[key]).is_absolute():
            brand[key] = str((base / brand[key]).resolve())
    if profile.get("photo") and not Path(profile["photo"]).is_absolute():
        profile["photo"] = str((Path(args.profile).parent / profile["photo"]).resolve())
    for st in profile.get("stickers") or []:
        if isinstance(st, dict) and st.get("image") and not Path(st["image"]).is_absolute():
            st["image"] = str((Path(args.profile).parent / st["image"]).resolve())
    opts = dict(layout=args.layout, pattern=args.pattern, theme=args.theme, fmt=args.fmt, corners=args.corners,
                photo_shape=args.photo_shape, intensity=args.intensity, lang=args.lang, qr_label=args.qr_label,
                back_style=args.back)
    try:
        result = render_card(profile, brand, **opts)
    except ValueError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2
    out = Path(args.out)
    files = write_outputs(result, profile, brand, out, png=not args.no_png, pdf=not args.no_pdf)
    if args.gallery:
        g = {k: v for k, v in opts.items() if k != "layout"}
        files["gallery.html"] = write_gallery(profile, brand, out / "gallery", **g)
    print(json.dumps({"files": {k: str(v) for k, v in files.items()}, "report": result["report"]},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
