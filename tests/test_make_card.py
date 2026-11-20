import shutil
import subprocess
import xml.etree.ElementTree as ET

import pytest

from make_card import FORMATS, LAYOUTS, PATTERNS, PHOTO_SHAPES, CORNERS, render_card

HAS_RSVG = shutil.which("rsvg-convert") is not None


def _parse(svg):
    return ET.fromstring(svg)


def test_catalog_sizes():
    assert len(LAYOUTS) >= 5
    assert len(PATTERNS) >= 7
    assert set(CORNERS) >= {"sharp", "soft", "round"}
    assert set(PHOTO_SHAPES) >= {"circle", "rounded", "square", "hexagon"}
    assert {"eu", "us", "wallet", "share"} <= set(FORMATS)


@pytest.mark.parametrize("layout", sorted(LAYOUTS))
@pytest.mark.parametrize("pattern", sorted(PATTERNS))
def test_all_layouts_and_patterns_render_valid_svg(profile, brand, layout, pattern):
    result = render_card(profile, brand, layout=layout, pattern=pattern)
    for side in ("front", "back"):
        root = _parse(result[side])
        assert root.tag.endswith("svg")
    assert result["report"]["text_fits"] is True
    assert result["report"]["min_text_contrast"] >= 4.5


@pytest.mark.parametrize("fmt", ["eu", "us", "wallet", "share"])
@pytest.mark.parametrize("theme", ["light", "dark", "brand"])
def test_formats_and_themes(profile, brand, fmt, theme):
    result = render_card(profile, brand, fmt=fmt, theme=theme)
    root = _parse(result["front"])
    assert root.get("viewBox")
    assert result["report"]["format"] == fmt


def test_print_format_has_bleed_and_digital_has_none(profile, brand):
    eu = render_card(profile, brand, fmt="eu")["report"]
    share = render_card(profile, brand, fmt="share")["report"]
    assert eu["bleed_mm"] == 3
    assert eu["trim_mm"] == [85, 55]
    assert share["bleed_mm"] == 0


def test_long_name_and_headline_still_fit(profile, brand):
    profile = dict(profile, name="Maximiliane Alexandra von Hohenzollern-Sigmaringen",
                   headline="Chief Transformation Officer für KI, Daten, Prozesse, Change, Organisationsentwicklung und Nachhaltigkeit im Mittelstand")
    for layout in LAYOUTS:
        result = render_card(profile, brand, layout=layout)
        assert result["report"]["text_fits"] is True, layout


def test_minimal_profile_without_optional_fields(brand):
    result = render_card({"name": "Ada", "linkedin_url": "https://www.linkedin.com/in/ada"}, brand)
    assert "Ada" in result["front"]


def test_missing_linkedin_url_is_rejected(brand):
    with pytest.raises(ValueError):
        render_card({"name": "Ada"}, brand)


def test_unknown_option_is_rejected(profile, brand):
    with pytest.raises(ValueError):
        render_card(profile, brand, layout="does-not-exist")


def test_no_linkedin_logo_or_brand_claim(profile, brand):
    result = render_card(profile, brand)
    for side in ("front", "back"):
        assert "linkedin-logo" not in result[side].lower()


@pytest.mark.skipif(not HAS_RSVG, reason="rsvg-convert fehlt")
@pytest.mark.parametrize("layout", sorted(LAYOUTS))
def test_qr_decodes_to_profile_url(tmp_path, profile, brand, layout):
    cv2 = pytest.importorskip("cv2")
    result = render_card(profile, brand, layout=layout, pattern="circuit")
    svg = tmp_path / "back.svg"
    png = tmp_path / "back.png"
    svg.write_text(result["back"], encoding="utf-8")
    subprocess.run(["rsvg-convert", "-w", "1400", "-b", "white", "-o", str(png), str(svg)], check=True)
    img = cv2.imread(str(png))
    data, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    assert data == "https://www.linkedin.com/in/mara-beispiel/"


LONG = dict(name="Maximiliane Alexandra von Hohenzollern-Sigmaringen",
            headline="Chief Transformation Officer für KI, Daten, Prozesse, Change, Organisationsentwicklung und Nachhaltigkeit",
            email="maximiliane.von-hohenzollern@beispiel-logistik-gruppe.example")


@pytest.mark.parametrize("layout", sorted(LAYOUTS))
@pytest.mark.parametrize("fmt", ["eu", "us"])
def test_print_text_never_below_minimum_size(profile, brand, layout, fmt):
    """Druck: keine Schrift unter 2,0 mm (≈ 5,7 pt) – auch bei extrem langen Angaben."""
    import re
    result = render_card(dict(profile, **LONG), brand, layout=layout, fmt=fmt)
    for side in ("front", "back"):
        sizes = [float(v) for v in re.findall(r'<text [^>]*font-size="([0-9.]+)"', result[side])]
        assert sizes and min(sizes) >= 2.0 * (FORMATS[fmt]["h"] / 55) - 1e-3, (side, min(sizes))


def test_long_email_is_wrapped_not_cut(profile, brand):
    result = render_card(dict(profile, **LONG), brand)
    assert "maximiliane.von-hohenzollern" in result["back"]
    assert "@beispiel-logistik-gruppe.example" in result["back"]
    assert "mail" not in result["report"]["truncated"]


def test_name_is_never_truncated_on_eu(profile, brand):
    for layout in LAYOUTS:
        result = render_card(dict(profile, **LONG), brand, layout=layout)
        assert "Name" not in result["report"]["truncated"], layout


def test_photo_is_clipped_into_shape(tmp_path, profile, brand):
    from PIL import Image
    photo = tmp_path / "me.png"
    Image.new("RGB", (64, 64), (200, 120, 80)).save(photo)
    for shape in PHOTO_SHAPES:
        res = render_card(dict(profile, photo=str(photo)), brand, layout="split", photo_shape=shape)
        assert "data:image/png;base64," in res["front"] and "clip-path" in res["front"]


def test_missing_font_is_reported(monkeypatch, tmp_path, profile, brand):
    import make_card
    monkeypatch.setattr(make_card, "font_installed", lambda name: False if name == "Sora" else True)
    res = render_card(profile, brand)
    make_card.write_outputs(res, profile, brand, tmp_path, png=False, pdf=False)
    assert any("Sora" in w and "nicht installiert" in w for w in res["report"]["warnings"])
    assert (tmp_path / "linkedin-native-card.md").is_file()


def test_cli_list_and_full_run(tmp_path):
    import json as _json
    from make_card import main
    from conftest import ROOT
    assert main(["--list"]) == 0
    out = tmp_path / "karte"
    assert main(["--profile", str(ROOT / "examples/demo/profile.json"), "--brand", str(ROOT / "examples/demo/brand.json"),
                 "--out", str(out), "--layout", "split", "--pattern", "circuit"]) == 0
    for f in ("front.svg", "back.svg", "preview.html", "report.json", "linkedin-native-card.md"):
        assert (out / f).is_file(), f
    if HAS_RSVG:
        assert (out / "card-print.pdf").read_bytes().startswith(b"%PDF")
    assert _json.loads((out / "report.json").read_text())["qr"]["url"].endswith("/in/mara-beispiel/")


def test_cli_rejects_bad_option(tmp_path, capsys):
    from make_card import main
    from conftest import ROOT
    with pytest.raises(SystemExit):
        main(["--profile", str(ROOT / "examples/demo/profile.json"), "--out", str(tmp_path), "--layout", "nope"])
