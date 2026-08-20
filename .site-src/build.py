#!/usr/bin/env python3
"""Static site generator for the apps site (sparkfallgames.com, hosted on GitHub Pages).

Design system v4 "火花电影 / Ember Cinema" (2026-08-20 用户赛马拍板 A 案):
dark charcoal shell site-wide, original spark-shower key art hero, cinematic
full-width bands for games/tools, ember-amber accent. Never pure black.

Reads apps.json + i18n/<lang>.json, emits:
  /index.html, /<app>/index.html            (English, site root)
  /<lang>/index.html, /<lang>/<app>/...     (30 more languages)
  /assets/img/*                             (compressed screenshots + icons)

Legal pages (/<app>/privacy.html, /<app>/support.html) are hand-written and
NEVER touched by this script — their URLs are referenced from shipped apps.
"""

import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent

CONFIG = json.loads((SRC / "apps.json").read_text())
SITE = CONFIG["site"]
APPS = CONFIG["apps"]
LANGS = CONFIG["languages"]


def load_i18n():
    """Load all translation files and verify key parity against en."""
    def flat(d, prefix=""):
        keys = set()
        for k, v in d.items():
            kk = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys |= flat(v, kk)
            else:
                keys.add(kk)
        return keys

    data = {}
    base = None
    for lang in LANGS:
        path = SRC / "i18n" / f"{lang['code']}.json"
        data[lang["code"]] = json.loads(path.read_text())
        keys = flat(data[lang["code"]])
        if base is None:
            base = keys
        elif keys != base:
            missing = base - keys
            extra = keys - base
            sys.exit(f"i18n key mismatch in {lang['code']}: missing={sorted(missing)[:5]} extra={sorted(extra)[:5]}")
    return data


def device_frame(shot_path, width=520):
    """给纯界面截图加程序绘制的设备边框（圆角深框 + 灵动岛胶囊），返回 RGBA。"""
    from PIL import Image, ImageDraw

    shot = Image.open(shot_path).convert("RGB")
    sw = width
    sh = round(shot.height * sw / shot.width)
    shot = shot.resize((sw, sh), Image.LANCZOS)
    B = round(sw * 0.045)
    R = round(sw * 0.155)
    W, H = sw + B * 2, sh + B * 2
    SS = 3  # 超采样抗锯齿
    frame = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(frame)
    d.rounded_rectangle([0, 0, W * SS - 1, H * SS - 1], radius=R * SS,
                        fill=(26, 24, 22, 255))
    frame = frame.resize((W, H), Image.LANCZOS)
    ir = round(R * 0.72)
    mask = Image.new("L", (sw * SS, sh * SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, sw * SS - 1, sh * SS - 1], radius=ir * SS, fill=255)
    mask = mask.resize((sw, sh), Image.LANCZOS)
    frame.paste(shot, (B, B), mask)
    d = ImageDraw.Draw(frame)
    pw, ph = round(sw * 0.26), round(sw * 0.065)
    px, py = (W - pw) // 2, B + round(sw * 0.032)
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=ph // 2,
                        fill=(16, 14, 13, 255))
    return frame


def process_images():
    """Resize raw simulator screenshots for web, copy app icons, grade key art."""
    from PIL import Image, ImageEnhance

    img_dir = ROOT / "assets" / "img"
    img_dir.mkdir(parents=True, exist_ok=True)

    def webp(src, out, width, budget=82_000):
        im = Image.open(src).convert("RGB")
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
        # WebP 有损 + 超预算自动降质：性能预算单图 ≤80KB（原画类 PNG 会到 1MB+）
        for q in (82, 72, 62, 52):
            im.save(out, quality=q, method=6)
            if out.stat().st_size <= budget:
                break

    # 深色版视觉素材：品牌 key art（hero 背景）+
    # 游戏原画压暗调色（游戏电影横幅背景；源画在 006 工程，与 icon_map 同一依赖口径）
    # key art 源图仅 1536 宽（AI 生图上限）：锐化上采样出桌面 2304 版 +
    # 手机 1280 版；整体压暗一档让文字站住（2026-08-20 用户反馈「糊+抢眼」）
    keyart = SRC / "art" / "keyart-dark.png"
    if keyart.exists():
        from PIL import ImageChops, ImageFilter
        base = Image.open(keyart).convert("RGB")
        base = ImageEnhance.Brightness(base).enhance(0.78)
        for name, width, budget in (("keyart-dark.webp", 2304, 220_000),
                                    ("keyart-dark-m.webp", 1280, 90_000)):
            im = base.resize((width, round(base.height * width / base.width)),
                             Image.LANCZOS)
            im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=2))
            # 细颗粒：掩盖上采样的软 + 电影质感
            grain = Image.effect_noise(im.size, 9).convert("L")
            im = ImageChops.add(im, Image.merge("RGB", [grain] * 3),
                                scale=1, offset=-128)
            out = img_dir / name
            for q in (82, 74, 66, 58):
                im.save(out, quality=q, method=6)
                if out.stat().st_size <= budget:
                    break
    chibi = (ROOT.parent / "006/Mergehold/Assets.xcassets/Art"
             / "env_chibi.imageset/env_chibi.jpg")
    if chibi.exists():
        im = Image.open(chibi).convert("RGB")
        im = im.crop((0, round(im.height * 0.60), im.width, im.height))
        im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
        im = ImageEnhance.Brightness(im).enhance(0.42)
        out = img_dir / "art-chibi.webp"
        for q in (80, 70, 60):
            im.save(out, quality=q, method=6)
            if out.stat().st_size <= 140_000:
                break

    for app in APPS:
        raw = SRC / "shots" / f"raw-{app['slug']}.png"
        if raw.exists():
            webp(raw, img_dir / f"shot-{app['slug']}.webp", 640)
            # 设备框版（B「斜放展示」拍板：列表卡/入口卡/产品页首屏用）
            framed = device_frame(raw, 520)
            out = img_dir / f"framed-{app['slug']}.webp"
            for q in (82, 72, 62):
                framed.save(out, quality=q, method=6)
                if out.stat().st_size <= 82_000:
                    break
        # 走查图（产品页功能讲解区，英文界面全语言通用）
        for n in range(1, 5):
            walk = SRC / "shots" / f"walk-{app['slug']}-{n}.png"
            if walk.exists():
                webp(walk, img_dir / f"walk-{app['slug']}-{n}.webp", 520)

    icon_map = {
        "quickcost": ROOT.parent / "001/QuickCost/Assets.xcassets/AppIcon.appiconset/AppIcon.png",
        "decibelmeter": ROOT.parent / "002/DecibelMeter/Assets.xcassets/AppIcon.appiconset/AppIcon.png",
        "fastzen": ROOT.parent / "003/FastZen/Assets.xcassets/AppIcon.appiconset/AppIcon1024.png",
        "numzen": ROOT.parent / "004/NumZen/Assets.xcassets/AppIcon.appiconset/AppIcon.png",
        "gloomfall": ROOT.parent / "005/Gloomfall/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png",
        "mergehold": ROOT.parent / "006/Mergehold/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png",
        "overlens": ROOT.parent / "007/OverLens/Assets.xcassets/AppIcon.appiconset/AppIcon.png",
        "packnest": ROOT.parent / "008/PackNest/Assets.xcassets/AppIcon.appiconset/AppIcon.png",
    }
    for slug, src in icon_map.items():
        if src.exists():
            im = Image.open(src).convert("RGB").resize((192, 192), Image.LANCZOS)
            im.save(img_dir / f"icon-{slug}.webp", quality=88, method=6)


