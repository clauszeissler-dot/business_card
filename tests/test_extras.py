import datetime as dt
import xml.etree.ElementTree as ET

import pytest

from extras import DEVICES, lockscreen_svg, reminder_ics, vcard


def test_vcard_contains_fields_and_escapes(profile):
    v = vcard(dict(profile, company="Beispiel; Logistik, GmbH"))
    assert v.startswith("BEGIN:VCARD\r\nVERSION:3.0\r\n") and v.endswith("END:VCARD\r\n")
    assert "FN:Mara Beispiel" in v and "N:Beispiel;Mara;;;" in v
    assert "ORG:Beispiel\; Logistik\\, GmbH" in v
    assert "EMAIL;TYPE=INTERNET:mara@example.com" in v
    assert "URL:https://www.linkedin.com/in/mara-beispiel/" in v
    assert "URL:https://example.com" in v
    assert all(len(line.encode()) <= 75 for line in v.split("\r\n"))  # RFC-Zeilenfaltung


def test_vcard_with_photo(tmp_path, profile):
    from PIL import Image
    ph = tmp_path / "p.jpg"
    Image.new("RGB", (40, 40), (10, 20, 30)).save(ph)
    assert "PHOTO;ENCODING=b;TYPE=JPEG:" in vcard(dict(profile, photo=str(ph)))


def test_vcard_rejects_newline_injection(profile):
    v = vcard(dict(profile, name="Mara\r\nEMAIL:evil@x.example Beispiel"))
    assert "\r\nEMAIL:evil" not in v


@pytest.mark.parametrize("device", sorted(DEVICES))
def test_lockscreen_layout_respects_clock_and_buttons(profile, brand, device):
    until = dt.date(2026, 11, 23)
    res = lockscreen_svg(profile, brand, device=device, valid_until=until, event="Messe Essen")
    root = ET.fromstring(res["svg"])
    w, h = DEVICES[device]["size"]
    assert root.get("viewBox") == f"0 0 {w} {h}"
    assert "23.11.2026" in res["svg"] and "Messe Essen" in res["svg"]
    # QR-Zone liegt unterhalb der Uhr (oberste 34 %) und oberhalb der Tasten (untere 12 %)
    top, bottom = res["qr_box"][1], res["qr_box"][1] + res["qr_box"][3]
    assert top >= 0.34 * h and bottom <= 0.88 * h
    assert res["qr_box"][2] >= 0.5 * w  # groß genug zum Scannen


def test_lockscreen_english(profile, brand):
    res = lockscreen_svg(profile, brand, valid_until=dt.date(2026, 11, 23), lang="en")
    assert "Valid until" in res["svg"] and "Scan to connect" in res["svg"]


def test_reminder_ics(profile):
    ics = reminder_ics(dt.date(2026, 11, 23), "de")
    assert "BEGIN:VCALENDAR" in ics and "DTSTART;VALUE=DATE:20261123" in ics
    assert "Sperrbildschirm" in ics and "BEGIN:VALARM" in ics
