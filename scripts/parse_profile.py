#!/usr/bin/env python3
"""Liest LinkedIn-Profildaten ohne Scraping ein und schreibt profile.json.

Erlaubte Quellen (alle vom Profilinhaber selbst erzeugt):
  1. LinkedIn-Datenexport (Einstellungen → Datenschutz → Kopie Ihrer Daten
     anfordern), entpackter Ordner mit Profile.csv, Positions.csv, …
  2. Profil als PDF (Profil → Mehr → Als PDF speichern), Text via pdftotext
  3. Eingefügter Text im Format „Feld: Wert“

Datenschutz: Adresse, Geburtsdatum und Postleitzahl werden nie übernommen.
Telefon nur, wenn ausdrücklich angefordert (--contact email,phone,website).

Beispiele:
    uv run scripts/parse_profile.py --export ~/Downloads/Basic_LinkedInDataExport --url linkedin.com/in/<name> --out profile.json
    uv run scripts/parse_profile.py --pdf Profile.pdf --out profile.json
    uv run scripts/parse_profile.py --text notizen.txt --out profile.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import validate_linkedin_url  # noqa: E402

DEFAULT_CONTACT = ("email", "website")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
LI_RE = re.compile(r"(?:https?://)?(?:[a-z]{2,3}\.|www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+/?", re.I)


def _short_location(loc: str) -> str:
    parts = [p.strip() for p in (loc or "").split(",") if p.strip()]
    if len(parts) >= 3:
        return f"{parts[0]}, {parts[-1]}"
    return ", ".join(parts)


def _short_url(url: str) -> str:
    return re.sub(r"^https?://", "", url or "").rstrip("/")


def _read_csv(path: Path):
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()
    # Manche Exporte beginnen mit einer „Notes:“-Zeile vor dem Kopf.
    while lines and lines[0].lower().startswith("notes"):
        lines = lines[1:]
        while lines and lines[0].strip() == "":
            lines = lines[1:]
    return list(csv.DictReader(lines))


def _apply_contact(profile: dict, contact) -> dict:
    for key in ("email", "phone", "website"):
        if key not in contact:
            profile.pop(key, None)
    return {k: v for k, v in profile.items() if v not in (None, "")}


def from_export(folder, url, contact=DEFAULT_CONTACT) -> dict:
    folder = Path(folder)
    rows = _read_csv(folder / "Profile.csv")
    if not rows:
        raise ValueError(f"Profile.csv nicht gefunden in {folder}")
    r = rows[0]
    profile = {
        "name": " ".join(x for x in (r.get("First Name", "").strip(), r.get("Last Name", "").strip()) if x),
        "headline": r.get("Headline", "").strip(),
        "location": _short_location(r.get("Geo Location", "")),
        "linkedin_url": validate_linkedin_url(url),
        "source": "LinkedIn-Datenexport",
    }
    sites = re.findall(r"(?:[A-Z_]+:)?(https?://[^,\]\s]+)", r.get("Websites", ""))
    company_site = re.search(r"COMPANY:(https?://[^,\]\s]+)", r.get("Websites", ""))
    if company_site or sites:
        profile["website"] = _short_url(company_site.group(1) if company_site else sites[0])
    for pos in _read_csv(folder / "Positions.csv"):
        if not pos.get("Finished On", "").strip():
            profile["company"] = pos.get("Company Name", "").strip()
            profile["title"] = pos.get("Title", "").strip()
            break
    emails = _read_csv(folder / "Email Addresses.csv")
    primary = next((e for e in emails if e.get("Primary", "").lower() == "yes"), emails[0] if emails else None)
    if primary:
        profile["email"] = primary.get("Email Address", "").strip()
    phones = _read_csv(folder / "PhoneNumbers.csv")
    if phones:
        profile["phone"] = phones[0].get("Number", "").strip()
    return _apply_contact(profile, contact)


SECTION_WORDS = {"contact", "kontakt", "top skills", "top-kenntnisse", "languages", "sprachen", "certifications",
                 "zertifikate", "honors-awards", "auszeichnungen", "publications", "publikationen", "summary",
                 "zusammenfassung", "experience", "berufserfahrung", "education", "ausbildung"}


def from_pdf_text(text: str, contact=DEFAULT_CONTACT) -> dict:
    """Heuristik für „Als PDF speichern“. Ergebnis immer prüfen lassen (needs_review)."""
    lines = [ln.strip() for ln in text.replace("\f", "\n").splitlines() if ln.strip()]
    joined = "\n".join(lines)
    profile = {"source": "LinkedIn-Profil-PDF", "needs_review": ["name", "headline", "location", "company"]}
    # URL kann umbrochen sein: „www.linkedin.com/in/mara-\nbeispiel (LinkedIn)“
    m = re.search(r"((?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+)\s*\n?\s*([A-Za-z0-9\-_%]*)\s*\(LinkedIn\)", joined)
    if m:
        profile["linkedin_url"] = validate_linkedin_url(m.group(1) + m.group(2))
    elif LI_RE.search(joined):
        profile["linkedin_url"] = validate_linkedin_url(LI_RE.search(joined).group(0))
    em = EMAIL_RE.search(joined)
    if em:
        profile["email"] = em.group(0)
    site = re.search(r"^(\S+\.\S+)\s*\((?:Company|Personal|Unternehmen|Persönlich|Portfolio|Other|Sonstige)\)", joined,
                     re.M)
    if site:
        profile["website"] = _short_url(site.group(1))
    # Name = erste Zeile nach dem linken Spaltenblock, die wie ein Name aussieht
    def is_meta(ln):
        low = ln.lower()
        return (low in SECTION_WORDS or "(linkedin)" in low or EMAIL_RE.search(ln) or "linkedin.com" in low
                or re.search(r"\((native|full|professional|limited|elementary|personal|company|muttersprache)", low)
                or low.startswith("page ") or low.startswith("seite "))
    try:
        start = next(i for i, ln in enumerate(lines) if ln.lower() in ("summary", "zusammenfassung", "experience",
                                                                         "berufserfahrung"))
    except StopIteration:
        start = len(lines)
    # Rückwärts vom ersten Hauptabschnitt: Ort, Headline, Name
    head = [ln for ln in lines[:start] if not is_meta(ln)]
    if len(head) >= 3:
        profile["location"] = _short_location(head[-1])
        profile["headline"] = head[-2]
        profile["name"] = head[-3]
    exp = next((i for i, ln in enumerate(lines) if ln.lower() in ("experience", "berufserfahrung")), None)
    if exp is not None and exp + 2 < len(lines):
        profile["company"] = lines[exp + 1]
        profile["title"] = lines[exp + 2]
    return _apply_contact(profile, contact)


KEYS = {
    "name": "name", "headline": "headline", "titel": "title", "title": "title", "position": "title",
    "firma": "company", "company": "company", "unternehmen": "company", "ort": "location", "location": "location",
    "standort": "location", "e-mail": "email", "email": "email", "mail": "email", "telefon": "phone", "phone": "phone",
    "mobil": "phone", "website": "website", "web": "website", "linkedin": "linkedin_url", "url": "linkedin_url",
    "foto": "photo", "photo": "photo", "pronomen": "pronouns", "pronouns": "pronouns",
}


def from_text(text: str) -> dict:
    profile = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = KEYS.get(key.strip().lower())
        if key and value.strip():
            profile[key] = value.strip()
    if "linkedin_url" in profile:
        profile["linkedin_url"] = validate_linkedin_url(profile["linkedin_url"])
    return profile


def pdf_to_text(path: Path) -> str:
    exe = shutil.which("pdftotext")
    if not exe:
        raise ValueError("pdftotext fehlt (brew install poppler). Alternativ den PDF-Text einfügen.")
    return subprocess.run([exe, "-enc", "UTF-8", str(path), "-"], check=True, capture_output=True, text=True).stdout


def main(argv=None):
    ap = argparse.ArgumentParser(description="LinkedIn-Profil (Export, PDF oder Text) → profile.json")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--export", help="entpackter Ordner des LinkedIn-Datenexports")
    src.add_argument("--pdf", help="Profil-PDF (Als PDF speichern)")
    src.add_argument("--text", help="Textdatei mit „Feld: Wert“-Zeilen")
    ap.add_argument("--url", help="öffentliche Profil-URL (beim Export Pflicht)")
    ap.add_argument("--contact", default=",".join(DEFAULT_CONTACT),
                    help="welche Kontaktdaten auf die Karte dürfen (email,phone,website)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    contact = tuple(x.strip() for x in args.contact.split(",") if x.strip())
    try:
        if args.export:
            if not args.url:
                raise ValueError("--url fehlt: der Datenexport enthält die öffentliche Profil-URL nicht.")
            profile = from_export(args.export, args.url, contact)
        elif args.pdf:
            profile = from_pdf_text(pdf_to_text(Path(args.pdf)), contact)
        else:
            profile = from_text(Path(args.text).read_text(encoding="utf-8"))
        if args.url:
            profile["linkedin_url"] = validate_linkedin_url(args.url)
    except ValueError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2
    missing = [k for k in ("name", "linkedin_url") if not profile.get(k)]
    if missing:
        profile.setdefault("needs_review", []).extend(missing)
    Path(args.out).write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