def t(d, dotted):
    cur = d
    for part in dotted.split("."):
        cur = cur[part]
    return cur


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def lang_url(lang, page):
    """Absolute path for a page in a language. page: '' (home) or '<slug>/'."""
    prefix = f"/{lang['path']}/" if lang["path"] else "/"
    return prefix + page


def hreflang_links(page):
    lines = []
    for lang in LANGS:
        lines.append(f'<link rel="alternate" hreflang="{lang["hreflang"]}" href="{SITE["base_url"]}{lang_url(lang, page)}">')
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{SITE["base_url"]}/{page}">')
    return "\n".join(lines)


def switcher(current, page):
    opts = []
    for lang in LANGS:
        sel = " selected" if lang["code"] == current["code"] else ""
        opts.append(f'<option value="{lang_url(lang, page)}"{sel}>{lang["name"]}</option>')
    return ('<select class="lang-switch" aria-label="Language" '
            'onchange="location.href=this.value">' + "".join(opts) + "</select>")


# Brand spark mark (four-point spark, ember gradient). Inline SVG, no asset request.
SPARK_MARK = (
    '<svg class="spark-mark" viewBox="0 0 24 24" aria-hidden="true">'
    '<defs><linearGradient id="sgrad" x1="0" y1="0" x2="24" y2="24">'
    '<stop stop-color="#ffb469"/><stop offset="1" stop-color="#e0664a"/>'
    '</linearGradient></defs>'
    '<path fill="url(#sgrad)" d="M12 1.5c.68 4.3 2.1 7 4 8.6 1.5 1.2 3.6 2 6.5 2.4-4.3.68-7 2.1-8.6 4-1.2 1.5-2 3.6-2.4 6.5-.68-4.3-2.1-7-4-8.6-1.5-1.2-3.6-2-6.5-2.4 4.3-.68 7-2.1 8.6-4 1.2-1.5 2-3.6 2.4-6.5z"/>'
    '</svg>')

VALUE_ICONS = {
    "private": ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
                'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                '<rect x="4" y="10.5" width="16" height="9.5" rx="2.5"/>'
                '<path d="M8 10.5V7a4 4 0 0 1 8 0v3.5"/></svg>'),
    "honest": ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
               'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
               '<path d="M20.6 13.3 13.3 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.7z"/>'
               '<circle cx="7.5" cy="7.5" r="1.4"/></svg>'),
    "global": ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
               'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
               '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/>'
               '<path d="M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/></svg>'),
}


def head(lang, s, title, desc, page, canonical, extra="", og_image="og-brand.jpg",
         hreflangs=True):
    direction = ' dir="rtl"' if lang.get("dir") == "rtl" else ""
    og_url = f"{SITE['base_url']}/assets/img/{og_image}"
    hl = hreflang_links(page) if hreflangs else ""
    return f"""<!DOCTYPE html>
<html lang="{lang['hreflang']}"{direction}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#0c0a09">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE['brand']}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_url}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{og_url}">
{hl}{extra}
<link rel="stylesheet" href="/assets/site.css">
<script defer src="/assets/site.js"></script>
</head>
<body>
"""


# 变现模式 → 首屏三徽章（总纲品牌卖点；hybrid 含订阅不得写"无订阅"）
BADGE_SETS = {
    "buyout": ["onetime", "nosub", "noads"],
    "hybrid": ["noads", "notracking", "honest"],
}
CATEGORY_SCHEMA = {
    "games": "GameApplication", "finance": "FinanceApplication",
    "health": "HealthApplication", "utilities": "UtilitiesApplication",
    "reference": "ReferenceApplication", "travel": "TravelApplication",
}


def badge_row(app, s):
    keys = BADGE_SETS.get(app.get("pricing", ""), BADGE_SETS["hybrid"])
    pills = "".join(f'<span class="pill">{esc(t(s, f"badges.{k}"))}</span>'
                    for k in keys)
    return f'<div class="badge-row">{pills}</div>'


def jsonld(obj):
    return ('<script type="application/ld+json">'
            + json.dumps(obj, ensure_ascii=False) + "</script>")


