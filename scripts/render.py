"""SVG → PNG/PDF, auch ohne Systemprogramme (z. B. in der Claude- oder ChatGPT-App).

PNG: resvg (pip-Paket `resvg-py`) mit den mitgelieferten Schriften, damit die Karte
überall gleich aussieht. PDF: bevorzugt Vektor über `rsvg-convert`; fehlt es, ein
Raster-PDF in 600 dpi über Pillow (für Digitaldruck ausreichend).
"""
from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "assets" / "fonts"


def svg_to_png_bytes(svg: str, width: int) -> bytes:
    import resvg_py

    return bytes(resvg_py.svg_to_bytes(svg_string=svg, width=int(width), dpi=96, font_dirs=[str(FONT_DIR)],
                                       sans_serif_family="Inter", serif_family="Source Serif 4"))


def svg_to_png(svg: str, out: Path, width: int) -> Path:
    out = Path(out)
    out.write_bytes(svg_to_png_bytes(svg, width))
    return out


def svgs_to_pdf(svgs, out: Path, fmt_key: str) -> str:
    """Mehrseitiges PDF. Rückgabe: 'vector' oder 'raster'."""
    from make_card import FORMATS

    out = Path(out)
    exe = shutil.which("rsvg-convert")
    if exe:
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i, svg in enumerate(svgs):
                p = Path(tmp) / f"{i}.svg"
                p.write_text(svg, encoding="utf-8")
                paths.append(str(p))
            subprocess.run([exe, "-f", "pdf", "-o", str(out)] + paths, check=True)
        return "vector"
    from PIL import Image

    f = FORMATS[fmt_key]
    w_mm = f["w"] + 2 * f["bleed"]
    dpi = 600
    px = round(w_mm / 25.4 * dpi) if f["unit"] == "mm" else int(f["w"] * 2)
    pages = [Image.open(io.BytesIO(svg_to_png_bytes(s, px))).convert("RGB") for s in svgs]
    pages[0].save(out, "PDF", resolution=dpi if f["unit"] == "mm" else 144, save_all=True, append_images=pages[1:])
    return "raster"
