const quizModules = import.meta.glob("../data/quizzes/*.json", { eager: true });

const QUIZ_TYPES = [
  "multiple_choice",
  "fill_in_blank",
  "multiple_response",
  "matching",
  "ordering",
];

const SECTION_ORDER = [
  "exam",
  "lec1",
  "lec2",
  "lec3",
  "lec4",
  "lec5",
  "lec6",
  "lec7",
  "lec8",
  "lec9",
  "l1",
  "l2",
  "l3",
  "l4",
  "l5",
  "l6",
  "l7",
  "l8",
  "l9",
];

const SECTION_TITLES = {
  exam: "Exam: Real-Style MCQ",
  lec1: "Lecturer Quiz: MLP",
  lec2: "Lecturer Quiz: MLP Activation & Backprop",
  lec3: "Lecturer Quiz: Gradient Descent & Optimizers",
  lec4: "Lecturer Quiz: PyTorch & Hyperparameters",
  lec5: "Lecturer Quiz: CNNs",
  lec6: "Lecturer Quiz: Regularization",
  lec7: "Lecturer Quiz: RNNs, LSTMs & GRUs",
  lec8: "Lecturer Quiz: Attention & Transformers",
  lec9: "Lecturer Quiz: Positional Encoding & Transformers",
  l1: "L1: MLPs",
  l2: "L2: Backpropagation",
  l3: "L3: Optimizers",
  l4: "L4: CNNs",
  l5: "L5: Regularization",
  l6: "L6: Recurrence",
  l7: "L7: Transformers",
  l8: "L8: Computer Vision",
  l9: "L9: Positional Encoding & Transformers",
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
    (id) => {
      const quizzes = getQuizzesForSection(id);
      return {
        id,
        title: SECTION_TITLES[id] ?? id,
        questionCount: quizzes.reduce(
          (sum, q) => sum + (q.questions?.length ?? 0),
          0,
        ),
        availableTypes: getAvailableTypes(id),
        lecturer: quizzes.some((q) => q.source === "lecturer"),
      };
    },
  );
}

export { QUIZ_TYPES };