def app_structured_data(lang, s, app, canonical):
    """SoftwareApplication + BreadcrumbList（评分字段上架后有数据再回填）。"""
    a = s["apps"][app["slug"]]
    software = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": app["name"],
        "description": a["meta_desc"],
        "operatingSystem": "iOS",
        "applicationCategory": CATEGORY_SCHEMA.get(app["category_key"],
                                                   "MobileApplication"),
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "url": canonical,
    }
    if app["released"] and app["store_url"]:
        software["installUrl"] = app["store_url"]
    # aggregateRating 占位：apps.json 填 rating_value/rating_count 后自动出现
    if app.get("rating_value") and app.get("rating_count"):
        software["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": app["rating_value"],
            "ratingCount": app["rating_count"],
        }
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE["brand"],
             "item": SITE["base_url"] + lang_url(lang, "")},
            {"@type": "ListItem", "position": 2, "name": app["name"],
             "item": canonical},
        ],
    }
    return "\n" + jsonld(software) + "\n" + jsonld(crumbs)


def header_nav(lang, s, page, switcher_on=True):
    """switcher_on=False 用于单语页面（如 /press/）——全语言切换器会指向不存在的
    /<lang>/<page>/ 造成 404（2026-08-20 实锤）。"""
    home = lang_url(lang, "")
    sw = switcher(lang, page) if switcher_on else ""
    return f"""<header class="nav">
  <div class="wrap nav-inner">
    <a class="brand" href="{home}">{SPARK_MARK}{SITE['brand']}</a>
    <nav>
      <a href="{lang_url(lang, 'games/')}">{t(s, 'nav.games')}</a>
      <a href="{lang_url(lang, 'tools/')}">{t(s, 'nav.tools')}</a>
      <a href="{home}#about">{t(s, 'nav.about')}</a>
      <a href="/social/">Follow</a>
      <a href="/press/">Press</a>
      <a href="mailto:{SITE['contact_email']}">{t(s, 'nav.contact')}</a>
      {sw}
    </nav>
  </div>
</header>
"""


# Inline monochrome marks (no third-party icon CDN — privacy + offline).
SOCIAL_ICONS = {
    "x": '<svg class="social-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M18.244 2H21.5l-7.5 8.57L22.5 22h-6.59l-5.16-6.74L5.2 22H1.94l8.03-9.17L1.5 2h6.75l4.66 6.18L18.244 2zm-1.16 18h1.82L7.08 3.94H5.13L17.084 20z"/></svg>',
    "reddit": '<svg class="social-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2C6.48 2 2 6.18 2 11.5c0 3.54 2.2 6.56 5.4 8.05-.07-.62-.14-1.57.03-2.25.15-.62.98-4.16.98-4.16s-.25-.5-.25-1.24c0-1.16.67-2.03 1.51-2.03.71 0 1.06.54 1.06 1.18 0 .72-.46 1.8-.7 2.8-.2.84.42 1.52 1.25 1.52 1.5 0 2.65-1.58 2.65-3.86 0-2.02-1.45-3.43-3.52-3.43-2.4 0-3.81 1.8-3.81 3.66 0 .72.28 1.5.63 1.92a.24.24 0 0 1 .06.23c-.07.28-.22.9-.25 1.02-.04.17-.14.2-.32.12-1.2-.56-1.95-2.32-1.95-3.74 0-3.05 2.22-5.85 6.4-5.85 3.36 0 5.97 2.4 5.97 5.6 0 3.34-2.1 6.03-5.02 6.03-.98 0-1.9-.51-2.22-1.11l-.6 2.3c-.22.84-.81 1.9-1.21 2.54A10.4 10.4 0 0 0 12 21c5.52 0 10-4.18 10-9.5S17.52 2 12 2z"/></svg>',
    "producthunt": '<svg class="social-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 1 0 .001 20.001A10 10 0 0 0 12 2zm1.75 11.25H12.5v2.5h-1.75v-2.5H8.5V9.5h5.25a2.38 2.38 0 0 1 0 4.75zM12.5 11h1.25a.88.88 0 0 0 0-1.75H12.5V11z"/></svg>',
    "linkedin": '<svg class="social-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4.98 3.5C4.98 4.88 3.87 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1s2.48 1.12 2.48 2.5zM.5 8.5h4V23h-4V8.5zM8.5 8.5h3.8v2h.05c.53-1 1.83-2.05 3.77-2.05 4.03 0 4.78 2.65 4.78 6.1V23h-4v-6.6c0-1.57-.03-3.6-2.2-3.6-2.2 0-2.54 1.72-2.54 3.5V23h-4V8.5z"/></svg>',
    "discord": '<svg class="social-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M19.27 5.33C17.94 4.71 16.5 4.26 15 4a.09.09 0 0 0-.07.03c-.18.33-.39.76-.53 1.09a16.1 16.1 0 0 0-4.8 0c-.14-.34-.36-.76-.54-1.09A.09.09 0 0 0 9 4c-1.5.26-2.94.71-4.27 1.33A.08.08 0 0 0 4.67 5.4C2.53 8.87 1.9 12.24 2.21 15.57a.1.1 0 0 0 .04.07 15.9 15.9 0 0 0 4.79 2.43.1.1 0 0 0 .11-.03c.37-.5.7-1.03.98-1.58a.09.09 0 0 0-.05-.13 10.5 10.5 0 0 1-1.5-.73.09.09 0 0 1 0-.15c.1-.08.2-.16.3-.24a.09.09 0 0 1 .09-.01c3.16 1.44 6.58 1.44 9.7 0a.09.09 0 0 1 .1.01c.1.08.2.16.3.24a.09.09 0 0 1 0 .15c-.48.28-.98.52-1.5.73a.09.09 0 0 0-.05.13c.29.55.62 1.08.98 1.58a.1.1 0 0 0 .11.03 15.85 15.85 0 0 0 4.8-2.43.1.1 0 0 0 .04-.07c.37-3.86-.63-7.2-2.66-10.17a.07.07 0 0 0-.06-.04zM8.7 13.73c-.95 0-1.73-.88-1.73-1.95s.76-1.95 1.73-1.95 1.75.88 1.73 1.95c0 1.07-.76 1.95-1.73 1.95zm6.61 0c-.95 0-1.73-.88-1.73-1.95s.76-1.95 1.73-1.95 1.75.88 1.73 1.95c0 1.07-.77 1.95-1.73 1.95z"/></svg>',
    "instagram": '<svg class="social-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 2h10a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5zm0 2a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3H7zm11.25 1.5a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5zM12 7.5A4.5 4.5 0 1 1 12 16.5 4.5 4.5 0 0 1 12 7.5zm0 2a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z"/></svg>',
    "youtube": '<svg class="social-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 6.2 31.5 31.5 0 0 0 0 12a31.5 31.5 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1A31.5 31.5 0 0 0 24 12a31.5 31.5 0 0 0-.5-5.8zM9.75 15.5v-7l6.5 3.5-6.5 3.5z"/></svg>',
    "tiktok": '<svg class="social-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M19.6 7.2a5.6 5.6 0 0 1-3.3-1.1v7.3a5.6 5.6 0 1 1-5.6-5.6c.3 0 .6 0 .9.1v2.8a2.8 2.8 0 1 0 2 2.7V2.5h2.7c.2 1.6 1.2 3.1 2.6 4 .9.5 1.9.8 2.7.9v2.8z"/></svg>',
}


