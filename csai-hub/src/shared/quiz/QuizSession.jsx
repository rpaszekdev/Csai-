import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { scoreQuestion, calculateTotalScore } from "./quizScoring";

const TYPE_LABELS = {
  mixed: "Mixed",
  multiple_choice: "Multiple Choice",
  fill_in_blank: "Fill in Blank",
  multiple_response: "Multiple Response",
  matching: "Matching",
  ordering: "Ordering",
};

// Question types that auto-reveal the correct answer immediately on selection
// (one-click answer). The rest require a "Check" button.
const AUTO_REVEAL_TYPES = new Set(["multiple_choice"]);

// Highlight the teacher's "style tells" inside an option label on reveal.
// `tells` are exact-substring phrases tagged likes/avoids (see exam quiz JSON).
function highlightTells(label, tells) {
  if (!tells || tells.length === 0) return label;
  const phrases = tells.map((t) => t.phrase).filter(Boolean);
  if (phrases.length === 0) return label;
  const kindOf = {};
  for (const t of tells) kindOf[t.phrase] = t.kind;
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp("(" + phrases.map(esc).join("|") + ")", "g");
  return label.split(re).map((part, i) =>
    kindOf[part] ? (
      <mark
        key={i}
        className={`quiz-tell-mark quiz-tell-mark--${kindOf[part]}`}
      >
        {part}
      </mark>
    ) : (
      part
    ),
  );
}

