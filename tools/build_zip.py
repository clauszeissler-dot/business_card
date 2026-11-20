"""Baut dist/business-card.zip zum Hochladen in die Claude-App (Customize → Skills) oder ChatGPT (Skills → Upload).

Enthält nur, was der Skill zur Laufzeit braucht: SKILL.md, scripts/, references/, assets/, requirements.txt, LICENSE.
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "business-card"
INCLUDE = ["SKILL.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "requirements.txt", "scripts", "references", "assets"]
SKIP = {"__pycache__", ".DS_Store"}


def build() -> Path:
    out = ROOT / "dist" / f"{NAME}.zip"
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for item in INCLUDE:
            p = ROOT / item
            files = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file())
            for f in files:
                if SKIP & set(f.parts):
                    continue
                z.write(f, f"{NAME}/{f.relative_to(ROOT)}")
    return out


if __name__ == "__main__":
    path = build()
    print(path, f"{path.stat().st_size // 1024} KB")
