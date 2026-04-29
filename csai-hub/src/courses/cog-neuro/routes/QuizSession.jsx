import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getQuiz } from "../lib/pregeneratedQuizzes";
import { scoreQuestion, calculateTotalScore } from "../lib/quizScoring";

const TYPE_LABELS = {
  multiple_choice: "Multiple Choice",
  fill_in_blank: "Fill in Blank",
  multiple_response: "Multiple Response",
  matching: "Matching",
  ordering: "Ordering",
};

function MultipleChoice({ question, value, onChange, submitted }) {
  return (
    <div className="quiz-options">
      {Object.entries(question.options).map(([key, label]) => {
        let cls = "quiz-option";
        if (submitted) {
          if (key === question.correct_answer) cls += " correct";
          else if (key === value) cls += " wrong";
        } else if (value === key) {
          cls += " selected";
        }
        return (
          <button
            type="button"
            key={key}
            className={cls}
            onClick={() => !submitted && onChange(key)}
            disabled={submitted}
          >
            <span className="quiz-option-key">{key}.</span>
            <span>{label}</span>
          </button>
        );
      })}
    </div>
  );
}

function MultipleResponse({ question, value = [], onChange, submitted }) {
  const correctSet = new Set(question.correct_answers || []);
  const selectedSet = new Set(value);

  const toggle = (key) => {
    if (submitted) return;
    const next = new Set(selectedSet);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    onChange([...next]);
  };

  return (
    <div className="quiz-options">
      {Object.entries(question.options).map(([key, label]) => {
        let cls = "quiz-option";
        if (submitted) {
          if (correctSet.has(key)) cls += " correct";
          else if (selectedSet.has(key)) cls += " wrong";
        } else if (selectedSet.has(key)) {
          cls += " selected";
        }
        return (
          <button
            type="button"
            key={key}
            className={cls}
            onClick={() => toggle(key)}
            disabled={submitted}
          >
            <span className="quiz-option-key">{selectedSet.has(key) ? "☑" : "☐"}</span>
            <span><strong>{key}.</strong> {label}</span>
          </button>
        );
      })}
    </div>
  );
}

function FillInBlank({ question, value = "", onChange, submitted }) {
  return (
    <div>
      <p className="quiz-q-blank">{question.blank_sentence}</p>
      <input
        type="text"
        className="quiz-fb-input"
        value={value}
        placeholder="Type your answer…"
        disabled={submitted}
        onChange={(e) => onChange(e.target.value)}
      />
      {submitted && (
        <p style={{ marginTop: "var(--space-sm)", fontSize: 13 }}>
          Correct: <strong>{question.correct_answer}</strong>
        </p>
      )}
    </div>
  );
}

