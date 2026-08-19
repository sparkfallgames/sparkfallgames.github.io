#!/usr/bin/env python3
"""Static site generator for the apps site (sparkfallgames.com, hosted on GitHub Pages).

Design system v2 "Ember": unified warm-ink shell (nav/footer), dual content zones —
zone-dark for games (ink + ember glow), zone-light for tools (warm paper, Apple-calm).

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


def process_images():
    """Resize raw simulator screenshots for web, copy app icons."""
    from PIL import Image

    img_dir = ROOT / "assets" / "img"
    img_dir.mkdir(parents=True, exist_ok=True)

    def webp(src, out, width):
        im = Image.open(src).convert("RGB")
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
        # WebP 有损 + 超预算自动降质：性能预算单图 ≤80KB（原画类 PNG 会到 1MB+）
        for q in (82, 72, 62, 52):
            im.save(out, quality=q, method=6)
            if out.stat().st_size <= 82_000:
                break

    for app in APPS:
        raw = SRC / "shots" / f"raw-{app['slug']}.png"
        if raw.exists():
            webp(raw, img_dir / f"shot-{app['slug']}.webp", 640)
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


def head(lang, s, title, desc, page, canonical, extra=""):
    direction = ' dir="rtl"' if lang.get("dir") == "rtl" else ""
    return f"""<!DOCTYPE html>
<html lang="{lang['hreflang']}"{direction}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#faf8f5">
<link rel="canonical" href="{canonical}">
{hreflang_links(page)}{extra}
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


def header_nav(lang, s, page):
    home = lang_url(lang, "")
    return f"""<header class="nav">
  <div class="wrap nav-inner">
    <a class="brand" href="{home}">{SPARK_MARK}{SITE['brand']}</a>
    <nav>
      <a href="{lang_url(lang, 'games/')}">{t(s, 'nav.games')}</a>
      <a href="{lang_url(lang, 'tools/')}">{t(s, 'nav.tools')}</a>
      <a href="{home}#about">{t(s, 'nav.about')}</a>
      <a href="mailto:{SITE['contact_email']}">{t(s, 'nav.contact')}</a>
      {switcher(lang, page)}
    </nav>
  </div>
</header>
"""


def footer(lang, s):
    rights = t(s, "common.footer_rights").replace("{year}", SITE["year"])
    legal = lang_url(lang, "legal/")
    return f"""<footer class="foot">
  <div class="wrap">
    <div class="foot-brand">{SPARK_MARK}{SITE['brand']}</div>
    <p>{rights} · <a href="mailto:{SITE['contact_email']}">{SITE['contact_email']}</a> · <a href="{legal}">{t(s, 'common.footer_privacy')}</a></p>
  </div>
</footer>
</body>
</html>
"""


def store_button(app, s):
    if app["released"] and app["store_url"]:
        return f'<a class="btn btn-store" href="{app["store_url"]}" rel="noopener">{t(s, "common.download")}</a>'
    return f'<span class="btn btn-soon">{t(s, "common.coming_soon")}</span>'


def phone(app, size=""):
    return f"""<div class="phone {size}" style="--pa:{app['gradient'][0]};--pb:{app['gradient'][1]};">
  <div class="phone-frame">
    <img src="/assets/img/shot-{app['slug']}.webp" alt="{app['name']}" loading="lazy">
  </div>
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
        <div class="game-shot"><img src="/assets/img/shot-{app['slug']}.webp" alt="{app['name']}" loading="lazy"></div>
      </a>"""


def tease_card(s):
    return f"""      <div class="tease-card">
        <h3>{t(s, 'teaser.title')}</h3>
        <p>{t(s, 'teaser.desc')}</p>
      </div>"""


def walkthrough(lang, s, app):
    """产品页功能走查：每条特性配一张截图，左右交替（截图缺失时回退纯文字卡）。"""
    slug = app["slug"]
    a = s["apps"][slug]
    blocks, plain = [], []
    for i, f in enumerate(a["features"], 1):
        shot = SRC / "shots" / f"walk-{slug}-{i}.png"
        if shot.exists():
            blocks.append(f"""      <div class="walk-item">
        <div class="walk-media"><img src="/assets/img/walk-{slug}-{i}.webp" alt="{esc(f['t'])}" loading="lazy" width="260"></div>
        <div class="walk-copy"><h3>{esc(f['t'])}</h3><p>{esc(f['d'])}</p></div>
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
    """短首页：品牌开场 + 游戏/工具两张大入口卡 + 价值观 + 关于。"""
    page = ""
    canonical = SITE["base_url"] + lang_url(lang, page)
    games = [a for a in APPS if a["kind"] == "game"]
    tools = [a for a in APPS if a["kind"] == "tool"]

    game_shots = "".join(
        f'<img src="/assets/img/shot-{a["slug"]}.webp" alt="{a["name"]}" loading="lazy">'
        for a in games)
    tool_shots = "".join(
        f'<img src="/assets/img/shot-{a["slug"]}.webp" alt="{a["name"]}" loading="lazy">'
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
    html = head(lang, s, t(s, "meta.home_title"), t(s, "meta.home_desc"),
                page, canonical, "\n" + org)
    html += header_nav(lang, s, page)
    html += f"""<section class="hero">
  <div class="hero-bg" aria-hidden="true"></div>
  <canvas id="sparks" aria-hidden="true"></canvas>
  <div class="wrap hero-inner">
    <span class="hero-kicker">{t(s, 'hero.kicker')}</span>
    <h1>{hero_title}</h1>
    <p>{t(s, 'hero.subtitle')}</p>
  </div>
</section>
<main class="wrap">
  <div class="entry-grid">
    <a class="entry-card" href="{lang_url(lang, 'games/')}">
      <div class="entry-media"><div class="entry-shots">{game_shots}</div></div>
      <h2>{t(s, 'nav.games')}</h2>
      <p>{t(s, 'home.games_card_desc')}</p>
      <span class="entry-cta">{t(s, 'home.games_cta')} →</span>
    </a>
    <a class="entry-card" href="{lang_url(lang, 'tools/')}">
      <div class="entry-media"><div class="entry-shots">{tool_shots}</div></div>
      <h2>{t(s, 'nav.tools')}</h2>
      <p>{t(s, 'home.tools_card_desc')}</p>
      <span class="entry-cta">{t(s, 'home.tools_cta')} →</span>
    </a>
  </div>
{values}
  <section id="about">
    <div class="about">
      <h2>{t(s, 'about.title')}</h2>
      <p>{t(s, 'about.body')}</p>
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
                page, canonical, extra)
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
    render_sitemap()
    render_llms()
    print(f"Generated {count} pages for {len(LANGS)} languages.")


if __name__ == "__main__":
    main()
