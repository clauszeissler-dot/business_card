import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def test_zip_contains_runtime_only():
    from build_zip import build
    z = zipfile.ZipFile(build())
    names = z.namelist()
    assert "business-card/SKILL.md" in names
    assert "business-card/scripts/make_card.py" in names
    assert "business-card/assets/fonts/Inter-400.ttf" in names
    assert "business-card/requirements.txt" in names
    assert not any("/tests/" in n or "/.venv/" in n or "__pycache__" in n or n.endswith(".pkpass") for n in names)
    assert sum(i.file_size for i in z.infolist()) < 10 * 1024 * 1024
    head = z.read("business-card/SKILL.md").decode()
    assert head.startswith("---\nname: business-card\n")