def social_icon(key):
    return SOCIAL_ICONS.get(key, "")


def footer(lang, s):
    rights = t(s, "common.footer_rights").replace("{year}", SITE["year"])
    legal = lang_url(lang, "legal/")
    social = SITE.get("social") or {}
    order = [("x", "X"), ("reddit", "Reddit"), ("producthunt", "Product Hunt"),
             ("linkedin", "LinkedIn"), ("discord", "Discord"),
             ("instagram", "Instagram"), ("youtube", "YouTube"), ("tiktok", "TikTok")]
    chips = []
    for k, label in order:
        if not social.get(k):
            continue
        chips.append(
            f'<a class="foot-social-chip" href="{esc(social[k])}" rel="me noopener" '
            f'target="_blank" aria-label="{esc(label)}">{social_icon(k)}'
            f'<span>{esc(label)}</span></a>')
    chips_html = "".join(chips)
    social_line = (
        f'\n    <div class="foot-social">'
        f'<a class="foot-social-hub" href="/social/">Follow us</a>'
        f'{chips_html}</div>'
    )
    return f"""<footer class="foot">
  <div class="wrap">
    <div class="foot-brand">{SPARK_MARK}{SITE['brand']}</div>
    <p>{rights} · <a href="mailto:{SITE['contact_email']}">{SITE['contact_email']}</a> · <a href="{legal}">{t(s, 'common.footer_privacy')}</a> · <a href="/press/">Press Kit</a></p>{social_line}
  </div>
</footer>
</body>
</html>
"""


def store_button(app, s):
    if app["released"] and app["store_url"]:
        return f'<a class="btn btn-store" href="{app["store_url"]}" rel="noopener">{t(s, "common.download")}</a>'
    # 上架前意向收集（零第三方 waitlist）：mailto 报名，标题带 App 名便于建名单
    notify = (f'mailto:{SITE["contact_email"]}'
              f'?subject=%5BNotify%5D%20{app["name"].replace(" ", "%20")}')
    return (f'<span class="btn btn-soon">{t(s, "common.coming_soon")}</span>\n'
            f'        <a class="btn btn-store" href="{notify}">{t(s, "common.notify_me")}</a>')


def phone(app, size=""):
    # 产品页首屏主图（B 斜放展示）：不 lazy + 提高抓取优先级（LCP）
    return f"""<div class="phone {size}">
  <img src="/assets/img/framed-{app['slug']}.webp" alt="{app['name']}" fetchpriority="high">
</div>"""


def game_card(lang, s, app):
    aurl = lang_url(lang, f"{app['slug']}/")
    return f"""      <a class="game-card" href="{aurl}" style="--aa:{app['gradient'][0]};--ab:{app['gradient'][1]};">
        <div class="game-copy">
          <h3>{app['name']}</h3>
          <p class="game-tagline">{t(s, f'apps.{app["slug"]}.tagline')}</p>
          <p class="game-desc">{t(s, f'apps.{app["slug"]}.card_desc')}</p>
          <span class="card-more">{t(s, 'common.learn_more')} →</span>
        </div>
        <div class="game-shot"><img src="/assets/img/framed-{app['slug']}.webp" alt="{app['name']}" loading="lazy"></div>
      </a>"""


def tease_card(s):
    return f"""      <div class="tease-card">
        <h3>{t(s, 'teaser.title')}</h3>
        <p>{t(s, 'teaser.desc')}</p>
      </div>"""


def walkthrough(lang, s, app):
    """产品页功能走查：一行四图，图下短标题 + 一句话（截图缺失时回退纯文字卡）。"""
    slug = app["slug"]
    a = s["apps"][slug]
    blocks, plain = [], []
    for i, f in enumerate(a["features"], 1):
        shot = SRC / "shots" / f"walk-{slug}-{i}.png"
        if shot.exists():
            blocks.append(f"""      <div class="walk-item">
        <div class="walk-media"><img src="/assets/img/walk-{slug}-{i}.webp" alt="{esc(f['t'])}" loading="lazy"></div>
        <h3>{esc(f['t'])}</h3>
        <p>{esc(f['d'])}</p>
      </div>""")
        else:
            plain.append(f"""      <div class="feat"><h3>{esc(f['t'])}</h3><p>{esc(f['d'])}</p></div>""")
    html = ""
    if blocks:
        html += '<div class="walk">\n' + "\n".join(blocks) + "\n    </div>"
    if plain:
        html += '\n    <div class="feat-grid">\n' + "\n".join(plain) + "\n    </div>"
    return html


