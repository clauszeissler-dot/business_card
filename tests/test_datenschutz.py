"""Die Datenschutzseite muss zum tatsächlichen Verhalten des Dienstes passen."""
import sys
from pathlib import Path

from conftest import ROOT

sys.path.insert(0, str(ROOT))
from service import core  # noqa: E402

PAGE_PATH = Path(__file__).resolve().parents[1] / "public" / "datenschutz.html"
PAGE = PAGE_PATH.read_text(encoding="utf-8")


def _html():
    return PAGE_PATH.read_text(encoding="utf-8")


def test_verantwortlicher_und_aufsicht_genannt():
    for text in ("Claus Zeißler", "KI AffAIrs Consulting", "info@affairs-consulting.de",
                 "Landesbeauftragte für Datenschutz und Informationsfreiheit Nordrhein-Westfalen"):
        assert text in PAGE


def test_cookies_stimmen_mit_code_ueberein():
    assert core.SESSION_COOKIE in PAGE and core.STATE_COOKIE in PAGE
    assert core.SESSION_TTL == 3600 and "1 Stunde" in PAGE
    assert core.STATE_TTL == 600 and "10 Minuten" in PAGE
    assert "§ 25 Abs. 2 Nr. 2 TDDDG" in PAGE


def test_linkedin_scopes_und_widerruf_beschrieben():
    for scope in core.SCOPES.split():
        assert scope in PAGE
    assert "Berechtigte Dienste" in PAGE


def test_empfaenger_genannt():
    for name in ("Vercel Inc.", "LinkedIn Ireland Unlimited Company", "Google", "Apple",
                 "Data Privacy Framework", "media.licdn.com"):
        assert name in PAGE


def test_serverfunktion_in_frankfurt_und_so_beschrieben():
    import json
    cfg = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert cfg.get("regions") == ["fra1"]
    assert "Frankfurt am Main" in PAGE
    assert "in den USA." not in PAGE.split("<h2>4.")[1].split("<h2>5.")[0].split("Unsere Zugangsdaten")[0].split("Für die Übermittlung")[0]


def test_datenschutz_nennt_tatsaechliche_dienstadresse():
    # business-card-wallet.vercel.app gehört einem fremden Projekt (geprüft 25.11.2026)
    assert "business-card-wallet-three.vercel.app" in PAGE
    assert "unter business-card-wallet.vercel.app" not in PAGE


def test_datenschutz_nennt_lokale_speicherung_im_browser():
    """A-018: Die Merkfunktion speichert Formularangaben im Browser; die Seite muss das nennen."""
    html = _html()
    app = (ROOT / "public" / "app.js").read_text(encoding="utf-8")
    assert "localStorage" in app and "bc_saved" in app
    assert "bc_saved" in html and "Auf diesem Gerät merken" in html


def test_datenschutz_nennt_freie_email_und_downloads():
    """A-019/A-020: E-Mail ist frei wählbar; vCard und Sperrbildschirm entstehen ohne Speicherung."""
    html = _html()
    assert "frei eintragen" in html
    assert "vCard" in html and "Sperrbildschirm" in html


def test_datenschutz_nennt_profilsuche_bei_brave():
    """A-021: Der Name geht nur auf Klick an Brave Search."""
    html = _html()
    assert "Brave Software" in html and "Mein Profil finden" in html
    assert core.BRAVE_URL.startswith("https://api.search.brave.com/")
