// shellQuiz.js — pure, render-agnostic quiz logic for the IDE shell.
//
// The shell renders two question types from the real deep-learning data
// (see ../shell/dlData.js):
//   - multiple_choice   : one correct option key (q.correct)
//   - multiple_response : a set of correct option keys (q.correctSet)
//
// Selection is modelled as an array of option keys for BOTH types: a
// single-choice question simply holds 0 or 1 keys. This keeps the option
// view-model identical to the prototype's while supporting set answers.

/** The correct option key(s) for a question, always as an array. */
export function correctKeysOf(q) {
  if (!q) return [];
  if (q.type === "multiple_response") return q.correctSet || [];
  return q.correct != null ? [q.correct] : [];
}

/** Order-independent set equality of two key arrays. */
export function sameSet(a, b) {
  if (a.length !== b.length) return false;
  const seen = new Set(a);
  return b.every((k) => seen.has(k));
}

/** True once the user's selection matches the question's correct answer. */
export function isAnswerCorrect(q, selected) {
  const correct = correctKeysOf(q);
  if (q && q.type === "multiple_response") return sameSet(selected, correct);
  return selected.length === 1 && selected[0] === correct[0];
}

/** Human label for the question's response mode. */
export function typeLabel(q) {
  return q && q.type === "multiple_response"
    ? "MULTIPLE RESPONSE"
    : "SINGLE RESPONSE";
}

/**
 * Apply a click on an option key to the current selection.
 * - multiple_choice  : replace (single select)
 * - multiple_response: toggle (multi select)
 * Returns a new array; never mutates the input.
 */
export function applySelection(q, selected, key) {
  if (q && q.type === "multiple_response") {
    return selected.includes(key)
      ? selected.filter((k) => k !== key)
      : [...selected, key];
  }
  return [key];
}

/**
 * Build the per-option view-model (faithful to the prototype's option styling).
 * options come in as q.options: { A: "text", B: "text", ... }.
 */
export function buildOptions(q, selected, revealed) {
  const correct = correctKeysOf(q);
  const opts = q && q.options ? q.options : {};
  return Object.keys(opts).map((letter) => {
    const text = opts[letter];
    const sel = selected.includes(letter);
    const isCorrect = revealed && correct.includes(letter);
    const isWrong = revealed && sel && !correct.includes(letter);
    const filled = sel || isCorrect;
    const faded = revealed && !isCorrect && !sel;
    return {
      letter,
      text,
      boxBd: isCorrect
        ? "var(--good)"
        : isWrong
          ? "var(--bad)"
          : faded
            ? "var(--line)"
            : "var(--ink)",
      boxBg: isCorrect
        ? "var(--good)"
        : isWrong
          ? "var(--bad)"
          : sel && !revealed
            ? "var(--ink)"
            : "transparent",
      checkIcon: isWrong ? "hn-times" : "hn-check",
      checkColor: isCorrect || isWrong ? "#ffffff" : "var(--onFill)",
      checkOp: filled ? 1 : 0,
      tickAnim: isCorrect ? "tickpop .42s ease-out" : "none",
      dim: faded ? "var(--mute)" : "var(--ink)",
      textWeight: filled ? 700 : 400,
      tag: isCorrect ? "CORRECT" : isWrong ? "WRONG" : "",
      tagColor: isCorrect
        ? "var(--good)"
        : isWrong
          ? "var(--bad)"
          : "var(--ink)",
      tagOp: isCorrect || isWrong ? 1 : 0,
    };
  });
}

/** The "answer" line shown in the explanation drawer. */
export function answerLabel(q) {
  const correct = correctKeysOf(q);
  const opts = q && q.options ? q.options : {};
  if (correct.length === 0) return "";
  if (correct.length === 1) {
    const k = correct[0];
    return `${k}. ${opts[k] ?? ""}`;
  }
  // Multiple-response: list each correct key (compact, drawer-friendly).
  return correct.map((k) => `${k}. ${opts[k] ?? ""}`).join("   ·   ");
}

/** Two-digit, zero-padded question number for the big stroked numeral. */
export function paddedNumber(index) {
  const n = index + 1;
  return (n < 10 ? "0" : "") + n;
}
