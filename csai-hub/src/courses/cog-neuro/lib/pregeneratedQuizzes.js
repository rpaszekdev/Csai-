const quizModules = import.meta.glob("../data/quizzes/*.json", { eager: true });

const QUIZ_TYPES = [
  "multiple_choice",
  "fill_in_blank",
  "multiple_response",
  "matching",
  "ordering",
];

const SECTION_ORDER = [
  "m1_l1",
  "m1_l2",
  "m2_l1",
  "m2_l2",
  "m3_l1",
  "m3_l2",
  "m4_l1",
  "m4_l2",
  "m5_l1",
  "m5_l2",
  "midterm",
];

const SECTION_TITLES = {
  m1_l1: "M1L1: History & Methodology",
  m1_l2: "M1L2: Methods",
  m2_l1: "M2L1: Motor Control",
  m2_l2: "M2L2: Motor Control (Flipped)",
  m3_l1: "M3L1: Memory",
  m3_l2: "M3L2: Memory (Flipped)",
  m4_l1: "M4L1: Emotion & Social Cognition",
  m4_l2: "M4L2: Emotion (Flipped)",
  m5_l1: "M5L1: Executive Function",
  m5_l2: "M5L2: Executive Function (Flipped)",
  midterm: "Midterm Review",
};

const quizMap = new Map();

for (const [path, mod] of Object.entries(quizModules)) {
  const fileName = path.split("/").pop().replace(".json", "");
  const data = mod.default ?? mod;
  if (data && Array.isArray(data.questions)) {
    quizMap.set(fileName, data);
  }
}

// "mixed" pulls one or two of every available type and shuffles them together.
// Each question keeps its own `type`; the QuestionRenderer picks the right UI.
function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function buildMixedQuiz(sectionId, perType = 2) {
  const sources = getQuizzesForSection(sectionId);
  if (sources.length === 0) return null;
  const picks = [];
  for (const src of sources) {
    const sample = shuffle(src.questions || []).slice(0, perType);
    for (const q of sample) {
      // Ensure each question carries its declared `type` so the renderer
      // can dispatch correctly when they're interleaved.
      picks.push({ ...q, type: q.type ?? src.quiz_type });
    }
  }
  if (picks.length === 0) return null;
  return {
    quiz_type: "mixed",
    title: `${SECTION_TITLES[sectionId] ?? sectionId} — Mixed`,
    questions: shuffle(picks),
  };
}

export function getQuiz(sectionId, quizType) {
  if (quizType === "mixed") return buildMixedQuiz(sectionId);
  return quizMap.get(`${sectionId}_${quizType}`) ?? null;
}

export function getQuizzesForSection(sectionId) {
  const out = [];
  for (const type of QUIZ_TYPES) {
    const quiz = quizMap.get(`${sectionId}_${type}`);
    if (quiz) out.push(quiz);
  }
  return out;
}

export function getAvailableTypes(sectionId) {
  return getQuizzesForSection(sectionId).map((q) => q.quiz_type);
}

export function listSections() {
  return SECTION_ORDER.filter((id) => getQuizzesForSection(id).length > 0).map(
    (id) => ({
      id,
      title: SECTION_TITLES[id] ?? id,
      questionCount: getQuizzesForSection(id).reduce(
        (sum, q) => sum + (q.questions?.length ?? 0),
        0,
      ),
      availableTypes: getAvailableTypes(id),
    }),
  );
}

export { QUIZ_TYPES };
