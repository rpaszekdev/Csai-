// dlData.js — real-data adapter for the deep-learning IDE shell quiz view.
//
// The shell prototype reads `window.DL_LESSONS`, an array of lesson objects:
//   lesson    = { topic, slug, sectionId, questions: [...] }
//   question  = a normalized, shell-friendly question (see shapes below).
//
// This module turns the pregenerated quiz JSON (the same files the
// deep-learn course loads) into that shape. It is a pure data/transform
// module: no React, no DOM, no mutation of the imported JSON. Every object
// returned is freshly constructed (and frozen) so callers can never corrupt
// the underlying quiz data.
//
// Normalized question shapes (discriminated by `type`):
//   multiple_choice:
//     { id, type:"multiple_choice", q, options:{A,B,...}, correct:"B",
//       explain, source:"generated"|"lecturer" }
//   multiple_response:
//     { id, type:"multiple_response", q, options:{A,B,...},
//       correctSet:["A","C"], explain, source:"generated"|"lecturer" }
//
// Only multiple_choice and multiple_response are emitted: those are the
// only types the shell's MCQ-style renderer can display with the
// { q, options, correct/correctSet, explain } contract. matching / ordering /
// fill_in_blank questions exist in the source JSON but are intentionally
// skipped here until the shell can render them.

import {
  getQuiz,
  listSections,
} from "../courses/deep-learn/lib/pregeneratedQuizzes.js";

// The 8 deep-learning topics + an Exam set, in canonical exam order. Each
// lesson lists its quiz sections in DISPLAY order: the LECTURER quizzes
// (source:"lecturer") come FIRST so the real lecturer questions lead, then the
// generated practice sections. `code` is the short tab label.
const TOPIC_CONFIG = [
  { topic: "MLPs", slug: "mlps", code: "L1", sections: ["lec1", "l1"] },
  {
    topic: "Backpropagation",
    slug: "backpropagation",
    code: "L2",
    sections: ["lec2", "l2"],
  },
  {
    topic: "Optimizers",
    slug: "optimizers",
    code: "L3",
    sections: ["lec3", "lec4", "l3"],
  },
  { topic: "CNNs", slug: "cnns", code: "L4", sections: ["lec5", "l4"] },
  {
    topic: "Regularization",
    slug: "regularization",
    code: "L5",
    sections: ["lec6", "l5"],
  },
  {
    topic: "Recurrence",
    slug: "recurrence",
    code: "L6",
    sections: ["lec7", "l6"],
  },
  {
    topic: "Transformers",
    slug: "transformers",
    code: "L7",
    sections: ["lec8", "lec9", "l7", "l9"],
  },
  {
    topic: "Computer Vision",
    slug: "computer-vision",
    code: "L8",
    sections: ["l8"],
  },
];

// The exam set is its own lesson (appended after the 8 topics). Its questions
// come from the real-style exam MCQ bank, flagged source:"exam".
const EXAM_CONFIG = {
  topic: "Exam · Real-Style",
  slug: "exam",
  code: "EX",
  sections: ["exam"],
};

function sourceOf(quiz) {
  if (quiz && (quiz.source === "lecturer" || quiz.source === "exam")) {
    return quiz.source;
  }
  return "generated";
}

function normalizeMultipleChoice(rawQ, source) {
  return Object.freeze({
    id: rawQ.id,
    type: "multiple_choice",
    q: rawQ.question,
    options: Object.freeze({ ...rawQ.options }),
    correct: rawQ.correct_answer,
    explain: rawQ.explanation,
    source,
  });
}

function normalizeMultipleResponse(rawQ, source) {
  return Object.freeze({
    id: rawQ.id,
    type: "multiple_response",
    q: rawQ.question,
    options: Object.freeze({ ...rawQ.options }),
    correctSet: Object.freeze([...(rawQ.correct_answers ?? [])]),
    explain: rawQ.explanation,
    source,
  });
}

// All renderable (MC + MR) questions for a single quiz section, MC first.
function questionsForSection(sectionId) {
  const out = [];

  const mc = getQuiz(sectionId, "multiple_choice");
  if (mc && Array.isArray(mc.questions)) {
    const source = sourceOf(mc);
    for (const rawQ of mc.questions) {
      out.push(normalizeMultipleChoice(rawQ, source));
    }
  }

  const mr = getQuiz(sectionId, "multiple_response");
  if (mr && Array.isArray(mr.questions)) {
    const source = sourceOf(mr);
    for (const rawQ of mr.questions) {
      out.push(normalizeMultipleResponse(rawQ, source));
    }
  }

  return out;
}

function buildLesson(config) {
  const questions = config.sections.flatMap(questionsForSection);
  return Object.freeze({
    topic: config.topic,
    slug: config.slug,
    code: config.code,
    sectionId: config.sections[0],
    sections: Object.freeze([...config.sections]),
    questions: Object.freeze(questions),
  });
}

// Built once at module load; the imported JSON never changes at runtime.
// 8 topic lessons followed by the exam set.
const LESSONS = Object.freeze([
  ...TOPIC_CONFIG.map(buildLesson),
  buildLesson(EXAM_CONFIG),
]);

// Lightweight topic descriptors (no questions), canonical order preserved.
// `count` is the lesson's question total; `code` is the short tab label.
const TOPICS = Object.freeze(
  LESSONS.map((l) =>
    Object.freeze({
      topic: l.topic,
      slug: l.slug,
      code: l.code,
      sectionId: l.sectionId,
      sections: l.sections,
      count: l.questions.length,
    }),
  ),
);

const LESSONS_BY_SLUG = new Map(LESSONS.map((l) => [l.slug, l]));

/** The 8 lesson objects, in canonical exam order. */
export function getLessons() {
  return LESSONS;
}

/** A single lesson by slug (e.g. "transformers"), or null if unknown. */
export function getLesson(slug) {
  return LESSONS_BY_SLUG.get(slug) ?? null;
}

/** Topic descriptors { topic, slug, sectionId, sections } in exam order. */
export function getTopics() {
  return TOPICS;
}

/**
 * Available quiz sections across the course (exam, lec1, l1..l9) with their
 * id, title, total question count, available types, and lecturer flag.
 * Delegates to the course loader so there is a single source of truth.
 */
export function listQuizSections() {
  return listSections();
}

// Convenience constants for `window.DL_LESSONS = DL_LESSONS`-style wiring.
export const DL_LESSONS = LESSONS;
export const DL_TOPICS = TOPICS;
