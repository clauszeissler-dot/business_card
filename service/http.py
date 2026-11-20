"""HTTP-Schicht des Dienstes (eine Vercel-Python-Funktion für alle /api/*-Routen)."""
from __future__ import annotations

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler

from . import core

MAX_BODY = 64 * 1024
SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "business-card"

    def log_message(self, *args):  # keine Personendaten in Logs
        pass

    # -- Antworten ---------------------------------------------------------
    def _send(self, status, body=b"", ctype="application/json; charset=utf-8", cookies=(), extra=None):
        self.send_response(status)
        for k, v in {**SECURITY_HEADERS, **(extra or {})}.items():
            self.send_header(k, v)
        for c in cookies:
            self.send_header("Set-Cookie", c)
        if body or ctype:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, data, cookies=()):
        self._send(status, json.dumps(data, ensure_ascii=False).encode(), cookies=cookies)

    def _redirect(self, location, cookies=()):
        self._send(302, b"", ctype="", cookies=cookies, extra={"Location": location})

    # -- Eingaben ----------------------------------------------------------
    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise core.ServiceError(413, "Anfrage zu groß.")
        raw = self.rfile.read(length) if length else b""
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if ctype == "application/json":
            return json.loads(raw or b"{}")
        if ctype == "application/x-www-form-urlencoded":
            data = {k: v[0] for k, v in urllib.parse.parse_qs(raw.decode(), keep_blank_values=True).items()}
            if "payload" in data:  # Formular-POST für den Apple-Pass (Safari öffnet dann Wallet)
                return json.loads(data["payload"])
            return data
        raise core.ServiceError(415, "Nur JSON oder Formulardaten.")

    def _check_origin(self):
        origin = self.headers.get("Origin") or ""
        if origin != core.base_url():
            raise core.ServiceError(403, "Anfrage von fremder Seite abgelehnt.")

    def _route(self):
        return urllib.parse.urlsplit(self.path).path.rstrip("/")

    # -- Routen ------------------------------------------------------------
    def do_GET(self):  # noqa: N802
        try:
            path = self._route()
            if path == "/api/login":
                url, c = core.login_redirect()
                return self._redirect(url, [c])
            if path == "/api/callback":
                q = {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).items()}
                cookies = core.handle_callback(q, self.headers)
                return self._redirect("/#angemeldet", cookies)
            if path == "/api/me":
                return self._json(200, core.public_me(core.session_from(self.headers)))
            if path == "/api/health":
                return self._json(200, {"ok": True, "configured": _configured()})
            return self._json(404, {"error": "Nicht gefunden."})
        except core.ServiceError as e:
            return self._json(e.status, {"error": e.message})
        except Exception:  # noqa: BLE001 - keine Interna nach außen
            return self._json(500, {"error": "Interner Fehler."})

    def do_POST(self):  # noqa: N802
        try:
            path = self._route()
            self._check_origin()
            session = core.session_from(self.headers)
            if path == "/api/logout":
                return self._json(200, {"ok": True}, [core.cookie(core.SESSION_COOKIE, "", 0)])
            body = self._body()
            if path == "/api/pass/apple":
                data = core.apple_pkpass(session, body)
                return self._send(200, data, "application/vnd.apple.pkpass",
                                  extra={"Content-Disposition": 'attachment; filename="business-card.pkpass"'})
            if path == "/api/pass/google":
                return self._json(200, {"url": core.google_link(session, body)})
            if path == "/api/share":
                return self._json(200, core.share(session, body))
            return self._json(404, {"error": "Nicht gefunden."})
        except core.ServiceError as e:
            return self._json(e.status, {"error": e.message})
        except (ValueError, json.JSONDecodeError):
            return self._json(400, {"error": "Ungültige Anfrage."})
        except Exception:  # noqa: BLE001
            return self._json(500, {"error": "Interner Fehler."})


def _configured():
    import os
    groups = {"linkedin": ["LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET"],
              "apple": ["APPLE_PASS_TYPE_ID", "APPLE_TEAM_ID", "APPLE_P12_BASE64", "APPLE_P12_PASSWORD"],
              "google": ["GOOGLE_ISSUER_ID", "GOOGLE_SA_JSON_BASE64"],
              "base": ["PUBLIC_BASE_URL", "SESSION_SECRET", "PASS_ORG_NAME"]}
    return {g: all(os.environ.get(k) for k in keys) for g, keys in groups.items()}
