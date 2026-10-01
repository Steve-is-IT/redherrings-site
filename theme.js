/* Light/dark theme toggle.
   The no-flash inline snippet in each page's <head> applies a saved choice
   before paint; this script adds the header button and keeps it in sync.
   Default (no saved choice) follows the OS via prefers-color-scheme. */
(function () {
  var root = document.documentElement;
  var KEY = "rh-theme";

  function systemDark() {
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function effective() {
    var t = root.getAttribute("data-theme");
    if (t === "dark" || t === "light") return t;
    return systemDark() ? "dark" : "light";
  }

  var btn;
  var SUN = '<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M19.1 4.9l-1.8 1.8M6.7 17.3l-1.8 1.8"/></svg>';
  var MOON = '<svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.5A8.5 8.5 0 1 1 11.5 3a6.5 6.5 0 0 0 9.5 9.5z"/></svg>';

  function refresh() {
    if (!btn) return;
    var e = effective();
    btn.setAttribute("data-eff", e);
    btn.setAttribute("aria-label", e === "dark" ? "Switch to light theme" : "Switch to dark theme");
    btn.setAttribute("title", e === "dark" ? "Switch to light theme" : "Switch to dark theme");
  }

  function set(theme) {
    root.setAttribute("data-theme", theme);
    try { localStorage.setItem(KEY, theme); } catch (e) {}
    refresh();
  }

  function init() {
    var nav = document.querySelector(".nav");
    if (!nav) return;
    btn = document.createElement("button");
    btn.className = "themetoggle";
    btn.type = "button";
    btn.innerHTML = SUN + MOON;
    btn.addEventListener("click", function () {
      set(effective() === "dark" ? "light" : "dark");
    });
    // Place it at the end of the nav, after the primary call-to-action.
    nav.appendChild(btn);
    refresh();

    // Follow OS changes while the viewer has made no explicit choice.
    if (window.matchMedia) {
      var mq = window.matchMedia("(prefers-color-scheme: dark)");
      var onChange = function () { if (!root.getAttribute("data-theme")) refresh(); };
      if (mq.addEventListener) mq.addEventListener("change", onChange);
      else if (mq.addListener) mq.addListener(onChange);
    }
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
