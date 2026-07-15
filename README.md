# Qiuyufei Apps 官网（矩阵 App #000）

静态官网，托管全部矩阵 App 的产品页、隐私政策和支持页。
部署为 GitHub Pages 用户主页仓库：`qiuyufei.github.io`。

## 线上地址

- 首页：https://qiuyufei.github.io/
- 各 App：`https://qiuyufei.github.io/<app>/`（产品页）、
  `/<app>/privacy.html`（隐私政策）、`/<app>/support.html`（支持页）

## 目录结构

```
index.html            首页（全部 App 卡片）
assets/style.css      共享样式（自适应深色模式）
quickcost/            001 QuickCost
decibelmeter/         002 Decibel Meter
fastzen/              003 FastZen
mathspark/            004 MathSpark
```

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
