/* ═════════════════════════════════════════════════════════════════════
   Shared annotations — drop-in module for any course lecture page.

   Usage:
     <link rel="stylesheet" href="/shared/annotations/annotations.css" />
     <article data-annot-scope="cog-neuro:m1_l1">…</article>
     <script src="/shared/annotations/annotations.js" defer></script>

   The script auto-mounts on the first element with `data-annot-scope`.
   The scope value becomes the storage key suffix:
     localStorage["annot:cog-neuro:m1_l1"] = […]
     localStorage["annot:auto-sys:lecture-01"] = […]

   Reads legacy per-course keys (`<course>:annot:<id>`) on first load and
   migrates them to the unified namespace, so existing notes carry over.

   Behaviour mirrors the (deprecated) per-course implementations:
     • drag-select → yellow <mark> + popover below the highlight
     • Enter saves, Shift+Enter newline, Escape cancels
     • click a saved mark → re-open its note in edit mode
     • viewport-pinned thumbnail menu (top-right) when ≥1 note exists
     • clicking a menu entry → scroll into view + open in edit mode
   ═════════════════════════════════════════════════════════════════════ */

(function () {
  "use strict";

  const STORAGE_PREFIX = "annot:";
  const POPOVER_BELOW_GAP = 8;
  const MIN_SELECTION_LEN = 4;

  // ─── Per-instance state. The module is single-mount — only one
  // [data-annot-scope] host is supported per page (which fits both courses).
  let scopeId = null;
  let bodyEl = null;
  let popoverEl = null;
  let panelEl = null;
  let panelOpen = false;
  let popoverState = null; // { mode, snippet, top, annotId? }
  let pendingMarks = [];

  // ─── Storage ──────────────────────────────────────────────────────────
  function storageKey(scope) {
    return STORAGE_PREFIX + scope;
  }

  // Legacy per-course keys looked like "<courseSlug>:annot:<sectionId>".
  // Given a unified scope of "<courseSlug>:<sectionId>", derive the old
  // key shape so we can migrate any existing notes once.
  function legacyKeyFor(scope) {
    const idx = scope.indexOf(":");
    if (idx < 0) return null;
    return scope.slice(0, idx) + ":annot:" + scope.slice(idx + 1);
  }

  function readAll() {
    if (!scopeId) return [];
    try {
      const raw = localStorage.getItem(storageKey(scopeId));
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function writeAll(list) {
    if (!scopeId) return;
    try {
      localStorage.setItem(storageKey(scopeId), JSON.stringify(list));
    } catch {
      /* quota / serialization — best effort. */
    }
  }

  function migrateLegacyOnce() {
    if (!scopeId) return;
    const newKey = storageKey(scopeId);
    const old = legacyKeyFor(scopeId);
    if (!old) return;
    if (localStorage.getItem(newKey) !== null) return;
    const legacyValue = localStorage.getItem(old);
    if (!legacyValue) return;
    try {
      const parsed = JSON.parse(legacyValue);
      if (Array.isArray(parsed)) {
        localStorage.setItem(newKey, legacyValue);
      }
    } catch {
      /* ignore — leave legacy data in place. */
    }
  }

  function listAnnotations() {
    return readAll()
      .slice()
      .sort((a, b) => a.ts - b.ts);
  }

  function addAnnotation({ snippet, note }) {
    const trimmedSnippet = String(snippet || "").trim();
    if (!trimmedSnippet) return null;
    const entry = {
      id:
        "a_" +
        Date.now().toString(36) +
        "_" +
        Math.random().toString(36).slice(2, 7),
      snippet: trimmedSnippet.slice(0, 280),
      note: String(note || "")
        .trim()
        .slice(0, 1000),
      ts: Date.now(),
    };
    const list = readAll();
    list.push(entry);
    writeAll(list);
    return entry;
  }

  function updateAnnotation(id, patch) {
    const next = readAll().map((a) =>
      a.id === id
        ? Object.assign({}, a, {
            ...(patch.note !== undefined && {
              note: String(patch.note).trim().slice(0, 1000),
            }),
          })
        : a,
    );
    writeAll(next);
  }

  function removeAnnotation(id) {
    writeAll(readAll().filter((a) => a.id !== id));
  }

  // ─── DOM helpers ──────────────────────────────────────────────────────
  function unwrapMarks(marks) {
    for (const m of marks) {
      const parent = m.parentNode;
      if (!parent) continue;
      while (m.firstChild) parent.insertBefore(m.firstChild, m);
      parent.removeChild(m);
      parent.normalize();
    }
  }

  function clearMarks(root) {
    if (!root) return;
    unwrapMarks(Array.from(root.querySelectorAll("mark.annot-mark")));
  }

  function findTextNode(root, snippet) {
    const needle = String(snippet || "")
      .replace(/\s+/g, " ")
      .trim();
    if (!needle || !root) return null;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    let node;
    while ((node = walker.nextNode())) {
      const haystack = node.nodeValue.replace(/\s+/g, " ");
      if (haystack.includes(needle)) return node;
    }
    return null;
  }

  function flashElement(el) {
    el.classList.add("annot-flash");
    setTimeout(() => el.classList.remove("annot-flash"), 1600);
  }

  function wrapPendingRange(range) {
    const created = [];
    try {
      const m = document.createElement("mark");
      m.className = "annot-mark annot-mark-pending";
      range.surroundContents(m);
      created.push(m);
      return created;
    } catch {
      // multi-node fallback below
    }

    const ancestor = range.commonAncestorContainer;
    if (!ancestor || ancestor.nodeType !== Node.ELEMENT_NODE) return created;

    const startContainer = range.startContainer;
    const endContainer = range.endContainer;
    const startOffset = range.startOffset;
    const endOffset = range.endOffset;

    const walker = document.createTreeWalker(ancestor, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) =>
        range.intersectsNode(n)
          ? NodeFilter.FILTER_ACCEPT
          : NodeFilter.FILTER_REJECT,
    });
    const textNodes = [];
    let n;
    while ((n = walker.nextNode())) textNodes.push(n);

    for (const t of textNodes) {
      const s = t === startContainer ? startOffset : 0;
      const e = t === endContainer ? endOffset : t.nodeValue.length;
      if (s >= e) continue;
      try {
        const r = document.createRange();
        r.setStart(t, s);
        r.setEnd(t, e);
        const m = document.createElement("mark");
        m.className = "annot-mark annot-mark-pending";
        r.surroundContents(m);
        created.push(m);
      } catch {
        /* skip mixed-element segment */
      }
    }
    return created;
  }

  function applyMarks(root, annotations) {
    if (!root || !annotations.length) return;
    for (const a of annotations) {
      const needle = String(a.snippet || "").trim();
      if (!needle) continue;
      const walker = document.createTreeWalker(
        root,
        NodeFilter.SHOW_TEXT,
        null,
      );
      let node;
      while ((node = walker.nextNode())) {
        if (node.parentElement?.closest?.("mark.annot-mark")) continue;
        const idx = node.nodeValue.indexOf(needle);
        if (idx < 0) continue;
        try {
          const range = document.createRange();
          range.setStart(node, idx);
          range.setEnd(node, idx + needle.length);
          const mark = document.createElement("mark");
          mark.className = "annot-mark";
          mark.dataset.annotId = a.id;
          range.surroundContents(mark);
        } catch {
          /* spans element boundaries — skip silently. */
        }
        break;
      }
    }
  }

  // Anchor popover BELOW the highlight so the yellow band stays visible
  // while typing. For multi-line marks, the bounding rect's bottom is the
  // bottom of the last visual line, which is what we want.
  function computePopoverTop(markEl) {
    if (!markEl) return 0;
    const rect = markEl.getBoundingClientRect();
    return Math.max(0, rect.bottom + window.scrollY + POPOVER_BELOW_GAP);
  }

  // ─── Popover ──────────────────────────────────────────────────────────
  function dismissPopover() {
    unwrapMarks(pendingMarks);
    pendingMarks = [];
    popoverState = null;
    if (popoverEl) {
      popoverEl.remove();
      popoverEl = null;
    }
    renderPanel();
  }

  function openPopover(state, opts) {
    popoverState = state;
    renderPopover(opts && opts.draftNote ? opts.draftNote : "");
    renderPanel(); // hide panel while popover is up
  }

  function renderPopover(initialDraft) {
    if (!popoverState) {
      if (popoverEl) {
        popoverEl.remove();
        popoverEl = null;
      }
      return;
    }
    if (!popoverEl) {
      popoverEl = document.createElement("div");
      popoverEl.className = "annot-popover";
      document.body.appendChild(popoverEl);
    }
    popoverEl.style.top = popoverState.top + "px";

    const { snippet, mode } = popoverState;
    const truncated =
      snippet.length > 90 ? snippet.slice(0, 90) + "…" : snippet;
    const placeholder =
      mode === "edit" ? "Edit note…" : "Add a note (optional)…";
    const saveLabel = mode === "edit" ? "Update" : "Save";
    const deleteBtn =
      mode === "edit"
        ? '<button type="button" class="annot-popover-delete">Delete</button>'
        : "";

    popoverEl.innerHTML =
      '<div class="annot-popover-snippet">"' +
      escapeHtml(truncated) +
      '"</div>' +
      '<textarea class="annot-popover-input" rows="3" placeholder="' +
      escapeAttr(placeholder) +
      '"></textarea>' +
      '<div class="annot-popover-actions">' +
      deleteBtn +
      '<button type="button" class="annot-popover-cancel">Cancel</button>' +
      '<button type="button" class="annot-popover-save" title="' +
      escapeAttr(saveLabel + " note (Enter)") +
      '">' +
      saveLabel +
      ' <span class="annot-popover-kbd" aria-hidden="true">⏎</span>' +
      "</button>" +
      "</div>";

    const ta = popoverEl.querySelector(".annot-popover-input");
    ta.value = initialDraft || "";
    ta.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSave(ta.value);
      }
      if (e.key === "Escape") dismissPopover();
    });
    setTimeout(() => ta.focus(), 0);

    popoverEl
      .querySelector(".annot-popover-cancel")
      .addEventListener("click", dismissPopover);
    popoverEl
      .querySelector(".annot-popover-save")
      .addEventListener("click", () => handleSave(ta.value));
    popoverEl.addEventListener("mousedown", (e) => e.stopPropagation());

    const del = popoverEl.querySelector(".annot-popover-delete");
    if (del) {
      del.addEventListener("click", () => {
        if (popoverState?.mode === "edit" && popoverState.annotId) {
          removeAnnotation(popoverState.annotId);
          dismissPopover();
          rerenderMarks();
          renderPanel();
        }
      });
    }
  }

  function handleSave(value) {
    if (!popoverState) return;
    if (popoverState.mode === "edit" && popoverState.annotId) {
      updateAnnotation(popoverState.annotId, { note: value });
    } else {
      addAnnotation({ snippet: popoverState.snippet, note: value });
    }
    dismissPopover();
    rerenderMarks();
    panelOpen = true;
    renderPanel();
    window.getSelection()?.removeAllRanges();
  }

  // ─── Thumbnail menu ───────────────────────────────────────────────────
  function renderPanel() {
    const annots = listAnnotations();
    if (annots.length === 0) {
      if (panelEl) {
        panelEl.remove();
        panelEl = null;
      }
      return;
    }
    if (!panelEl) {
      panelEl = document.createElement("aside");
      panelEl.setAttribute("aria-label", "Saved annotations");
      document.body.appendChild(panelEl);
    }
    panelEl.className =
      "annot-panel " +
      (panelOpen ? "open" : "closed") +
      (popoverState ? " annot-panel--hidden" : "");

    const toggleHtml =
      '<button type="button" class="annot-panel-toggle" title="' +
      (panelOpen ? "Hide notes" : "Show notes") +
      '">' +
      '<span class="annot-panel-icon">✎</span>' +
      '<span class="annot-panel-count">' +
      annots.length +
      "</span>" +
      '<span class="annot-panel-label">notes</span>' +
      "</button>";

    let listHtml = "";
    if (panelOpen) {
      listHtml += '<ol class="annot-panel-list">';
      annots.forEach((a, i) => {
        listHtml +=
          '<li class="annot-card" data-annot-id="' +
          escapeAttr(a.id) +
          '">' +
          '<button type="button" class="annot-card-jump" title="Open note in context">' +
          '<span class="annot-card-num">' +
          (i + 1) +
          "</span>" +
          '<span class="annot-card-body">' +
          '<span class="annot-card-snippet">' +
          escapeHtml(a.snippet) +
          "</span>" +
          (a.note
            ? '<span class="annot-card-note">' + escapeHtml(a.note) + "</span>"
            : "") +
          "</span>" +
          "</button>" +
          '<button type="button" class="annot-card-remove" aria-label="Delete annotation">×</button>' +
          "</li>";
      });
      listHtml += "</ol>";
    }

    panelEl.innerHTML = toggleHtml + listHtml;

    panelEl
      .querySelector(".annot-panel-toggle")
      .addEventListener("click", () => {
        panelOpen = !panelOpen;
        renderPanel();
      });

    panelEl.querySelectorAll(".annot-card").forEach((cardEl) => {
      const id = cardEl.dataset.annotId;
      const annot = annots.find((a) => a.id === id);
      cardEl
        .querySelector(".annot-card-jump")
        .addEventListener("click", () => navigateTo(annot));
      cardEl
        .querySelector(".annot-card-remove")
        .addEventListener("click", (e) => {
          e.stopPropagation();
          removeAnnotation(id);
          rerenderMarks();
          renderPanel();
        });
    });
  }

  function navigateTo(annotation) {
    if (!annotation || !bodyEl) return;
    unwrapMarks(pendingMarks);
    pendingMarks = [];

    const markEl = bodyEl.querySelector(
      'mark.annot-mark[data-annot-id="' + annotation.id + '"]',
    );
    let anchorEl = markEl;
    if (!anchorEl) {
      const node = findTextNode(bodyEl, annotation.snippet);
      anchorEl = node?.parentElement || null;
    }
    if (!anchorEl) return;

    anchorEl.scrollIntoView({ behavior: "smooth", block: "center" });
    flashElement(anchorEl);
    requestAnimationFrame(() => {
      const top = computePopoverTop(anchorEl);
      openPopover(
        {
          mode: "edit",
          annotId: annotation.id,
          snippet: annotation.snippet,
          top,
        },
        { draftNote: annotation.note || "" },
      );
    });
  }

  // ─── Event handlers ───────────────────────────────────────────────────
  function rerenderMarks() {
    if (!bodyEl) return;
    clearMarks(bodyEl);
    applyMarks(bodyEl, listAnnotations());
  }

  function onMouseUp(e) {
    if (e.target?.closest?.("mark.annot-mark")) return;
    if (e.target?.closest?.(".annot-popover")) return;
    if (e.target?.closest?.(".annot-panel")) return;

    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;
    const range = sel.getRangeAt(0);
    if (!bodyEl || !bodyEl.contains(range.commonAncestorContainer)) return;

    const text = sel.toString().trim();
    if (text.length < MIN_SELECTION_LEN) return;

    unwrapMarks(pendingMarks);
    pendingMarks = wrapPendingRange(range.cloneRange());
    sel.removeAllRanges();

    const anchor = pendingMarks[0];
    const top = computePopoverTop(anchor);
    openPopover({ mode: "new", snippet: text, top }, { draftNote: "" });
  }

  function onBodyClick(e) {
    const mark = e.target?.closest?.("mark.annot-mark");
    if (!mark || !bodyEl.contains(mark)) return;
    if (mark.classList.contains("annot-mark-pending")) return;
    const id = mark.dataset.annotId;
    if (!id) return;
    const annot = listAnnotations().find((a) => a.id === id);
    if (!annot) return;
    e.stopPropagation();
    unwrapMarks(pendingMarks);
    pendingMarks = [];
    const top = computePopoverTop(mark);
    openPopover(
      { mode: "edit", annotId: id, snippet: annot.snippet, top },
      { draftNote: annot.note || "" },
    );
  }

  function onDocumentMouseDown(e) {
    if (!popoverState) return;
    if (e.target.closest(".annot-popover")) return;
    if (e.target.closest("mark.annot-mark:not(.annot-mark-pending)")) return;
    dismissPopover();
  }

  // ─── Boot ─────────────────────────────────────────────────────────────
  function escapeHtml(s) {
    return String(s).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  }
  function escapeAttr(s) {
    return escapeHtml(s);
  }

  function init() {
    const host = document.querySelector("[data-annot-scope]");
    if (!host) return; // page didn't opt in.
    scopeId = host.getAttribute("data-annot-scope");
    if (!scopeId) return;
    bodyEl = host;

    migrateLegacyOnce();

    panelOpen = listAnnotations().length > 0;
    rerenderMarks();
    renderPanel();

    document.addEventListener("mouseup", onMouseUp);
    document.addEventListener("mousedown", onDocumentMouseDown);
    bodyEl.addEventListener("click", onBodyClick);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
