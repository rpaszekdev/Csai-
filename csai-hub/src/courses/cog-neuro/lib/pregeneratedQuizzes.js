const quizModules = import.meta.glob("../data/quizzes/*.json", { eager: true });

const QUIZ_TYPES = [
  "multiple_choice",
  "fill_in_blank",
  "multiple_response",
  "matching",
  "ordering",
];

const SECTION_ORDER = ["m1_l1", "m1_l2", "m2_l1", "m2_l2", "m3_l1", "m3_l2", "midterm"];

const SECTION_TITLES = {
  m1_l1: "M1L1: History & Methodology",
  m1_l2: "M1L2: Methods",
  m2_l1: "M2L1: Motor Control",
  m2_l2: "M2L2: Motor Control (Flipped)",
  m3_l1: "M3L1: Memory",
  m3_l2: "M3L2: Memory (Flipped)",
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

export function getQuiz(sectionId, quizType) {
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
  return SECTION_ORDER
    .filter((id) => getQuizzesForSection(id).length > 0)
    .map((id) => ({
      id,
      title: SECTION_TITLES[id] ?? id,
      questionCount: getQuizzesForSection(id).reduce(
        (sum, q) => sum + (q.questions?.length ?? 0),
        0,
      ),
      availableTypes: getAvailableTypes(id),
    }));
}

export { QUIZ_TYPES };
