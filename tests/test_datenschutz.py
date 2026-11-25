"""Die Datenschutzseite muss zum tatsächlichen Verhalten des Dienstes passen."""
from pathlib import Path

from service import core

PAGE = (Path(__file__).resolve().parents[1] / "public" / "datenschutz.html").read_text(encoding="utf-8")


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
