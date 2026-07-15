# Qiuyufei Apps 官网（矩阵 App #000）

静态官网，托管全部矩阵 App 的产品页、隐私政策和支持页。
部署为 GitHub Pages 用户主页仓库：`2645809444.github.io`。

## 线上地址

- 首页：https://2645809444.github.io/
- 各 App：`https://2645809444.github.io/<app>/`（产品页）、
  `/<app>/privacy.html`（隐私政策）、`/<app>/support.html`（支持页）

## 目录结构

```
index.html            品牌首页（主张/数据条/App 卡片/理念/工作室介绍）
assets/style.css      共享样式（品牌渐变设计系统、自适应深色模式、滚动动画）
assets/site.js        增强脚本（粒子特效、滚动渐入、WebAudio 原创音效——默认关、
                      用户主动开启，偏好存 localStorage；尊重 prefers-reduced-motion）
quickcost/            001 QuickCost
decibelmeter/         002 Decibel Meter
fastzen/              003 FastZen
mathspark/            004 MathSpark
```

JS 铁律：自写自托管、零第三方、无跟踪；音效全部 WebAudio 合成（无采样素材）。
产品页下载按钮在 App 上架前是置灰的 "Coming Soon"，上架后回填真实链接。

每个 App 目录固定三个文件：`index.html`（产品页）、`privacy.html`（隐私政策，
英文 + 中文）、`support.html`（支持页 + FAQ）。

## 新增 App 流程

1. 复制任一 App 目录，改文案、配色（`style.css` 里加 `--<app>` 变量）
2. 首页 `index.html` 加卡片 + 页脚隐私链接
3. 隐私政策必须按 App 真实数据行为撰写（见 privacy-page 技能），三方口径一致
4. commit + push，等 1-2 分钟后 `curl -sI` 验证 200
5. 工程内 `AppConfig`/`AppLinks` 填入正式 URL

## 部署

推送 main 分支即自动发布（Pages 开在 main 根目录）。无构建步骤、无依赖。
