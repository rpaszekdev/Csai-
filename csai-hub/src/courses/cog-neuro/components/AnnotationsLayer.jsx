import { useCallback, useEffect, useRef, useState } from "react";
import {
  addAnnotation,
  listAnnotations,
  removeAnnotation,
  updateAnnotation,
} from "../lib/annotations";

function findTextNode(root, snippet) {
  const needle = snippet.replace(/\s+/g, " ").trim();
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

// Wrap the user's live drag-selection in a `<mark>` so the yellow stays
// visible after focus moves into the popover textarea (where the native
// ::selection would otherwise vanish). For selections that span multiple
// text nodes (e.g. across `<strong>`), wrap each segment.
function wrapPendingRange(range) {
  const created = [];
  try {
    const m = document.createElement("mark");
    m.className = "annot-mark annot-mark-pending";
    range.surroundContents(m);
    created.push(m);
    return created;
  } catch {
    // fall through to multi-node walk
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
      // skip mixed-element segments
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
        // snippet spans element boundaries — skip silently.
      }
      break;
    }
  }
}

// Compute the popover's vertical offset within the .editorial container so
// the input sits in the right gutter at the same vertical band as the mark.
function computePopoverTop(markEl, bodyEl) {
  if (!markEl || !bodyEl) return 0;
  const editorial = bodyEl.closest(".editorial") || bodyEl.parentElement;
  if (!editorial) return 0;
  const m = markEl.getBoundingClientRect();
  const e = editorial.getBoundingClientRect();
  return Math.max(0, m.top - e.top);
}

