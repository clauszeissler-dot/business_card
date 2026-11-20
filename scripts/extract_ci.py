#!/usr/bin/env python3
"""Liest das Corporate Design (Farben, Schriften, Logo) einer öffentlichen Website.

Nur Standardbibliothek. Schutzmaßnahmen gegen SSRF: nur http/https, keine
Zugangsdaten in der URL, jede aufgelöste Adresse muss öffentlich sein, die
Verbindung geht direkt an die geprüfte IP (kein zweiter DNS-Lookup),
Weiterleitungen werden einzeln geprüft, Zeit- und Größenlimits.

Beispiele:
    uv run scripts/extract_ci.py https://example.com --out brand/
    uv run scripts/extract_ci.py --html seite.html --css style.css --out brand/   # offline
"""
from __future__ import annotations

import argparse
import colorsys
import http.client
import ipaddress
import json
import re
import socket
import ssl
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import contrast_ratio, normalize_hex, relative_luminance, rgb_to_hex  # noqa: E402

TIMEOUT = 10
MAX_BYTES = 2 * 1024 * 1024
MAX_LOGO_BYTES = 1024 * 1024
MAX_REDIRECTS = 5
MAX_STYLESHEETS = 6
USER_AGENT = "Mozilla/5.0 (compatible; business-card-skill/1.0)"  # nur ASCII (HTTP-Header)

IMAGE_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/svg+xml": ".svg", "image/gif": ".gif"}


class FetchError(Exception):
    pass


# ---------------------------------------------------------------------------
# Sicherer Abruf
# ---------------------------------------------------------------------------

