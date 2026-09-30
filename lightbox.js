/* Minimal, dependency-free lightbox using the native <dialog> element.
   Any image inside a .shot, or any img[data-zoomable], becomes clickable and
   opens full size. Esc and a backdrop click close it. */
(function () {
  function init() {
    var dlg = document.createElement("dialog");
    dlg.className = "lightbox";
    dlg.setAttribute("aria-label", "Enlarged screenshot");
    dlg.innerHTML =
      '<button type="button" class="lb-close" aria-label="Close">&times;</button>' +
      '<img alt="">';
    document.body.appendChild(dlg);
    var big = dlg.querySelector("img");

    var imgs = document.querySelectorAll(".shot img, img[data-zoomable]");
    imgs.forEach(function (t) {
      // Skip a poster image that lives inside a <video> fallback.
      if (t.closest("video")) return;
      t.classList.add("zoomable");
      t.setAttribute("role", "button");
      t.setAttribute("tabindex", "0");
      var open = function () {
        big.src = t.currentSrc || t.src;
        big.alt = t.alt || "";
        if (typeof dlg.showModal === "function") dlg.showModal();
        else window.open(big.src, "_blank");
      };
      t.addEventListener("click", open);
      t.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); }
      });
    });

    dlg.querySelector(".lb-close").addEventListener("click", function () { dlg.close(); });
    // A click on the backdrop (outside the image) closes the dialog.
    dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.close(); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