function MultipleChoice({ question, value, onChange, revealed }) {
  return (
    <ul className="quiz-options">
      {Object.entries(question.options).map(([key, label]) => {
        let cls = "quiz-option";
        if (revealed) {
          if (key === question.correct_answer) cls += " correct";
          else if (key === value) cls += " wrong";
        } else if (value === key) {
          cls += " selected";
        }
        const tells = revealed
          ? (question.tells || []).filter((t) => t.option === key)
          : [];
        return (
          <li key={key}>
            <button
              type="button"
              className={cls}
              onClick={() => !revealed && onChange(key)}
              disabled={revealed}
            >
              <span className="quiz-option-key">{key}</span>
              <span className="quiz-option-label">
                {tells.length ? highlightTells(label, tells) : label}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

function MultipleResponse({ question, value = [], onChange, revealed }) {
  const correctSet = new Set(question.correct_answers || []);
  const selectedSet = new Set(value);

  const toggle = (key) => {
    if (revealed) return;
    const next = new Set(selectedSet);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    onChange([...next]);
  };

  return (
    <ul className="quiz-options">
      {Object.entries(question.options).map(([key, label]) => {
        let cls = "quiz-option";
        if (revealed) {
          if (correctSet.has(key)) cls += " correct";
          else if (selectedSet.has(key)) cls += " wrong";
        } else if (selectedSet.has(key)) {
          cls += " selected";
        }
        return (
          <li key={key}>
            <button
              type="button"
              className={cls}
              onClick={() => toggle(key)}
              disabled={revealed}
            >
              <span className="quiz-option-key">
                {selectedSet.has(key) ? "\u2611" : "\u2610"}
              </span>
              <span className="quiz-option-label">
                <strong>{key}.</strong> {label}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

function FillInBlank({ question, value = "", onChange, revealed }) {
  return (
    <div className="quiz-fb">
      <p className="quiz-q-blank">{question.blank_sentence}</p>
      <input
        type="text"
        className="quiz-fb-input"
        value={value}
        placeholder="Type your answer…"
        disabled={revealed}
        onChange={(e) => onChange(e.target.value)}
      />
      {revealed && (
        <p className="quiz-fb-correct">
          Correct: <strong>{question.correct_answer}</strong>
        </p>
      )}
    </div>
  );
}

function Matching({ question, value = {}, onChange, revealed }) {
  return (
    <div className="quiz-matching">
      {(question.items || []).map((item) => (
        <label key={item} className="quiz-matching-row">
          <span className="quiz-matching-item">{item}</span>
          <select
            className="quiz-matching-select"
            value={value[item] ?? ""}
            disabled={revealed}
            onChange={(e) => onChange({ ...value, [item]: e.target.value })}
          >
            <option value="">— pick category —</option>
            {(question.categories || []).map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
          {revealed && (
            <small
              className={
                value[item] === question.correct_mapping[item]
                  ? "quiz-matching-feedback correct"
                  : "quiz-matching-feedback wrong"
              }
            >
              {value[item] === question.correct_mapping[item]
                ? "\u2713 correct"
                : `\u2717 ${question.correct_mapping[item]}`}
            </small>
          )}
        </label>
      ))}
    </div>
  );
}

function Ordering({ question, value, onChange, revealed }) {
  const items =
    Array.isArray(value) && value.length > 0 ? value : question.items || [];

  const move = (i, delta) => {
    if (revealed) return;
    const j = i + delta;
    if (j < 0 || j >= items.length) return;
    const next = [...items];
    [next[i], next[j]] = [next[j], next[i]];
    onChange(next);
  };

  return (
    <ol className="quiz-ordering">
      {items.map((item, i) => {
        const isCorrect = revealed && item === question.correct_order?.[i];
        const isWrong = revealed && !isCorrect;
        let cls = "quiz-ordering-item";
        if (isCorrect) cls += " correct";
        if (isWrong) cls += " wrong";
        return (
          <li key={item} className={cls}>
            <span className="quiz-ordering-rank">{i + 1}</span>
            <span className="quiz-ordering-text">{item}</span>
            <span className="quiz-ordering-controls">
              <button
                type="button"
                className="quiz-ordering-button"
                onClick={() => move(i, -1)}
                disabled={revealed || i === 0}
                aria-label="Move up"
              >
                ↑
              </button>
              <button
                type="button"
                className="quiz-ordering-button"
                onClick={() => move(i, 1)}
                disabled={revealed || i === items.length - 1}
                aria-label="Move down"
              >
                ↓
              </button>
            </span>
            {isWrong && (
              <small className="quiz-ordering-feedback">
                should be: {question.correct_order?.[i]}
              </small>
            )}
          </li>
        );
      })}
    </ol>
  );
}

function QuestionRenderer({ question, value, onChange, revealed }) {
  switch (question.type) {
    case "multiple_choice":
      return (
        <MultipleChoice
          question={question}
          value={value}
          onChange={onChange}
          revealed={revealed}
        />
      );
    case "multiple_response":
      return (
        <MultipleResponse
          question={question}
          value={value}
          onChange={onChange}
          revealed={revealed}
        />
      );
    case "fill_in_blank":
      return (
        <FillInBlank
          question={question}
          value={value}
          onChange={onChange}
          revealed={revealed}
        />
      );
    case "matching":
      return (
        <Matching
          question={question}
          value={value}
          onChange={onChange}
          revealed={revealed}
        />
      );
    case "ordering":
      return (
        <Ordering
          question={question}
          value={value}
          onChange={onChange}
          revealed={revealed}
        />
      );
    default:
      return <p>Unsupported question type: {question.type}</p>;
  }
}

export default function QuizSession({
  courseId,
  sectionId,
  quizType,
  getQuiz,
  backPath,
}) {
  const quiz = useMemo(
    () => getQuiz(sectionId, quizType),
    [sectionId, quizType, getQuiz],
  );
  const [answers, setAnswers] = useState(new Map());
  // Per-question reveal -- auto-set on MC selection, manual via "Check" button
  // for multi-select / fill-in / matching / ordering.
  const [revealed, setRevealed] = useState(new Set());
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setAnswers(new Map());
    setRevealed(new Set());
    setIndex(0);
  }, [sectionId, quizType]);

  if (!quiz) {
    return (
      <div className="quiz-list">
        <header className="quiz-list-head">
          <p className="quiz-list-eyebrow">Quiz not found</p>
          <h1 className="quiz-list-title">
            {sectionId} / {quizType}
          </h1>
        </header>
        <Link to={backPath} className="quiz-btn">
          ← Back to quizzes
        </Link>
      </div>
    );
  }

  const questions = quiz.questions;
  const current = questions[index];
  const value = answers.get(current.id);
  const isRevealed = revealed.has(current.id);
  const allRevealed = questions.every((q) => revealed.has(q.id));

  const setAnswer = (val) => {
    setAnswers((prev) => {
      const next = new Map(prev);
      next.set(current.id, val);
      return next;
    });
    if (AUTO_REVEAL_TYPES.has(current.type)) {
      setRevealed((prev) => {
        const next = new Set(prev);
        next.add(current.id);
        return next;
      });
    }
  };

  const checkCurrent = () => {
    setRevealed((prev) => {
      const next = new Set(prev);
      next.add(current.id);
      return next;
    });
  };

  const reset = () => {
    setAnswers(new Map());
    setRevealed(new Set());
    setIndex(0);
  };

  // When the last question is revealed, persist the cumulative score so the
  // quiz index can show "last attempt" badges.
  useEffect(() => {
    if (!quiz || !allRevealed) return;
    const result = calculateTotalScore(questions, answers);
    try {
      localStorage.setItem(
        `${courseId}:quiz:${sectionId}:${quizType}:lastScore`,
        JSON.stringify({
          correct: result.totalCorrect,
          partial: Number(result.totalPartial.toFixed(2)),
          total: result.total,
          at: Date.now(),
        }),
      );
    } catch {
      /* storage unavailable; ignore */
    }
  }, [allRevealed, quiz, questions, answers, sectionId, quizType, courseId]);

  const totalScore = allRevealed
    ? calculateTotalScore(questions, answers)
    : null;
  const result = isRevealed && current ? scoreQuestion(current, value) : null;
  const lectureCode = sectionId.replace("_", "\u00b7").toUpperCase();
  const typeLabel = TYPE_LABELS[quizType] ?? quizType;
  const num = String(index + 1).padStart(2, "0");
  const hasAnswer =
    value !== undefined &&
    value !== "" &&
    !(Array.isArray(value) && value.length === 0) &&
    !(
      typeof value === "object" &&
      !Array.isArray(value) &&
      Object.keys(value).length === 0
    );

  return (
    <div className="quiz-list quiz-session">
      <header className="quiz-list-head">
        <p className="quiz-list-eyebrow">
          {lectureCode} · {typeLabel}
        </p>
        <h1 className="quiz-list-title">{quiz.title}</h1>
        <p className="quiz-list-meta">
          <span>
            Question {index + 1} of {questions.length}
          </span>
          <span className="quiz-list-dot">·</span>
          <span>{questions.length} total</span>
          {totalScore && (
            <>
              <span className="quiz-list-dot">·</span>
              <span>
                Score {totalScore.totalCorrect}/{totalScore.total}
              </span>
            </>
          )}
        </p>
      </header>

      <div className="roadmap-list-rule" aria-hidden="true" />

      <section className="quiz-card">
        <div className="quiz-card-head">
          <span className="quiz-card-num">{num}</span>
          <span className="quiz-card-type">
            {current.type.replace(/_/g, " ")}
          </span>
        </div>

        <h2 className="quiz-card-question">
          {current.type === "fill_in_blank"
            ? "Fill in the blank"
            : current.question}
        </h2>

        <div className="quiz-body">
          <QuestionRenderer
            question={current}
            value={value}
            onChange={setAnswer}
            revealed={isRevealed}
          />

          {!isRevealed && !AUTO_REVEAL_TYPES.has(current.type) && (
            <div className="quiz-actions quiz-actions--center">
              <button
                type="button"
                className="quiz-btn quiz-btn--primary"
                onClick={checkCurrent}
                disabled={!hasAnswer}
              >
                Check answer
              </button>
            </div>
          )}

          {isRevealed && current.tells && current.tells.length > 0 && (
            <div className="quiz-tells">
              <span className="quiz-tells-label">
                {"\ud83e\udded"} Teacher&apos;s tell
              </span>
              <ul>
                {current.tells.map((t, i) => (
                  <li key={i} className={`quiz-tell quiz-tell--${t.kind}`}>
                    <span className="quiz-tell-badge">
                      {t.kind === "likes" ? "\u2713 likes" : "\u2717 avoids"}
                    </span>
                    <span className="quiz-tell-opt">{t.option}</span>
                    <span className="quiz-tell-phrase">
                      {"\u201c"}
                      {t.phrase}
                      {"\u201d"}
                    </span>
                    <span className="quiz-tell-rule">{t.rule}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {isRevealed && current.explanation && (
            <div
              className={`quiz-explanation ${result?.correct ? "correct" : "wrong"}`}
            >
              <span className="quiz-explanation-label">
                {result?.correct ? "\u2713 Correct" : "\u2717 Wrong"}
              </span>
              <p>{current.explanation}</p>
            </div>
          )}

          <div className="quiz-actions">
            <button
              type="button"
              className="quiz-btn quiz-btn--ghost"
              onClick={() => setIndex((i) => Math.max(0, i - 1))}
              disabled={index === 0}
            >
              ← Prev
            </button>
            {index < questions.length - 1 ? (
              <button
                type="button"
                className="quiz-btn"
                onClick={() =>
                  setIndex((i) => Math.min(questions.length - 1, i + 1))
                }
              >
                Next →
              </button>
            ) : (
              <button
                type="button"
                className="quiz-btn quiz-btn--primary"
                onClick={reset}
              >
                Try again
              </button>
            )}
            <Link
              to={backPath}
              className="quiz-btn quiz-btn--ghost quiz-btn--right"
            >
              All quizzes
            </Link>
          </div>
        </div>
      </section>

      {totalScore && (
        <section className="quiz-summary">
          <div className="quiz-summary-score">
            <span className="quiz-summary-num">{totalScore.totalCorrect}</span>
            <span className="quiz-summary-of">/ {totalScore.total}</span>
          </div>
          <p className="quiz-summary-meta">
            Partial: {totalScore.totalPartial.toFixed(1)} / {totalScore.total}
          </p>
        </section>
      )}
    </div>
  );
}
