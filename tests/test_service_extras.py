"""A-018 bis A-020: Vorbelegung, frei wählbare E-Mail, vCard und Sperrbildschirm im Online-Dienst."""
import datetime as dt
import sys
import time

import pytest

from conftest import ROOT
sys.path.insert(0, str(ROOT))
from service import core  # noqa: E402

BASE = "https://bc.example.test"
BODY = {"linkedin_url": "linkedin.com/in/mara-beispiel", "headline": "Gründerin", "valid_days": 3}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "x" * 48)
    monkeypatch.setenv("PUBLIC_BASE_URL", BASE)
    monkeypatch.setenv("PASS_ORG_NAME", "KI AffAIrs")


def _session(**kw):
    return {"sub": "abc123", "name": "Mara Beispiel", "email": "mara@gmx.de", "picture": "", "token": "tok",
            "exp": time.time() + 600, **kw}


# --- A-019: E-Mail frei wählbar, Name bleibt an LinkedIn gebunden ---------------------------------

def test_email_comes_from_form_and_name_stays_locked():
    profile, *_ = core.card_input(_session(), dict(BODY, name="Elon Fake", email="mara@firma.de"))
    assert profile["name"] == "Mara Beispiel"
    assert profile["email"] == "mara@firma.de"


def test_empty_email_means_no_email_on_card():
    profile, *_ = core.card_input(_session(), dict(BODY, email=""))
    assert "email" not in profile
    profile, *_ = core.card_input(_session(), dict(BODY))
    assert "email" not in profile


@pytest.mark.parametrize("bad", ["keine-mail", "a@b", "x@y.de\r\nBCC:z@q.de", "a" * 120 + "@x.de",
                                 "<script>@x.de", {"x": 1}])
def test_invalid_email_is_rejected(bad):
    with pytest.raises(core.ServiceError) as e:
        core.card_input(_session(), dict(BODY, email=bad))
    assert e.value.status == 400


# --- A-018: weniger Tippen nach der Anmeldung ----------------------------------------------------

def test_public_me_suggests_business_domain_only_for_non_freemail():
    me = core.public_me(_session(email="mara@firma-beispiel.de"))
    assert me["email_domain"] == "firma-beispiel.de"
    for free in ("mara@gmx.de", "m@gmail.com", "m@googlemail.com", "m@web.de", "m@t-online.de", "m@outlook.com"):
        assert core.public_me(_session(email=free))["email_domain"] == ""


def test_public_me_passes_language_from_linkedin_locale():
    assert core.public_me(_session(locale="en_US"))["lang"] == "en"
    assert core.public_me(_session(locale="de_DE"))["lang"] == "de"
    assert core.public_me(_session())["lang"] == "de"


def test_callback_keeps_locale(monkeypatch):
    import json
    import urllib.parse
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "cid")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "cs")
    url, state_cookie = core.login_redirect()
    state = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["state"][0]
    sealed = state_cookie.split(";")[0].split("=", 1)[1]

    def fake_http(u, data=None, headers=None, method=None):
        if "accessToken" in u:
            return 200, {}, json.dumps({"access_token": "t"}).encode()
        return 200, {}, json.dumps({"sub": "s1", "name": "Mara", "email": "m@x.de", "email_verified": True,
                                    "locale": {"country": "US", "language": "en"}}).encode()

    cookies = core.handle_callback({"code": "c", "state": state}, {"Cookie": f"{core.STATE_COOKIE}={sealed}"},
                                   http=fake_http)
    session = core.unseal(cookies[0].split(";")[0].split("=", 1)[1])
    assert session["locale"] == "en_US"


# --- A-020: vCard und Sperrbildschirm im Dienst ---------------------------------------------------

def test_vcard_requires_session():
    with pytest.raises(core.ServiceError) as e:
        core.vcard_file(None, BODY)
    assert e.value.status == 401


def test_vcard_contains_card_data():
    data, filename = core.vcard_file(_session(), dict(BODY, email="mara@firma.de", company="Firma GmbH"))
    text = data.decode("utf-8")
    assert text.startswith("BEGIN:VCARD") and "FN:Mara Beispiel" in text
    assert "EMAIL;TYPE=INTERNET:mara@firma.de" in text and "ORG:Firma GmbH" in text
    assert "linkedin.com/in/mara-beispiel" in text
    assert filename == "Mara-Beispiel.vcf"