def _is_public(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return addr.is_global and not (addr.is_multicast or addr.is_reserved or addr.is_loopback
                                   or addr.is_link_local or addr.is_private or addr.is_unspecified)


def check_host(host: str, port: int = 443) -> str:
    """Löst den Host auf; alle Adressen müssen öffentlich sein. Liefert die erste IP."""
    if not host:
        raise FetchError("Kein Hostname.")
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise FetchError(f"Host nicht auflösbar: {host}") from e
    ips = [info[4][0] for info in infos]
    if not ips:
        raise FetchError(f"Keine Adresse für {host}.")
    for ip in ips:
        if not _is_public(ip):
            raise FetchError(f"Abgelehnt: {host} zeigt auf eine nicht öffentliche Adresse ({ip}).")
    return ips[0]


def _validate_url(url: str):
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise FetchError(f"Nur http/https erlaubt, nicht {parts.scheme or 'ohne Schema'}.")
    if parts.username or parts.password:
        raise FetchError("URLs mit Zugangsdaten sind nicht erlaubt.")
    host = parts.hostname
    if not host:
        raise FetchError("URL ohne Host.")
    try:
        ipaddress.ip_address(host)
        literal = True
    except ValueError:
        literal = False
    if literal and not _is_public(host):
        raise FetchError(f"Abgelehnt: nicht öffentliche Adresse {host}.")
    if host.lower() in ("localhost",) or host.lower().endswith((".localhost", ".local", ".internal")):
        raise FetchError(f"Abgelehnt: lokaler Hostname {host}.")
    return parts


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, ip, port, **kw):
        super().__init__(host, port, **kw)
        self._ip = ip

    def connect(self):
        sock = socket.create_connection((self._ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host, ip, port, **kw):
        super().__init__(host, port, **kw)
        self._ip = ip

    def connect(self):
        self.sock = socket.create_connection((self._ip, self.port), self.timeout)


def fetch(url: str, limit: int = MAX_BYTES, accept: str = "text/html,text/css,*/*;q=0.5"):
    """GET mit SSRF-Schutz. Rückgabe: (endgültige URL, Content-Type, Bytes)."""
    for _ in range(MAX_REDIRECTS + 1):
        parts = _validate_url(url)
        port = parts.port or (443 if parts.scheme == "https" else 80)
        ip = check_host(parts.hostname, port)
        if parts.scheme == "https":
            conn = _PinnedHTTPSConnection(parts.hostname, ip, port, timeout=TIMEOUT, context=ssl.create_default_context())
        else:
            conn = _PinnedHTTPConnection(parts.hostname, ip, port, timeout=TIMEOUT)
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        try:
            conn.request("GET", path, headers={"User-Agent": USER_AGENT, "Accept": accept, "Accept-Encoding": "identity"})
            resp = conn.getresponse()
            if resp.status in (301, 302, 303, 307, 308):
                loc = resp.getheader("Location")
                if not loc:
                    raise FetchError("Weiterleitung ohne Ziel.")
                url = urljoin(url, loc)
                continue
            if resp.status != 200:
                raise FetchError(f"HTTP {resp.status} für {url}")
            length = resp.getheader("Content-Length")
            if length and length.isdigit() and int(length) > limit:
                raise FetchError(f"Antwort zu groß ({int(length) // 1024} KB).")
            data = resp.read(limit + 1)
            if len(data) > limit:
                raise FetchError("Antwort zu groß.")
            ctype = (resp.getheader("Content-Type") or "").split(";")[0].strip().lower()
            return url, ctype, data
        except (OSError, http.client.HTTPException) as e:
            raise FetchError(f"Abruf fehlgeschlagen: {e}") from e
        finally:
            conn.close()
    raise FetchError("Zu viele Weiterleitungen.")


# ---------------------------------------------------------------------------
# HTML-Auswertung
# ---------------------------------------------------------------------------

class _Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.stylesheets = []
        self.icons = []
        self.logo_imgs = []
        self.inline_css = []
        self._in_style = False
        self.inline_svgs = []
        self._svg_depth = 0
        self._svg_buf = []
        self._svg_is_logo = False
        self._ancestors = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        hint = " ".join([a.get("class", ""), a.get("id", ""), a.get("alt", ""), a.get("src", ""),
                         a.get("aria-label", "")]).lower()
        if tag in ("header", "nav", "a"):
            self._ancestors.append(tag + ":" + hint)
        if tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            rel = a.get("rel", "").lower()
            if "stylesheet" in rel and a.get("href"):
                self.stylesheets.append(a["href"])
            if "icon" in rel and a.get("href"):
                self.icons.append((rel, a.get("sizes", ""), a.get("type", ""), a["href"]))
        elif tag == "style":
            self._in_style = True
        elif tag == "title":
            self._in_title = True
        elif tag == "img":
            in_header = any(x.startswith(("header", "nav")) for x in self._ancestors)
            src = a.get("src") or a.get("data-src") or ""
            if src and ("logo" in hint or (in_header and any("logo" in x or "brand" in x for x in self._ancestors))):
                self.logo_imgs.append(src)
            elif src and in_header and not self.logo_imgs:
                self.logo_imgs.append(src)
        elif tag == "svg" and self._svg_depth == 0:
            ctx = " ".join(self._ancestors).lower()
            self._svg_is_logo = "logo" in hint or "logo" in ctx or "brand" in ctx
            self._svg_depth = 1
            self._svg_buf = [self.get_starttag_text() or "<svg>"]
            return
        if self._svg_depth:
            self._svg_depth += 1
            self._svg_buf.append(self.get_starttag_text() or "")

    def handle_endtag(self, tag):
        if self._svg_depth:
            self._svg_buf.append(f"</{tag}>")
            self._svg_depth -= 1
            if self._svg_depth == 0 and self._svg_is_logo:
                self.inline_svgs.append("".join(self._svg_buf))
            return
        if tag == "style":
            self._in_style = False
        elif tag == "title":
            self._in_title = False
        elif tag in ("header", "nav", "a") and self._ancestors:
            self._ancestors.pop()

    def handle_startendtag(self, tag, attrs):
        if self._svg_depth:
            self._svg_buf.append(self.get_starttag_text() or "")
            return
        self.handle_starttag(tag, attrs)
        if tag in ("header", "nav", "a") and self._ancestors:
            self._ancestors.pop()

    def handle_data(self, data):
        if self._in_style:
            self.inline_css.append(data)
        elif self._in_title:
            self.title += data
        elif self._svg_depth:
            self._svg_buf.append(data)


# ---------------------------------------------------------------------------
# Farben und Schriften aus CSS
# ---------------------------------------------------------------------------

_HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_RGB = re.compile(r"rgba?\(\s*(\d{1,3})[\s,]+(\d{1,3})[\s,]+(\d{1,3})(?:[\s,/]+([\d.]+%?))?\s*\)")
_HSL = re.compile(r"hsla?\(\s*([\d.]+)(?:deg)?[\s,]+([\d.]+)%[\s,]+([\d.]+)%")
_VAR = re.compile(r"--([\w-]+)\s*:\s*([^;}{]+)")
_FONT_FAMILY = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)
_FONT_FACE = re.compile(r"@font-face\s*{[^}]*font-family\s*:\s*['\"]?([^;'\"}]+)", re.I)

