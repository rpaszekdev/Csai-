import { Link } from "react-router-dom";
import { listSections, QUIZ_TYPES } from "../lib/pregeneratedQuizzes";

const TYPE_LABELS = {
  mixed: "Mixed (all types)",
  multiple_choice: "Multiple Choice",
  fill_in_blank: "Fill in Blank",
  multiple_response: "Multiple Response",
  matching: "Matching",
  ordering: "Ordering",
};

// Render order: Mixed first (highlighted), then each individual type.
const ROW_ORDER = [
  "mixed",
  "multiple_choice",
  "multiple_response",
  "fill_in_blank",
  "matching",
  "ordering",
];

function getSavedScore(sectionId, type) {
  try {
    const raw = localStorage.getItem(
      `cog-neuro:quiz:${sectionId}:${type}:lastScore`,
    );
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export default function QuizIndex() {
  const sections = listSections();
  const totalQuestions = sections.reduce((s, x) => s + x.questionCount, 0);

  return (
    <div className="quiz-list">
      <header className="quiz-list-head">
        <p className="quiz-list-eyebrow">Quizzes</p>
        <h1 className="quiz-list-title">Practice questions per lecture</h1>
        <p className="quiz-list-meta">
          <span>{sections.length} lectures</span>
          <span className="quiz-list-dot">·</span>
          <span>{totalQuestions} questions</span>
          <span className="quiz-list-dot">·</span>
          <span>5 types · MC · MR · Fill · Match · Order</span>
        </p>
      </header>

      <div className="roadmap-list-rule" aria-hidden="true" />

      {sections.map((section, idx) => {
        const num = String(idx + 1).padStart(2, "0");
        return (
          <section key={section.id} className="quiz-mod">
            <div className="quiz-mod-head">
              <span className="quiz-mod-num">{num}</span>
              <h2 className="quiz-mod-title">{section.title}</h2>
              <span className="quiz-mod-meta">
                <span>{section.questionCount} Q</span>
                <span className="quiz-mod-dot">·</span>
                <span>{section.availableTypes.length} types</span>
              </span>
            </div>

            <ul className="quiz-type-list">
              {ROW_ORDER.filter(
                (t) =>
                  t === "mixed" ||
                  (QUIZ_TYPES.includes(t) &&
                    section.availableTypes.includes(t)),
              ).map((type) => {
                const score = getSavedScore(section.id, type);
                const cls =
                  "quiz-type-row" +
                  (type === "mixed" ? " quiz-type-row--mixed" : "");
                return (
                  <li key={type} className={cls}>
                    <Link
                      to={`${section.id}/${type}`}
                      className="quiz-type-link"
                    >
                      <span className="quiz-type-arrow">→</span>
                      <span className="quiz-type-name">
                        {TYPE_LABELS[type]}
                      </span>
                      {score ? (
                        <span className="quiz-type-score">
                          {score.correct}/{score.total}
                        </span>
                      ) : (
                        <span className="quiz-type-score quiz-type-score--empty">
                          —
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>

            <div className="roadmap-list-rule" aria-hidden="true" />
          </section>
        );
      })}
    </div>
  );
}
