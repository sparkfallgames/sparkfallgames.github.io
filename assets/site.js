/* Site enhancements: scroll reveal, hero particles, optional UI sounds.
   Self-hosted, zero dependencies, no tracking. Sounds are opt-in (default off). */
(function () {
  "use strict";

  document.documentElement.classList.add("js");

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Scroll reveal ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length && "IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- Hero particles ---------- */
  var canvas = document.getElementById("fx-canvas");
  if (canvas && !reduceMotion) {
    var ctx = canvas.getContext("2d");
    var COLORS = ["#2e9e5b", "#0f8a9d", "#d98a2b", "#7c5cff"];
    var parts = [];
    var running = true;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = 0, h = 0;

    function resize() {
      var r = canvas.parentElement.getBoundingClientRect();
      w = r.width; h = r.height;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function spawn(n) {
      for (var i = 0; i < n; i++) {
        parts.push({
          x: Math.random() * w,
          y: Math.random() * h,
          r: 1.2 + Math.random() * 2.6,
          vx: (Math.random() - 0.5) * 0.22,
          vy: -0.06 - Math.random() * 0.20,
          c: COLORS[(Math.random() * COLORS.length) | 0],
          a: 0.12 + Math.random() * 0.25,
          tw: Math.random() * Math.PI * 2
        });
      }
    }

    function tick(t) {
      if (!running) return;
      ctx.clearRect(0, 0, w, h);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        p.x += p.vx; p.y += p.vy;
        if (p.y < -8 || p.x < -8 || p.x > w + 8) {
          p.x = Math.random() * w; p.y = h + 8;
        }
        var pulse = 0.75 + 0.25 * Math.sin(t / 900 + p.tw);
        ctx.globalAlpha = p.a * pulse;
        ctx.fillStyle = p.c;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      requestAnimationFrame(tick);
    }

    resize();
    spawn(Math.min(70, Math.max(30, (w / 14) | 0)));
    requestAnimationFrame(tick);
    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", function () {
      var was = running;
      running = !document.hidden;
      if (running && !was) requestAnimationFrame(tick);
    });
  }

  /* ---------- Optional UI sounds (WebAudio, synthesized, opt-in) ---------- */
  var KEY = "site-sound";
  var soundOn = false;
  try { soundOn = localStorage.getItem(KEY) === "1"; } catch (e) {}
  var actx = null;

  function ensureCtx() {
    if (!actx) {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      actx = new AC();
    }
    if (actx.state === "suspended") actx.resume();
    return actx;
  }

  /* freq sweep + short envelope; all sounds synthesized, nothing sampled */
  function blip(f0, f1, dur, type, vol) {
    if (!soundOn) return;
    var ac = ensureCtx();
    if (!ac) return;
    var t0 = ac.currentTime;
    var osc = ac.createOscillator();
    var g = ac.createGain();
    osc.type = type || "sine";
    osc.frequency.setValueAtTime(f0, t0);
    if (f1 && f1 !== f0) osc.frequency.exponentialRampToValueAtTime(f1, t0 + dur);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(vol || 0.12, t0 + 0.008);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    osc.connect(g).connect(ac.destination);
    osc.start(t0);
    osc.stop(t0 + dur + 0.02);
  }

  var sfx = {
    hover: function () { blip(1150, 1350, 0.05, "sine", 0.05); },
    click: function () { blip(420, 940, 0.09, "sine", 0.10); },
    on:    function () { blip(523, 1046, 0.16, "triangle", 0.12); },
    off:   function () { blip(660, 330, 0.14, "triangle", 0.10); }
  };

  /* Toggle button injected into nav */
  var nav = document.querySelector("nav.site");
  if (nav) {
    var btn = document.createElement("button");
    btn.className = "sound-toggle";
    btn.type = "button";
    btn.setAttribute("aria-pressed", soundOn ? "true" : "false");
    btn.setAttribute("aria-label", "Toggle interface sounds");
    btn.title = "Interface sounds";
    var ICON_ON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="currentColor" stroke="none"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18.5 5.5a9 9 0 0 1 0 13"/></svg>';
    var ICON_OFF = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="currentColor" stroke="none"/><line x1="16" y1="9" x2="22" y2="15"/><line x1="22" y1="9" x2="16" y2="15"/></svg>';
    btn.innerHTML = soundOn ? ICON_ON : ICON_OFF;
    btn.addEventListener("click", function () {
      soundOn = !soundOn;
      try { localStorage.setItem(KEY, soundOn ? "1" : "0"); } catch (e) {}
      btn.setAttribute("aria-pressed", soundOn ? "true" : "false");
      btn.innerHTML = soundOn ? ICON_ON : ICON_OFF;
      (soundOn ? sfx.on : sfx.off)();
    });
    nav.appendChild(btn);
  }

  /* Wire sounds to interactive elements */
  document.addEventListener("click", function (e) {
    if (e.target.closest("a, button:not(.sound-toggle)")) sfx.click();
  });
  var hoverables = document.querySelectorAll(".card, .btn");
  hoverables.forEach(function (el) {
    el.addEventListener("mouseenter", function () { sfx.hover(); });
  });
})();
