const quizModules = import.meta.glob("../data/quizzes/*.json", { eager: true });

const QUIZ_TYPES = [
  "multiple_choice",
  "fill_in_blank",
  "multiple_response",
  "matching",
  "ordering",
];

const SECTION_ORDER = ["s1", "s2", "s3", "s4", "s5", "s6"];

const SECTION_TITLES = {
  s1: "S1: Course Introduction",
  s2: "S2: Research Question & Literature Review",
  s3: "S3: Experimental Design",
  s4: "S4: Writing a Research Proposal",
  s5: "S5: Data Analysis & ML Pitfalls",
  s6: "S6: Writing a Research Paper",
};

const quizMap = new Map();

for (const [path, mod] of Object.entries(quizModules)) {
  const fileName = path.split("/").pop().replace(".json", "");
  const data = mod.default ?? mod;
  if (data && Array.isArray(data.questions)) {
    quizMap.set(fileName, data);
  }
}

// "mixed" pulls a sample of every available type and shuffles them together.
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
