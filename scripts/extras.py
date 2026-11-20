#!/usr/bin/env python3
"""Zusätze zur Karte: Sperrbildschirm-Bild (mit „gültig bis“), vCard und Kalender-Erinnerung.

Beispiel:
    uv run scripts/extras.py --profile profile.json --brand brand/brand.json --out extras/ \
        --valid-days 3 --event "Messe Essen" --device iphone --theme dark
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import io
import json
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import segno  # noqa: E402

from common import build_palette, esc, fit_text, validate_linkedin_url  # noqa: E402
from make_card import Canvas, _safe_font, avatar, paint_pattern, qr_block, _load_image  # noqa: E402

DEVICES = {
    "iphone": {"size": (1179, 2556), "label": "iPhone (6,1 Zoll, z. B. 15/16)"},
    "iphone-max": {"size": (1290, 2796), "label": "iPhone Pro Max / Plus (6,7 Zoll)"},
    "android": {"size": (1080, 2400), "label": "Android (20:9, Full HD+)"},
}

TXT = {
    "de": {"until": "Gültig bis", "scan": "Scannen & vernetzen",
           "ics_sum": "Sperrbildschirm zurücksetzen (Business Card)",
           "ics_desc": "Die Business Card auf dem Sperrbildschirm ist abgelaufen. Hintergrundbild zurückstellen."},
    "en": {"until": "Valid until", "scan": "Scan to connect",
           "ics_sum": "Reset lock screen (business card)",
           "ics_desc": "Your business card lock screen has expired. Switch back to your usual wallpaper."},
}


def valid_until(days: int, today: dt.date | None = None) -> dt.date:
    if days < 1 or days > 366:
        raise ValueError("Gültigkeit muss zwischen 1 und 366 Tagen liegen.")
    return (today or dt.date.today()) + dt.timedelta(days=days - 1)


def _date_str(d: dt.date, lang: str) -> str:
    return d.strftime("%d.%m.%Y") if lang == "de" else d.strftime("%d %b %Y")


def _fonts(brand):
    try:
        from extract_ci import classify_font
    except ImportError:  # pragma: no cover
        classify_font = lambda n: "sans"  # noqa: E731
    fonts = (brand or {}).get("fonts") or {}
    head = _safe_font(fonts.get("heading"), "Inter")
    body = _safe_font(fonts.get("body"), head)
    sans = "'Inter', 'Helvetica Neue', Arial, sans-serif"
    serif = "'Source Serif 4', Georgia, serif"
    fh = f"'{head}', " + (serif if classify_font(head) == "serif" else sans)
    fb = f"'{body}', " + (serif if classify_font(body) == "serif" else sans)
    return fh, fb


def lockscreen_svg(profile, brand, device="iphone", valid_until=None, event=None, theme="dark", pattern="dots",
                   lang="de", photo_shape="circle"):
    """Hochformat-Bild für den Sperrbildschirm. Oben bleibt Platz für die Uhr, unten für die Tasten."""
    if device not in DEVICES:
        raise ValueError(f"Unbekanntes Gerät: {device!r}. Erlaubt: {', '.join(DEVICES)}")
    lang = "en" if lang == "en" else "de"
    t = TXT[lang]
    url = validate_linkedin_url(profile.get("linkedin_url"))
    w, h = DEVICES[device]["size"]
    pal = build_palette(brand or {}, theme)
    c = Canvas("share", "lock", re.sub(r"[^a-z0-9]", "", profile.get("name", "x").lower())[:10] or "x")
    c.f = {"w": w, "h": h, "unit": "px", "bleed": 0, "print": False}
    c.w, c.h, c.cw, c.ch, c.b = w, h, w, h, 0
    c.s = w / 85.0
    c.m = 0.07 * w
    font_h, font_b = _fonts(brand)
    ctx = {"profile": profile, "photo_shape": photo_shape, "font_h": font_h, "font_b": font_b,
           "photo": _load_image(profile.get("photo"), [], "Foto", allow_svg=False),
           "qr": segno.make(url, error="m", micro=False, boost_error=True), "corner_r": 0.04 * w, "fmt": "share"}
    bg = pal["bg"]
    c.rect(0, 0, w, h, bg)
    paint_pattern(c, pattern, pal["pattern"], 0.1, f'<rect width="{w}" height="{h}"/>', bg)

    # Kopf: Avatar + Name + Headline (unterhalb der Uhr, ab 35 %)
    y = 0.355 * h
    av = 0.13 * w
    avatar(c, ctx, c.m + av / 2, y + av / 2, av, pal["primary"], pal["on_primary"], around=bg)
    tx = c.m + av + 0.04 * w
    tw = w - tx - c.m
    lines, size, _ = fit_text(profile.get("name", ""), tw, 0.062 * w, 0.045 * w, 2, True)
    yy = c.text_lines(tx, y, lines, size, pal["text"], font_h, 700, "start", 1.15, bg)
    sub = profile.get("headline") or profile.get("company") or ""
    if sub:
        lines, size, _ = fit_text(sub, tw, 0.034 * w, 0.028 * w, 2)
        c.text_lines(tx, yy + 0.008 * w, lines, size, pal["muted"], font_b, 400, "start", 1.2, bg)

    # QR-Kachel groß und mittig
    q = 0.6 * w
    qx, qy = (w - q) / 2, 0.49 * h
    qr_block(c, ctx, pal, qx, qy, q, pal["text"], bg)
    cap_y = qy + q + 0.035 * w
    c.text_lines(w / 2, cap_y, [t["scan"]], 0.04 * w, pal["text"], font_b, 700, "middle", 1.2, bg)
    foot = []
    if valid_until:
        foot.append(f"{t['until']} {_date_str(valid_until, lang)}")
    if event:
        foot.append(" ".join(str(event).split())[:40])
    if foot:
        c.text_lines(w / 2, cap_y + 0.065 * w, [" · ".join(foot)], 0.032 * w, pal["accent_text"], font_b, 600,
                     "middle", 1.2, bg)
    svg = c.svg(f"Lock screen – {profile.get('name', '')}", 0)
    return {"svg": svg, "qr_box": (qx, qy, q, q), "size": (w, h), "min_text_contrast": round(c.min_contrast, 2)}


# ---------------------------------------------------------------------------
# vCard 3.0 (RFC 2426)
# ---------------------------------------------------------------------------

def _v(value) -> str:
    value = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    return (value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n"))


def _fold(line: str) -> str:
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    parts, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        limit = 75 if not parts else 74
        if len(cur) + len(b) > limit:
            parts.append(cur.decode("utf-8"))
            cur = b""
        cur += b
    parts.append(cur.decode("utf-8"))
    return "\r\n ".join(parts)


def _photo_jpeg_b64(path):
    if not path or not Path(path).is_file() or Path(path).stat().st_size > 1024 * 1024:
        return None
    from PIL import Image

    im = Image.open(path).convert("RGB")
    im.thumbnail((400, 400))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def vcard(profile: dict) -> str:
    name = " ".join(str(profile.get("name", "")).split())
    parts = name.split(" ")
    family, given = (parts[-1], " ".join(parts[:-1])) if len(parts) > 1 else (name, "")
    lines = ["BEGIN:VCARD", "VERSION:3.0", f"N:{_v(family)};{_v(given)};;;", f"FN:{_v(name)}"]
    if profile.get("company"):
        lines.append(f"ORG:{_v(profile['company'])}")
    title = profile.get("title") or profile.get("headline")
    if title:
        lines.append(f"TITLE:{_v(title)}")
    if profile.get("email"):
        lines.append(f"EMAIL;TYPE=INTERNET:{_v(profile['email'])}")
    if profile.get("phone"):
        lines.append(f"TEL;TYPE=CELL:{_v(profile['phone'])}")
    if profile.get("linkedin_url"):
        lines.append(f"URL:{_v(validate_linkedin_url(profile['linkedin_url']))}")
    if profile.get("website"):
        site = profile["website"]
        lines.append(f"URL:{_v(site if re.match(r'^https?://', site) else 'https://' + site)}")
    if profile.get("location"):
        lines.append(f"ADR;TYPE=WORK:;;;{_v(profile['location'])};;;")
    photo = _photo_jpeg_b64(profile.get("photo"))
    if photo:
        lines.append(f"PHOTO;ENCODING=b;TYPE=JPEG:{photo}")
    lines.append("END:VCARD")
    return "".join(_fold(ln) + "\r\n" for ln in lines)


def reminder_ics(until: dt.date, lang="de") -> str:
    t = TXT["en" if lang == "en" else "de"]
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    end = until + dt.timedelta(days=1)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//business-card-skill//DE", "BEGIN:VEVENT",
             f"UID:{uuid.uuid4()}@business-card-skill", f"DTSTAMP:{stamp}",
             f"DTSTART;VALUE=DATE:{until:%Y%m%d}", f"DTEND;VALUE=DATE:{end:%Y%m%d}",
             f"SUMMARY:{_v(t['ics_sum'])}", f"DESCRIPTION:{_v(t['ics_desc'])}",
             "BEGIN:VALARM", "ACTION:DISPLAY", "TRIGGER:PT18H", f"DESCRIPTION:{_v(t['ics_sum'])}", "END:VALARM",
             "END:VEVENT", "END:VCALENDAR"]
    return "".join(_fold(ln) + "\r\n" for ln in lines)


GUIDE = {
    "de": """# Sperrbildschirm mit Business Card