GENERIC_FONTS = {"sans-serif", "serif", "monospace", "system-ui", "inherit", "initial", "cursive", "fantasy",
                 "-apple-system", "blinkmacsystemfont", "segoe ui", "roboto", "helvetica neue", "helvetica", "arial",
                 "ui-sans-serif", "ui-serif", "ui-monospace", "apple color emoji", "segoe ui emoji", "noto sans",
                 "segoe ui symbol", "noto color emoji", "var", "unset", "emoji", "math", "fangsong", "ui-rounded"}

BRAND_VAR_HINTS = ("primary", "brand", "accent", "secondary", "main", "theme", "highlight", "cta")


def _colors_in(value: str):
    out = []
    for m in _HEX.finditer(value):
        try:
            out.append(normalize_hex(m.group(0)))
        except ValueError:
            pass
    for m in _RGB.finditer(value):
        alpha = m.group(4)
        if alpha:
            a = float(alpha.rstrip("%")) / (100 if alpha.endswith("%") else 1)
            if a < 0.6:
                continue
        out.append(rgb_to_hex(tuple(int(m.group(i)) for i in (1, 2, 3))))
    for m in _HSL.finditer(value):
        h, s, li = float(m.group(1)) / 360, float(m.group(2)) / 100, float(m.group(3)) / 100
        r, g, b = colorsys.hls_to_rgb(h, li, s)
        out.append(rgb_to_hex((r * 255, g * 255, b * 255)))
    return out


def _saturation(hexcolor):
    r, g, b = (int(hexcolor[i:i + 2], 16) / 255 for i in (1, 3, 5))
    _, l, s = colorsys.rgb_to_hls(r, g, b)  # noqa: E741
    return s, l


_NOT_FONTS = {"normal", "bold", "bolder", "lighter", "italic", "none", "auto", "inherit", "initial", "unset"}


def _looks_like_font(name: str) -> bool:
    return bool(name) and bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9 \-]{1,40}", name)) \
        and name.lower() not in GENERIC_FONTS and name.lower() not in _NOT_FONTS


def analyze_css(css: str):
    counts = Counter()
    var_colors = {}
    for name, value in _VAR.findall(css):
        cols = _colors_in(value)
        if cols:
            var_colors[name.lower()] = cols[0]
    for col in _colors_in(css):
        counts[col] += 1
    fonts = Counter()
    for decl in _FONT_FAMILY.findall(css):
        first = decl.split(",")[0].strip().strip("'\"")
        if first.startswith("var("):
            continue
        if _looks_like_font(first):
            fonts[first] += 1
    for fam in _FONT_FACE.findall(css):
        fam = fam.strip()
        if _looks_like_font(fam):
            fonts[fam] += 2
    # Schriften aus Variablen (z. B. --font-heading: "Sora", sans-serif)
    for name, value in _VAR.findall(css):
        if "font" in name.lower() and not _colors_in(value):
            first = value.split(",")[0].strip().strip("'\"")
            if _looks_like_font(first):
                fonts[first] += 3
    return counts, var_colors, fonts


STATE_HINTS = ("hover", "active", "focus", "disabled", "pressed", "visited", "light", "lighter", "subtle",
               "muted", "tint", "bg", "background", "surface", "border", "shadow", "overlay")


def _quality(col):
    """0..1: wie gut taugt eine Farbe als Markenfarbe (gesättigt, mittlere Helligkeit)."""
    s, l = _saturation(col)  # noqa: E741
    if s < 0.2 or l < 0.1 or l > 0.82:
        return 0.0
    return min(1.0, 0.4 + s * 0.6) * max(0.25, 1 - abs(l - 0.45) * 1.6)


_RADIUS = re.compile(r"border-radius\s*:\s*([0-9.]+)(px|rem|em|%)?", re.I)


