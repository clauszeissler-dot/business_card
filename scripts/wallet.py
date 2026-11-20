#!/usr/bin/env python3
"""Apple-Wallet-Pass (.pkpass) und Google-Wallet-Link für die Business Card.

Geheimnisse (Apple-Zertifikat .p12 und Passwort, Google-Dienstkontoschlüssel) werden nur
aus Dateien bzw. Umgebungsvariablen gelesen – nie als Kommandozeilenwert und nie über einen
Chat. In der Claude- oder ChatGPT-App deshalb nicht signieren, sondern den Online-Dienst nutzen.

Beispiele (lokal, z. B. in Claude Code):
    BC_P12_PASSWORD=… uv run scripts/wallet.py apple --profile profile.json --brand brand.json \
        --pass-type-id pass.de.example.card --team-id ABCDE12345 --org "Beispiel GmbH" \
        --p12 ~/secure/pass.p12 --wwdr ~/secure/AppleWWDRCAG4.cer --valid-days 3 --out wallet/
    uv run scripts/wallet.py google --profile profile.json --brand brand.json \
        --issuer-id 3388000000012345678 --service-account ~/secure/sa.json --valid-days 3
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
import time
import uuid
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import build_palette, hex_to_rgb, initials, validate_linkedin_url  # noqa: E402

TEXT = {"de": {"position": "Position", "company": "Firma", "location": "Ort", "email": "E-Mail", "phone": "Telefon",
               "web": "Website", "li": "LinkedIn", "desc": "Business Card", "scan": "Scannen & vernetzen"},
        "en": {"position": "Role", "company": "Company", "location": "Location", "email": "Email", "phone": "Phone",
               "web": "Website", "li": "LinkedIn", "desc": "Business card", "scan": "Scan to connect"}}


def _end_of_validity(valid_days, today=None):
    if not valid_days:
        return None
    if valid_days < 1 or valid_days > 366:
        raise ValueError("Gültigkeit muss zwischen 1 und 366 Tagen liegen.")
    day = (today or dt.date.today()) + dt.timedelta(days=valid_days - 1)
    return dt.datetime.combine(day, dt.time(23, 59, 59))


def _rgb(hexcolor):
    r, g, b = hex_to_rgb(hexcolor)
    return f"rgb({r},{g},{b})"


def _clean(v, n=120):
    return " ".join(str(v or "").split())[:n]


# ---------------------------------------------------------------------------
# Apple
# ---------------------------------------------------------------------------

def apple_pass_json(profile, brand, pass_type_id, team_id, org_name, valid_days=0, today=None, lang="de",
                    serial=None):
    t = TEXT["en" if lang == "en" else "de"]
    url = validate_linkedin_url(profile.get("linkedin_url"))
    pal = build_palette(brand or {}, "brand")
    name = _clean(profile.get("name"), 60)
    pj = {
        "formatVersion": 1,
        "passTypeIdentifier": pass_type_id,
        "teamIdentifier": team_id,
        "organizationName": _clean(org_name, 60),
        "serialNumber": serial or str(uuid.uuid4()),
        "description": f"{t['desc']} – {name}",
        "logoText": _clean(profile.get("company") or name, 30),
        "backgroundColor": _rgb(pal["bg"]),
        "foregroundColor": _rgb(pal["text"]),
        "labelColor": _rgb(pal["muted"]),
        "generic": {
            "primaryFields": [{"key": "name", "label": "", "value": name}],
            "secondaryFields": [{"key": "headline", "label": t["position"], "value": _clean(profile.get("headline"))}]
            if profile.get("headline") else [],
            "auxiliaryFields": [f for f in (
                {"key": "company", "label": t["company"], "value": _clean(profile.get("company"))}
                if profile.get("company") else None,
                {"key": "location", "label": t["location"], "value": _clean(profile.get("location"))}
                if profile.get("location") else None) if f],
            "backFields": [f for f in (
                {"key": "email", "label": t["email"], "value": _clean(profile.get("email"))} if profile.get("email") else None,
                {"key": "phone", "label": t["phone"], "value": _clean(profile.get("phone"))} if profile.get("phone") else None,
                {"key": "web", "label": t["web"], "value": _clean(profile.get("website"))} if profile.get("website") else None,
                {"key": "li", "label": t["li"], "value": url}) if f],
        },
        "barcodes": [{"format": "PKBarcodeFormatQR", "message": url, "messageEncoding": "iso-8859-1",
                      "altText": t["scan"]}],
    }
    end = _end_of_validity(valid_days, today)
    if end:
        pj["expirationDate"] = end.astimezone().isoformat(timespec="seconds") if today is None \
            else end.isoformat() + "+00:00"
    return pj


def _png(size, draw):
    from PIL import Image, ImageDraw

    im = Image.new("RGBA", size, (0, 0, 0, 0))
    draw(ImageDraw.Draw(im), im)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def default_images(profile, brand):
    """Icon, Logo und Vorschaubild ohne Fremddateien (Monogramm in Markenfarbe)."""
    from PIL import ImageFont

    pal = build_palette(brand or {}, "brand")
    font_path = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "Inter-700.ttf"
    letters = initials(profile.get("name", ""))

    def mono(px, fill, ink):
        def draw(d, im):
            d.ellipse((0, 0, px - 1, px - 1), fill=fill)
            f = ImageFont.truetype(str(font_path), int(px * 0.4))
            d.text((px / 2, px / 2), letters, font=f, fill=ink, anchor="mm")
        return _png((px, px), draw)

    out = {}
    for suffix, k in (("", 1), ("@2x", 2), ("@3x", 3)):
        out[f"icon{suffix}.png"] = mono(29 * k, pal["text"], pal["bg"])
        out[f"thumbnail{suffix}.png"] = mono(90 * k, pal["text"], pal["bg"])
    for suffix, k in (("", 1), ("@2x", 2)):
        def logo(d, im, k=k):
            f = ImageFont.truetype(str(font_path), 18 * k)
            d.text((0, 25 * k), _clean(profile.get("company") or profile.get("name"), 22), font=f,
                   fill=pal["text"], anchor="lm")
        out[f"logo{suffix}.png"] = _png((160 * k, 50 * k), logo)
    return out


def build_pkpass(pass_json: dict, images: dict, p12: bytes, p12_password: bytes, wwdr: bytes,
                 profile=None, brand=None) -> bytes:
    """Bündelt und signiert (PKCS#7, detached, DER) einen Apple-Wallet-Pass."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.serialization import pkcs7, pkcs12

    try:
        key, cert, _ = pkcs12.load_key_and_certificates(p12, p12_password)
    except Exception as e:  # falsches Passwort oder defekte Datei
        raise ValueError("Apple-Zertifikat (.p12) lässt sich nicht öffnen – Passwort oder Datei prüfen.") from e
    if key is None or cert is None:
        raise ValueError("Die .p12-Datei enthält keinen privaten Schlüssel mit Zertifikat.")
    wwdr_cert = x509.load_pem_x509_certificate(wwdr) if b"BEGIN CERTIFICATE" in wwdr else x509.load_der_x509_certificate(wwdr)
    files = dict(default_images(profile or {"name": pass_json.get("generic", {}).get("primaryFields", [{}])[0].get("value", "")},
                                brand or {}))
    files.update(images or {})
    files["pass.json"] = json.dumps(pass_json, ensure_ascii=False, indent=2).encode("utf-8")
    manifest = {name: hashlib.sha1(data).hexdigest() for name, data in sorted(files.items())}
    manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
    signature = (pkcs7.PKCS7SignatureBuilder().set_data(manifest_bytes)
                 .add_signer(cert, key, hashes.SHA256()).add_certificate(wwdr_cert)
                 .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature, pkcs7.PKCS7Options.Binary]))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            z.writestr(name, data)
        z.writestr("manifest.json", manifest_bytes)
        z.writestr("signature", signature)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Google
