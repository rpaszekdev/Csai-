// Cog-neuro lecture lightbox — generalised port of the auto-sys lightbox.
// Listens for clicks on any `<a href*="study-images/M0X_LX_images/…">` (or any
// `<a class="lightbox-link">`) inside the article and shows a fullscreen viewer.
// ESC / arrow keys / backdrop / close button to dismiss.

(function () {
  const lightbox = document.getElementById("lightbox");
  if (!lightbox) return;

  const lightboxImg = document.getElementById("lightboxImg");
  const lightboxMeta = document.getElementById("lightboxMeta");
  const lightboxClose = document.getElementById("lightboxClose");
  const lightboxPrev = document.getElementById("lightboxPrev");
  const lightboxNext = document.getElementById("lightboxNext");

  // Collect every slide link inside the article (in DOM order). Each one
  // points to a slide image — we navigate this list with prev / next.
  function gatherSlides() {
    return Array.from(
      document.querySelectorAll(
        'article a[href*="/cog-neuro/study-images/"], article a[href*="/cog-neuro/slides/"]',
      ),
    );
  }

  let slides = [];
  let currentIndex = 0;

  function open(href, idx) {
    if (idx == null) {
      slides = gatherSlides();
      idx = slides.findIndex((a) => a.href === href || a.getAttribute("href") === href);
      if (idx < 0) idx = 0;
    } else {
      slides = gatherSlides();
    }
    currentIndex = Math.max(0, Math.min(slides.length - 1, idx));
    const link = slides[currentIndex];
    if (!link) return;
    lightboxImg.src = link.href;
    lightboxImg.alt = link.querySelector("img")?.alt || "Slide";
    if (lightboxMeta) {
      const slideNum = (link.dataset.slide || "").toString();
      lightboxMeta.innerHTML = slideNum
        ? `<span class="num">slide ${slideNum.padStart(2, "0")}</span>${currentIndex + 1} / ${slides.length}`
        : `${currentIndex + 1} / ${slides.length}`;
    }
    lightbox.classList.add("open");
    lightbox.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function close() {
    lightbox.classList.remove("open");
    lightbox.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  function step(delta) {
    if (!slides.length) return;
    currentIndex = (currentIndex + delta + slides.length) % slides.length;
    const link = slides[currentIndex];
    if (!link) return;
    lightboxImg.src = link.href;
    lightboxImg.alt = link.querySelector("img")?.alt || "Slide";
    if (lightboxMeta) {
      const slideNum = (link.dataset.slide || "").toString();
      lightboxMeta.innerHTML = slideNum
        ? `<span class="num">slide ${slideNum.padStart(2, "0")}</span>${currentIndex + 1} / ${slides.length}`
        : `${currentIndex + 1} / ${slides.length}`;
    }
  }

  // Click delegation — any anchor pointing to a cog-neuro slide image
  document.addEventListener("click", (e) => {
    const link = e.target.closest(
      'a[href*="/cog-neuro/study-images/"], a[href*="/cog-neuro/slides/"]',
    );
    if (!link) return;
    if (!link.closest("article")) return;
    e.preventDefault();
    open(link.href);
  });

  if (lightboxClose) lightboxClose.addEventListener("click", close);
  lightbox.addEventListener("click", (e) => {
    if (e.target === lightbox) close();
  });
  if (lightboxPrev) lightboxPrev.addEventListener("click", (e) => { e.stopPropagation(); step(-1); });
  if (lightboxNext) lightboxNext.addEventListener("click", (e) => { e.stopPropagation(); step(1); });

  document.addEventListener("keydown", (e) => {
    if (!lightbox.classList.contains("open")) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowLeft") step(-1);
    else if (e.key === "ArrowRight") step(1);
  });
})();
