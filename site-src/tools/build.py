#!/usr/bin/env python3
"""Static site generator for 2645809444.github.io.

Reads site-src/content/<lang>.json and writes the whole site (all languages)
into the repo root. English lives at /, other languages at /<code>/.
Run:  python3 site-src/tools/build.py
"""

import json
import html
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # repo root (000/)
SRC = ROOT / "site-src"
CONTENT = SRC / "content"
BASE_URL = "https://2645809444.github.io"
APP_ORDER = ["quickcost", "decibelmeter", "fastzen", "mathspark"]
CANONICAL_EMAIL = "2645809444@qq.com"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def load_langs():
    langs = {}
    for f in sorted(CONTENT.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        langs[data["meta"]["code"]] = data
    assert "en" in langs, "en.json is the master and must exist"
    return langs


def lang_prefix(code: str) -> str:
    return "" if code == "en" else f"/{code}"


def page_url(code: str, rel: str) -> str:
    """rel like '' (home), 'quickcost/', 'quickcost/privacy.html'"""
    return f"{lang_prefix(code)}/{rel}" if rel else (lang_prefix(code) + "/")


def hreflang_links(langs, rel):
    out = []
    for code in langs:
        out.append(f'<link rel="alternate" hreflang="{code}" href="{BASE_URL}{page_url(code, rel)}">')
    out.append(f'<link rel="alternate" hreflang="x-default" href="{BASE_URL}{page_url("en", rel)}">')
    return "\n".join(out)


def lang_switcher(langs, cur, rel):
    items = []
    for code, data in langs.items():
        name = esc(data["meta"]["nativeName"])
        href = page_url(code, rel)
        current = ' aria-current="true"' if code == cur else ""
        items.append(f'<a role="option" href="{href}" data-lang="{code}"{current}>{name}</a>')
    label = esc(langs[cur]["site"]["labels"]["language"])
    return f'''<details class="lang">
  <summary aria-label="{label}"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg><span>{esc(langs[cur]["meta"]["nativeName"])}</span></summary>
  <div class="lang-menu" role="listbox">{''.join(items)}</div>
</details>'''


def head(langs, code, rel, title, desc, extra=""):
    data = langs[code]
    dirattr = data["meta"]["dir"]
    canonical = f"{BASE_URL}{page_url(code, rel)}"
    return f'''<!DOCTYPE html>
<html lang="{data["meta"]["htmlLang"]}" dir="{dirattr}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="Qiuyufei Apps">
<meta name="theme-color" content="#0e0d12">
{hreflang_links(langs, rel)}
<link rel="stylesheet" href="/assets/style.css">
{extra}</head>
<body>'''


def header_nav(langs, code, rel, home_active=False):
    site = langs[code]["site"]
    home = page_url(code, "")
    return f'''<header class="site">
  <div class="wrap">
    <a class="brand" href="{home}"><span class="brand-dot" aria-hidden="true"></span>{esc(site["brand"])}</a>
    <nav class="site-nav">
      <a href="{home}#apps">{esc(site["nav"]["apps"])}</a>
      <a href="mailto:{CANONICAL_EMAIL}">{esc(site["nav"]["contact"])}</a>
      {lang_switcher(langs, code, rel)}
    </nav>
  </div>
</header>'''


def footer(langs, code):
    site = langs[code]["site"]
    labels = site["labels"]
    apps = langs[code]["apps"]
    links = " · ".join(
        f'<a href="{page_url(code, a + "/privacy.html")}">{esc(apps[a]["name"])}</a>'
        for a in APP_ORDER
    )
    return f'''<footer class="site">
  <div class="wrap">
    <p>{esc(labels["footerRights"])} · <a href="mailto:{CANONICAL_EMAIL}">{CANONICAL_EMAIL}</a></p>
    <p>{esc(labels["footerPrivacyRow"])}: {links}</p>
  </div>
</footer>
<script src="/assets/site.js" defer></script>
</body>
</html>'''


def home_page(langs, code):
    data = langs[code]
    site = data["site"]
    labels = site["labels"]
    rel = ""
    principles = "".join(
        f'''<div class="principle reveal"><h3>{esc(p["t"])}</h3><p>{esc(p["d"])}</p></div>'''
        for p in site["principles"]
    )
    cards = ""
    for a in APP_ORDER:
        app = data["apps"][a]
        cards += f'''
    <a class="card reveal app-{a}" href="{page_url(code, a + "/")}">
      <div class="card-glow" aria-hidden="true"></div>
      <div class="app-mark" aria-hidden="true">{esc(app["name"][0])}</div>
      <h3>{esc(app["name"])}</h3>
      <p class="tagline">{esc(app["tagline"])}</p>
      <p class="carddesc">{esc(app["heroSub"])}</p>
      <span class="badge">{esc(app["category"])}</span>
    </a>'''
    # first-visit language auto-redirect, root page only
    redirect = ""
    if code == "en":
        codes = json.dumps(list(langs.keys()))
        redirect = f'''<script>
(function () {{
  try {{
    var supported = {codes};
    var saved = localStorage.getItem("site-lang");
    if (saved === "en") return;
    if (saved && supported.indexOf(saved) > -1) {{ location.replace("/" + saved + "/"); return; }}
    if (saved) return;
    var nav = (navigator.languages || [navigator.language || ""]).map(function (l) {{ return l.toLowerCase(); }});
    for (var i = 0; i < nav.length; i++) {{
      var l = nav[i];
      var hit = null;
      if (l.indexOf("zh") === 0) hit = (l.indexOf("tw") > -1 || l.indexOf("hk") > -1 || l.indexOf("hant") > -1) ? "zh-hant" : "zh-hans";
      else if (l.indexOf("pt") === 0) hit = (l.indexOf("pt-pt") === 0) ? "pt-pt" : "pt-br";
      else if (l.indexOf("no") === 0 || l.indexOf("nb") === 0) hit = "no";
      else {{ var base = l.split("-")[0]; if (supported.indexOf(base) > -1) hit = base; }}
      if (hit && hit !== "en" && supported.indexOf(hit) > -1) {{ localStorage.setItem("site-lang", hit); location.replace("/" + hit + "/"); return; }}
      if (hit === "en") return;
    }}
  }} catch (e) {{}}
}})();
</script>\n'''
    out = head(langs, code, rel, site["titleHome"], site["descHome"], redirect)
    out += header_nav(langs, code, rel, home_active=True)
    out += f'''
<section class="hero">
  <canvas id="fx" aria-hidden="true"></canvas>
  <div class="blob b1" aria-hidden="true"></div>
  <div class="blob b2" aria-hidden="true"></div>
  <div class="blob b3" aria-hidden="true"></div>
  <div class="wrap hero-inner">
    <p class="kicker reveal">{esc(site["heroKicker"])}</p>
    <h1 class="reveal">{esc(site["heroTitle"])}</h1>
    <p class="sub reveal">{esc(site["heroSub"])}</p>
    <p class="reveal"><a class="btn primary big" href="#apps">{esc(site["heroCta"])}</a></p>
    <div class="stats reveal">
      <div><strong>4</strong><span>{esc(site["statApps"])}</span></div>
      <div><strong>31</strong><span>{esc(site["statLanguages"])}</span></div>
      <div><strong>0</strong><span>{esc(site["statTracking"])}</span></div>
    </div>
  </div>
</section>

<section class="principles">
  <div class="wrap">
    <h2 class="reveal">{esc(site["principlesTitle"])}</h2>
    <div class="principle-grid">{principles}</div>
  </div>
</section>

<main class="apps" id="apps">
  <div class="wrap">
    <h2 class="reveal">{esc(site["appsTitle"])}</h2>
    <p class="sectionsub reveal">{esc(site["appsSub"])}</p>
    <div class="grid">{cards}
    </div>
  </div>
</main>
'''
    out += footer(langs, code)
    return out


def product_page(langs, code, slug):
    data = langs[code]
    app = data["apps"][slug]
    labels = data["site"]["labels"]
    rel = f"{slug}/"
    feats = "".join(
        f'''<div class="feature reveal"><h3>{esc(f["t"])}</h3><p>{esc(f["d"])}</p></div>'''
        for f in app["features"]
    )
    shots = "".join(
        f'''<div class="phone reveal"><div class="phone-notch" aria-hidden="true"></div><img src="/assets/shots/{s["file"]}" alt="{esc(s["alt"])}" loading="lazy" width="410" height="890"></div>'''
        for s in app.get("shots", [])
    )
    disclaimer = f'<p class="disclaimer">{esc(app["disclaimer"])}</p>' if app.get("disclaimer") else ""
    out = head(langs, code, rel, app["titleProduct"], app["descProduct"])
    out += header_nav(langs, code, rel)
    out += f'''
<section class="hero app-hero app-{slug}">
  <div class="blob b1" aria-hidden="true"></div>
  <div class="blob b2" aria-hidden="true"></div>
  <div class="wrap hero-inner product">
    <div class="hero-copy">
      <div class="app-mark big" aria-hidden="true">{esc(app["name"][0])}</div>
      <h1 class="reveal">{esc(app["name"])}</h1>
      <p class="tagline-big reveal">{esc(app["tagline"])}</p>
      <p class="sub reveal">{esc(app["heroSub"])}</p>
      <div class="link-row reveal">
        <span class="btn primary soon" aria-disabled="true">{esc(labels["comingSoon"])}</span>
        <a class="btn" href="{page_url(code, slug + "/privacy.html")}">{esc(labels["privacy"])}</a>
        <a class="btn" href="{page_url(code, slug + "/support.html")}">{esc(labels["support"])}</a>
      </div>
    </div>
    <div class="hero-shots">{shots}</div>
  </div>
</section>

<main class="wrap page">
  <h2 class="reveal">{esc(labels["features"])}</h2>
  <div class="feature-grid">{feats}</div>

  <section class="privacy-callout app-{slug} reveal">
    <h2>{esc(labels["privacyHeading"])}</h2>
    <p>{esc(app["privacyBlurb"])} <a href="{page_url(code, slug + "/privacy.html")}">{esc(labels["privacy"])}</a></p>
    {disclaimer}
  </section>
</main>
'''
    out += footer(langs, code)
    return out


def support_page(langs, code, slug):
    data = langs[code]
    app = data["apps"][slug]
    labels = data["site"]["labels"]
    rel = f"{slug}/support.html"
    faq = "".join(
        f'''<h3>{esc(f["q"])}</h3><p>{esc(f["a"])}</p>'''
        for f in app["support"]["faq"]
    )
    out = head(langs, code, rel, f'{app["name"]} — {labels["support"]}', app["descProduct"])
    out += header_nav(langs, code, rel)
    out += f'''
<main class="wrap page static">
  <p class="crumb"><a href="{page_url(code, slug + "/")}">&larr; {esc(labels["backToApp"])}</a></p>
  <h1>{esc(app["support"]["title"])}</h1>
  <p class="subtitle">{esc(labels["contactReply"])}</p>
  <h2>{esc(labels["contactHeading"])}</h2>
  <p><a href="mailto:{CANONICAL_EMAIL}">{CANONICAL_EMAIL}</a></p>
  <p>{esc(labels["contactHint"])}</p>
  <h2>{esc(labels["faqHeading"])}</h2>
  {faq}
</main>
'''
    out += footer(langs, code)
    return out


def privacy_page(langs, code, slug):
    data = langs[code]
    app = data["apps"][slug]
    labels = data["site"]["labels"]
    rel = f"{slug}/privacy.html"
    pv = app["privacy"]
    sections = "".join(f'''<h2>{esc(s["h"])}</h2><p>{esc(s["p"])}</p>''' for s in pv["sections"])
    out = head(langs, code, rel, pv["title"], app["descProduct"])
    out += header_nav(langs, code, rel)
    out += f'''
<main class="wrap page static">
  <p class="crumb"><a href="{page_url(code, slug + "/")}">&larr; {esc(labels["backToApp"])}</a></p>
  <h1>{esc(pv["title"])}</h1>
  <p class="updated">{esc(labels["lastUpdated"])}: {esc(pv["updated"])}</p>
  {sections}
</main>
'''
    out += footer(langs, code)
    return out


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build():
    langs = load_langs()
    pages = []  # (rel, per-lang) for sitemap

    rels = [""] + [f"{a}/" for a in APP_ORDER] + \
           [f"{a}/privacy.html" for a in APP_ORDER] + \
           [f"{a}/support.html" for a in APP_ORDER]

    for code in langs:
        prefix = ROOT if code == "en" else ROOT / code
        write(prefix / "index.html", home_page(langs, code))
        for a in APP_ORDER:
            write(prefix / a / "index.html", product_page(langs, code, a))
            write(prefix / a / "privacy.html", privacy_page(langs, code, a))
            write(prefix / a / "support.html", support_page(langs, code, a))

    # sitemap
    urls = []
    for rel in rels:
        for code in langs:
            urls.append(f"  <url><loc>{BASE_URL}{page_url(code, rel)}</loc></url>")
    write(ROOT / "sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "\n".join(urls) + "\n</urlset>\n")
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")

    n_pages = len(langs) * len(rels)
    print(f"Built {n_pages} pages in {len(langs)} languages.")


if __name__ == "__main__":
    build()
