#!/usr/bin/env python3
"""Static site generator for the apps site (2645809444.github.io).

Reads apps.json + i18n/<lang>.json, emits:
  /index.html, /<app>/index.html            (English, site root)
  /<lang>/index.html, /<lang>/<app>/...     (30 more languages)
  /assets/img/*                             (compressed screenshots + icons)

Legal pages (/<app>/privacy.html, /<app>/support.html) are hand-written and
NEVER touched by this script — their URLs are referenced from shipped apps.
"""

import json
import shutil
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

    for app in APPS:
        raw = SRC / "shots" / f"raw-{app['slug']}.png"
        if raw.exists():
            im = Image.open(raw)
            w = 640
            h = round(im.height * w / im.width)
            im.resize((w, h), Image.LANCZOS).save(
                img_dir / f"shot-{app['slug']}.png", optimize=True)

    icon_map = {
        "quickcost": ROOT.parent / "001/QuickCost/Assets.xcassets/AppIcon.appiconset/AppIcon.png",
        "decibelmeter": ROOT.parent / "002/DecibelMeter/Assets.xcassets/AppIcon.appiconset/AppIcon.png",
        "fastzen": ROOT.parent / "003/FastZen/Assets.xcassets/AppIcon.appiconset/AppIcon1024.png",
        "mathspark": ROOT.parent / "004/MathSpark/Assets.xcassets/AppIcon.appiconset/AppIcon.png",
    }
    for slug, src in icon_map.items():
        if src.exists():
            im = Image.open(src).resize((192, 192), Image.LANCZOS)
            im.save(img_dir / f"icon-{slug}.png", optimize=True)


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


def head(lang, s, title, desc, page, canonical):
    direction = ' dir="rtl"' if lang.get("dir") == "rtl" else ""
    asset = "../" if page.count("/") and lang["path"] == "" else ""
    # Use absolute asset paths — simplest and works at any depth.
    return f"""<!DOCTYPE html>
<html lang="{lang['hreflang']}"{direction}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
{hreflang_links(page)}
<link rel="stylesheet" href="/assets/site.css">
<script defer src="/assets/site.js"></script>
</head>
"""


def header_nav(lang, s, page):
    home = lang_url(lang, "")
    return f"""<header class="nav">
  <div class="wrap nav-inner">
    <a class="brand" href="{home}">{SITE['brand']}</a>
    <nav>
      <a href="{home}#games">{t(s, 'nav.games')}</a>
      <a href="{home}#tools">{t(s, 'nav.tools')}</a>
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
    <img src="/assets/img/shot-{app['slug']}.png" alt="{app['name']}" loading="lazy">
  </div>
</div>"""


def game_card(lang, s, app):
    aurl = lang_url(lang, f"{app['slug']}/")
    return f"""    <a class="game-card reveal" href="{aurl}" style="--aa:{app['gradient'][0]};--ab:{app['gradient'][1]};">
      <div class="game-copy">
        <span class="badge">{t(s, f'categories.{app["category_key"]}')}</span>
        <h3>{app['name']}</h3>
        <p class="game-tagline">{t(s, f'apps.{app["slug"]}.tagline')}</p>
        <p class="game-desc">{t(s, f'apps.{app["slug"]}.card_desc')}</p>
        <span class="card-more">{t(s, 'common.learn_more')} →</span>
      </div>
      <div class="game-shot"><img src="/assets/img/shot-{app['slug']}.png" alt="{app['name']}" loading="lazy"></div>
    </a>"""


def tease_card(s):
    return f"""    <div class="tease-card reveal">
      <span class="badge" style="--aa:#8b5cf6;">{t(s, 'teaser.badge')}</span>
      <h3>{t(s, 'teaser.title')}</h3>
      <p>{t(s, 'teaser.desc')}</p>
      <span class="tease-glyph" aria-hidden="true">?</span>
    </div>"""


def tool_card(lang, s, app):
    aurl = lang_url(lang, f"{app['slug']}/")
    return f"""    <a class="tool-card reveal" href="{aurl}" style="--aa:{app['gradient'][0]};--ab:{app['gradient'][1]};">
      <div class="tool-top">
        <img class="app-icon" src="/assets/img/icon-{app['slug']}.png" alt="" width="52" height="52">
        <span class="badge">{t(s, f'categories.{app["category_key"]}')}</span>
      </div>
      <h3>{app['name']}</h3>
      <p class="tool-tagline">{t(s, f'apps.{app["slug"]}.tagline')}</p>
      <span class="card-more">{t(s, 'common.learn_more')} →</span>
    </a>"""


