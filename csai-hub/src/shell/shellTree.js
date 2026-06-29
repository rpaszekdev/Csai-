// shellTree.js — pure builders for the VS Code-style file tree and the tab bar.
//
// Faithful port of the prototype's `renderVals()` tree section. Each builder
// takes the current view state plus a bag of handlers and returns plain row
// descriptors; no React, no mutation. The component maps these to elements.

const INDENT = 18;
const BASE_PAD = 12;

function pad(depth) {
  return `${BASE_PAD + depth * INDENT}px`;
}

/**
 * Build the sidebar file-tree rows.
 *
 * @param {object} ctx
 * @param {string} ctx.open        currently open file/view id
 * @param {object} ctx.expanded    folder-key -> boolean expanded map
 * @param {number} ctx.dlLesson    active deep-learning lesson index
 * @param {Array}  ctx.topics      getTopics() descriptors { topic, slug, ... }
 * @param {object} handlers        { onToggle, onOpenFile, onOpenDlLesson }
 * @returns {Array} row descriptors
 */
export function buildFileRows(ctx, handlers) {
  const {
    open,
    expanded,
    dlLesson,
    topics,
    progress = {},
    summaries = [],
    summarySlug,
  } = ctx;
  const {
    onToggle,
    onOpenFile,
    onOpenDlLesson,
    onOpenQuizLesson,
    onOpenSummary,
  } = handlers;
  const rows = [];

  const folder = (key, label, depth) => {
    const ex = !!expanded[key];
    rows.push({
      key,
      label,
      pad: pad(depth),
      chev: ex ? "hn-angle-down" : "hn-angle-right",
      chevOp: 1,
      icon: ex ? "hn-folder-open" : "hn-folder",
      iconColor: "var(--ink)",
      fg: "var(--ink)",
      weight: 700,
      bg: "transparent",
      mark: "transparent",
      onClick: () => onToggle(key),
    });
    return ex;
  };

  const file = (id, label, depth, icon) => {
    const active = open === id;
    rows.push({
      key: id,
      label,
      pad: pad(depth),
      chev: "hn-blank",
      chevOp: 0,
      icon,
      iconColor: active ? "var(--ink)" : "var(--mute)",
      fg: "var(--ink)",
      weight: active ? 700 : 400,
      bg: active ? "var(--sel)" : "transparent",
      mark: active ? "var(--ink)" : "transparent",
      onClick: () => onOpenFile(id),
    });
  };

  // ---- deep-learning branch (real data) ----
  // Faithful to the v3 design: quizzes are individual .mc files (one per topic
  // plus the exam set) in a "quizzes" folder; the "lectures" folder holds the
  // .dl reader files (exam excluded — it has no lecture).
  if (folder("deeplearn", "deep-learning", 0)) {
    if (folder("dlquizzes", "quizzes", 1)) {
      topics.forEach((t, i) => {
        const active = open === "quiz" && dlLesson === i;
        const isExam = t.slug === "exam";
        const total = t.count || 0;
        const answered = Object.keys(progress[i] || {}).length;
        const done = total > 0 && answered >= total;
        const prog = done ? "" : answered > 0 ? `${answered}/${total}` : "";
        rows.push({
          key: `dlq${i}`,
          label: isExam ? "exam.mc" : `l${i + 1}-${t.slug}.mc`,
          pad: pad(2),
          chev: "hn-blank",
          chevOp: 0,
          icon: "hn-check-list",
          iconColor: active ? "var(--ink)" : "var(--mute)",
          fg: "var(--ink)",
          weight: active ? 700 : 400,
          bg: active ? "var(--sel)" : "transparent",
          mark: active ? "var(--ink)" : "transparent",
          prog,
          tagIcon: done ? "hn-check" : null,
          onClick: () => onOpenQuizLesson(i),
        });
      });
    }
    if (folder("dllectures", "lectures", 1)) {
      topics.forEach((t, i) => {
        if (t.slug === "exam") return; // exam has no lecture reader
        const active = open === "dllecture" && dlLesson === i;
        rows.push({
          key: `dll${i}`,
          label: `l${i + 1}-${t.slug}.dl`,
          pad: pad(2),
          chev: "hn-blank",
          chevOp: 0,
          icon: "hn-book",
          iconColor: active ? "var(--ink)" : "var(--mute)",
          fg: "var(--ink)",
          weight: active ? 700 : 400,
          bg: active ? "var(--sel)" : "transparent",
          mark: active ? "var(--ink)" : "transparent",
          prog: "",
          onClick: () => onOpenDlLesson(i),
        });
      });
    }
    if (folder("dlsummaries", "summaries", 1)) {
      summaries.forEach((s, i) => {
        const active = open === "summary" && summarySlug === s.slug;
        rows.push({
          key: `dls${i}`,
          label: `${s.slug}.md`,
          pad: pad(2),
          chev: "hn-blank",
          chevOp: 0,
          icon: "hn-copy",
          iconColor: active ? "var(--ink)" : "var(--mute)",
          fg: "var(--ink)",
          weight: active ? 700 : 400,
          bg: active ? "var(--sel)" : "transparent",
          mark: active ? "var(--ink)" : "transparent",
          prog: "",
          onClick: () => onOpenSummary(s.slug),
        });
      });
    }
  }

  // ---- cognitive-neuroscience branch (sample content for v1) ----
  if (folder("cogneuro", "cognitive-neuroscience", 0)) {
    file("dashboard", "overview.md", 1, "hn-chart-network");
    if (folder("m3", "module-3-memory", 1)) {
      file("m3l1", "memory-systems.lec", 2, "hn-notebook");
      file("m3l2", "learning-plasticity.lec", 2, "hn-notebook");
    }
    if (folder("m4", "module-4-emotion", 1)) {
      file("m4l1", "emotion-social.lec", 2, "hn-notebook");
    }
    file("notes", "notes.txt", 1, "hn-notebook");
  }

  return rows;
}

// Tab metadata: label + icon for every id that can appear as an editor tab.
export const TAB_FILES = Object.freeze({
  dllecture: { label: "lecture.dl", icon: "hn-book" },
  dashboard: { label: "overview.md", icon: "hn-chart-network" },
  quiz: { label: "quizzes.mc", icon: "hn-check-list" },
  summary: { label: "summary.md", icon: "hn-copy" },
  m3l1: { label: "memory-systems.lec", icon: "hn-notebook" },
  m3l2: { label: "learning-plasticity.lec", icon: "hn-notebook" },
  m4l1: { label: "emotion-social.lec", icon: "hn-notebook" },
  notes: { label: "notes.txt", icon: "hn-notebook" },
});

/**
 * Build the tab display descriptors from the ordered tab id list. Click and
 * drag handlers are wired in the component (event handlers, not here) so the
 * builder stays a pure view-model transform.
 *
 * @param {string[]} tabIds   ordered open-tab ids
 * @param {string}   open     active tab id
 */
export function buildTabs(tabIds, open) {
  return tabIds.map((id) => {
    const meta = TAB_FILES[id] || { icon: "hn-notebook", label: id };
    const active = open === id;
    return {
      id,
      label: meta.label,
      icon: meta.icon,
      iconColor: active ? "var(--ink)" : "var(--mute)",
      fg: active ? "var(--ink)" : "var(--mute)",
      weight: active ? 700 : 400,
      ind: active ? "var(--ink)" : "transparent",
    };
  });
}
