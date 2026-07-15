/* Sparkfall Games — site enhancements.
   Self-written, zero third-party code, no tracking.
   1. Scroll-reveal animations
   2. Hero spark particles (canvas, skipped for reduced motion / saved data)
   3. First-visit language redirect + explicit choice memory */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- Scroll reveal ----
  document.addEventListener("DOMContentLoaded", function () {
    var els = document.querySelectorAll(".reveal");
    if (reduced || !("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("in"); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        });
      }, { threshold: 0.15 });
      els.forEach(function (el) { io.observe(el); });
    }
    sparks();
  });

  // ---- Hero spark particles ----
  function sparks() {
    var canvas = document.getElementById("sparks");
    if (!canvas || reduced) return;
    var ctx = canvas.getContext("2d");
    if (!ctx) return;

    var COLORS = ["#a78bfa", "#60a5fa", "#22d3ee", "#f472b6"];
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = 0, h = 0, parts = [], raf = 0;

    function resize() {
      var r = canvas.parentElement.getBoundingClientRect();
      w = r.width; h = r.height;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var n = Math.min(70, Math.max(28, Math.round(w / 16)));
      parts = [];
      for (var i = 0; i < n; i++) parts.push(spawn(true));
    }

    function spawn(anywhere) {
      return {
        x: Math.random() * w,
        y: anywhere ? Math.random() * h : h + 6,
        vx: (Math.random() - 0.5) * 0.22,
        vy: -(0.25 + Math.random() * 0.6),
        r: 0.6 + Math.random() * 1.7,
        c: COLORS[(Math.random() * COLORS.length) | 0],
        a: 0.25 + Math.random() * 0.55,
        tw: Math.random() * Math.PI * 2
      };
    }

    function tick() {
      ctx.clearRect(0, 0, w, h);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        p.x += p.vx; p.y += p.vy; p.tw += 0.04;
        if (p.y < -8 || p.x < -8 || p.x > w + 8) parts[i] = p = spawn(false);
        var glow = p.a * (0.65 + 0.35 * Math.sin(p.tw));
        ctx.globalAlpha = glow;
        ctx.fillStyle = p.c;
        ctx.shadowColor = p.c;
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      ctx.shadowBlur = 0;
      raf = requestAnimationFrame(tick);
    }

    // Pause when the tab is hidden.
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) { cancelAnimationFrame(raf); }
      else { raf = requestAnimationFrame(tick); }
    });

    window.addEventListener("resize", resize);
    resize();
    raf = requestAnimationFrame(tick);
  }

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
