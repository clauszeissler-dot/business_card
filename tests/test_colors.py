import itertools

import pytest

from common import build_palette, contrast_ratio, hue_family_de


def test_contrast_extremes():
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0, rel=1e-3)
    assert contrast_ratio("#777777", "#777777") == pytest.approx(1.0)


@pytest.mark.parametrize("hexcolor,family", [("#E11D48", "Rot"), ("#0F766E", "Türkis"), ("#1D4ED8", "Blau"),
                                             ("#F59E0B", "Orange"), ("#111111", "Schwarz"), ("#FAFAFA", "Weiß")])
def test_hue_family(hexcolor, family):
    assert hue_family_de(hexcolor) == family


BRANDS = ["#FFFF00", "#FFFFFF", "#000000", "#0F766E", "#F59E0B", "#E11D48", "#7DD3FC", "#1E1B4B"]


@pytest.mark.parametrize("primary,theme", itertools.product(BRANDS, ["light", "dark", "brand"]))
def test_palette_always_readable(primary, theme):
    pal = build_palette({"colors": {"primary": primary}}, theme)
    # Auf Markenfläche (brand) genügt AA 4,5:1, damit die Markenfarbe nicht verfälscht wird.
    assert contrast_ratio(pal["text"], pal["bg"]) >= (4.5 if theme == "brand" else 7.0)
    assert contrast_ratio(pal["muted"], pal["bg"]) >= 4.5
    assert contrast_ratio(pal["on_primary"], pal["primary"]) >= 4.5
    assert contrast_ratio(pal["accent_text"], pal["bg"]) >= 4.5
    # QR: dunkel auf hell, starker Kontrast
    assert contrast_ratio(pal["qr_dark"], pal["qr_light"]) >= 7.0
    assert contrast_ratio(pal["qr_light"], "#000000") > contrast_ratio(pal["qr_dark"], "#000000")
