import { Link } from "react-router-dom";
import { listSections, QUIZ_TYPES } from "../lib/pregeneratedQuizzes";

const TYPE_LABELS = {
  multiple_choice: "Multiple Choice",
  fill_in_blank: "Fill in Blank",
  multiple_response: "Multiple Response",
  matching: "Matching",
  ordering: "Ordering",
};

function getSavedScore(sectionId, type) {
  try {
    const raw = localStorage.getItem(`cog-neuro:quiz:${sectionId}:${type}:lastScore`);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export default function QuizIndex() {
  const sections = listSections();

  return (
    <>
      <header className="roadmap-header">
        <span className="roadmap-eyebrow">Quizzes</span>
        <h2 className="roadmap-title">Practice questions per lecture</h2>
        <p className="roadmap-meta">
          5 question types per section · scoring with explanations · localStorage progress.
        </p>
      </header>

      {sections.map((section) => (
        <section key={section.id} className="quiz-section">
          <header className="quiz-section-head">
            <h3 className="quiz-section-title">{section.title}</h3>
            <span className="quiz-section-count">
              {section.questionCount} questions · {section.availableTypes.length} types
            </span>
          </header>

          <div className="quiz-types-grid">
            {QUIZ_TYPES.filter((t) => section.availableTypes.includes(t)).map(
              (type) => {
                const score = getSavedScore(section.id, type);
                return (
                  <Link
                    key={type}
                    to={`${section.id}/${type}`}
                    className="quiz-type-card"
                  >
                    <div className="quiz-type-name">{TYPE_LABELS[type]}</div>
                    <div className="quiz-type-meta">Last attempt</div>
                    {score && (
                      <span className="saved-score">
                        {score.correct}/{score.total}
                      </span>
                    )}
                  </Link>
                );
              },
            )}
          </div>
        </section>
      ))}
    </>
  );
}
