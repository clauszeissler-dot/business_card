import http.server
import json
import threading

import pytest

import extract_ci
from extract_ci import FetchError, classify_font, extract, fetch, main
from conftest import FIXTURES


def test_extracts_colors_fonts_logo(tmp_path):
    brand = extract((FIXTURES / "site.html").read_text(), [], "https://nordlicht.example", None, tmp_path)
    assert brand["colors"]["primary"] == "#4F46E5"
    assert brand["colors"]["secondary"] == "#F97316"
    assert brand["colors"]["background"] == "#FAFAF9"
    assert brand["colors"]["text"] == "#1C1917"
    assert brand["fonts"]["heading"] == "Space Grotesk"
    assert brand["fonts"]["body"] == "DM Sans"
    assert brand["name"] == "Nordlicht Studio"
    assert brand["logo"] == "logo.svg"
    assert (tmp_path / "logo.svg").read_text().startswith("<svg")


def test_site_without_ci_gives_warnings(tmp_path):
    brand = extract("<html><body><p>Nur Text</p></body></html>", [], "", None, tmp_path)
    assert "primary" not in brand["colors"]
    joined = " ".join(brand["warnings"])
    assert "Markenfarbe" in joined and "Logo" in joined


def test_cli_offline(tmp_path):
    assert main(["--html", str(FIXTURES / "site.html"), "--out", str(tmp_path)]) == 0
    data = json.loads((tmp_path / "brand.json").read_text())
    assert data["colors"]["primary"] == "#4F46E5"


@pytest.mark.parametrize("name,kind", [("Playfair Display", "serif"), ("Inter", "sans"), ("JetBrains Mono", "mono"),
                                       ("Dancing Script", "script"), ("Noto Sans", "sans")])
def test_classify_font(name, kind):
    assert classify_font(name) == kind


# --- Missbrauch über echten lokalen Server (Host-Prüfung nur für diesen Test gelockert) ---

class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/redirect-internal":
            self.send_response(302)
            self.send_header("Location", "http://169.254.169.254/latest/meta-data/")
            self.end_headers()
        elif self.path == "/big":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            try:
                self.wfile.write(b"x" * (3 * 1024 * 1024))
            except OSError:
                pass
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><title>ok</title></html>")


@pytest.fixture
def local_server(monkeypatch):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    # Nur der Testhost darf auf 127.0.0.1 zeigen; alles andere bleibt geschützt.
    real = extract_ci.check_host
    monkeypatch.setattr(extract_ci, "check_host",
                        lambda host, port=443: "127.0.0.1" if host == "testhost.example" else real(host, port))
    yield f"http://testhost.example:{srv.server_address[1]}"
    srv.shutdown()


def test_control_normal_fetch_works(local_server):
    url, ctype, data = fetch(local_server + "/")
    assert b"<title>ok</title>" in data and ctype == "text/html"


def test_redirect_to_metadata_service_is_blocked(local_server):
    with pytest.raises(FetchError):
        fetch(local_server + "/redirect-internal")


def test_oversized_response_is_blocked(local_server):
    with pytest.raises(FetchError):
        fetch(local_server + "/big")


# --- Regressionen aus Realtests (20.11.2026) ---

def test_white_theme_color_is_not_primary(tmp_path):
    html = '<html><head><meta name="theme-color" content="#ffffff"><style>:root{--brand-text:#ED0007;--accent-fill:#007BC0}</style></head></html>'
    brand = extract(html, [], "", None, tmp_path)
    assert brand["colors"]["primary"] == "#ED0007"


def test_light_tints_and_hover_states_lose_against_core_brand(tmp_path):
    css = (":root{--brand-100:#D6D9FC;--brand-200:#B9B9F9;--brand-500:#635BFF;"
           "--btn-primary-hover:#C7D5E6} .a{color:#635BFF}.b{background:#635BFF}")
    brand = extract("<html></html>", [css], "", None, tmp_path)
    assert brand["colors"]["primary"] == "#635BFF"
    assert brand["colors"].get("secondary") not in ("#D6D9FC", "#B9B9F9", "#C7D5E6")


def test_letter_spacing_variables_are_not_fonts(tmp_path):
    css = ':root{--font-letter-spacing:-0.01em;--font-weight-bold:700;--font-sans:"Sohne",sans-serif}'
    brand = extract("<html></html>", [css], "", None, tmp_path)
    assert brand["fonts"]["heading"] == "Sohne"


def test_firecrawl_branding_is_mapped(tmp_path):
    from extract_ci import from_firecrawl
    data = json.loads((FIXTURES / "firecrawl_branding.json").read_text())
    brand = from_firecrawl(data, tmp_path, source="https://www.sparkasse.de")
    assert brand["colors"]["primary"] == "#EE0000"
    assert "secondary" not in brand["colors"]          # accent == primary -> keine zweite Farbe
    assert brand["colors"]["text"] == "#444444"
    assert brand["fonts"] == {"heading": "sparkasseHead", "body": "Sparkasse"}
    assert brand["suggest"]["corners"] == "round"
    assert brand["suggest"]["personality"]["energy"] == "high"
    assert (tmp_path / brand["logo"]).read_text().startswith("<svg")
    assert any("Logo" in w and "prüfen" in w for w in brand["warnings"])


def test_css_radius_suggests_corners(tmp_path):
    css = ".btn{border-radius:0}.card{border-radius:0px}.x{border-radius:2px}"
    assert extract("<html></html>", [css], "", None, tmp_path)["suggest"]["corners"] == "sharp"
    css = ".btn{border-radius:999px}.card{border-radius:24px}.x{border-radius:16px}"
    assert extract("<html></html>", [css], "", None, tmp_path)["suggest"]["corners"] == "round"
