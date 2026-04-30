/* ═══════════════════════════════════════════════════════════════
   lightbox.js — shared slide lightbox for course lecture pages.

   Auto-discovers two anchor flavors with no markup changes:
     • .slide-strip > a       (top strip)
     • figure.slide-embed > a (in-article slide thumbs)
   Anchors are merged in DOM order to form one navigable sequence.

   Anchor href is shown in the lightbox; the optional [data-slide]
   attribute supplies a "slide NN" label. <figcaption> text or
   [data-lb-cap] override the caption.

   Page must include ONE lightbox markup block:
     <div class="lightbox" id="lightbox">
       <button class="lightbox-close">×</button>
       <button class="lightbox-nav lightbox-prev">‹</button>
       <button class="lightbox-nav lightbox-next">›</button>
       <img class="lightbox-img" id="lightboxImg" alt=""/>
       <div class="lightbox-meta" id="lightboxMeta"></div>
     </div>

   Loaded as <script src="/shared/lightbox.js" defer> — defer ensures
   the page DOM (including JS-built strips) is parsed before scan.
   ═══════════════════════════════════════════════════════════════ */

(function () {
  function init() {
    const lightbox = document.getElementById("lightbox");
    if (!lightbox) return;

    const imgEl = document.getElementById("lightboxImg");
    const metaEl = document.getElementById("lightboxMeta");
    const closeBtn = lightbox.querySelector(".lightbox-close");
    const prevBtn = lightbox.querySelector(".lightbox-prev");
    const nextBtn = lightbox.querySelector(".lightbox-next");

    const anchors = Array.from(
      document.querySelectorAll(".slide-strip a, figure.slide-embed > a, a[data-lb]")
    );
    if (anchors.length === 0) return;

    let cursor = 0;

    function captionFor(a) {
      if (a.dataset.lbCap) return a.dataset.lbCap;
      const fig = a.closest("figure.slide-embed");
      const cap = fig?.querySelector("figcaption");
      if (cap) return cap.textContent.trim();
      return a.querySelector("img")?.alt || "";
    }

    function numFor(a, idx) {
      return a.dataset.slide || a.dataset.lbNum || String(idx + 1).padStart(2, "0");
    }

    function open(idx) {
      cursor = Math.max(0, Math.min(anchors.length - 1, idx));
      const a = anchors[cursor];
      imgEl.src = a.getAttribute("href");
      imgEl.alt = captionFor(a);
      const num = numFor(a, cursor);
      metaEl.innerHTML =
        `<span class="num">slide ${num}</span>${cursor + 1} / ${anchors.length}`;
      lightbox.classList.add("open");
      lightbox.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
    }

    function close() {
      lightbox.classList.remove("open");
      lightbox.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
    }

    function step(delta) { open(cursor + delta); }

    anchors.forEach((a, i) => {
      a.addEventListener("click", (ev) => {
        ev.preventDefault();
        open(i);
      });
    });

    closeBtn?.addEventListener("click", close);
    lightbox.addEventListener("click", (ev) => {
      if (ev.target === lightbox) close();
    });
    prevBtn?.addEventListener("click", (ev) => { ev.stopPropagation(); step(-1); });
    nextBtn?.addEventListener("click", (ev) => { ev.stopPropagation(); step(1); });

    document.addEventListener("keydown", (ev) => {
      if (!lightbox.classList.contains("open")) return;
      if (ev.key === "Escape") close();
      else if (ev.key === "ArrowLeft") step(-1);
      else if (ev.key === "ArrowRight") step(1);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
