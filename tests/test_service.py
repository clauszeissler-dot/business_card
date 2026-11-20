import base64
import http.client
import io
import json
import threading
import time
import zipfile
from http.server import ThreadingHTTPServer

import pytest

from conftest import ROOT  # noqa: F401
import sys
sys.path.insert(0, str(ROOT))
from service import core  # noqa: E402
from service.http import Handler  # noqa: E402

BASE = "https://bc.example.test"


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "x" * 48)
    monkeypatch.setenv("PUBLIC_BASE_URL", BASE)
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "cid")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("PASS_ORG_NAME", "KI AffAIrs")


def _session(**kw):
    return {"sub": "abc123", "name": "Mara Beispiel", "email": "mara@example.com", "picture": "", "token": "tok",
            "exp": time.time() + 600, **kw}


BODY = {"linkedin_url": "linkedin.com/in/mara-beispiel", "headline": "Gründerin", "primary": "#0F766E",
        "valid_days": 3}


def test_seal_roundtrip_and_tamper():
    tok = core.seal(_session())
    assert core.unseal(tok)["name"] == "Mara Beispiel"
    bad = tok[:-3] + ("A" if tok[-3] != "A" else "B") + tok[-2:]
    assert core.unseal(bad) is None
    assert core.unseal(core.seal(_session(exp=time.time() - 1))) is None


def test_other_secret_cannot_read_session(monkeypatch):
    tok = core.seal(_session())
    monkeypatch.setenv("SESSION_SECRET", "y" * 48)
    assert core.unseal(tok) is None


def test_missing_config_gives_503(monkeypatch):
    monkeypatch.delenv("SESSION_SECRET")
    with pytest.raises(core.ServiceError) as e:
        core.seal({})
    assert e.value.status == 503


def test_login_redirect_has_state_cookie():
    url, cookie = core.login_redirect()
    assert url.startswith("https://www.linkedin.com/oauth/v2/authorization?")
    assert "redirect_uri=https%3A%2F%2Fbc.example.test%2Fapi%2Fcallback" in url
    assert "scope=openid+profile+email+w_member_social" in url
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=Lax" in cookie


def _state_headers(state):
    sealed = core.seal({"state": state, "exp": time.time() + 60})
    return {"Cookie": f"{core.STATE_COOKIE}={sealed}"}


def test_callback_rejects_wrong_state():
    with pytest.raises(core.ServiceError) as e:
        core.handle_callback({"state": "evil", "code": "c"}, _state_headers("good"), http=lambda *a, **k: None)
    assert e.value.status == 400


def test_callback_success_creates_session():
    calls = []

    def fake_http(url, data=None, headers=None, method=None, timeout=10):
        calls.append(url)
        if url == core.TOKEN_URL:
            assert b"client_secret=csecret" in data
            return 200, {}, json.dumps({"access_token": "T"}).encode()
        assert headers["Authorization"] == "Bearer T"
        return 200, {}, json.dumps({"sub": "s1", "name": "Mara Beispiel", "email": "m@example.com",
                                    "email_verified": True}).encode()

    cookies = core.handle_callback({"state": "good", "code": "c"}, _state_headers("good"), http=fake_http)
    token = cookies[0].split(";")[0].split("=", 1)[1]
    assert core.unseal(token)["name"] == "Mara Beispiel"
    assert calls == [core.TOKEN_URL, core.USERINFO_URL]


def test_card_input_requires_session_and_ignores_foreign_name():
    with pytest.raises(core.ServiceError) as e:
        core.card_input(None, BODY)
    assert e.value.status == 401
    profile, brand, days, lang = core.card_input(_session(), dict(BODY, name="Elon Fake", email="x@evil.example"))
    assert profile["name"] == "Mara Beispiel" and profile["email"] == "mara@example.com"
    assert days == 3 and brand["colors"]["primary"] == "#0F766E"


@pytest.mark.parametrize("patch", [{"linkedin_url": "https://evil.example/in/x"}, {"primary": "red;}"},
                                   {"valid_days": 999}, {"valid_days": "drei"}, {"phone": "<script>"},
                                   {"headline": {"x": 1}}])
def test_card_input_rejects_bad_values(patch):
    with pytest.raises(core.ServiceError) as e:
        core.card_input(_session(), dict(BODY, **patch))
    assert e.value.status == 400


