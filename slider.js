/* Lightweight, dependency-free hero screenshot slider.
   Progressive enhancement: without JS the first slide shows and the rest stack
   (CSS keeps the track visible). Respects prefers-reduced-motion (no autoplay). */
(function () {
  var reduce = false;
  try { reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}

  function initSlider(root) {
    var track = root.querySelector(".hs-track");
    var slides = Array.prototype.slice.call(root.querySelectorAll(".hs-slide"));
    if (!track || slides.length < 2) return;
    var dotsWrap = root.querySelector(".hs-dots");
    var prev = root.querySelector(".hs-prev");
    var next = root.querySelector(".hs-next");
    var i = 0, timer = null, DELAY = 5000;

    // Build dots
    var dots = [];
    if (dotsWrap) {
      slides.forEach(function (s, idx) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "hs-dot";
        b.setAttribute("role", "tab");
        var label = s.getAttribute("data-label") || ("Screen " + (idx + 1));
        b.setAttribute("aria-label", label);
        b.addEventListener("click", function () { go(idx, true); });
        dotsWrap.appendChild(b);
        dots.push(b);
      });
    }

    function render() {
      track.style.transform = "translateX(" + (-i * 100) + "%)";
      slides.forEach(function (s, idx) {
        s.setAttribute("aria-hidden", idx === i ? "false" : "true");
      });
      dots.forEach(function (d, idx) {
        d.setAttribute("aria-selected", idx === i ? "true" : "false");
        d.classList.toggle("is-on", idx === i);
      });
    }
    function go(n, user) {
      i = (n + slides.length) % slides.length;
      render();
      if (user) restart();
    }
    function nextSlide() { go(i + 1); }
    function start() { if (!reduce && !timer) timer = setInterval(nextSlide, DELAY); }
    function stop() { if (timer) { clearInterval(timer); timer = null; } }
    function restart() { stop(); start(); }

    if (next) next.addEventListener("click", function () { go(i + 1, true); });
    if (prev) prev.addEventListener("click", function () { go(i - 1, true); });

    // Pause on hover / focus; stop when tab hidden or scrolled off.
    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    root.addEventListener("focusin", stop);
    root.addEventListener("focusout", start);
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stop(); else start();
    });

    // Keyboard when the slider has focus.
    root.setAttribute("tabindex", "-1");
    root.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); go(i + 1, true); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); go(i - 1, true); }
    });

    // Touch swipe.
    var x0 = null;
    root.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; stop(); }, { passive: true });
    root.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 40) go(i + (dx < 0 ? 1 : -1), true); else start();
      x0 = null;
    }, { passive: true });

    // Only autoplay while visible in the viewport.
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) start(); else stop(); });
      }, { threshold: 0.25 }).observe(root);
    } else { start(); }

    render();
    start();
  }

  function boot() {
    document.querySelectorAll("[data-slider]").forEach(initSlider);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