Gültig bis: **{until}**{event}

## iPhone
1. `lockscreen-{device}.png` in die Fotos sichern (AirDrop, Mail oder Dateien → „Bild sichern“).
2. Sperrbildschirm lange drücken → **+** → **Fotos** → Bild wählen. Den Ausschnitt nicht verschieben: Die Uhr sitzt oben frei.
3. Zurückstellen: `erinnerung.ics` öffnen und in den Kalender übernehmen. Am Ablauftag erinnert dich der Kalender.
   Optional automatisch: App **Kurzbefehle** → **Automation** → **Tageszeit** am Ablaufdatum → Aktion zum Wechseln des Hintergrundbilds wählen (heißt je nach iOS-Version z. B. „Zwischen Hintergrundbildern wechseln“).

## Android
1. `lockscreen-android.png` in der Galerie öffnen → **Als Hintergrund festlegen** → **Sperrbildschirm**.
2. Zurückstellen: `erinnerung.ics` in den Kalender übernehmen.

Tipp: Bildschirm-Helligkeit hoch, dann scannt der QR-Code zuverlässig.
""",
    "en": """# Business card lock screen

Valid until: **{until}**{event}

## iPhone
1. Save `lockscreen-{device}.png` to Photos (AirDrop, Mail or Files → "Save Image").
2. Long-press the lock screen → **+** → **Photos** → pick the image. Do not move it: the clock area at the top is kept free.
3. To switch back: open `reminder.ics` and add it to your calendar. It reminds you on the expiry day.
   Optional automation: **Shortcuts** app → **Automation** → **Time of Day** on the expiry date → choose the action that switches wallpapers (name depends on your iOS version).