# ---------------------------------------------------------------------------

def google_pass(profile, brand, issuer_id, valid_days=0, today=None, lang="de", class_suffix="business_card_v1",
                logo_url=None):
    if not re.fullmatch(r"\d{10,25}", str(issuer_id)):
        raise ValueError("Google-Issuer-ID muss eine Zahlenfolge sein.")
    t = TEXT["en" if lang == "en" else "de"]
    loc = "en" if lang == "en" else "de"
    url = validate_linkedin_url(profile.get("linkedin_url"))
    pal = build_palette(brand or {}, "brand")
    cls = {"id": f"{issuer_id}.{class_suffix}"}

    def lv(v):
        return {"defaultValue": {"language": loc, "value": _clean(v)}}

    obj = {
        "id": f"{issuer_id}.{uuid.uuid4().hex}",
        "classId": cls["id"],
        "state": "ACTIVE",
        "cardTitle": lv(profile.get("company") or t["desc"]),
        "header": lv(profile.get("name")),
        "hexBackgroundColor": pal["bg"],
        "barcode": {"type": "QR_CODE", "value": url, "alternateText": t["scan"]},
        "textModulesData": [m for m in (
            {"id": "email", "header": t["email"], "body": _clean(profile.get("email"))} if profile.get("email") else None,
            {"id": "phone", "header": t["phone"], "body": _clean(profile.get("phone"))} if profile.get("phone") else None,
            {"id": "web", "header": t["web"], "body": _clean(profile.get("website"))} if profile.get("website") else None,
            {"id": "li", "header": t["li"], "body": url}) if m],
    }
    if profile.get("headline"):
        obj["subheader"] = lv(profile["headline"])
    if logo_url:
        obj["logo"] = {"sourceUri": {"uri": logo_url}}
    end = _end_of_validity(valid_days, today)
    if end:
        start = dt.datetime.combine(today or dt.date.today(), dt.time(0, 0))
        obj["validTimeInterval"] = {"start": {"date": start.isoformat() + "Z"}, "end": {"date": end.isoformat() + "Z"}}
    return cls, obj


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def google_save_url(sa_email: str, private_key_pem: bytes, cls: dict, obj: dict, origins=()) -> str:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    key = serialization.load_pem_private_key(private_key_pem, password=None)
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {"iss": sa_email, "aud": "google", "typ": "savetowallet", "iat": int(time.time()),
               "origins": list(origins), "payload": {"genericClasses": [cls], "genericObjects": [obj]}}
    signing_input = f"{_b64(json.dumps(header).encode())}.{_b64(json.dumps(payload).encode())}"
    sig = key.sign(signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
    return f"https://pay.google.com/gp/v/save/{signing_input}.{_b64(sig)}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Wallet-Pässe für die Business Card (lokal signieren)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("apple", "google"):
        p = sub.add_parser(name)
        p.add_argument("--profile", required=True)
        p.add_argument("--brand")
        p.add_argument("--valid-days", type=int, default=0)
        p.add_argument("--lang", default="de", choices=["de", "en"])
    a = sub.choices["apple"]
    a.add_argument("--pass-type-id", required=True)
    a.add_argument("--team-id", required=True)
    a.add_argument("--org", required=True, help="Organisationsname im Pass")
    a.add_argument("--p12", required=True, help="Pfad zur .p12-Datei; Passwort aus BC_P12_PASSWORD")
    a.add_argument("--wwdr", required=True, help="Apple WWDR-Zwischenzertifikat (G4), .cer oder .pem")
    a.add_argument("--out", required=True)
    g = sub.choices["google"]
    g.add_argument("--issuer-id", required=True)
    g.add_argument("--service-account", required=True, help="Pfad zur JSON-Schlüsseldatei des Dienstkontos")
    g.add_argument("--logo-url", help="öffentliche https-URL des Logos (empfohlen)")
    args = ap.parse_args(argv)
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    brand = json.loads(Path(args.brand).read_text(encoding="utf-8")) if args.brand else {}
    try:
        if args.cmd == "apple":
            pw = os.environ.get("BC_P12_PASSWORD")
            if pw is None:
                import getpass
                pw = getpass.getpass("Passwort der .p12-Datei: ")
            pj = apple_pass_json(profile, brand, args.pass_type_id, args.team_id, args.org, args.valid_days,
                                 lang=args.lang)
            data = build_pkpass(pj, {}, Path(args.p12).expanduser().read_bytes(), pw.encode(),
                                Path(args.wwdr).expanduser().read_bytes(), profile, brand)
            out = Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            target = out / "business-card.pkpass"
            target.write_bytes(data)
            print(json.dumps({"pkpass": str(target), "expires": pj.get("expirationDate")}, ensure_ascii=False))
        else:
            sa = json.loads(Path(args.service_account).expanduser().read_text(encoding="utf-8"))
            cls, obj = google_pass(profile, brand, args.issuer_id, args.valid_days, lang=args.lang,
                                   logo_url=args.logo_url)
            print(google_save_url(sa["client_email"], sa["private_key"].encode(), cls, obj))
    except (ValueError, KeyError, OSError) as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
