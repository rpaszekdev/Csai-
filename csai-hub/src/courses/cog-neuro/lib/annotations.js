// Annotation storage for cognitive-neuroscience lesson notes.
// One bucket per sectionId, persisted to localStorage so annotations survive
// reloads without needing a backend.

const KEY_PREFIX = "cog-neuro:annot:";

function key(sectionId) {
  return `${KEY_PREFIX}${sectionId}`;
}

function read(sectionId) {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(key(sectionId));
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function write(sectionId, list) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key(sectionId), JSON.stringify(list));
  } catch {
    // quota or serialization failure — best-effort, ignore.
  }
}

export function listAnnotations(sectionId) {
  return read(sectionId)
    .slice()
    .sort((a, b) => b.ts - a.ts);
}

export function addAnnotation(sectionId, { snippet, note }) {
  const trimmedSnippet = String(snippet || "").trim();
  if (!trimmedSnippet) return null;
  const entry = {
    id: `a_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
    snippet: trimmedSnippet.slice(0, 280),
    note: String(note || "")
      .trim()
      .slice(0, 1000),
    ts: Date.now(),
  };
  const next = [...read(sectionId), entry];
  write(sectionId, next);
  return entry;
}

export function removeAnnotation(sectionId, id) {
  const next = read(sectionId).filter((a) => a.id !== id);
  write(sectionId, next);
}

export function updateAnnotation(sectionId, id, patch) {
  const next = read(sectionId).map((a) =>
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
  write(sectionId, next);
}
