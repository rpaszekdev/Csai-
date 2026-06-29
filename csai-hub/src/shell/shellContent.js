// shellContent.js — static sample content for the v1 shell.
//
// The cognitive-neuroscience dashboard + lecture/doc views keep the
// prototype's sample copy for v1 (this is a known gap; the real cog-neuro
// data lives behind /courses/cog-neuro). Where a real static lecture page
// exists under public/cog-neuro/lectures/, the doc view deep-links to it via
// COG_NEURO_DOCS[id].href so the sample card opens the real page.

// Deep-learning lecture "material" toggles (placeholder content per topic).
export const DL_MATERIALS = Object.freeze([
  Object.freeze({ key: "transcript", label: "TRANSCRIPT", icon: "hn-align-left" }),
  Object.freeze({ key: "chapter", label: "CHAPTER", icon: "hn-book" }),
  Object.freeze({ key: "pptx", label: "PPTX", icon: "hn-grid" }),
  Object.freeze({ key: "podcast", label: "PODCAST", icon: "hn-podcasts" }),
  Object.freeze({ key: "notes", label: "NOTES", icon: "hn-copy" }),
]);

// Real static cog-neuro lecture pages (served from public/cog-neuro/lectures).
const LECTURE_BASE = "/cog-neuro/lectures";

export const COG_NEURO_DOCS = Object.freeze({
  m3l1: Object.freeze({
    eyebrow: "Module 3 · Lecture 1",
    title: "MEMORY SYSTEMS",
    href: `${LECTURE_BASE}/m3_l1.html`,
    goals: Object.freeze([
      "Distinguish declarative vs. non-declarative memory",
      "Explain the hippocampus in consolidation",
      "Describe working memory & capacity limits",
      "Relate amnesia cases to brain structures",
    ]),
    body1:
      "Human memory is not a single store but a set of dissociable systems. Declarative (explicit) memory handles facts and events and depends heavily on medial temporal lobe structures — above all the hippocampus, which binds distributed cortical traces during consolidation.",
    body2:
      "Non-declarative (implicit) memory covers skills, priming and conditioning, supported by the basal ganglia, cerebellum and neocortex. Patient H.M. showed that bilateral hippocampal removal devastates new declarative learning while sparing motor-skill acquisition.",
  }),
  m3l2: Object.freeze({
    eyebrow: "Module 3 · Lecture 2",
    title: "LEARNING & PLASTICITY",
    href: `${LECTURE_BASE}/m3_l2.html`,
    goals: Object.freeze([
      "Define synaptic plasticity",
      "Explain LTP and LTD",
      "Connect Hebbian learning to circuits",
      "Describe critical periods",
    ]),
    body1:
      "Plasticity is the brain's capacity to reorganise in response to experience. Long-term potentiation (LTP) strengthens synapses that fire together, providing a cellular basis for Hebbian learning and memory formation.",
    body2:
      "Long-term depression (LTD) weakens unused connections, balancing the network. Together these mechanisms sculpt circuits during development and continue to support learning throughout life.",
  }),
  m4l1: Object.freeze({
    eyebrow: "Module 4 · Lecture 1",
    title: "EMOTION & SOCIAL",
    href: `${LECTURE_BASE}/m4_l1.html`,
    goals: Object.freeze([
      "Map core affect onto neural circuits",
      "Explain the amygdala in threat detection",
      "Describe theory-of-mind networks",
      "Connect emotion to decision-making",
    ]),
    body1:
      "Emotion arises from coordinated subcortical and cortical circuits. The amygdala rapidly evaluates salience and threat, modulating attention and memory through projections to the hippocampus and prefrontal cortex.",
    body2:
      "Social cognition recruits the temporoparietal junction and medial prefrontal cortex to represent others' mental states, letting us predict behaviour and integrate affect into decisions.",
  }),
  notes: Object.freeze({
    eyebrow: "Personal · Scratchpad",
    title: "NOTES",
    href: null,
    goals: Object.freeze([
      "Review H.M. case before final",
      "Re-watch LTP animation",
      "Summarise amygdala pathways",
      "Make flashcards for MTL anatomy",
    ]),
    body1:
      "Loose notes kept across the module. Consolidation seems to be the recurring theme in every lecture — hippocampus first, cortex later.",
    body2:
      "Exam is mostly applied: expect case studies rather than definitions. Focus on dissociations between memory systems and the structures that support each.",
  }),
});

// Cog-neuro dashboard lecture rows (sample). `href` deep-links to the real
// static page where one exists; `fileId` opens the in-shell doc view.
export const DASHBOARD_LECTURES = Object.freeze([
  Object.freeze({
    mod: "M1·L1",
    title: "History & Approaches",
    status: "DONE",
    icon: "hn-check",
    href: `${LECTURE_BASE}/m1_l1.html`,
  }),
  Object.freeze({
    mod: "M2·L2",
    title: "Attention",
    status: "DONE",
    icon: "hn-check",
    href: `${LECTURE_BASE}/m2_l2.html`,
  }),
  Object.freeze({
    mod: "M3·L1",
    title: "Memory Systems",
    status: "OPEN",
    icon: "hn-angle-right",
    fileId: "m3l1",
  }),
  Object.freeze({
    mod: "M4·L1",
    title: "Emotion & Social Cognition",
    status: "NOW",
    icon: "hn-play",
    fileId: "m4l1",
  }),
  Object.freeze({
    mod: "M5·L1",
    title: "Executive Function",
    status: "LOCKED",
    icon: "hn-lock",
    href: `${LECTURE_BASE}/m5_l1.html`,
  }),
]);

/** Deterministic podcast equalizer bars (36 bars, first 11 "played"). */
export function buildPodcastBars() {
  return Array.from({ length: 36 }, (_, i) => ({
    h: `${6 + Math.round(18 * Math.abs(Math.sin(i * 0.7)))}px`,
    bg: i < 11 ? "var(--ink)" : "var(--line)",
  }));
}
