/* Scroll-reveal animations + first-visit language redirect. */
(function () {
  "use strict";

  // Reveal on scroll (skipped when the user prefers reduced motion).
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.addEventListener("DOMContentLoaded", function () {
    var els = document.querySelectorAll(".reveal");
    if (reduced || !("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.15 });
    els.forEach(function (el) { io.observe(el); });
  });

  // Remember an explicit language choice made via the switcher.
  document.addEventListener("change", function (e) {
    if (e.target.classList && e.target.classList.contains("lang-switch")) {
      try { localStorage.setItem("site-lang-chosen", "1"); } catch (err) {}
    }
  });

  // On the English homepage only: offer a one-time redirect that matches
  // the browser language. Never loops — runs once per session, and never
  // after the user has explicitly picked a language.
  var LANG_PATHS = ["zh-hans", "zh-hant", "es", "de", "fr", "ja", "pt-br", "ko",
    "it", "nl", "pt-pt", "ru", "uk", "tr", "ar", "th", "vi", "id", "ms", "hi",
    "pl", "sv", "da", "fi", "no", "cs", "hu", "ro", "el", "he"];

  function match(nav) {
    nav = nav.toLowerCase();
    if (nav.startsWith("zh")) {
      return (nav.includes("hant") || nav.includes("tw") || nav.includes("hk") || nav.includes("mo"))
        ? "zh-hant" : "zh-hans";
    }
    if (nav.startsWith("pt")) return nav.includes("pt") && !nav.includes("br") ? "pt-pt" : "pt-br";
    if (nav.startsWith("nb") || nav.startsWith("nn")) return "no";
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