def render_home(lang, s):
    """短首页（v4 火花电影）：key art 满屏 hero + 游戏/工具两条电影横幅 + 价值观 + 关于。"""
    page = ""
    canonical = SITE["base_url"] + lang_url(lang, page)
    games = [a for a in APPS if a["kind"] == "game"]
    tools = [a for a in APPS if a["kind"] == "tool"]

    # 反序让 Mergehold（三国原画）打头，与横幅标题「从三国到万国」对齐
    game_shots = "".join(
        f'<img src="/assets/img/framed-{a["slug"]}.webp" alt="{a["name"]}" loading="lazy">'
        for a in reversed(games))
    tool_shots = "".join(
        f'<img src="/assets/img/framed-{a["slug"]}.webp" alt="{a["name"]}" loading="lazy">'
        for a in tools[:3])

    values = f"""    <section class="values">
      <div class="value"><div class="value-ic">{VALUE_ICONS['private']}</div><h3>{t(s, 'values.private_title')}</h3><p>{t(s, 'values.private_desc')}</p></div>
      <div class="value"><div class="value-ic">{VALUE_ICONS['honest']}</div><h3>{t(s, 'values.honest_title')}</h3><p>{t(s, 'values.honest_desc')}</p></div>
      <div class="value"><div class="value-ic">{VALUE_ICONS['global']}</div><h3>{t(s, 'values.global_title')}</h3><p>{t(s, 'values.global_desc')}</p></div>
    </section>"""

    # Wrap the last word of the hero title in a gradient span.
    title_words = t(s, "hero.title").rsplit(" ", 1)
    if len(title_words) == 2:
        hero_title = f'{esc(title_words[0])} <span class="grad">{esc(title_words[1])}</span>'
    else:
        hero_title = f'<span class="grad">{esc(t(s, "hero.title"))}</span>'

    org = jsonld({
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": SITE["brand"],
        "url": SITE["base_url"],
        "email": SITE["contact_email"],
        "description": t(s, "meta.home_desc"),
    })
    preload = ('\n<link rel="preload" as="image" href="/assets/img/keyart-dark.webp"'
               ' media="(min-width:701px)" fetchpriority="high">'
               '\n<link rel="preload" as="image" href="/assets/img/keyart-dark-m.webp"'
               ' media="(max-width:700px)" fetchpriority="high">')
    html = head(lang, s, t(s, "meta.home_title"), t(s, "meta.home_desc"),
                page, canonical, "\n" + org + preload)
    html += header_nav(lang, s, page)
    html += f"""<section class="hero">
  <div class="hero-bg" aria-hidden="true"></div>
  <canvas id="sparks" aria-hidden="true"></canvas>
  <div class="wrap hero-inner">
    <span class="hero-kicker">{t(s, 'hero.kicker')}</span>
    <h1>{hero_title}</h1>
    <p>{t(s, 'hero.subtitle')}</p>
    <div class="cta-row">
      <a class="btn btn-primary" href="{lang_url(lang, 'games/')}">{t(s, 'hero.explore')}</a>
      <a class="btn" href="{lang_url(lang, 'tools/')}">{t(s, 'hero.explore_tools')}</a>
    </div>
  </div>
</section>
<main class="wrap">
  <a class="band band-games" href="{lang_url(lang, 'games/')}">
    <div class="band-inner">
      <div class="band-copy">
        <span class="band-label">{t(s, 'nav.games')}</span>
        <h2>{t(s, 'home.games_card_title')}</h2>
        <p>{t(s, 'home.games_card_desc')}</p>
        <span class="band-more">{t(s, 'home.games_cta')} →</span>
      </div>
      <div class="band-shots">{game_shots}</div>
    </div>
  </a>
  <a class="band band-tools" href="{lang_url(lang, 'tools/')}">
    <div class="band-inner">
      <div class="band-copy">
        <span class="band-label">{t(s, 'nav.tools')}</span>
        <h2>{t(s, 'home.tools_card_title')}</h2>
        <p>{t(s, 'home.tools_card_desc')}</p>
        <span class="band-more">{t(s, 'home.tools_cta')} →</span>
      </div>
      <div class="band-shots">{tool_shots}</div>
    </div>
  </a>
{values}
  <section id="about" class="studio">
    <h2>{t(s, 'about.title')}</h2>
    <div class="stats">
      <div class="stat"><span class="stat-n">9</span><span class="stat-l">{t(s, 'about.stat_apps')}</span></div>
      <div class="stat"><span class="stat-n">34</span><span class="stat-l">{t(s, 'about.stat_langs')}</span></div>
      <div class="stat"><span class="stat-n">0</span><span class="stat-l">{t(s, 'about.stat_clean')}</span></div>
      <div class="stat"><span class="stat-n">1</span><span class="stat-l">{t(s, 'about.stat_person')}</span></div>
    </div>
    <div class="studio-cols">
      <div class="studio-story">
        <p>{t(s, 'about.body')}</p>
        <p>{t(s, 'about.story2')}</p>
      </div>
      <div class="studio-promises">
        <h3>{t(s, 'about.promises_title')}</h3>
        <ul>
          <li>{t(s, 'badges.noads')}</li>
          <li>{t(s, 'badges.notracking')}</li>
          <li>{t(s, 'badges.honest')}</li>
          <li>{t(s, 'badges.ondevice')}</li>
        </ul>
      </div>
    </div>
  </section>
</main>
"""
    html += footer(lang, s)
    out = ROOT / lang["path"] / "index.html" if lang["path"] else ROOT / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def render_games(lang, s):
    """独立游戏页（暗色 zone）：游戏大卡 + 009 预告。"""
    page = "games/"
    canonical = SITE["base_url"] + lang_url(lang, page)
    games = [a for a in APPS if a["kind"] == "game"]
    cards = "\n".join(game_card(lang, s, a) for a in games)
    cards += "\n" + tease_card(s)
    html = head(lang, s, t(s, "meta.games_title"), t(s, "meta.games_desc"),
                page, canonical)
    html += header_nav(lang, s, page)
    html += f"""<main>
  <section class="page-head" id="games">
    <div class="wrap">
      <div class="sec-head">
        <h2>{t(s, 'sections.games_title')}</h2>
        <p>{t(s, 'sections.games_sub')}</p>
      </div>
      <div class="game-grid">
{cards}
      </div>
    </div>
  </section>
</main>
"""
    html += footer(lang, s)
    out = (ROOT / lang["path"] if lang["path"] else ROOT) / "games" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def render_tools(lang, s):
    """独立工具页（亮色 zone）：工具卡阵。"""
    page = "tools/"
    canonical = SITE["base_url"] + lang_url(lang, page)
    tools = [a for a in APPS if a["kind"] == "tool"]
    cards = "\n".join(game_card(lang, s, a) for a in tools)
    html = head(lang, s, t(s, "meta.tools_title"), t(s, "meta.tools_desc"),
                page, canonical)
    html += header_nav(lang, s, page)
    html += f"""<main>
  <section class="page-head" id="tools">
    <div class="wrap">
      <div class="sec-head">
        <h2>{t(s, 'sections.tools_title')}</h2>
        <p>{t(s, 'sections.tools_sub')}</p>
      </div>
      <div class="game-grid">
{cards}
      </div>
    </div>
  </section>
</main>
"""
    html += footer(lang, s)
    out = (ROOT / lang["path"] if lang["path"] else ROOT) / "tools" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def render_app(lang, s, app):
    slug = app["slug"]
    page = f"{slug}/"
    canonical = SITE["base_url"] + lang_url(lang, page)
    a = s["apps"][slug]
    disclaimer = f'<p class="disclaimer">{esc(a["disclaimer"])}</p>' if a["disclaimer"] else ""
    features_heading = t(s, "common.features").replace("{app}", app["name"])

    extra = app_structured_data(lang, s, app, canonical)
    if app.get("store_id"):
        extra += (f'\n<meta name="apple-itunes-app" '
                  f'content="app-id={app["store_id"]}">')
    html = head(lang, s, f"{app['name']} — {a['tagline']}", a["meta_desc"],
                page, canonical, extra, og_image=f"og-{slug}.jpg")
    html += header_nav(lang, s, page)
    html += f"""<section class="app-hero" style="--aa:{app['gradient'][0]};--ab:{app['gradient'][1]};">
  <div class="wrap app-hero-inner">
    <div class="app-hero-copy">
      <img class="app-icon-lg" src="/assets/img/icon-{slug}.webp" alt="" width="92" height="92">
      <h1>{app['name']}</h1>
      <p class="lede">{esc(a['subtitle'])}</p>
      {badge_row(app, s)}
      <div class="cta-row">
        {store_button(app, s)}
        <a class="btn" href="/{slug}/privacy.html">{t(s, 'common.privacy_policy')}</a>
        <a class="btn" href="/{slug}/support.html">{t(s, 'common.support')}</a>
      </div>
    </div>
    {phone(app)}
  </div>
</section>
<main class="wrap">
  <section class="features-sec">
    <h2>{esc(features_heading)}</h2>
    {walkthrough(lang, s, app)}
  </section>
  <section class="privacy-strip" style="--aa:{app['gradient'][0]};">
    <h2>{t(s, 'common.privacy_heading')}</h2>
    <p>{esc(a['privacy_blurb'])} <a href="/{slug}/privacy.html">{t(s, 'common.privacy_policy')}</a></p>
    {disclaimer}
    <p style="margin-top:14px;"><a href="/{slug}/support.html">{t(s, 'common.support')}</a> · <a href="mailto:{SITE['contact_email']}">{SITE['contact_email']}</a></p>
  </section>
</main>
"""
    html += footer(lang, s)
    if lang["path"]:
        out = ROOT / lang["path"] / slug / "index.html"
    else:
        out = ROOT / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def render_legal(lang, s):
    """Per-language hub listing every app's privacy policy and support page.
    Keeps the footer at a single link no matter how many apps ship."""
    page = "legal/"
    canonical = SITE["base_url"] + lang_url(lang, page)
    title = f"{t(s, 'common.footer_privacy')} — {SITE['brand']}"
    rows = []
    for app in APPS:
        rows.append(f"""    <div class="legal-row" style="--aa:{app['gradient'][0]};">
      <img class="app-icon" src="/assets/img/icon-{app['slug']}.webp" alt="" width="44" height="44">
      <h3>{app['name']}</h3>
      <div class="legal-links">
        <a href="/{app['slug']}/privacy.html">{t(s, 'common.privacy_policy')}</a>
        <a href="/{app['slug']}/support.html">{t(s, 'common.support')}</a>
      </div>
    </div>""")

    html = head(lang, s, title, t(s, "meta.home_desc"), page, canonical)
    html += header_nav(lang, s, page)
    html += f"""<main class="wrap legal-hub">
  <div class="sec-head">
    <h2>{t(s, 'common.footer_privacy')}</h2>
  </div>
  <div class="legal-list">
{chr(10).join(rows)}
  </div>
</main>
"""
    html += footer(lang, s)
    out = (ROOT / lang["path"] if lang["path"] else ROOT) / "legal" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def render_press():
    """Press Kit 单页（行业惯例英文单语；资产 ZIP 在 /press/sparkfall-presskit.zip）。"""
    en = next(l for l in LANGS if l["code"] == "en")
    s = json.loads((SRC / "i18n" / "en.json").read_text())
    canonical = f"{SITE['base_url']}/press/"
    games = [a for a in APPS if a["kind"] == "game"]
    tools = [a for a in APPS if a["kind"] == "tool"]

    def title_rows(apps_list, label):
        rows = "".join(
            f'<li><strong>{a["name"]}</strong> — {esc(s["apps"][a["slug"]]["tagline"])} '
            f'<a href="/{a["slug"]}/">page</a></li>'
            for a in apps_list)
        return f"<h3>{label}</h3><ul>{rows}</ul>"

    shots_grid = "".join(
        f'<img src="/assets/img/framed-{a["slug"]}.webp" alt="{a["name"]}" loading="lazy">'
        for a in (games + tools)[:8])

    html = head(en, s, f"Press Kit — {SITE['brand']}",
                "Press kit for Sparkfall Games: factsheet, logos, key art, icons and "
                "high-resolution screenshots. One-person indie studio making private, "
                "honest iOS games and tools.",
                "press/", canonical, hreflangs=False)
    html += header_nav(en, s, "press/", switcher_on=False)
    html += f"""<main class="wrap" style="padding-top:64px;">
  <div class="sec-head">
    <h2>Press Kit</h2>
    <p>Everything you need to cover Sparkfall Games — free to use in articles and videos.</p>
  </div>
  <div class="cta-row" style="margin-bottom:40px;">
    <a class="btn btn-primary" href="/press/sparkfall-presskit.zip" download>Download all assets (ZIP, 5.5 MB)</a>
    <a class="btn" href="/social/">Follow us</a>
    <a class="btn" href="mailto:{SITE['contact_email']}?subject=%5BPress%5D">Press contact</a>
  </div>
  <div class="studio-cols" style="margin-bottom:44px;">
    <div class="studio-story">
      <h3 style="margin-top:0;">About</h3>
      <p>{esc(s['about']['body'])}</p>
      <p>{esc(s['about']['story2'])}</p>
      {title_rows(games, 'Games')}
      {title_rows(tools, 'Tools')}
    </div>
    <div class="studio-promises">
      <h3>Factsheet</h3>
      <ul style="font-weight:400;">
        <li><strong>Studio:</strong> {SITE['brand']}</li>
        <li><strong>Type:</strong> Independent one-person studio</li>
        <li><strong>Founded:</strong> 2026</li>
        <li><strong>Platform:</strong> iOS, 100% native</li>
        <li><strong>Languages:</strong> 34 per title</li>
        <li><strong>Pricing:</strong> honest one-time purchases</li>
        <li><strong>Privacy:</strong> no ads, no tracking, no accounts</li>
        <li><strong>Web:</strong> sparkfallgames.com</li>
        <li><strong>Contact:</strong> {SITE['contact_email']}</li>
        <li><strong>X:</strong> <a href="{esc((SITE.get('social') or {}).get('x',''))}">@SparkfallGames</a></li>
        <li><strong>Reddit:</strong> <a href="{esc((SITE.get('social') or {}).get('reddit',''))}">u/SparkfallGames</a></li>
        <li><strong>Product Hunt:</strong> <a href="{esc((SITE.get('social') or {}).get('producthunt',''))}">@sparkfallgames</a></li>
        <li><strong>LinkedIn:</strong> <a href="{esc((SITE.get('social') or {}).get('linkedin',''))}">Sparkfall Games</a></li>
        <li><strong>Discord:</strong> <a href="{esc((SITE.get('social') or {}).get('discord',''))}">discord.gg/srg5buCFW</a></li>
      </ul>
    </div>
  </div>
  <div class="sec-head"><h2 style="font-size:1.5rem;">Logos &amp; key art</h2></div>
  <div class="feat-grid" style="margin-bottom:44px;">
    <div class="feat" style="text-align:center;"><img src="/assets/press/spark-512.png" alt="Spark logo" style="width:96px;"><p><a href="/assets/press/spark-512.png" download>spark-512.png</a> · <a href="/favicon.svg" download>spark.svg</a></p></div>
    <div class="feat" style="text-align:center;"><img src="/assets/press/wordmark-on-light.png" alt="Wordmark" style="max-width:100%;background:#f5f1ea;border-radius:10px;padding:10px 14px;box-sizing:border-box;"><p><a href="/assets/press/wordmark-on-light.png" download>wordmark-on-light.png</a></p></div>
    <div class="feat" style="text-align:center;"><img src="/assets/press/wordmark-on-dark.png" alt="Wordmark dark" style="max-width:100%;"><p><a href="/assets/press/wordmark-on-dark.png" download>wordmark-on-dark.png</a></p></div>
    <div class="feat" style="text-align:center;"><img src="/assets/press/keyart-1200x630.jpg" alt="Key art" style="max-width:100%;border-radius:10px;"><p><a href="/assets/press/keyart-1200x630.jpg" download>keyart-1200x630.jpg</a></p></div>
  </div>
  <div class="sec-head"><h2 style="font-size:1.5rem;">Screenshots</h2><p>High-resolution originals for all eight titles are included in the ZIP.</p></div>
  <div class="entry-shots" style="justify-content:flex-start;flex-wrap:wrap;gap:14px;margin-bottom:56px;">{shots_grid}</div>
</main>
"""
    html += footer(en, s)
    out = ROOT / "press" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def render_social():
    """Follow hub — English-only like Press. Big one-tap cards, live platforms only."""
    en = next(l for l in LANGS if l["code"] == "en")
    s = json.loads((SRC / "i18n" / "en.json").read_text())
    canonical = f"{SITE['base_url']}/social/"
    social = SITE.get("social") or {}
    # label, blurb, cta — only emitted when URL present (Tier1 live).
    catalog = [
        ("x", "X", "Dev logs, release notes, and short clips.", "Follow on X"),
        ("reddit", "Reddit", "Niche threads and honest product talk.", "Follow on Reddit"),
        ("producthunt", "Product Hunt", "Launch days and maker updates.", "Follow on Product Hunt"),
        ("linkedin", "LinkedIn", "Studio notes for press and partners.", "Follow on LinkedIn"),
        ("discord", "Discord", "Announcements and community chat.", "Join Discord"),
        ("instagram", "Instagram", "Visual highlights and Reels.", "Follow on Instagram"),
        ("youtube", "YouTube", "Longer demos and Shorts.", "Subscribe on YouTube"),
        ("tiktok", "TikTok", "Short gameplay and tool demos.", "Follow on TikTok"),
    ]
    cards = []
    for key, name, blurb, cta in catalog:
        url = social.get(key)
        if not url:
            continue
        cards.append(f"""    <a class="social-card" href="{esc(url)}" rel="me noopener" target="_blank">
      <span class="social-card-icon" aria-hidden="true">{social_icon(key)}</span>
      <div class="social-card-copy">
        <h3>{esc(name)}</h3>
        <p>{esc(blurb)}</p>
      </div>
      <span class="social-card-cta">{esc(cta)} →</span>
    </a>""")
    grid = "\n".join(cards) if cards else (
        '    <p class="lede">Social links coming soon.</p>')

    html = head(en, s, f"Follow — {SITE['brand']}",
                "Follow Sparkfall Games on X, Reddit, Product Hunt, LinkedIn, and more. "
                "No ads, no tracking — just indie games and honest iOS tools.",
                "social/", canonical, hreflangs=False)
    html += header_nav(en, s, "social/", switcher_on=False)
    html += f"""<main class="wrap social-page">
  <div class="social-hero">
    <p class="social-kicker">Sparkfall Games</p>
    <h1>Follow the studio</h1>
    <p class="lede">One tap to each official channel. Same brand everywhere — no ads, no tracking.</p>
  </div>
  <div class="social-grid">
{grid}
  </div>
  <p class="social-note">Press kit and logos → <a href="/press/">sparkfallgames.com/press</a></p>
</main>
"""
    html += footer(en, s)
    out = ROOT / "social" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def render_404():
    """品牌化 404（GitHub Pages 全站共用根目录单文件，英文）。"""
    en = next(l for l in LANGS if l["code"] == "en")
    s_en = json.loads((SRC / "i18n" / "en.json").read_text())
    html = head(en, s_en, f"Page not found — {SITE['brand']}",
                s_en["meta"]["home_desc"], "", f"{SITE['base_url']}/404.html")
    html += header_nav(en, s_en, "")
    html += f"""<main class="wrap" style="min-height:56vh;display:grid;place-items:center;text-align:center;">
  <div>
    <p style="font-size:5rem;margin:0;line-height:1;">404</p>
    <h1 style="font-size:1.6rem;margin:14px 0 10px;">Page not found</h1>
    <p style="color:var(--text-2);margin:0 0 28px;">The page you're looking for doesn't exist or has moved.</p>
    <div class="cta-row" style="justify-content:center;">
      <a class="btn btn-primary" href="/">{SITE['brand']}</a>
      <a class="btn" href="/games/">{s_en['nav']['games']}</a>
      <a class="btn" href="/tools/">{s_en['nav']['tools']}</a>
    </div>
  </div>
</main>
"""
    html += footer(en, s_en)
    (ROOT / "404.html").write_text(html)