function Matching({ question, value = {}, onChange, submitted }) {
  return (
    <div className="quiz-matching">
      {(question.items || []).map((item) => (
        <label key={item}>
          <span>{item}</span>
          <select
            value={value[item] ?? ""}
            disabled={submitted}
            onChange={(e) => onChange({ ...value, [item]: e.target.value })}
          >
            <option value="">— pick category —</option>
            {(question.categories || []).map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          {submitted && (
            <small style={{ fontSize: 11 }}>
              {value[item] === question.correct_mapping[item]
                ? "✓ correct"
                : `✗ correct: ${question.correct_mapping[item]}`}
            </small>
          )}
        </label>
      ))}
    </div>
  );
}

function Ordering({ question, value, onChange, submitted }) {
  const items = Array.isArray(value) && value.length > 0
    ? value
    : (question.items || []);

  const move = (i, delta) => {
    if (submitted) return;
    const j = i + delta;
    if (j < 0 || j >= items.length) return;
    const next = [...items];
    [next[i], next[j]] = [next[j], next[i]];
    onChange(next);
  };

  return (
    <div className="quiz-ordering">
      {items.map((item, i) => {
        const isCorrect = submitted && item === question.correct_order?.[i];
        const isWrong = submitted && !isCorrect;
        return (
          <div
            key={item}
            className="quiz-ordering-item"
            style={
              submitted
                ? {
                    background: isCorrect ? "#5B7553" : "#B84747",
                    color: "var(--cream)",
                  }
                : undefined
            }
          >
            <button
              type="button"
              className="quiz-ordering-button"
              onClick={() => move(i, -1)}
              disabled={submitted || i === 0}
            >
              ↑
            </button>
            <button
              type="button"
              className="quiz-ordering-button"
              onClick={() => move(i, 1)}
              disabled={submitted || i === items.length - 1}
            >
              ↓
            </button>
            <span className="quiz-ordering-item-text">{i + 1}. {item}</span>
            {isWrong && (
              <small style={{ fontSize: 11 }}>(should be: {question.correct_order?.[i]})</small>
            )}
          </div>
        );
      })}
    </div>
  );
}

function QuestionRenderer({ question, value, onChange, submitted }) {
  switch (question.type) {
    case "multiple_choice":
      return <MultipleChoice question={question} value={value} onChange={onChange} submitted={submitted} />;
    case "multiple_response":
      return <MultipleResponse question={question} value={value} onChange={onChange} submitted={submitted} />;
    case "fill_in_blank":
      return <FillInBlank question={question} value={value} onChange={onChange} submitted={submitted} />;
    case "matching":
      return <Matching question={question} value={value} onChange={onChange} submitted={submitted} />;
    case "ordering":
      return <Ordering question={question} value={value} onChange={onChange} submitted={submitted} />;
    default:
      return <p>Unsupported question type: {question.type}</p>;
  }
}

export default function QuizSession() {
  const { sectionId, quizType } = useParams();
  const quiz = useMemo(() => getQuiz(sectionId, quizType), [sectionId, quizType]);
  const [answers, setAnswers] = useState(new Map());
  const [submitted, setSubmitted] = useState(false);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setAnswers(new Map());
    setSubmitted(false);
    setIndex(0);
  }, [sectionId, quizType]);

  if (!quiz) {
    return (
      <div className="quiz-question">
        <p>No quiz found for {sectionId} / {quizType}.</p>
        <Link to="../" className="quiz-button secondary">Back to quizzes</Link>
      </div>
    );
  }

  const questions = quiz.questions;
  const current = questions[index];
  const value = answers.get(current.id);

  const setAnswer = (val) => {
    setAnswers((prev) => {
      const next = new Map(prev);
      next.set(current.id, val);
      return next;
    });
  };

  const handleSubmit = () => {
    setSubmitted(true);
    const result = calculateTotalScore(questions, answers);
    try {
      localStorage.setItem(
        `cog-neuro:quiz:${sectionId}:${quizType}:lastScore`,
        JSON.stringify({
          correct: result.totalCorrect,
          partial: Number(result.totalPartial.toFixed(2)),
          total: result.total,
          at: Date.now(),
        }),
      );
    } catch {
      // Storage unavailable; safe to ignore.
    }
  };

  const reset = () => {
    setAnswers(new Map());
    setSubmitted(false);
    setIndex(0);
  };

  const totalScore = submitted
    ? calculateTotalScore(questions, answers)
    : null;

  const result = submitted && current ? scoreQuestion(current, value) : null;

  return (
    <div className="quiz-session">
      <header className="roadmap-header">
        <span className="roadmap-eyebrow">{sectionId.toUpperCase()} · {TYPE_LABELS[quizType] ?? quizType}</span>
        <h2 className="roadmap-title">{quiz.title}</h2>
      </header>

      <div className="quiz-progress">
        <span>Question {index + 1} / {questions.length}</span>
        <span>
          <Link to="../" className="lecture-action">All quizzes</Link>
        </span>
      </div>

      <article className="quiz-question">
        {current.type !== "fill_in_blank" && (
          <p className="quiz-q-text">
            {index + 1}. {current.question}
          </p>
        )}

        <QuestionRenderer
          question={current}
          value={value}
          onChange={setAnswer}
          submitted={submitted}
        />

        {submitted && current.explanation && (
          <div className="quiz-explanation">
            <span className={`quiz-result-badge ${result?.correct ? "correct" : "wrong"}`}>
              {result?.correct ? "Correct" : "Wrong"}
            </span>
            <p style={{ marginTop: 8 }}>{current.explanation}</p>
          </div>
        )}

        <div className="quiz-actions">
          <button
            type="button"
            className="quiz-button secondary"
            onClick={() => setIndex((i) => Math.max(0, i - 1))}
            disabled={index === 0}
          >
            Prev
          </button>
          {index < questions.length - 1 ? (
            <button
              type="button"
              className="quiz-button"
              onClick={() => setIndex((i) => Math.min(questions.length - 1, i + 1))}
            >
              Next
            </button>
          ) : !submitted ? (
            <button
              type="button"
              className="quiz-button"
              onClick={handleSubmit}
              disabled={answers.size === 0}
            >
              Submit
            </button>
          ) : (
            <button type="button" className="quiz-button" onClick={reset}>
              Try again
            </button>
          )}
        </div>
      </article>

      {submitted && totalScore && (
        <div className="quiz-summary">
          <div className="quiz-summary-score">
            {totalScore.totalCorrect}/{totalScore.total}
          </div>
          <p>Partial score: {totalScore.totalPartial.toFixed(1)}/{totalScore.total}</p>
          <Link to="../" className="quiz-button secondary">Back to quiz catalogue</Link>
        </div>
      )}
    </div>
  );
}
