import xml.etree.ElementTree as ET

import pytest

from extract_ci import FetchError, check_host, fetch
from make_card import render_card


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "ftp://example.com/",
    "gopher://example.com/",
    "http://127.0.0.1/",
    "http://localhost/",
    "http://[::1]/",
    "http://10.0.0.5/",
    "http://192.168.1.1/",
    "http://172.16.0.1/",
    "http://169.254.169.254/latest/meta-data/",
    "http://0.0.0.0/",
    "http://user:pass@example.com/",
])
def test_fetch_rejects_dangerous_targets(url):
    with pytest.raises(FetchError):
        fetch(url)


def test_check_host_rejects_private_resolution(monkeypatch):
    import extract_ci
    monkeypatch.setattr(extract_ci.socket, "getaddrinfo",
                        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 80)), (2, 1, 6, "", ("10.1.2.3", 80))])
    with pytest.raises(FetchError):
        check_host("rebind.example")


def test_check_host_accepts_public(monkeypatch):
    import extract_ci
    monkeypatch.setattr(extract_ci.socket, "getaddrinfo",
                        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))])
    assert check_host("example.com") == "93.184.216.34"


def test_markup_injection_is_escaped(brand):
    evil = {"name": '<script>alert(1)</script> & "x"', "headline": "</text><image href='x'/>",
            "linkedin_url": "https://www.linkedin.com/in/ada"}
    result = render_card(evil, brand)
    for side in ("front", "back"):
        root = ET.fromstring(result[side])  # gültiges XML
        assert not any(el.tag.endswith("script") for el in root.iter())
        assert "<script>" not in result[side]


def test_malicious_svg_logo_is_only_embedded_as_image(tmp_path, profile, brand):
    logo = tmp_path / "logo.svg"
    logo.write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script><rect width="10" height="10"/></svg>')
    result = render_card(profile, dict(brand, logo=str(logo)))
    assert "<script" not in result["front"] and "<script" not in result["back"]
    assert "data:image/svg+xml;base64," in result["front"] + result["back"]


def test_oversized_logo_is_ignored(tmp_path, profile, brand):
    logo = tmp_path / "logo.png"
    logo.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * (2 * 1024 * 1024))
    result = render_card(profile, dict(brand, logo=str(logo)))
    assert "data:image/png" not in result["front"]
    assert any("Logo" in w for w in result["report"]["warnings"])
