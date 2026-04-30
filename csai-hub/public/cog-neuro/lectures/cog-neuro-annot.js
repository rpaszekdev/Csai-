// Vanilla-JS port of cog-neuro's React AnnotationsLayer.
// Storage schema is identical to the React version
// (key: cog-neuro:annot:<sectionId>) so existing annotations carry over.

(function () {
  // ─── storage ───────────────────────────────────────────────────────────
  const KEY_PREFIX = "cog-neuro:annot:";
  const key = (sid) => `${KEY_PREFIX}${sid}`;

  function read(sid) {
    try {
      const raw = window.localStorage.getItem(key(sid));
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  function write(sid, list) {
    try {
      window.localStorage.setItem(key(sid), JSON.stringify(list));
    } catch {
      // quota / serialization — best-effort
    }
  }

  function listAnnotations(sid) {
    return read(sid).slice().sort((a, b) => b.ts - a.ts);
  }
  function addAnnotation(sid, { snippet, note }) {
    const trimmed = String(snippet || "").trim();
    if (!trimmed) return null;
    const entry = {
      id: `a_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
      snippet: trimmed.slice(0, 280),
      note: String(note || "").trim().slice(0, 1000),
      ts: Date.now(),
    };
    write(sid, [...read(sid), entry]);
    return entry;
  }
  function removeAnnotation(sid, id) {
    write(sid, read(sid).filter((a) => a.id !== id));
  }
  function updateAnnotation(sid, id, patch) {
    const next = read(sid).map((a) =>
      a.id === id
        ? {
            ...a,
            ...(patch.snippet !== undefined && {
              snippet: String(patch.snippet).trim().slice(0, 280),
            }),
            ...(patch.note !== undefined && {
              note: String(patch.note).trim().slice(0, 1000),
            }),
          }
        : a,
    );
    write(sid, next);
  }

  // ─── DOM helpers ───────────────────────────────────────────────────────
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

  function wrapPendingRange(range) {
    const created = [];
    try {
      const m = document.createElement("mark");
      m.className = "annot-mark annot-mark-pending";
      range.surroundContents(m);
      created.push(m);
      return created;
    } catch {
      // multi-node fallback
    }
    const ancestor = range.commonAncestorContainer;
    if (!ancestor || ancestor.nodeType !== Node.ELEMENT_NODE) return created;
    const startC = range.startContainer;
    const endC = range.endContainer;
    const startO = range.startOffset;
    const endO = range.endOffset;

    const walker = document.createTreeWalker(ancestor, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) =>
        range.intersectsNode(n) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT,
    });
    const textNodes = [];
    let n;
    while ((n = walker.nextNode())) textNodes.push(n);

    for (const t of textNodes) {
      const s = t === startC ? startO : 0;
      const e = t === endC ? endO : t.nodeValue.length;
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
        /* skip mixed-element segments */
      }
    }
    return created;
  }

  function applyMarks(root, annotations) {
    if (!root || !annotations.length) return;
    for (const a of annotations) {
      const needle = String(a.snippet || "").trim();
      if (!needle) continue;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
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
          /* snippet spans element boundaries — skip silently */
        }
        break;
      }
    }
  }

  function findTextNode(root, snippet) {
    const needle = (snippet || "").replace(/\s+/g, " ").trim();
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

  function computePopoverTop(markEl, contentEl) {
    if (!markEl || !contentEl) return 0;
    const m = markEl.getBoundingClientRect();
    const e = contentEl.getBoundingClientRect();
    return Math.max(0, m.top - e.top);
  }

  // ─── mount ─────────────────────────────────────────────────────────────
  function mount({ sectionId, contentEl, panelEl }) {
    if (!contentEl || !panelEl) return;
    const countEl = panelEl.querySelector(".annot-panel-count");
    const listEl = panelEl.querySelector(".annot-panel-list");
    const toggleBtn = panelEl.querySelector(".annot-panel-toggle");

    let annotations = listAnnotations(sectionId);
    let popoverEl = null;
    let popoverState = null;
    let pendingMarks = [];

    function refresh() {
      annotations = listAnnotations(sectionId);
      clearMarks(contentEl);
      applyMarks(contentEl, annotations);
      if (countEl) countEl.textContent = annotations.length;
      renderPanelList();
    }

    function renderPanelList() {
      if (!listEl) return;
      listEl.innerHTML = "";
      if (annotations.length === 0) {
        const empty = document.createElement("div");
        empty.className = "annot-panel-empty";
        empty.textContent = "Highlight any text to start annotating.";
        listEl.appendChild(empty);
        return;
      }
      for (const a of annotations) {
        const card = document.createElement("div");
        card.className = "annot-card";
        const jump = document.createElement("button");
        jump.type = "button";
        jump.className = "annot-card-jump";
        jump.title = "Jump to source";
        const snip = document.createElement("div");
        snip.className = "annot-card-snippet";
        snip.textContent = `"${a.snippet}"`;
        jump.appendChild(snip);
        if (a.note) {
          const note = document.createElement("div");
          note.className = "annot-card-note";
          note.textContent = a.note;
          jump.appendChild(note);
        }
        jump.addEventListener("click", () => {
          const node = findTextNode(contentEl, a.snippet);
          if (!node || !node.parentElement) return;
          node.parentElement.scrollIntoView({ behavior: "smooth", block: "center" });
          flashElement(node.parentElement);
        });
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "annot-card-remove";
        remove.setAttribute("aria-label", "Delete annotation");
        remove.textContent = "×";
        remove.addEventListener("click", () => {
          removeAnnotation(sectionId, a.id);
          refresh();
        });
        card.appendChild(jump);
        card.appendChild(remove);
        listEl.appendChild(card);
      }
    }

    function dismissPopover() {
      unwrapMarks(pendingMarks);
      pendingMarks = [];
      if (popoverEl) {
        popoverEl.remove();
        popoverEl = null;
      }
      popoverState = null;
    }

    function showPopover(state) {
      dismissPopover();
      popoverState = state;
      popoverEl = document.createElement("div");
      popoverEl.className = "annot-popover";
      popoverEl.style.top = `${state.top}px`;
      popoverEl.addEventListener("mousedown", (e) => e.stopPropagation());

      const snip = document.createElement("div");
      snip.className = "annot-popover-snippet";
      snip.textContent = `"${state.snippet.length > 90 ? state.snippet.slice(0, 90) + "…" : state.snippet}"`;
      popoverEl.appendChild(snip);

      const input = document.createElement("textarea");
      input.className = "annot-popover-input";
      input.rows = 3;
      input.placeholder = state.mode === "edit" ? "Edit note…" : "Add a note (optional)…";
      input.value = state.note || "";
      popoverEl.appendChild(input);

      const actions = document.createElement("div");
      actions.className = "annot-popover-actions";
      if (state.mode === "edit") {
        const del = document.createElement("button");
        del.type = "button";
        del.className = "annot-popover-delete";
        del.textContent = "Delete";
        del.addEventListener("click", () => {
          removeAnnotation(sectionId, state.annotId);
          dismissPopover();
          refresh();
        });
        actions.appendChild(del);
      }
      const cancel = document.createElement("button");
      cancel.type = "button";
      cancel.textContent = "Cancel";
      cancel.addEventListener("click", dismissPopover);
      actions.appendChild(cancel);

      const save = document.createElement("button");
      save.type = "button";
      save.className = "annot-popover-save";
      save.title = state.mode === "edit" ? "Update note (Enter)" : "Save note (Enter)";
      save.innerHTML = `${state.mode === "edit" ? "Update" : "Save"} <span class="annot-popover-kbd" aria-hidden="true">⏎</span>`;
      save.addEventListener("click", doSave);
      actions.appendChild(save);

      popoverEl.appendChild(actions);
      contentEl.appendChild(popoverEl);
      input.focus();

      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          doSave();
        }
        if (e.key === "Escape") dismissPopover();
      });

      function doSave() {
        const note = input.value;
        if (state.mode === "edit") {
          updateAnnotation(sectionId, state.annotId, { note });
        } else {
          addAnnotation(sectionId, { snippet: state.snippet, note });
          panelEl.classList.add("open");
        }
        dismissPopover();
        const sel = window.getSelection();
        if (sel) sel.removeAllRanges();
        refresh();
      }
    }

    // Drag-select inside contentEl → "new" popover
    document.addEventListener("mouseup", (event) => {
      if (event.target?.closest?.("mark.annot-mark")) return;
      if (event.target?.closest?.(".annot-popover")) return;
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;
      const range = sel.getRangeAt(0);
      if (!contentEl.contains(range.commonAncestorContainer)) return;
      const text = sel.toString().trim();
      if (text.length < 4) return;
      unwrapMarks(pendingMarks);
      pendingMarks = wrapPendingRange(range.cloneRange());
      sel.removeAllRanges();
      const anchor = pendingMarks[0];
      showPopover({
        mode: "new",
        snippet: text,
        top: computePopoverTop(anchor, contentEl),
      });
    });

    // Click on saved mark → "edit" popover
    contentEl.addEventListener("click", (event) => {
      const mark = event.target?.closest?.("mark.annot-mark");
      if (!mark || !contentEl.contains(mark)) return;
      if (mark.classList.contains("annot-mark-pending")) return;
      const id = mark.dataset.annotId;
      if (!id) return;
      event.stopPropagation();
      const annot = annotations.find((a) => a.id === id);
      if (!annot) return;
      unwrapMarks(pendingMarks);
      pendingMarks = [];
      showPopover({
        mode: "edit",
        annotId: id,
        snippet: annot.snippet,
        note: annot.note,
        top: computePopoverTop(mark, contentEl),
      });
    });

    // Dismiss popover on outside click
    document.addEventListener("mousedown", (e) => {
      if (!popoverEl) return;
      if (e.target.closest(".annot-popover")) return;
      if (e.target.closest("mark.annot-mark:not(.annot-mark-pending)")) return;
      dismissPopover();
    });

    // Panel toggle
    if (toggleBtn) {
      toggleBtn.addEventListener("click", (e) => {
        e.preventDefault();
        panelEl.classList.toggle("open");
      });
    }

    // Initial render — open the panel if there are existing annotations
    if (annotations.length > 0) panelEl.classList.add("open");
    refresh();
  }

  window.cogAnnot = {
    listAnnotations,
    addAnnotation,
    removeAnnotation,
    updateAnnotation,
    mount,
  };
})();
