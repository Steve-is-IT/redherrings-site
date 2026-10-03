/* Mega-menu header behaviour.
   Desktop panels open on hover and keyboard focus via CSS alone; this script
   only runs the mobile sheet (hamburger) and closes panels on Escape. */
(function () {
  function init() {
    var burger = document.querySelector(".navburger");
    var sheet = document.getElementById("mobilenav");
    if (!burger || !sheet) return;

    var BARS = burger.innerHTML;
    var X = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 5l14 14M19 5L5 19"/></svg>';
    function open() {
      sheet.hidden = false;
      burger.setAttribute("aria-expanded", "true");
      burger.setAttribute("aria-label", "Close menu");
      burger.innerHTML = X;
      document.body.classList.add("navopen");
    }
    function close() {
      sheet.hidden = true;
      burger.setAttribute("aria-expanded", "false");
      burger.setAttribute("aria-label", "Open menu");
      burger.innerHTML = BARS;
      document.body.classList.remove("navopen");
    }
    function toggle() {
      if (sheet.hidden) open(); else close();
    }

    burger.addEventListener("click", toggle);
    // Close after following a link inside the sheet.
    sheet.addEventListener("click", function (e) {
      if (e.target.closest("a")) close();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        if (!sheet.hidden) close();
        var open = document.activeElement && document.activeElement.closest(".mnitem.haspanel");
        if (open) document.activeElement.blur();
      }
    });
    // If the viewport grows back to desktop, make sure the sheet is closed.
    window.matchMedia("(min-width:900px)").addEventListener("change", function (ev) {
      if (ev.matches) close();
    });
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