def corners_from_radius(values_px):
    """Median der Rundungen -> sharp/soft/round (Ecken der Karte)."""
    if not values_px:
        return "soft"
    v = sorted(values_px)[len(values_px) // 2]
    if v <= 2:
        return "sharp"
    if v <= 10:
        return "soft"
    return "round"


def css_radii(css: str):
    out = []
    for num, unit in _RADIUS.findall(css):
        n = float(num)
        unit = (unit or "px").lower()
        if unit in ("rem", "em"):
            n *= 16
        elif unit == "%":
            n = 999 if n >= 50 else n
        out.append(n)
    return out


def rank_brand_colors(counts: Counter, var_colors: dict, theme_color=None):
    """Sortiert Kandidaten: theme-color > benannte Markenvariablen > häufige, gesättigte Farben.

    Helle Abstufungen, Hover-/Aktiv-Zustände und Flächenfarben werden abgewertet.
    """
    scored = {}

    def add(col, score, why):
        if score <= 0:
            return
        if col not in scored or scored[col][0] < score:
            scored[col] = (score, why)

    if theme_color:
        add(theme_color, 100 * _quality(theme_color), "meta theme-color")
    for name, col in var_colors.items():
        if not any(h in name for h in BRAND_VAR_HINTS):
            continue
        base = 90 if ("primary" in name or "brand" in name) else 70
        if any(h in name for h in STATE_HINTS):
            base *= 0.45
        usage = min(1.3, 1 + counts.get(col, 0) * 0.03)
        add(col, base * _quality(col) * usage, f"CSS-Variable --{name}")
    for col, n in counts.most_common(60):
        add(col, min(60, 10 + n * 3) * _quality(col), f"{n}× im CSS")
    ranked = sorted(scored.items(), key=lambda kv: -kv[1][0])
    out = []
    for col, (score, why) in ranked:
        if all(_distance(col, o["hex"]) > 40 for o in out):
            out.append({"hex": col, "score": round(score, 1), "source": why})
    return out[:6]


def _distance(a, b):
    ra = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    rb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return sum((x - y) ** 2 for x, y in zip(ra, rb)) ** 0.5


def pick_neutrals(counts: Counter, var_colors: dict):
    bg, text = "#FFFFFF", "#111827"
    for name, col in var_colors.items():
        if re.search(r"(^|-)(bg|background|surface)($|-)", name) and relative_luminance(col) > 0.85:
            bg = col
            break
    darks = [c for c, _ in counts.most_common(80) if relative_luminance(c) < 0.05]
    if darks:
        text = darks[0]
    for name, col in var_colors.items():
        if re.search(r"(^|-)(text|foreground|fg|body-color|ink)($|-)", name) and contrast_ratio(col, bg) >= 7:
            text = col
            break
    return bg, text


def google_fonts(html: str, stylesheets):
    fams = []
    for href in list(stylesheets) + re.findall(r"fonts\.googleapis\.com/css2?\?[^\"'\s>]+", html):
        if "fonts.googleapis.com" not in href:
            continue
        for fam in re.findall(r"family=([^&:\"'\s>]+)", href):
            name = fam.replace("+", " ").split(":")[0]
            if name not in fams:
                fams.append(name)
    return fams


def classify_font(name: str) -> str:
    n = (name or "").lower()
    if any(k in n for k in ("mono", "code", "courier", "consol")):
        return "mono"
    if any(k in n for k in ("script", "hand", "pacifico", "dancing", "caveat", "satisfy", "brush", "marker")):
        return "script"
    if any(k in n for k in ("serif", "playfair", "merriweather", "lora", "garamond", "georgia", "times", "baskerville",
                            "bodoni", "libre caslon", "crimson", "dm serif", "fraunces", "cormorant", "spectral")) \
            and "sans" not in n:
        return "serif"
    return "sans"


# ---------------------------------------------------------------------------
# Logo
# ---------------------------------------------------------------------------

def _logo_candidates(col: _Collector, base_url: str):
    cands = []
    for src in col.logo_imgs:
        cands.append(("img[logo]", urljoin(base_url, src)))
    for rel, sizes, typ, href in col.icons:
        if "svg" in typ or href.lower().endswith(".svg"):
            cands.append(("icon(svg)", urljoin(base_url, href)))
    for rel, sizes, typ, href in col.icons:
        if "apple-touch-icon" in rel:
            cands.append(("apple-touch-icon", urljoin(base_url, href)))
    if col.meta.get("og:image"):
        cands.append(("og:image", urljoin(base_url, col.meta["og:image"])))
    seen, out = set(), []
    for kind, url in cands:
        if url not in seen and urlsplit(url).scheme in ("http", "https"):
            seen.add(url)
            out.append((kind, url))
    return out


def _sniff_image(data: bytes, ctype: str):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if b"<svg" in data[:4096].lower():
        return "image/svg+xml"
    return None


def save_logo(data: bytes, out_dir: Path, name="logo"):
    mime = _sniff_image(data, "")
    if not mime or len(data) > MAX_LOGO_BYTES:
        return None
    path = out_dir / f"{name}{IMAGE_TYPES[mime]}"
    path.write_bytes(data)
    return path


# ---------------------------------------------------------------------------
# Hauptablauf
# ---------------------------------------------------------------------------

def extract(html: str, css_texts, base_url: str = "", fetch_logo=None, out_dir: Path | None = None):
    col = _Collector()
    col.feed(html)
    css = "\n".join(list(col.inline_css) + list(css_texts))
    counts, var_colors, fonts = analyze_css(css)
    # Inline-style-Attribute zählen mit
    for m in re.finditer(r'style="([^"]+)"', html):
        for c in _colors_in(m.group(1)):
            counts[c] += 1
    theme = None
    if col.meta.get("theme-color"):
        found = _colors_in(col.meta["theme-color"])
        theme = found[0] if found else None
    ranked = rank_brand_colors(counts, var_colors, theme)
    bg, text = pick_neutrals(counts, var_colors)
    gfonts = google_fonts(html, col.stylesheets)
    font_order = list(dict.fromkeys(gfonts + [f for f, _ in fonts.most_common(6)]))
    heading = font_order[0] if font_order else None
    body = font_order[1] if len(font_order) > 1 else heading

    warnings = []
    logo_path, logo_source = None, None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        if col.inline_svgs:
            svg = col.inline_svgs[0]
            if "xmlns" not in svg[:200]:
                svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
            if len(svg.encode()) <= MAX_LOGO_BYTES:
                logo_path = out_dir / "logo.svg"
                logo_path.write_text(svg, encoding="utf-8")
                logo_source = "Inline-SVG im Header"
        if not logo_path and fetch_logo:
            for kind, url in _logo_candidates(col, base_url):
                try:
                    _, ctype, data = fetch_logo(url)
                except FetchError as e:
                    warnings.append(f"Logo-Kandidat übersprungen ({kind}): {e}")
                    continue
                saved = save_logo(data, out_dir)
                if saved:
                    logo_path, logo_source = saved, f"{kind}: {url}"
                    break
    if not ranked:
        warnings.append("Keine eindeutige Markenfarbe gefunden – bitte Primärfarbe manuell angeben.")
    if not heading:
        warnings.append("Keine Markenschrift gefunden – Standard ist eine neutrale Grotesk (Inter).")
    if logo_path is None:
        warnings.append("Kein Logo gefunden – Karte nutzt Firmennamen oder Monogramm.")
    if logo_path and logo_path.suffix == ".svg":
        warnings.append("Logo ist SVG: vor dem Druck prüfen, ob es auf hellem Grund gut sichtbar ist.")

    suggest = {"corners": corners_from_radius(css_radii(css))}
    primary = ranked[0]["hex"] if ranked else None
    secondary = next((c["hex"] for c in ranked[1:] if _distance(c["hex"], primary) > 80), None) if primary else None
    name = (col.meta.get("og:site_name") or col.meta.get("application-name") or col.title.split("|")[0].split("–")[0]
            .split(" - ")[0]).strip()
    brand = {
        "name": name[:80],
        "source": base_url or "lokale Datei",
        "colors": {k: v for k, v in {"primary": primary, "secondary": secondary, "background": bg, "text": text}.items() if v},
        "fonts": {k: v for k, v in {"heading": heading, "body": body}.items() if v},
        "font_style": classify_font(heading) if heading else "sans",
        "candidates": {"colors": ranked, "fonts": font_order[:6]},
        "suggest": suggest,
        "warnings": warnings,
    }
    if logo_path:
        brand["logo"] = logo_path.name
        brand["logo_source"] = logo_source
    return brand


def _decode_data_uri(uri: str):
    import base64
    from urllib.parse import unquote_to_bytes

    m = re.match(r"data:([\w/+.-]+)(;base64)?(?:;[\w=-]+)*,(.*)$", uri or "", re.S)
    if not m:
        return None
    raw = m.group(3)
    try:
        return base64.b64decode(raw) if m.group(2) else unquote_to_bytes(raw)
    except ValueError:
        return None


def from_firecrawl(branding: dict, out_dir: Path, source: str = "", fetch_logo=None):
    """Bildet Firecrawl `formats: ["branding"]` auf brand.json ab."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = branding.get("colors") or {}
    warnings = []

    def hx(v):
        found = _colors_in(v or "")
        return found[0] if found else None

    primary = hx(cols.get("primary"))
    secondary = None
    for key in ("accent", "secondary", "link"):
        c = hx(cols.get(key))
        if c and primary and _distance(c, primary) > 60 and _quality(c) > 0:
            secondary = c
            break
    fams = (branding.get("typography") or {}).get("fontFamilies") or {}
    roles = {f.get("role"): f.get("family") for f in branding.get("fonts") or [] if f.get("family")}
    heading = fams.get("heading") or roles.get("heading") or fams.get("primary")
    body = fams.get("primary") or roles.get("body") or heading
    radius = (branding.get("spacing") or {}).get("borderRadius")
    suggest = {"corners": corners_from_radius(css_radii(f"border-radius:{radius}")) if radius else "soft"}
    if branding.get("personality"):
        suggest["personality"] = branding["personality"]
    brand = {
        "name": (branding.get("brandName") or "").replace("_", " ").strip()[:80],
        "source": f"Firecrawl branding: {source}" if source else "Firecrawl branding",
        "colors": {k: v for k, v in {"primary": primary, "secondary": secondary,
                                     "background": hx(cols.get("background")),
                                     "text": hx(cols.get("textPrimary") or cols.get("text"))}.items() if v},
        "fonts": {k: v for k, v in {"heading": heading, "body": body}.items() if v},
        "font_style": classify_font(heading) if heading else "sans",
        "suggest": suggest,
        "warnings": warnings,
    }
    logo_uri = (branding.get("images") or {}).get("logo") or branding.get("logo")
    data = None
    if logo_uri and logo_uri.startswith("data:"):
        data = _decode_data_uri(logo_uri)
    elif logo_uri and fetch_logo:
        try:
            data = fetch_logo(logo_uri)[2]
        except FetchError as e:
            warnings.append(f"Logo nicht geladen: {e}")
    saved = save_logo(data, out_dir) if data else None
    if saved:
        brand["logo"] = saved.name
        brand["logo_source"] = "Firecrawl branding"
        warnings.append("Logo automatisch erkannt – bitte prüfen (manchmal ist es nur ein Icon oder weiß auf weiß).")
    else:
        warnings.append("Kein verwendbares Logo – Karte nutzt Firmennamen oder Monogramm.")
    if not primary:
        warnings.append("Keine eindeutige Markenfarbe gefunden – bitte Primärfarbe manuell angeben.")
    return brand


def from_url(url: str, out_dir: Path):
    final, ctype, data = fetch(url)
    html = data.decode("utf-8", errors="replace")
    col = _Collector()
    col.feed(html)
    css_texts = []
    for href in col.stylesheets[:MAX_STYLESHEETS]:
        if "fonts.googleapis.com" in href:
            continue
        try:
            _, _, css = fetch(urljoin(final, href))
            css_texts.append(css.decode("utf-8", errors="replace"))
        except FetchError:
            continue
    return extract(html, css_texts, final, lambda u: fetch(u, MAX_LOGO_BYTES, "image/*"), out_dir)


def main(argv=None):
    ap = argparse.ArgumentParser(description="CI (Farben, Schriften, Logo) einer Website auslesen → brand.json")
    ap.add_argument("url", nargs="?", help="öffentliche Website, z. B. https://example.com")
    ap.add_argument("--html", help="lokale HTML-Datei statt URL")
    ap.add_argument("--css", action="append", default=[], help="lokale CSS-Datei(en)")
    ap.add_argument("--firecrawl", help="JSON-Datei mit Firecrawl-Ausgabe (formats: [\"branding\"])")
    ap.add_argument("--out", required=True, help="Ausgabeordner für brand.json und Logo")
    args = ap.parse_args(argv)
    out = Path(args.out)
    try:
        if args.firecrawl:
            raw = json.loads(Path(args.firecrawl).read_text(encoding="utf-8"))
            raw = raw.get("branding", raw)
            brand = from_firecrawl(raw, out, args.url or "", lambda u: fetch(u, MAX_LOGO_BYTES, "image/*"))
        elif args.html:
            html = Path(args.html).read_text(encoding="utf-8", errors="replace")
            css = [Path(p).read_text(encoding="utf-8", errors="replace") for p in args.css]
            brand = extract(html, css, "", None, out)
        elif args.url:
            url = args.url if "://" in args.url else "https://" + args.url
            brand = from_url(url, out)
        else:
            ap.error("URL oder --html angeben")
    except FetchError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    (out / "brand.json").write_text(json.dumps(brand, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(brand, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