## Android
1. Open `lockscreen-android.png` in your gallery → **Set as wallpaper** → **Lock screen**.
2. To switch back: add `reminder.ics` to your calendar.

Tip: turn screen brightness up so the QR code scans reliably.
""",
}


def main(argv=None):
    from render import svg_to_png

    ap = argparse.ArgumentParser(description="Sperrbildschirm-Bild, vCard und Erinnerung erzeugen")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--brand")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="all", choices=["all", *DEVICES])
    ap.add_argument("--valid-days", type=int, default=0, help="0 = ohne Ablaufdatum")
    ap.add_argument("--event", help="z. B. Messe Essen (max. 40 Zeichen)")
    ap.add_argument("--theme", default="dark", choices=["light", "dark", "brand"])
    ap.add_argument("--pattern", default="dots")
    ap.add_argument("--lang", default="de", choices=["de", "en"])
    args = ap.parse_args(argv)
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    brand = json.loads(Path(args.brand).read_text(encoding="utf-8")) if args.brand else {}
    if profile.get("photo") and not Path(profile["photo"]).is_absolute():
        profile["photo"] = str((Path(args.profile).parent / profile["photo"]).resolve())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        until = valid_until(args.valid_days) if args.valid_days else None
        files = {}
        for dev in (DEVICES if args.device == "all" else [args.device]):
            res = lockscreen_svg(profile, brand, dev, until, args.event, args.theme, args.pattern, args.lang)
            p = out / f"lockscreen-{dev}.png"
            svg_to_png(res["svg"], p, res["size"][0])
            files[p.name] = str(p)
        vcf = out / ((re.sub(r"[^A-Za-z0-9]+", "-", profile.get("name", "kontakt")).strip("-") or "kontakt") + ".vcf")
        vcf.write_text(vcard(profile), encoding="utf-8")
        files[vcf.name] = str(vcf)
        if until:
            ics = out / ("erinnerung.ics" if args.lang == "de" else "reminder.ics")
            ics.write_text(reminder_ics(until, args.lang), encoding="utf-8")
            files[ics.name] = str(ics)
        guide = GUIDE[args.lang].format(until=_date_str(until, args.lang) if until else "–",
                                        event=f" · {esc(args.event)}" if args.event else "",
                                        device="iphone" if args.device == "all" else args.device)
        (out / ("sperrbildschirm.md" if args.lang == "de" else "lockscreen.md")).write_text(guide, encoding="utf-8")
    except ValueError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2
    print(json.dumps({"files": files, "valid_until": str(until) if until else None}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