def render_sitemap():
    urls = []
    for lang in LANGS:
        urls.append(SITE["base_url"] + lang_url(lang, ""))
        urls.append(SITE["base_url"] + lang_url(lang, "games/"))
        urls.append(SITE["base_url"] + lang_url(lang, "tools/"))
        urls.append(SITE["base_url"] + lang_url(lang, "legal/"))
        for app in APPS:
            urls.append(SITE["base_url"] + lang_url(lang, f"{app['slug']}/"))
    for app in APPS:
        urls.append(f"{SITE['base_url']}/{app['slug']}/privacy.html")
        urls.append(f"{SITE['base_url']}/{app['slug']}/support.html")
    urls.append(f"{SITE['base_url']}/press/")
    urls.append(f"{SITE['base_url']}/social/")
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n")
    # AI 爬虫放行（GEO：想被 AI 搜索引用就得让爬）+ llms.txt 指引
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE['base_url']}/sitemap.xml\n"
        f"# AI crawlers welcome — see {SITE['base_url']}/llms.txt\n")


def render_llms():
    """站根 llms.txt：手选核心页索引（app-site GEO 模板，英文单份）。"""
    en = json.loads((SRC / "i18n" / "en.json").read_text())
    lines = [f"# {SITE['brand']}",
             "> Independent iOS apps & games. No ads, no tracking, "
             "honest one-time pricing, all data stays on-device.",
             "", "## Apps"]
    for app in APPS:
        tag = en["apps"][app["slug"]]["tagline"]
        lines.append(f"- [{app['name']}]({SITE['base_url']}/{app['slug']}/): {tag}")
    lines += ["", "## Support"]
    for app in APPS:
        lines.append(f"- [{app['name']} support & FAQ]"
                     f"({SITE['base_url']}/{app['slug']}/support.html)")
    lines += ["", "## Studio",
              f"- [Follow us]({SITE['base_url']}/social/)",
              f"- [Press kit]({SITE['base_url']}/press/)"]
    (ROOT / "llms.txt").write_text("\n".join(lines) + "\n")


def main():
    i18n = load_i18n()
    process_images()
    count = 0
    for lang in LANGS:
        s = i18n[lang["code"]]
        render_home(lang, s)
        render_games(lang, s)
        render_tools(lang, s)
        render_legal(lang, s)
        count += 4
        for app in APPS:
            render_app(lang, s, app)
            count += 1
    render_press()
    render_social()
    render_404()
    render_sitemap()
    render_llms()
    print(f"Generated {count} pages for {len(LANGS)} languages.")


if __name__ == "__main__":
    main()
