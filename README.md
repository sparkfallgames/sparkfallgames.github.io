# Qiuyufei Apps 官网（矩阵 App #000）

静态官网，托管全部矩阵 App 的产品页、隐私政策和支持页。
部署为 GitHub Pages 用户主页仓库：`2645809444.github.io`。

## 线上地址

- 首页：https://2645809444.github.io/
- 各 App：`https://2645809444.github.io/<app>/`（产品页）、
  `/<app>/privacy.html`（隐私政策）、`/<app>/support.html`（支持页）

## 目录结构（页面由生成器产出，不要手改仓库根的 HTML）

```
site-src/content/<lang>.json   ★ 唯一的内容源（en 为主，zh-hans/ja/de/fr/es）
site-src/tools/build.py        生成器：python3 site-src/tools/build.py
index.html + <app>/…           en 版（根目录）——生成产物
<lang>/…                       其他语言版本——生成产物
assets/style.css               设计系统（品牌渐变、深色优先、动画、语言菜单）
assets/site.js                 增强脚本（滚动渐入、粒子特效、语言偏好记忆、
                               WebAudio 原创音效——默认关，尊重 prefers-reduced-motion）
sitemap.xml / robots.txt       生成产物（含全语言 hreflang）
```

多语言机制：每种语言一套静态页面（`/` 英文、`/<lang>/` 其他），SEO 友好
（hreflang 互链）；根页有首访自动跳转脚本（按浏览器语言，选择存 localStorage），
导航栏有手动语言菜单。改文案 = 改 `site-src/content/*.json` → 跑 build.py → push。

JS 铁律：自写自托管、零第三方、无跟踪；音效全部 WebAudio 合成（无采样素材）。
产品页下载按钮在 App 上架前是置灰的 "Coming Soon"，上架后回填真实链接
（改 en.json 等全部语言的 JSON + build）。

## 新增 App 流程

1. 在每个 `site-src/content/<lang>.json` 的 `apps` 里加该 App 的完整条目
   （文案从 aso-copy 的 listing.md 取；隐私政策内容见 privacy-page 技能，三方口径一致）
2. `build.py` 的 `APP_ORDER` 加 slug；`style.css` 加 `--<app>` 主色变量和 `.app-<slug>`
3. 跑 `python3 site-src/tools/build.py`，本地 `python3 -m http.server` 肉眼过一遍
4. commit + push，等 1-2 分钟后 `curl -sI` 验证 200
5. 工程内 `AppConfig`/`AppLinks` 填入正式 URL

## 部署

推送 main 分支即自动发布（Pages 开在 main 根目录）。构建在本地完成，线上无依赖。