def test_lockscreen_png_with_valid_until():
    png, svg = core.lockscreen(_session(), dict(BODY, device="iphone"), today=dt.date(2026, 11, 25))
    assert png.startswith(b"\x89PNG")
    assert "27.11.2026" in svg


def test_lockscreen_without_days_has_no_date():
    _, svg = core.lockscreen(_session(), dict(BODY, device="android", valid_days=0), today=dt.date(2026, 11, 25))
    assert "Gültig bis" not in svg


def test_lockscreen_rejects_unknown_device():
    with pytest.raises(core.ServiceError) as e:
        core.lockscreen(_session(), dict(BODY, device="toaster"))
    assert e.value.status == 400


def test_reminder_needs_days_and_uses_end_date():
    with pytest.raises(core.ServiceError):
        core.reminder_file(_session(), dict(BODY, valid_days=0))
    data = core.reminder_file(_session(), BODY, today=dt.date(2026, 11, 25)).decode()
    assert "DTSTART;VALUE=DATE:20261127" in data


# --- HTTP-Routen für die Downloads ---------------------------------------------------------------

@pytest.fixture
def server():
    import threading
    from http.server import ThreadingHTTPServer
    from service.http import Handler
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv.server_address[1]
    srv.shutdown()


def _post_form(port, path, payload, cookie=True, origin=BASE):
    import http.client
    import json
    import urllib.parse
    headers = {"Origin": origin, "Content-Type": "application/x-www-form-urlencoded"}
    if cookie:
        headers["Cookie"] = f"{core.SESSION_COOKIE}={core.seal(_session())}"
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    c.request("POST", path, urllib.parse.urlencode({"payload": json.dumps(payload)}), headers)
    r = c.getresponse()
    return r.status, dict(r.getheaders()), r.read()


@pytest.mark.parametrize("path,ctype,ext", [("/api/vcard", "text/vcard", ".vcf"),
                                            ("/api/lockscreen", "image/png", ".png"),
                                            ("/api/reminder", "text/calendar", ".ics")])
def test_download_routes(server, path, ctype, ext):
    status, headers, body = _post_form(server, path, dict(BODY, device="android"))
    assert status == 200, body[:200]
    assert headers["Content-Type"].startswith(ctype)
    assert headers["Content-Disposition"].startswith("attachment;") and ext in headers["Content-Disposition"]


@pytest.mark.parametrize("path", ["/api/vcard", "/api/lockscreen", "/api/reminder"])
def test_download_routes_need_session_and_origin(server, path):
    assert _post_form(server, path, BODY, cookie=False)[0] == 401
    assert _post_form(server, path, BODY, origin="https://evil.example")[0] == 403


# --- Anmeldung robust gegen falsche Adresse und alte Rückleitungen ---------------------------------

def _get(port, path, host=None):
    import http.client
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.request("GET", path, headers={"Host": host} if host else {})
    r = c.getresponse()
    return r.status, dict(r.getheaders()), r.read()


def test_login_on_other_host_redirects_to_canonical_address(server, monkeypatch):
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "cid")
    status, headers, _ = _get(server, "/api/login", host="business-card-wallet-abc123-team.vercel.app")
    assert status == 302 and headers["Location"] == BASE + "/api/login?canonical=1"
    assert "Set-Cookie" not in headers
    status, headers, _ = _get(server, "/api/login?canonical=1", host="intern.example")
    assert headers["Location"].startswith("https://www.linkedin.com/")  # keine Schleife


def test_login_on_canonical_host_goes_to_linkedin(server, monkeypatch):
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "cid")
    status, headers, _ = _get(server, "/api/login", host="bc.example.test")
    assert status == 302 and headers["Location"].startswith("https://www.linkedin.com/oauth/v2/authorization?")


def test_callback_error_returns_to_page_with_hint(server):
    status, headers, _ = _get(server, "/api/callback?code=x&state=y", host="bc.example.test")
    assert status == 302 and headers["Location"] == "/?anmeldung=fehler"