def test_apple_pass_with_test_certificate(monkeypatch):
    from test_wallet import _cert
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import pkcs12
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    p12 = pkcs12.serialize_key_and_certificates(b"t", key, _cert("Pass Type ID: pass.t", key), None,
                                                serialization.BestAvailableEncryption(b"pw"))
    monkeypatch.setenv("APPLE_PASS_TYPE_ID", "pass.t")
    monkeypatch.setenv("APPLE_TEAM_ID", "TEAM123456")
    monkeypatch.setenv("APPLE_P12_BASE64", base64.b64encode(p12).decode())
    monkeypatch.setenv("APPLE_P12_PASSWORD", "pw")
    data = core.apple_pkpass(_session(), BODY)
    pj = json.loads(zipfile.ZipFile(io.BytesIO(data)).read("pass.json"))
    assert pj["generic"]["primaryFields"][0]["value"] == "Mara Beispiel"


def test_google_link(monkeypatch):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.NoEncryption()).decode()
    sa = {"client_email": "sa@x.iam.gserviceaccount.com", "private_key": pem}
    monkeypatch.setenv("GOOGLE_SA_JSON_BASE64", base64.b64encode(json.dumps(sa).encode()).decode())
    monkeypatch.setenv("GOOGLE_ISSUER_ID", "3388000000012345678")
    assert core.google_link(_session(), BODY).startswith("https://pay.google.com/gp/v/save/")


def test_share_needs_confirmation_and_text():
    with pytest.raises(core.ServiceError):
        core.share(_session(), dict(BODY, text="Hallo"), http=lambda *a, **k: None)
    with pytest.raises(core.ServiceError):
        core.share(_session(), dict(BODY, text="", confirm=True), http=lambda *a, **k: None)


def test_share_flow_uploads_image_and_posts():
    calls = []

    def fake_http(url, data=None, headers=None, method=None, timeout=10):
        calls.append((method, url))
        if "registerUpload" in url:
            return 200, {}, json.dumps({"value": {"asset": "urn:li:digitalmediaAsset:1", "uploadMechanism": {
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {"uploadUrl": "https://up.example/x"}}}}).encode()
        if url == "https://up.example/x":
            assert data[:8] == b"\x89PNG\r\n\x1a\n"
            return 201, {}, b""
        post = json.loads(data)
        assert post["author"] == "urn:li:person:abc123"
        return 201, {"x-restli-id": "urn:li:share:9"}, b"{}"

    res = core.share(_session(), dict(BODY, text="Meine neue Karte", confirm=True), http=fake_http)
    assert res == {"ok": True, "post": "urn:li:share:9"}
    assert [m for m, _ in calls] == ["POST", "PUT", "POST"]


# --- HTTP-Ebene: echter lokaler Server --------------------------------------------------

@pytest.fixture
def server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv.server_address[1]
    srv.shutdown()


def _req(port, method, path, body=None, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.request(method, path, body=body, headers=headers or {})
    r = c.getresponse()
    return r.status, dict(r.getheaders()), r.read()


def test_http_me_and_health(server):
    status, headers, body = _req(server, "GET", "/api/me")
    assert status == 200 and json.loads(body) == {"signed_in": False}
    assert headers["Cache-Control"] == "no-store" and headers["X-Frame-Options"] == "DENY"
    status, _, body = _req(server, "GET", "/api/health")
    assert json.loads(body)["configured"]["linkedin"] is True


def test_http_post_from_foreign_origin_is_rejected(server):
    sess = core.seal(_session())
    status, _, body = _req(server, "POST", "/api/pass/google", json.dumps(BODY),
                           {"Origin": "https://evil.example", "Content-Type": "application/json",
                            "Cookie": f"{core.SESSION_COOKIE}={sess}"})
    assert status == 403


def test_http_post_without_session_is_401(server):
    status, _, body = _req(server, "POST", "/api/pass/google", json.dumps(BODY),
                           {"Origin": BASE, "Content-Type": "application/json"})
    assert status == 401 and "anmelden" in json.loads(body)["error"]


def test_http_oversized_body(server):
    status, _, _ = _req(server, "POST", "/api/share", "x" * (70 * 1024),
                        {"Origin": BASE, "Content-Type": "application/json"})
    assert status == 413


def test_http_internal_errors_do_not_leak(server, monkeypatch):
    monkeypatch.setattr(core, "public_me", lambda s: 1 / 0)
    status, _, body = _req(server, "GET", "/api/me")
    assert status == 500 and b"ZeroDivision" not in body
