/* Hero screenshot slider — crossfade carousel, dependency-free.
   Slides are stacked and cross-faded (GPU-composited opacity), so there is no
   horizontal motion to stutter. Autoplay only starts once every image has
   decoded, so a slide never shows before it is fully painted. Degrades to the
   first slide (marked .is-active in the markup) with no JS, and honours
   prefers-reduced-motion by swapping instantly. */
(function () {
  var reduce = false;
  try { reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}

  function initSlider(root) {
    var slides = Array.prototype.slice.call(root.querySelectorAll(".hs-slide"));
    if (slides.length < 2) return;
    var dotsWrap = root.querySelector(".hs-dots");
    var prev = root.querySelector(".hs-prev");
    var next = root.querySelector(".hs-next");
    var i = Math.max(0, slides.findIndex(function (s) { return s.classList.contains("is-active"); }));
    if (i < 0) i = 0;
    var timer = null, DELAY = 6000, dots = [];

    if (dotsWrap) {
      slides.forEach(function (s, idx) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "hs-dot";
        b.setAttribute("role", "tab");
        b.setAttribute("aria-label", s.getAttribute("data-label") || ("Screen " + (idx + 1)));
        b.addEventListener("click", function () { go(idx, true); });
        dotsWrap.appendChild(b);
        dots.push(b);
      });
    }

    function render() {
      slides.forEach(function (s, idx) {
        s.classList.toggle("is-active", idx === i);
        s.setAttribute("aria-hidden", idx === i ? "false" : "true");
      });
      dots.forEach(function (d, idx) {
        d.classList.toggle("is-on", idx === i);
        d.setAttribute("aria-selected", idx === i ? "true" : "false");
      });
    }
    function go(n, user) { i = (n + slides.length) % slides.length; render(); if (user) restart(); }
    function start() { if (!reduce && !timer) timer = setInterval(function () { go(i + 1); }, DELAY); }
    function stop() { if (timer) { clearInterval(timer); timer = null; } }
    function restart() { stop(); start(); }

    if (next) next.addEventListener("click", function () { go(i + 1, true); });
    if (prev) prev.addEventListener("click", function () { go(i - 1, true); });
    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    root.addEventListener("focusin", stop);
    root.addEventListener("focusout", start);
    document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); else start(); });

    root.setAttribute("tabindex", "-1");
    root.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); go(i + 1, true); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); go(i - 1, true); }
    });
    var x0 = null;
    root.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; stop(); }, { passive: true });
    root.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 40) go(i + (dx < 0 ? 1 : -1), true); else start();
      x0 = null;
    }, { passive: true });

    render();

    // Decode every image before autoplaying, so no slide appears half-painted.
    var imgs = Array.prototype.slice.call(root.querySelectorAll(".hs-slide img"));
    var decoded = imgs.map(function (im) {
      if (im.decode) { return im.decode().catch(function () {}); }
      return (im.complete) ? Promise.resolve() : new Promise(function (res) { im.onload = im.onerror = res; });
    });
    Promise.all(decoded).then(function () {
      root.classList.add("is-ready");
      if ("IntersectionObserver" in window) {
        new IntersectionObserver(function (entries) {
          entries.forEach(function (en) { if (en.isIntersecting) start(); else stop(); });
        }, { threshold: 0.25 }).observe(root);
      } else { start(); }
    });
  }

  function boot() { document.querySelectorAll("[data-slider]").forEach(initSlider); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
