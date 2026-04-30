// Hero-toggle panels for transcript / book chapter.
// Each .hero-tool button toggles a .hero-panel with id matched by
// data-toggle-panel. Text inside the panel is lazy-fetched on first reveal.
(function () {
  function fetchInto(pre) {
    if (pre.dataset.loaded === "1") return Promise.resolve(pre.textContent);
    var src = pre.getAttribute("data-src");
    if (!src) return Promise.resolve("");
    pre.dataset.loaded = "loading";
    pre.textContent = "Loading…";
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
    var prev = btn.textContent;
    var done = function (ok) {
      btn.textContent = ok ? "✓ copied" : "✗ failed";
      btn.classList.toggle("copied", ok);
      setTimeout(function () {
        btn.textContent = prev || "copy";
        btn.classList.remove("copied");
      }, 1400);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(
        function () {
          done(true);
        },
        function () {
          done(false);
        },
      );
      return;
    }
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

  // Toggle: hero buttons reveal/hide their target panel and fetch text on first open.
  document
    .querySelectorAll(".hero-tool[data-toggle-panel]")
    .forEach(function (btn) {
      var targetId = btn.getAttribute("data-toggle-panel");
      btn.addEventListener("click", function () {
        var panel = document.getElementById(targetId);
        if (!panel) return;
        var willOpen = panel.hasAttribute("hidden");
        // Close all other panels (one open at a time keeps the page tidy).
        document.querySelectorAll(".hero-panel").forEach(function (p) {
          p.setAttribute("hidden", "");
        });
        document.querySelectorAll(".hero-tool").forEach(function (b) {
          b.classList.remove("active");
        });
        if (willOpen) {
          panel.removeAttribute("hidden");
          btn.classList.add("active");
          var pre = panel.querySelector("pre.hero-panel-text");
          if (pre) fetchInto(pre);
          // Smooth-scroll panel into view.
          panel.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    });

  // Inline copy button inside each panel.
  document
    .querySelectorAll(".hero-panel-copy[data-copy-target]")
    .forEach(function (btn) {
      btn.addEventListener("click", function () {
        var pre = document.getElementById(btn.getAttribute("data-copy-target"));
        if (!pre) return;
        fetchInto(pre).then(function (txt) {
          if (txt) copyText(txt, btn);
        });
      });
    });

  // Close button (×) on each panel.
  document
    .querySelectorAll(".hero-panel-close[data-close]")
    .forEach(function (btn) {
      btn.addEventListener("click", function () {
        var panel = document.getElementById(btn.getAttribute("data-close"));
        if (panel) panel.setAttribute("hidden", "");
        document
          .querySelectorAll(
            '.hero-tool[data-toggle-panel="' +
              btn.getAttribute("data-close") +
              '"]',
          )
          .forEach(function (b) {
            b.classList.remove("active");
          });
      });
    });
})();
