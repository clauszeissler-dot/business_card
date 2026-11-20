#!/usr/bin/env python3
"""Deterministischer Teil der Evals: führt die Skript-Schritte je Fall aus und prüft die Assertions.

Prüft NICHT das Agentenverhalten (Antworttext). Dafür die Prompts aus evals.json im Agenten ausführen.
Fall 1 braucht Internet (sparkasse.de); mit --offline wird er übersprungen.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import hue_family_de  # noqa: E402
from extract_ci import FetchError, fetch  # noqa: E402
from make_card import render_card  # noqa: E402
from native import recommend_native  # noqa: E402

results = []


def check(case, name, ok):
    results.append((case, name, bool(ok)))


def run(*args):
    return subprocess.run([sys.executable, "-I", *map(str, args)], capture_output=True, text=True)


tmp = Path(tempfile.mkdtemp())
offline = "--offline" in sys.argv

# Fall 1
if not offline:
    r = run(ROOT / "scripts/extract_ci.py", "https://www.sparkasse.de", "--out", tmp / "b1")
    brand = json.loads((tmp / "b1/brand.json").read_text()) if r.returncode == 0 else {}
    check(1, "primary ist Rot", hue_family_de(brand.get("colors", {}).get("primary", "#000000")) == "Rot")
    p = {"name": "Erika Muster", "headline": "Filialleiterin Privatkunden", "company": "Sparkasse Musterstadt",
         "email": "erika@example.com", "linkedin_url": "linkedin.com/in/erika-muster"}
    res = render_card(p, brand, theme="brand", layout="profile")
    rep = res["report"]
    check(1, "QR-URL", rep["qr"]["url"] == "https://www.linkedin.com/in/erika-muster/")
    check(1, "Text passt + Kontrast", rep["text_fits"] and rep["min_text_contrast"] >= 4.5)
    check(1, "kein Telefon-Icon", "lucide-phone" not in res["back"] and "+49" not in res["back"])

# Fall 2
md = recommend_native({"name": "Test", "linkedin_url": "linkedin.com/in/test"},
                      {"colors": {"primary": "#1E3A5F", "secondary": "#B08D57"}, "fonts": {"heading": "Georgia"}},
                      render_card({"name": "Test", "linkedin_url": "linkedin.com/in/test"},
                                  {"colors": {"primary": "#1E3A5F"}, "fonts": {"heading": "Georgia"}})["report"])
check(2, "alle Optionen", all(o in md for o in ("Info", "Layout", "Font", "Colors", "Pattern", "Stickers and Doodle")))
check(2, "Serif", "Serif" in md)
check(2, "Doppeltippen", "doppelt" in md.lower() or "Doppeltippen" in md)
check(2, "keine Hex-Eingabe behauptet", "nicht vorgesehen" in md)
check(2, "Quelle + Stand", "a16648713" in md and "Stand" in md)

# Fall 3
res = render_card({"name": "Lea Sommer", "headline": "Creative Director", "company": "Pulse Studio",
                   "location": "Berlin", "linkedin_url": "linkedin.com/in/lea-sommer-beispiel"},
                  {"colors": {"primary": "#DB2777"}, "fonts": {"heading": "Sora"}},
                  fmt="share", lang="en", theme="dark", layout="diagonal")
check(3, "Scan to connect", "Scan to connect" in res["back"])
check(3, "Format share", res["report"]["trim_px"] == [1200, 627])
md3 = recommend_native({"name": "Lea Sommer", "linkedin_url": "linkedin.com/in/lea-sommer-beispiel"},
                       {"colors": {"primary": "#DB2777"}}, res["report"])
check(3, "App-Anleitung englisch", "Tap your" in md3 and "Pink" in md3 and "Stand der Fakten" not in md3)

# Fall 4
try:
    fetch("http://192.168.0.10/intranet")
    check(4, "intern abgelehnt", False)
except FetchError as e:
    check(4, "intern abgelehnt", "nicht öffentliche" in str(e))

# Fall 5
res = render_card({"name": "Maximiliane Alexandra von Hohenzollern-Sigmaringen",
                   "headline": "Chief Transformation Officer für KI, Daten, Prozesse, Change und Nachhaltigkeit",
                   "linkedin_url": "linkedin.com/in/max-hz"}, {})
check(5, "Name nicht gekürzt", "Name" not in res["report"]["truncated"])

# Fall 6
import datetime as _dt  # noqa: E402
from extras import lockscreen_svg, valid_until, vcard  # noqa: E402
prof6 = {"name": "Mara Beispiel", "linkedin_url": "linkedin.com/in/mara-beispiel", "email": "mara@example.com"}
until = valid_until(3)
ls = lockscreen_svg(prof6, {}, "iphone", until, "Messe Essen")
check(6, "Datum heute+2", until == _dt.date.today() + _dt.timedelta(days=2) and until.strftime("%d.%m.%Y") in ls["svg"])
check(6, "Event", "Messe Essen" in ls["svg"])
vc = vcard(prof6)
check(6, "vCard", "FN:Mara Beispiel" in vc and "URL:https://www.linkedin.com/in/mara-beispiel/" in vc)

failed = [r for r in results if not r[2]]
for case, name, ok in results:
    print(f"{'PASS' if ok else 'FAIL'}  Fall {case}: {name}")
print(f"\n{len(results) - len(failed)}/{len(results)} bestanden")
sys.exit(1 if failed else 0)
