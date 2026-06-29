// summaries.js — loads the visual exam-summary data files (one JSON per topic)
// and exposes them to the shell. Each JSON follows the SUMMARY_DATA schema from
// the design (eyebrow/title/sub/podcast/source/sections[]). Pure data; the
// SummaryView component owns all rendering.

const modules = import.meta.glob(
  "../courses/deep-learn/data/summaries/*-summary.json",
  { eager: true },
);

// Canonical topic order for the sidebar.
const ORDER = [
  "mlps",
  "backpropagation",
  "optimizers",
  "cnns",
  "regularization",
  "rnns",
  "transformers",
  "computer-vision",
];

const BY_SLUG = {};
for (const mod of Object.values(modules)) {
  const data = mod.default ?? mod;
  if (data && data.slug) BY_SLUG[data.slug] = Object.freeze(data);
}

/** Lightweight list { slug, title } in canonical order (only those present). */
export function listSummaries() {
  const known = ORDER.filter((s) => BY_SLUG[s]);
  const extra = Object.keys(BY_SLUG).filter((s) => !ORDER.includes(s));
  return [...known, ...extra].map((slug) => ({
    slug,
    title: BY_SLUG[slug].title,
  }));
}

/** Full summary data for a slug, or null. */
export function getSummary(slug) {
  return BY_SLUG[slug] ?? null;
}
