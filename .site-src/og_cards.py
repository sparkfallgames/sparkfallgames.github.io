#!/usr/bin/env python3
"""og/twitter 分享卡生成器（v4 火花电影深色版）。

产出 assets/img/og-brand.jpg + og-<slug>.jpg（1200×630）。
品牌卡 = key art 压字；App 卡 = 深炭底 + 品牌色辉光 + 图标 + 名字 +
tagline + 设备框截图。手动运行：python3 .site-src/og_cards.py
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
IMG = ROOT / "assets" / "img"
W, H = 1200, 630

CONFIG = json.loads((SRC / "apps.json").read_text())
EN = json.loads((SRC / "i18n" / "en.json").read_text())

BG = (13, 11, 10)
TEXT = (242, 236, 228)
TEXT2 = (179, 168, 156)
AMBER = (255, 180, 105)
EMBER = (224, 102, 74)


def font(size, bold=True):
    candidates = [
        ("/System/Library/Fonts/HelveticaNeue.ttc", 1 if bold else 0),
        ("/System/Library/Fonts/Helvetica.ttc", 1 if bold else 0),
    ]
    for path, idx in candidates:
        try:
            return ImageFont.truetype(path, size, index=idx)
        except OSError:
            continue
    return ImageFont.load_default(size)


def spark_mark(size, color=AMBER):
    """四角火花徽记（近似官网 SVG spark）。"""
    ss = 4
    s = size * ss
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, r, ri = s / 2, s / 2, s * 0.14
    pts = []
    for i in range(4):
        import math
        a = math.pi / 2 * i
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        am = a + math.pi / 4
        pts.append((c + ri * math.cos(am), c + ri * math.sin(am)))
    d.polygon(pts, fill=color + (255,))
    return im.resize((size, size), Image.LANCZOS)


def glow_layer(color, cx, cy, radius, alpha=90):
    """品牌色径向辉光层。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=color + (alpha,))
    return layer.filter(ImageFilter.GaussianBlur(radius / 2.2))


def hex_rgb(hx):
    hx = hx.lstrip("#")
    return tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))


def rounded_icon(path, size, radius_frac=0.23):
    icon = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    ss = 3
    mask = Image.new("L", (size * ss, size * ss), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size * ss - 1, size * ss - 1],
        radius=round(size * ss * radius_frac), fill=255)
    return icon, mask.resize((size, size), Image.LANCZOS)


def save(im, name):
    out = IMG / name
    im.convert("RGB").save(out, quality=86, optimize=True)
    print(f"{name}  {out.stat().st_size // 1024}KB")


def brand_card():
    ka = Image.open(SRC / "art" / "keyart-dark.png").convert("RGB")
    scale = W / ka.width
    ka = ka.resize((W, round(ka.height * scale)), Image.LANCZOS)
    im = ka.crop((0, (ka.height - H) // 2, W, (ka.height - H) // 2 + H))
    # 左侧压字暗部
    scrim = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(scrim)
    for x in range(W):
        a = round(max(0.0, 0.82 - 1.05 * x / W) * 255)
        d.line([(x, 0), (x, H)], fill=a)
    im = Image.composite(Image.new("RGB", (W, H), (5, 4, 3)), im, scrim)
    d = ImageDraw.Draw(im)

    mark = spark_mark(44)
    im.paste(mark, (86, 118), mark)
    d.text((146, 122), "Sparkfall Games", font=font(34), fill=TEXT2)
    d.text((84, 208), "Playful games.", font=font(78), fill=TEXT)
    d.text((84, 300), "Honest tools.", font=font(78), fill=AMBER)
    d.text((86, 428), "Built solo. Private by design — no accounts,",
           font=font(30, bold=False), fill=TEXT2)
    d.text((86, 470), "no servers, no tracking.",
           font=font(30, bold=False), fill=TEXT2)
    save(im, "og-brand.jpg")


def app_card(app):
    slug = app["slug"]
    accent = hex_rgb(app["accent"])
    im = Image.new("RGB", (W, H), BG)
    im = Image.alpha_composite(im.convert("RGBA"),
                               glow_layer(accent, W - 180, -60, 420, 60))
    im = Image.alpha_composite(im, glow_layer(EMBER, -80, H + 80, 360, 36))

    # 右侧设备框截图
    framed_p = IMG / f"framed-{slug}.webp"
    if framed_p.exists():
        ph = Image.open(framed_p).convert("RGBA")
        target_h = 560
        pw = round(ph.width * target_h / ph.height)
        ph = ph.resize((pw, target_h), Image.LANCZOS)
        px, py = W - pw - 96, 96
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle([px + 10, py + 22, px + pw + 10, py + target_h + 22],
                             radius=60, fill=(0, 0, 0, 140))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(18)))
        im.paste(ph, (px, py), ph)

    d = ImageDraw.Draw(im)
    icon_p = IMG / f"icon-{slug}.webp"
    ty = 150
    if icon_p.exists():
        icon, mask = rounded_icon(icon_p, 110)
        im.paste(icon, (86, ty), mask)
    d.text((86, ty + 140), app["name"], font=font(64), fill=TEXT)
    tagline = EN["apps"][slug]["tagline"]
    d.text((86, ty + 226), tagline, font=font(32, bold=False), fill=TEXT2)

    mark = spark_mark(26)
    im.paste(mark, (86, H - 92), mark)
    d.text((124, H - 96), "Sparkfall Games", font=font(26), fill=TEXT2)
    save(im, f"og-{slug}.jpg")


if __name__ == "__main__":
    brand_card()
    for app in CONFIG["apps"]:
        app_card(app)
