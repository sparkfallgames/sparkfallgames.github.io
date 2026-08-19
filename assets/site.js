/* Sparkfall Games — site enhancements.
   Self-written, zero third-party code, no tracking. Site is fully static;
   the only motion is a whisper of falling embers in the home hero.
   1. Hero ember motes (canvas; skipped for reduced motion)
   2. First-visit language redirect + explicit choice memory */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- Hero ember motes（纸白底上的极轻余烬，品牌记忆点） ----
  document.addEventListener("DOMContentLoaded", function () {
    var canvas = document.getElementById("sparks");
    if (!canvas || reduced) return;
    var ctx = canvas.getContext("2d");
    if (!ctx) return;

    // 深一档的暖色，低透明度——纸上可见但不抢戏
    var COLORS = ["#e06f28", "#d99a3c", "#c94f22", "#e8975a"];
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = 0, h = 0, parts = [], raf = 0;

    function resize() {
      var r = canvas.parentElement.getBoundingClientRect();
      w = r.width; h = r.height;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var n = Math.min(18, Math.max(10, Math.round(w / 90)));
      parts = [];
      for (var i = 0; i < n; i++) parts.push(spawn(true));
    }

    function spawn(anywhere) {
      return {
        x: Math.random() * w,
        y: anywhere ? Math.random() * h : -6,
        vx: (Math.random() - 0.5) * 0.12,
        vy: 0.16 + Math.random() * 0.34,
        r: 0.8 + Math.random() * 1.4,
        c: COLORS[(Math.random() * COLORS.length) | 0],
        a: 0.12 + Math.random() * 0.22,
        tw: Math.random() * Math.PI * 2,
        sway: 0.2 + Math.random() * 0.4
      };
    }

    function tick() {
      ctx.clearRect(0, 0, w, h);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        p.tw += 0.03;
        p.x += p.vx + Math.sin(p.tw) * 0.1 * p.sway;
        p.y += p.vy;
        if (p.y > h + 8 || p.x < -8 || p.x > w + 8) parts[i] = p = spawn(false);
        ctx.globalAlpha = p.a * (0.6 + 0.4 * Math.sin(p.tw));
        ctx.fillStyle = p.c;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(tick);
    }

    document.addEventListener("visibilitychange", function () {
      if (document.hidden) { cancelAnimationFrame(raf); }
      else { raf = requestAnimationFrame(tick); }
    });

    window.addEventListener("resize", resize);
    resize();
    raf = requestAnimationFrame(tick);
  });

  // ---- Language handling ----
  document.addEventListener("change", function (e) {
    if (e.target.classList && e.target.classList.contains("lang-switch")) {
      try { localStorage.setItem("site-lang-chosen", "1"); } catch (err) {}
    }
  });

  var LANG_PATHS = ["zh-hans", "zh-hant", "es", "de", "fr", "ja", "pt-br", "ko",
    "it", "nl", "pt-pt", "ru", "uk", "tr", "ar", "th", "vi", "id", "ms", "hi",
    "pl", "sv", "da", "fi", "no", "cs", "hu", "ro", "el", "he"];

  function match(nav) {
    nav = nav.toLowerCase();
    if (nav.indexOf("zh") === 0) {
      return (nav.indexOf("hant") !== -1 || nav.indexOf("tw") !== -1 ||
              nav.indexOf("hk") !== -1 || nav.indexOf("mo") !== -1)
        ? "zh-hant" : "zh-hans";
    }
    if (nav.indexOf("pt") === 0) return nav.indexOf("br") === -1 ? "pt-pt" : "pt-br";
    if (nav.indexOf("nb") === 0 || nav.indexOf("nn") === 0) return "no";
    var two = nav.slice(0, 2);
    return LANG_PATHS.indexOf(two) !== -1 ? two : null;
  }

  try {
    var path = location.pathname;
    var isRootHome = path === "/" || path === "/index.html";
    if (isRootHome &&
        !sessionStorage.getItem("site-lang-redirected") &&
        !localStorage.getItem("site-lang-chosen")) {
      sessionStorage.setItem("site-lang-redirected", "1");
      var target = match(navigator.language || "");
      if (target) location.replace("/" + target + "/");
    }
  } catch (err) { /* storage blocked — stay on English */ }
})();
