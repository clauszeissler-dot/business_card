from render import svg_to_png
from make_card import render_card


def test_png_without_system_tools_uses_bundled_fonts(tmp_path, profile, brand, monkeypatch):
    import render
    monkeypatch.setattr(render.shutil, "which", lambda n: None)  # wie in der App-Sandbox
    res = render_card(profile, brand)
    out = tmp_path / "front.png"
    svg_to_png(res["front"], out, 1000)
    from PIL import Image
    im = Image.open(out)
    assert im.size[0] == 1000 and im.getbbox() is not None


def test_pdf_fallback_without_rsvg(tmp_path, profile, brand, monkeypatch):
    import render
    monkeypatch.setattr(render.shutil, "which", lambda n: None)
    res = render_card(profile, brand)
    out = tmp_path / "card.pdf"
    render.svgs_to_pdf([res["front"], res["back"]], out, "eu")
    data = out.read_bytes()
    assert data.startswith(b"%PDF") and data.count(b"/Type /Page") >= 2 or data.count(b"/Type/Page") >= 2
