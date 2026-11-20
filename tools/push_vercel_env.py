"""Überträgt die Werte aus ~/Desktop/business-card-secrets nach Vercel, ohne sie auszugeben.

Aufruf (im Repo, nach `npx vercel login` und `npx vercel link`):
    python3 tools/push_vercel_env.py [--dir ~/Desktop/business-card-secrets] [--dry-run]
"""
import argparse
import base64
import subprocess
import sys
from pathlib import Path

REQUIRED = ["SESSION_SECRET", "PASS_ORG_NAME", "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "APPLE_PASS_TYPE_ID",
            "APPLE_TEAM_ID", "APPLE_P12_PASSWORD", "GOOGLE_ISSUER_ID"]
FILES = {"APPLE_P12_BASE64": "pass.p12", "GOOGLE_SA_JSON_BASE64": "google-service-account.json"}


def collect(folder: Path):
    values, missing = {}, []
    for line in (folder / "secrets.env").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if v.strip():
                values[k.strip()] = v.strip()
    for key, name in FILES.items():
        p = folder / name
        if p.is_file():
            values[key] = base64.b64encode(p.read_bytes()).decode()
    for key in REQUIRED + list(FILES):
        if key not in values:
            missing.append(key)
    return values, missing


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path.home() / "Desktop" / "business-card-secrets"))
    ap.add_argument("--extra", action="append", default=[], help="KEY=VALUE für nicht geheime Werte")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--write-env", action="store_true",
                    help="schreibt vercel-import.env in den Ordner (zum Einfügen in Vercel → Environment Variables)")
    args = ap.parse_args(argv)
    values, missing = collect(Path(args.dir).expanduser())
    for kv in args.extra:
        k, v = kv.split("=", 1)
        values[k] = v
    print("Vorhanden:", ", ".join(sorted(values)))
    if missing:
        print("Fehlt noch:", ", ".join(missing))
    if args.write_env:
        target = Path(args.dir).expanduser() / "vercel-import.env"
        target.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
        target.chmod(0o600)
        print("Geschrieben:", target)
        return 0 if not missing else 1
    if args.dry_run:
        return 0 if not missing else 1
    for key, value in values.items():
        for target in ("production", "preview"):
            r = subprocess.run(["npx", "-y", "vercel@latest", "env", "add", key, target, "--force"],
                               input=value, text=True, capture_output=True)
            ok = r.returncode == 0
            print(f"{'OK ' if ok else 'FEHLER'} {key} ({target})")
            if not ok:
                print("   ", (r.stderr or r.stdout).strip().splitlines()[-1][:200].replace(value, "***"))
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