// Parent (NotesView) passes `key={sectionId}` so this component remounts
// on every section change — that lets us seed `annotations` from
// localStorage in the useState initializer instead of resetting it inside
// a useEffect (which the React 19 lint rule rightly flags).
export default function AnnotationsLayer({ sectionId, bodyRef, markdown }) {
  const [annotations, setAnnotations] = useState(() =>
    listAnnotations(sectionId),
  );
  const [panelOpen, setPanelOpen] = useState(false);
  // popover: { mode: 'new' | 'edit', snippet, top, annotId? }
  const [popover, setPopover] = useState(null);
  const [draftNote, setDraftNote] = useState("");
  const inputRef = useRef(null);
  const pendingMarksRef = useRef([]);

  // Keep a ref to the latest annotations so the body click delegate can read
  // current state without re-binding on every change.
  const annotationsRef = useRef(annotations);
  useEffect(() => {
    annotationsRef.current = annotations;
  }, [annotations]);

  const dismissPopover = useCallback(() => {
    unwrapMarks(pendingMarksRef.current);
    pendingMarksRef.current = [];
    setPopover(null);
    setDraftNote("");
  }, []);

  // Re-apply yellow highlights to the rendered body whenever annotations
  // change OR the body content is re-rendered (section switch). ReactMarkdown
  // produces a fresh subtree on each render, so we clear stale marks first.
  useEffect(() => {
    const body = bodyRef.current;
    if (!body) return;
    clearMarks(body);
    applyMarks(body, annotations);
    return () => clearMarks(body);
  }, [bodyRef, annotations, markdown, sectionId]);

  // Drag-select inside the body opens a "new" popover anchored to the new mark.
  // Click on a saved mark opens an "edit" popover preloaded with its note.
  useEffect(() => {
    const body = bodyRef.current;
    if (!body) return;

    const onMouseUp = (event) => {
      // Ignore if user clicked an existing mark — that's handled by onClick.
      if (event.target?.closest?.("mark.annot-mark")) return;

      const sel = window.getSelection();
      if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;
      const range = sel.getRangeAt(0);
      if (!body.contains(range.commonAncestorContainer)) return;

      const text = sel.toString().trim();
      if (text.length < 4) return;

      unwrapMarks(pendingMarksRef.current);
      pendingMarksRef.current = wrapPendingRange(range.cloneRange());
      sel.removeAllRanges();

      const anchorEl = pendingMarksRef.current[0];
      const top = computePopoverTop(anchorEl, body);
      setPopover({ mode: "new", snippet: text, top });
      setDraftNote("");
    };

    const onClick = (event) => {
      const mark = event.target?.closest?.("mark.annot-mark");
      if (!mark || !body.contains(mark)) return;
      if (mark.classList.contains("annot-mark-pending")) return;
      const id = mark.dataset.annotId;
      if (!id) return;
      const annot = annotationsRef.current.find((a) => a.id === id);
      if (!annot) return;
      event.stopPropagation();

      // Clear any pending state from a prior selection.
      unwrapMarks(pendingMarksRef.current);
      pendingMarksRef.current = [];

      const top = computePopoverTop(mark, body);
      setPopover({
        mode: "edit",
        annotId: id,
        snippet: annot.snippet,
        top,
      });
      setDraftNote(annot.note || "");
    };

    document.addEventListener("mouseup", onMouseUp);
    body.addEventListener("click", onClick);
    return () => {
      document.removeEventListener("mouseup", onMouseUp);
      body.removeEventListener("click", onClick);
    };
  }, [bodyRef]);

  // Dismiss popover when clicking anywhere outside it. Saved marks survive —
  // dismissPopover only unwraps `pending` marks (because clearMarks/applyMarks
  // is keyed to annotations, which haven't changed).
  useEffect(() => {
    if (!popover) return;
    const onDocDown = (e) => {
      if (e.target.closest(".annot-popover")) return;
      // Click on a saved mark routes through the body click handler, which
      // re-opens the popover for that mark.
      if (e.target.closest("mark.annot-mark:not(.annot-mark-pending)")) return;
      dismissPopover();
    };
    document.addEventListener("mousedown", onDocDown);
    return () => document.removeEventListener("mousedown", onDocDown);
  }, [popover, dismissPopover]);

  const handleSave = useCallback(() => {
    if (!popover) return;
    if (popover.mode === "edit" && popover.annotId) {
      updateAnnotation(sectionId, popover.annotId, { note: draftNote });
    } else {
      addAnnotation(sectionId, {
        snippet: popover.snippet,
        note: draftNote,
      });
    }
    refresh();
    setPanelOpen(true);
    dismissPopover();
    window.getSelection()?.removeAllRanges();
  }, [popover, draftNote, sectionId, dismissPopover, refresh]);

  const handleDeleteCurrent = useCallback(() => {
    if (popover?.mode !== "edit" || !popover.annotId) return;
    removeAnnotation(sectionId, popover.annotId);
    refresh();
    dismissPopover();
  }, [popover, sectionId, dismissPopover, refresh]);

  const handleJump = useCallback(
    (snippet) => {
      const node = findTextNode(bodyRef.current, snippet);
      if (!node || !node.parentElement) return;
      node.parentElement.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      flashElement(node.parentElement);
    },
    [bodyRef],
  );

  const handleRemove = useCallback(
    (id) => {
      removeAnnotation(sectionId, id);
      refresh();
    },
    [sectionId, refresh],
  );

  return (
    <>
      {popover && (
        <div
          className="annot-popover"
          style={{ top: popover.top }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <div className="annot-popover-snippet">
            "
            {popover.snippet.length > 90
              ? popover.snippet.slice(0, 90) + "…"
              : popover.snippet}
            "
          </div>
          <textarea
            ref={inputRef}
            className="annot-popover-input"
            placeholder={
              popover.mode === "edit" ? "Edit note…" : "Add a note (optional)…"
            }
            rows={3}
            value={draftNote}
            onChange={(e) => setDraftNote(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                handleSave();
              }
              if (e.key === "Escape") dismissPopover();
            }}
            autoFocus
          />
          <div className="annot-popover-actions">
            {popover.mode === "edit" && (
              <button
                type="button"
                className="annot-popover-delete"
                onClick={handleDeleteCurrent}
                title="Remove annotation"
              >
                Delete
              </button>
            )}
            <button type="button" onClick={dismissPopover}>
              Cancel
            </button>
            <button
              type="button"
              className="annot-popover-save"
              onClick={handleSave}
            >
              {popover.mode === "edit" ? "Update" : "Save"}
            </button>
          </div>
        </div>
      )}

      <aside
        className={`annot-panel ${panelOpen ? "open" : "closed"}`}
        aria-label="Saved annotations"
      >
        <button
          type="button"
          className="annot-panel-toggle"
          onClick={() => setPanelOpen((v) => !v)}
        >
          <span className="annot-panel-icon">✎</span>
          <span className="annot-panel-count">{annotations.length}</span>
          <span className="annot-panel-label">notes</span>
        </button>

        {panelOpen && (
          <div className="annot-panel-list">
            {annotations.length === 0 ? (
              <div className="annot-panel-empty">
                Highlight any text below to start annotating.
              </div>
            ) : (
              annotations.map((a) => (
                <div key={a.id} className="annot-card">
                  <button
                    type="button"
                    className="annot-card-jump"
                    onClick={() => handleJump(a.snippet)}
                    title="Jump to source"
                  >
                    <div className="annot-card-snippet">"{a.snippet}"</div>
                    {a.note && <div className="annot-card-note">{a.note}</div>}
                  </button>
                  <button
                    type="button"
                    className="annot-card-remove"
                    aria-label="Delete annotation"
                    onClick={() => handleRemove(a.id)}
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        )}
      </aside>
    </>
  );
}
