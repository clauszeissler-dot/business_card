from make_card import render_card
from native import recommend_native


def test_native_recommendation_is_concrete(profile, brand):
    rep = render_card(profile, dict(brand, fonts={"heading": "Playfair Display", "body": "Inter"}),
                      layout="split", pattern="circuit")["report"]
    md = recommend_native(profile, brand, rep)
    for needle in ("Profilfoto", "QR-Code", "Edit", "Info", "Layout", "Font", "Colors", "Pattern",
                   "Stickers", "Add to Wallet", "Save", "#0F766E", "Türkis", "a16648713", "Stand"):
        assert needle in md, needle
    assert "Serif" in md            # Playfair → Serifenschrift empfehlen
    assert "nur in der LinkedIn-App" in md


def test_long_headline_gets_shortening_hint(profile, brand):
    p = dict(profile, headline="x" * 140)
    md = recommend_native(p, brand, render_card(p, brand)["report"])
    assert "kürzen" in md


def test_no_brand_colors_gives_neutral_advice(profile):
    md = recommend_native(profile, {}, render_card(profile, {})["report"])
    assert "Markenfarbe" in md
