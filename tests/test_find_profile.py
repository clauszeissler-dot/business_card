"""A-021: LinkedIn-Profil über Brave Search finden (Name nur aus der Sitzung, Nutzer bestätigt den Treffer)."""
import json
import sys
import time
import urllib.parse

import pytest

from conftest import ROOT
sys.path.insert(0, str(ROOT))
from service import core  # noqa: E402

BASE = "https://bc.example.test"


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "x" * 48)
    monkeypatch.setenv("PUBLIC_BASE_URL", BASE)
    monkeypatch.setenv("BRAVE_API_KEY", "brave-test-key")


def _session(**kw):
    return {"sub": "abc123", "name": "Mara Beispiel", "email": "", "picture": "", "token": "tok",
            "exp": time.time() + 600, **kw}


RESULTS = {"web": {"results": [
    {"url": "https://de.linkedin.com/in/mara-beispiel", "title": "Mara Beispiel – Gründerin & Strategin – Beispiel GmbH | LinkedIn",
     "description": "Berufserfahrung: <strong>Beispiel GmbH</strong> · Ausbildung: Uni Essen · Ort: Essen · 500+ Kontakte"},
    {"url": "https://www.linkedin.com/company/beispiel-gmbh", "title": "Beispiel GmbH | LinkedIn", "description": ""},
    {"url": "https://www.linkedin.com/in/mara-beispiel-123", "title": "Mara Beispiel - Steuerberaterin | LinkedIn",
     "description": "Experience: Kanzlei Muster · Location: Berlin"},
    {"url": "https://www.linkedin.com/in/otto-anders", "title": "Otto Anders - Mara Beispiel Fan | LinkedIn", "description": ""},
    {"url": "https://evil.example/in/mara", "title": "Mara Beispiel | LinkedIn", "description": ""},
    {"url": "https://de.linkedin.com/in/mara-beispiel", "title": "Mara Beispiel – Duplikat | LinkedIn", "description": ""},
]}}


def _fake(captured, payload=RESULTS, status=200):
    def http(url, data=None, headers=None, method=None, timeout=10):
        captured.append((url, headers))
        if status != 200:
            import urllib.error
            raise urllib.error.HTTPError(url, status, "x", {}, None)
        return 200, {}, json.dumps(payload).encode()
    return http


def test_find_requires_session():
    with pytest.raises(core.ServiceError) as e:
        core.find_profiles(None, {}, http=_fake([]))
    assert e.value.status == 401


def test_find_uses_only_session_name_and_api_key():
    cap = []
    core.find_profiles(_session(), {"q": "ignorier mich", "name": "Elon Fake"}, http=_fake(cap))
    url, headers = cap[0]
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["q"][0]
    assert url.startswith("https://api.search.brave.com/res/v1/web/search?")
    assert "Mara Beispiel" in q and "linkedin.com/in" in q and "Elon" not in q and "ignorier" not in q
    assert headers["X-Subscription-Token"] == "brave-test-key"


def test_find_returns_matching_profiles_with_headline_company_location():
    hits = core.find_profiles(_session(), {}, http=_fake([]))["matches"]
    assert [h["linkedin_url"] for h in hits] == ["https://www.linkedin.com/in/mara-beispiel/",
                                                  "https://www.linkedin.com/in/mara-beispiel-123/"]
    assert hits[0]["headline"] == "Gründerin & Strategin"
    assert hits[0]["company"] == "Beispiel GmbH" and hits[0]["location"] == "Essen"
    assert hits[1]["headline"] == "Steuerberaterin" and hits[1]["company"] == "Kanzlei Muster"
    assert "<" not in json.dumps(hits)


def test_find_limits_to_three():
    many = {"web": {"results": [{"url": f"https://www.linkedin.com/in/mara-beispiel-{i}",
                                 "title": "Mara Beispiel - X | LinkedIn", "description": ""} for i in range(8)]}}
    assert len(core.find_profiles(_session(), {}, http=_fake([], many))["matches"]) == 3


def test_find_without_key_is_503(monkeypatch):
    monkeypatch.delenv("BRAVE_API_KEY")
    with pytest.raises(core.ServiceError) as e:
        core.find_profiles(_session(), {}, http=_fake([]))
    assert e.value.status == 503


def test_find_upstream_error_is_502_without_details():
    with pytest.raises(core.ServiceError) as e:
        core.find_profiles(_session(), {}, http=_fake([], status=429))
    assert e.value.status == 502 and "brave-test-key" not in e.value.message


def test_find_is_limited_per_session():
    sess = _session()
    for _ in range(core.FIND_LIMIT):
        res = core.find_profiles(sess, {}, http=_fake([]))
        sess = core.unseal(res["cookie"].split(";")[0].split("=", 1)[1])
    with pytest.raises(core.ServiceError) as e:
        core.find_profiles(sess, {}, http=_fake([]))
    assert e.value.status == 429


def test_find_route_needs_session_and_origin():
    import http.client
    import threading
    from http.server import ThreadingHTTPServer
    from service.http import Handler
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        def post(headers):
            c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=5)
            c.request("POST", "/api/find-profile", "{}", {"Content-Type": "application/json", **headers})
            return c.getresponse().status
        assert post({"Origin": BASE}) == 401
        sess = core.seal(_session())
        assert post({"Origin": "https://evil.example", "Cookie": f"{core.SESSION_COOKIE}={sess}"}) == 403
    finally:
        srv.shutdown()
