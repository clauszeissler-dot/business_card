import json

import pytest

from common import validate_linkedin_url
from conftest import FIXTURES
from parse_profile import from_export, from_pdf_text, from_text, main


@pytest.mark.parametrize("url,expected", [
    ("https://www.linkedin.com/in/mara-beispiel", "https://www.linkedin.com/in/mara-beispiel/"),
    ("linkedin.com/in/mara-beispiel/?trk=x", "https://www.linkedin.com/in/mara-beispiel/"),
    ("https://de.linkedin.com/in/mara-beispiel/", "https://www.linkedin.com/in/mara-beispiel/"),
    ("http://www.linkedin.com/in/m%C3%BCller-k/", "https://www.linkedin.com/in/m%C3%BCller-k/"),
])
def test_valid_linkedin_urls(url, expected):
    assert validate_linkedin_url(url) == expected


@pytest.mark.parametrize("url", ["https://evil.example/in/x", "https://www.linkedin.com/company/acme",
                                 "javascript:alert(1)", "https://linkedin.com.evil.example/in/x",
                                 "https://www.linkedin.com/in/<script>/", ""])
def test_invalid_linkedin_urls(url):
    with pytest.raises(ValueError):
        validate_linkedin_url(url)


def test_export_folder_privacy_by_default():
    p = from_export(FIXTURES / "export", "https://www.linkedin.com/in/mara-beispiel")
    assert p["name"] == "Mara Beispiel"
    assert p["headline"].startswith("Gründerin")
    assert p["company"] == "Beispiel Logistik GmbH"
    assert p["title"] == "Gründerin"
    assert p["location"] == "Essen, Deutschland"
    assert p["website"] == "www.example.com"
    assert p["email"] == "mara@example.com"
    assert "phone" not in p            # Telefon nur auf Wunsch
    dump = json.dumps(p, ensure_ascii=False)
    assert "Geheimstraße" not in dump and "1990" not in dump  # Adresse/Geburtstag nie übernehmen


def test_export_with_phone():
    p = from_export(FIXTURES / "export", "linkedin.com/in/mara-beispiel", contact=("email", "phone", "website"))
    assert p["phone"] == "+49 201 000000"


def test_pdf_text():
    p = from_pdf_text((FIXTURES / "profile_pdf.txt").read_text())
    assert p["name"] == "Mara Beispiel"
    assert p["headline"] == "Gründerin & Strategin für nachhaltige Lieferketten"
    assert p["location"] == "Essen, Deutschland"
    assert p["linkedin_url"] == "https://www.linkedin.com/in/mara-beispiel/"
    assert p["email"] == "mara@example.com"
    assert p["company"] == "Beispiel Logistik GmbH"
    assert p["needs_review"]


def test_key_value_text():
    p = from_text("Name: Ada Lovelace\nHeadline: Mathematikerin\nLinkedIn: linkedin.com/in/ada-l\nE-Mail: ada@example.com")
    assert p == {**p, "name": "Ada Lovelace", "headline": "Mathematikerin",
                 "linkedin_url": "https://www.linkedin.com/in/ada-l/", "email": "ada@example.com"}


def test_cli_writes_profile(tmp_path):
    out = tmp_path / "profile.json"
    assert main(["--export", str(FIXTURES / "export"), "--url", "linkedin.com/in/mara-beispiel", "--out", str(out)]) == 0
    assert json.loads(out.read_text())["linkedin_url"] == "https://www.linkedin.com/in/mara-beispiel/"


def test_cli_rejects_bad_url(tmp_path):
    assert main(["--export", str(FIXTURES / "export"), "--url", "https://evil.example/in/x",
                 "--out", str(tmp_path / "p.json")]) == 2
