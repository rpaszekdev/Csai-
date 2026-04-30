// Lazy-load transcript and book-chapter raw text into the lecture-extras
// <details> blocks. Each <pre data-src="..."> is prefetched once on page
// load so the [copy] button works instantly even before the user expands
// the section.
(function () {
  function fetchInto(pre) {
    if (pre.dataset.loaded === "1") return Promise.resolve(pre.textContent);
    var src = pre.getAttribute("data-src");
    if (!src) return Promise.resolve("");
    pre.dataset.loaded = "loading";
    if (!pre.textContent) pre.textContent = "Loading…";
    return fetch(src)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.text();
      })
      .then(function (txt) {
        pre.textContent = txt;
        pre.dataset.loaded = "1";
        return txt;
      })
      .catch(function (err) {
        pre.textContent = "Could not load: " + err.message;
        pre.dataset.loaded = "0";
        return "";
      });
  }

  function copyText(text, btn) {
    var done = function (ok) {
      var prev = btn.textContent;
      btn.textContent = ok ? "✓ copied" : "✗ failed";
      btn.classList.toggle("copied", ok);
      btn.classList.toggle("failed", !ok);
      setTimeout(function () {
        btn.textContent = prev || "copy";
        btn.classList.remove("copied", "failed");
      }, 1400);
    };

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(
        function () { done(true); },
        function () { done(false); },
      );
      return;
    }
    // Fallback: hidden textarea + execCommand.
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      var ok = document.execCommand("copy");
      document.body.removeChild(ta);
      done(ok);
    } catch (e) {
      done(false);
    }
  }

  // Wire up every fold: prefetch in background + add copy button.
  document.querySelectorAll(".extras-fold").forEach(function (det) {
    var pre = det.querySelector("pre.extras-text");
    var summary = det.querySelector("summary");
    if (!pre || !summary) return;

    // Add copy button to summary (skip if one already exists).
    if (!summary.querySelector(".extras-copy")) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "extras-copy";
      btn.textContent = "copy";
      btn.setAttribute("aria-label", "Copy text to clipboard");
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        // Make sure text is loaded before copying.
        fetchInto(pre).then(function (txt) {
          if (txt) copyText(txt, btn);
        });
      });
      summary.appendChild(btn);
    }

    // Auto-load on first expand (and prefetch transcripts immediately).
    det.addEventListener("toggle", function () {
      if (det.open) fetchInto(pre);
    });
  });

  // Eager-prefetch transcripts only — they're smaller (~70 KB) and the
  // user is likely to want to copy them. Book chapters (~150 KB+) stay
  // lazy until expanded or copied.
  document
    .querySelectorAll('.extras-fold pre.extras-text[data-src*="/transcripts/"]')
    .forEach(fetchInto);
})();
