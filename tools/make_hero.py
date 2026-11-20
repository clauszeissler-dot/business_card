"""Erzeugt docs/assets/hero.png (1600 × 900) aus den Beispielkarten. Nur für die Repo-Präsentation."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "docs" / "assets" / "examples"
W, H = 1600, 900
bold, regular = sys.argv[1], sys.argv[2]

bg = Image.new("RGB", (W, H), "#0B1220")
grad = Image.linear_gradient("L").rotate(90).resize((W, H))
bg = Image.composite(Image.new("RGB", (W, H), "#13233F"), bg, grad)
d = ImageDraw.Draw(bg)
for x in range(0, W, 40):
    for y in range(0, H, 40):
        d.ellipse((x - 1, y - 1, x + 1, y + 1), fill="#1E2C47")


def card(path, width, angle):
    im = Image.open(path).convert("RGBA")
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *im.size), radius=width // 40, fill=255)
    im.putalpha(mask)
    return im.rotate(angle, expand=True, resample=Image.BICUBIC)


def place(im, x, y):
    shadow = Image.new("RGBA", (im.width + 80, im.height + 80), (0, 0, 0, 0))
    sm = im.split()[3].point(lambda a: int(a * 0.55))
    shadow.paste((0, 0, 0, 255), (40, 52), sm)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    bg.paste(shadow, (x - 40, y - 40), shadow)
    bg.paste(im, (x, y), im)


place(card(D / "kanzlei-front.png", 500, 7), 1010, 40)
place(card(D / "demo-back.png", 500, -4), 720, 320)
place(card(D / "studio-front.png", 440, 5), 1110, 530)

f1 = ImageFont.truetype(bold, 68)
f2 = ImageFont.truetype(regular, 30)
f3 = ImageFont.truetype(bold, 22)
d = ImageDraw.Draw(bg)
d.text((90, 150), "Business Card", font=f1, fill="#F8FAFC")
d.text((90, 232), "im eigenen CI", font=f1, fill="#5EEAD4")
d.multiline_text((90, 340), "Website-CI auslesen · LinkedIn-Profil\nübernehmen · Druck-PDF mit QR-Code ·\nAnleitung für die LinkedIn Business Card",
                 font=f2, fill="#CBD5E1", spacing=12)
d.rounded_rectangle((90, 520, 440, 568), radius=24, fill="#5EEAD4")
d.text((115, 532), "Agent-Skill · Open Source", font=f3, fill="#0B1220")
bg.save(ROOT / "docs" / "assets" / "hero.png", optimize=True)
print("ok")