def render_home(lang, s):
    page = ""
    canonical = SITE["base_url"] + lang_url(lang, page)
    games = [a for a in APPS if a["kind"] == "game"]
    tools = [a for a in APPS if a["kind"] == "tool"]

    game_cards = "\n".join(game_card(lang, s, a) for a in games)
    game_cards += "\n" + tease_card(s)
    tool_cards = "\n".join(tool_card(lang, s, a) for a in tools)

    values = f"""  <section class="values wrap">
    <div class="value reveal"><div class="value-ic">🔒</div><h3>{t(s, 'values.private_title')}</h3><p>{t(s, 'values.private_desc')}</p></div>
    <div class="value reveal"><div class="value-ic">🤝</div><h3>{t(s, 'values.honest_title')}</h3><p>{t(s, 'values.honest_desc')}</p></div>
    <div class="value reveal"><div class="value-ic">🌍</div><h3>{t(s, 'values.global_title')}</h3><p>{t(s, 'values.global_desc')}</p></div>
  </section>"""

    # Wrap the last word of the hero title in a gradient span.
    title_words = t(s, "hero.title").rsplit(" ", 1)
    if len(title_words) == 2:
        hero_title = f'{esc(title_words[0])} <span class="grad">{esc(title_words[1])}</span>'
    else:
        hero_title = f'<span class="grad">{esc(t(s, "hero.title"))}</span>'

    html = head(lang, s, t(s, "meta.home_title"), t(s, "meta.home_desc"), page, canonical)
    html += "<body>\n" + header_nav(lang, s, page)
    html += f"""<section class="hero">
  <div class="hero-bg" aria-hidden="true"></div>
  <div class="hero-grid" aria-hidden="true"></div>
  <canvas id="sparks" aria-hidden="true"></canvas>
  <div class="wrap hero-inner">
    <span class="hero-kicker">{t(s, 'hero.kicker')}</span>
    <h1>{hero_title}</h1>
    <p>{t(s, 'hero.subtitle')}</p>
    <div class="cta-row">
      <a class="btn btn-primary" href="#games">{t(s, 'hero.explore')}</a>
      <a class="btn" href="#tools">{t(s, 'hero.explore_tools')}</a>
    </div>
  </div>
</section>
<main class="wrap">
  <section class="sec" id="games">
    <div class="sec-head reveal">
      <h2><span class="grad">{t(s, 'sections.games_title')}</span></h2>
      <p>{t(s, 'sections.games_sub')}</p>
    </div>
    <div class="game-grid">
{game_cards}
    </div>
  </section>
  <section class="sec" id="tools">
    <div class="sec-head reveal">
      <h2>{t(s, 'sections.tools_title')}</h2>
      <p>{t(s, 'sections.tools_sub')}</p>
    </div>
    <div class="tool-grid">
{tool_cards}
    </div>
  </section>
</main>
{values}
<section class="wrap" id="about">
  <div class="about reveal">
    <h2>{t(s, 'about.title')}</h2>
    <p>{t(s, 'about.body')}</p>
  </div>
</section>
"""
    html += footer(lang, s)
    out = ROOT / lang["path"] / "index.html" if lang["path"] else ROOT / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def render_app(lang, s, app):
    slug = app["slug"]
    page = f"{slug}/"
    canonical = SITE["base_url"] + lang_url(lang, page)
    a = s["apps"][slug]
    feats = []
    for f in a["features"]:
        feats.append(f"""      <div class="feat reveal"><h3>{esc(f['t'])}</h3><p>{esc(f['d'])}</p></div>""")
    disclaimer = f'<p class="disclaimer">{esc(a["disclaimer"])}</p>' if a["disclaimer"] else ""
    features_heading = t(s, "common.features").replace("{app}", app["name"])

    html = head(lang, s, f"{app['name']} — {a['tagline']}", a["meta_desc"], page, canonical)
    html += "<body>\n" + header_nav(lang, s, page)
    html += f"""<section class="app-hero" style="--aa:{app['gradient'][0]};--ab:{app['gradient'][1]};">
  <div class="wrap app-hero-inner">
    <div class="app-hero-copy">
      <img class="app-icon-lg" src="/assets/img/icon-{slug}.png" alt="" width="88" height="88">
      <h1>{app['name']}</h1>
      <p class="lede">{esc(a['subtitle'])}</p>
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
    <div class="feat-grid">
{chr(10).join(feats)}
    </div>
  </section>
  <section class="privacy-strip reveal">
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
        rows.append(f"""    <div class="legal-row reveal" style="--aa:{app['gradient'][0]};">
      <img class="app-icon" src="/assets/img/icon-{app['slug']}.png" alt="" width="44" height="44">
      <h3>{app['name']}</h3>
      <div class="legal-links">
        <a href="/{app['slug']}/privacy.html">{t(s, 'common.privacy_policy')}</a>
        <a href="/{app['slug']}/support.html">{t(s, 'common.support')}</a>
      </div>
    </div>""")

    html = head(lang, s, title, t(s, "meta.home_desc"), page, canonical)
    html += "<body>\n" + header_nav(lang, s, page)
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
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE['base_url']}/sitemap.xml\n")


def main():
    i18n = load_i18n()
    process_images()
    count = 0
    for lang in LANGS:
        s = i18n[lang["code"]]
        render_home(lang, s)
        render_legal(lang, s)
        count += 2
        for app in APPS:
            render_app(lang, s, app)
            count += 1
    render_sitemap()
    print(f"Generated {count} pages for {len(LANGS)} languages.")


if __name__ == "__main__":
    main()
