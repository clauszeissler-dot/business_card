"""Kern des Online-Dienstes (Vercel): LinkedIn-Anmeldung, Wallet-Signatur, Teilen.

Zustandslos: Es gibt keine Datenbank. Die Sitzung liegt verschlüsselt (AES-GCM) in einem
HttpOnly-Cookie und läuft nach einer Stunde ab. Personendaten werden nicht protokolliert.

Sicherheitsinvarianten (getestet in tests/test_service.py):
- Der Name im Pass stammt aus der LinkedIn-Anmeldung, nie aus Formulardaten.
- Die E-Mail ist frei wählbar (A-019), wird aber streng geprüft (Format, Länge, keine Zeilenumbrüche).
- Ohne gültige Sitzung keine Signatur und kein Posten.
- OAuth-State ist signiert, zeitlich begrenzt und an ein Cookie gebunden.
- Eingaben werden validiert (Profil-URL, Farben, Tage, Längen).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import normalize_hex, validate_linkedin_url  # noqa: E402

SESSION_COOKIE = "bc_session"
STATE_COOKIE = "bc_state"
SESSION_TTL = 3600
STATE_TTL = 600
SCOPES = "openid profile email w_member_social"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"


class ServiceError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def env(name, required=True):
    value = os.environ.get(name, "")
    if required and not value:
        raise ServiceError(503, f"Dienst noch nicht eingerichtet: {name} fehlt.")
    return value


def base_url():
    return env("PUBLIC_BASE_URL").rstrip("/")


# ---------------------------------------------------------------------------
# Verschlüsselte Cookies
# ---------------------------------------------------------------------------

def _key():
    raw = env("SESSION_SECRET")
    if len(raw) < 32:
        raise ServiceError(503, "SESSION_SECRET ist zu kurz (mindestens 32 Zeichen).")
    return hashlib.sha256(raw.encode()).digest()


def seal(data: dict) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = secrets.token_bytes(12)
    ct = AESGCM(_key()).encrypt(nonce, json.dumps(data, separators=(",", ":")).encode(), b"bc1")
    return base64.urlsafe_b64encode(nonce + ct).decode().rstrip("=")


def unseal(token: str):
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    try:
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        data = json.loads(AESGCM(_key()).decrypt(raw[:12], raw[12:], b"bc1"))
    except (ValueError, InvalidTag, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or data.get("exp", 0) < time.time():
        return None
    return data


def parse_cookies(header: str) -> dict:
    out = {}
    for part in (header or "").split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            out[k] = v
    return out


def cookie(name, value, max_age):
    return f"{name}={value}; Path=/; Max-Age={max_age}; HttpOnly; Secure; SameSite=Lax"


def session_from(headers) -> dict | None:
    token = parse_cookies(headers.get("Cookie", "")).get(SESSION_COOKIE)
    return unseal(token) if token else None


# ---------------------------------------------------------------------------
# OAuth (LinkedIn OpenID Connect)
# ---------------------------------------------------------------------------

def login_redirect():
    state = secrets.token_urlsafe(24)
    params = {"response_type": "code", "client_id": env("LINKEDIN_CLIENT_ID"),
              "redirect_uri": base_url() + "/api/callback", "state": state, "scope": SCOPES}
    sealed = seal({"state": state, "exp": time.time() + STATE_TTL})
    return AUTH_URL + "?" + urllib.parse.urlencode(params), cookie(STATE_COOKIE, sealed, STATE_TTL)


def _http(url, data=None, headers=None, method=None, timeout=10):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - feste https-Ziele
        body = resp.read(1024 * 1024)
        return resp.status, dict(resp.headers), body


def handle_callback(query: dict, headers, http=_http):
    if query.get("error"):
        raise ServiceError(400, "Anmeldung bei LinkedIn abgebrochen.")
    state_cookie = unseal(parse_cookies(headers.get("Cookie", "")).get(STATE_COOKIE, "") or "")
    if not state_cookie or not hmac.compare_digest(state_cookie.get("state", ""), query.get("state", "")):
        raise ServiceError(400, "Ungültige oder abgelaufene Anmeldung. Bitte erneut starten.")
    code = query.get("code", "")
    if not code or len(code) > 2000:
        raise ServiceError(400, "Kein Anmeldecode erhalten.")
    form = urllib.parse.urlencode({"grant_type": "authorization_code", "code": code,
                                   "client_id": env("LINKEDIN_CLIENT_ID"),
                                   "client_secret": env("LINKEDIN_CLIENT_SECRET"),
                                   "redirect_uri": base_url() + "/api/callback"}).encode()
    _, _, body = http(TOKEN_URL, form, {"Content-Type": "application/x-www-form-urlencoded"}, "POST")
    token = json.loads(body).get("access_token")
    if not token:
        raise ServiceError(502, "LinkedIn hat kein Zugriffstoken geliefert.")
    _, _, body = http(USERINFO_URL, None, {"Authorization": f"Bearer {token}"}, "GET")
    info = json.loads(body)
    session = {"sub": str(info.get("sub", ""))[:64], "name": str(info.get("name", ""))[:80],
               "email": str(info.get("email", ""))[:120] if info.get("email_verified", True) else "",
               "picture": str(info.get("picture", ""))[:500], "locale": _locale(info.get("locale")), "token": token,
               "exp": time.time() + SESSION_TTL}
    if not session["sub"] or not session["name"]:
        raise ServiceError(502, "LinkedIn hat keinen Namen geliefert.")
    return [cookie(SESSION_COOKIE, seal(session), SESSION_TTL), cookie(STATE_COOKIE, "", 0)]


def _locale(value) -> str:
    if isinstance(value, dict):
        value = f"{value.get('language', '')}_{value.get('country', '')}"
    value = str(value or "").replace("-", "_")
    return value if re.fullmatch(r"[a-z]{2}(_[A-Z]{2})?", value) else ""


FREEMAIL = {"gmx.de", "gmx.net", "gmx.at", "gmx.ch", "web.de", "t-online.de", "freenet.de", "gmail.com",
            "googlemail.com", "outlook.com", "outlook.de", "hotmail.com", "hotmail.de", "live.com", "live.de",
            "msn.com", "yahoo.com", "yahoo.de", "icloud.com", "me.com", "mac.com", "aol.com", "aol.de",
            "posteo.de", "mailbox.org", "proton.me", "protonmail.com", "gmx.com", "mail.de", "arcor.de"}


def public_me(session):
    if not session:
        return {"signed_in": False}
    email = session.get("email", "")
    domain = email.rsplit("@", 1)[-1].lower() if "@" in email else ""
    return {"signed_in": True, "name": session["name"], "email": email,
            "email_domain": "" if domain in FREEMAIL else domain,
            "lang": "en" if session.get("locale", "").startswith("en") else "de",
            "picture": session.get("picture", "")}


# ---------------------------------------------------------------------------
# Kartendaten
# ---------------------------------------------------------------------------

def card_input(session: dict, body: dict) -> tuple[dict, dict, int, str]:
    """Baut Profil/Marke aus Sitzung (Name, E-Mail) und Formular (Rest). Validiert alles."""
    if not session:
        raise ServiceError(401, "Bitte zuerst mit LinkedIn anmelden.")
    if not isinstance(body, dict):
        raise ServiceError(400, "Ungültige Anfrage.")

    def text(key, n):
        v = body.get(key) or ""
        if not isinstance(v, str):
            raise ServiceError(400, f"Feld {key} ist ungültig.")
        return " ".join(v.split())[:n]

    try:
        url = validate_linkedin_url(body.get("linkedin_url"))
    except ValueError as e:
        raise ServiceError(400, str(e)) from e
    profile = {"name": session["name"], "linkedin_url": url, "headline": text("headline", 120),
               "company": text("company", 80), "location": text("location", 60), "website": text("website", 80),
               "phone": text("phone", 40)}
    email = body.get("email") or ""
    if not isinstance(email, str) or len(email) > 120 or (
            email and not re.fullmatch(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}", email)):
        raise ServiceError(400, "E-Mail-Adresse ist ungültig.")
    if email:
        profile["email"] = email
    if profile["phone"] and not re.fullmatch(r"[+0-9 ()/\-]{4,40}", profile["phone"]):
        raise ServiceError(400, "Telefonnummer ist ungültig.")
    colors = {}
    for key in ("primary", "secondary"):
        if body.get(key):
            try:
                colors[key] = normalize_hex(body[key])
            except ValueError as e:
                raise ServiceError(400, f"Farbe {key} ist ungültig.") from e
    try:
        days = int(body.get("valid_days") or 0)
    except (TypeError, ValueError) as e:
        raise ServiceError(400, "Gültigkeit ist ungültig.") from e
    if days < 0 or days > 366:
        raise ServiceError(400, "Gültigkeit muss zwischen 0 und 366 Tagen liegen.")
    lang = "en" if body.get("lang") == "en" else "de"
    return {k: v for k, v in profile.items() if v}, {"colors": colors}, days, lang


# ---------------------------------------------------------------------------
# Wallet
# ---------------------------------------------------------------------------

def apple_pkpass(session, body):
    from wallet import apple_pass_json, build_pkpass

    profile, brand, days, lang = card_input(session, body)
    pj = apple_pass_json(profile, brand, env("APPLE_PASS_TYPE_ID"), env("APPLE_TEAM_ID"),
                         env("PASS_ORG_NAME"), days, lang=lang)
    wwdr = (ROOT / "assets" / "apple" / "AppleWWDRCAG4.cer").read_bytes()
    try:
        p12 = base64.b64decode(env("APPLE_P12_BASE64"))
    except ValueError as e:
        raise ServiceError(503, "APPLE_P12_BASE64 ist kein gültiges Base64.") from e
    return build_pkpass(pj, {}, p12, env("APPLE_P12_PASSWORD").encode(), wwdr, profile, brand)


def google_link(session, body):
    from wallet import google_pass, google_save_url

    profile, brand, days, lang = card_input(session, body)
    try:
        sa = json.loads(base64.b64decode(env("GOOGLE_SA_JSON_BASE64")))
    except ValueError as e:
        raise ServiceError(503, "GOOGLE_SA_JSON_BASE64 ist ungültig.") from e
    cls, obj = google_pass(profile, brand, env("GOOGLE_ISSUER_ID"), days, lang=lang,
                           logo_url=env("PASS_LOGO_URL", required=False) or None)
    return google_save_url(sa["client_email"], sa["private_key"].encode(), cls, obj, [base_url()])


# ---------------------------------------------------------------------------
# vCard, Sperrbildschirm, Erinnerung (A-020)
# ---------------------------------------------------------------------------

def _file_stem(name):
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-") or "kontakt"


def vcard_file(session, body):
    from extras import vcard

    profile, *_ = card_input(session, body)
    return vcard(profile).encode("utf-8"), _file_stem(profile["name"]) + ".vcf"


def lockscreen(session, body, today=None):
    """PNG für den Sperrbildschirm. Rückgabe (png, svg); 0 Tage = ohne Datum."""
    import extras
    from render import svg_to_png_bytes

    profile, brand, days, lang = card_input(session, body)
    device = body.get("device") or "iphone"
    if device not in extras.DEVICES:
        raise ServiceError(400, "Unbekanntes Gerät.")
    until = extras.valid_until(days, today) if days else None
    svg = extras.lockscreen_svg(profile, brand, device, until, lang=lang)["svg"]
    return svg_to_png_bytes(svg, extras.DEVICES[device]["size"][0]), svg


def reminder_file(session, body, today=None):
    import extras

    _, _, days, lang = card_input(session, body)
    if not days:
        raise ServiceError(400, "Für eine Erinnerung bitte eine Gültigkeit in Tagen angeben.")
    return extras.reminder_ics(extras.valid_until(days, today), lang).encode("utf-8")


# ---------------------------------------------------------------------------
# Teilen auf LinkedIn (Share on LinkedIn, w_member_social)
# ---------------------------------------------------------------------------

def share(session, body, http=_http):
    profile, brand, _, lang = card_input(session, body)
    text_ = body.get("text") or ""
    if not isinstance(text_, str) or not text_.strip() or len(text_) > 2800:
        raise ServiceError(400, "Beitragstext fehlt oder ist zu lang (max. 2800 Zeichen).")
    if body.get("confirm") is not True:
        raise ServiceError(400, "Bitte den Beitrag ausdrücklich bestätigen.")
    from make_card import render_card
    from render import svg_to_png_bytes

    png = svg_to_png_bytes(render_card(profile, brand, layout=body.get("layout") or "classic",
                                       pattern=body.get("pattern") or "dots", fmt="share", lang=lang)["front"], 1200)
    author = f"urn:li:person:{session['sub']}"
    auth = {"Authorization": f"Bearer {session['token']}", "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"}
    reg = {"registerUploadRequest": {"recipes": ["urn:li:digitalmediaRecipe:feedshare-image"], "owner": author,
                                     "serviceRelationships": [{"relationshipType": "OWNER",
                                                               "identifier": "urn:li:userGeneratedContent"}]}}
    _, _, rb = http("https://api.linkedin.com/v2/assets?action=registerUpload", json.dumps(reg).encode(), auth, "POST")
    rj = json.loads(rb)["value"]
    upload_url = rj["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    if not upload_url.startswith("https://"):
        raise ServiceError(502, "Unerwartete Upload-Adresse von LinkedIn.")
    http(upload_url, png, {"Authorization": f"Bearer {session['token']}", "Content-Type": "image/png"}, "PUT")
    post = {"author": author, "lifecycleState": "PUBLISHED",
            "specificContent": {"com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text_.strip()}, "shareMediaCategory": "IMAGE",
                "media": [{"status": "READY", "media": rj["asset"],
                           "title": {"text": "Business Card"}}]}},
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}}
    status, headers, _ = http("https://api.linkedin.com/v2/ugcPosts", json.dumps(post).encode(), auth, "POST")
    return {"ok": status in (200, 201), "post": headers.get("x-restli-id", "")}
