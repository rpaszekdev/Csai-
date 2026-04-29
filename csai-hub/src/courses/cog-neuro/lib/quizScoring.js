function levenshtein(a, b) {
  const la = a.length;
  const lb = b.length;
  const dp = Array.from({ length: la + 1 }, () => Array(lb + 1).fill(0));
  for (let i = 0; i <= la; i++) dp[i][0] = i;
  for (let j = 0; j <= lb; j++) dp[0][j] = j;
  for (let i = 1; i <= la; i++) {
    for (let j = 1; j <= lb; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost);
    }
  }
  return dp[la][lb];
}

function fuzzyMatch(userAnswer, correctAnswer, acceptableAnswers = [], maxDistance = 2) {
  const normalized = (userAnswer ?? "").toString().trim().toLowerCase();
  if (!normalized) return false;
  const candidates = [correctAnswer, ...(acceptableAnswers || [])].map((s) =>
    (s ?? "").toString().trim().toLowerCase(),
  );
  for (const candidate of candidates) {
    if (!candidate) continue;
    if (normalized === candidate) return true;
    if (levenshtein(normalized, candidate) <= maxDistance) return true;
  }
  return false;
}

export function scoreQuestion(question, userAnswer) {
  switch (question.type) {
    case "multiple_choice": {
      const correct = userAnswer === question.correct_answer;
      return { correct, partialScore: correct ? 1 : 0 };
    }
    case "fill_in_blank": {
      const correct = fuzzyMatch(
        userAnswer,
        question.correct_answer,
        question.acceptable_answers,
      );
      return { correct, partialScore: correct ? 1 : 0 };
    }
    case "multiple_response": {
      const selected = Array.isArray(userAnswer) ? userAnswer : [];
      const correctSet = new Set(question.correct_answers || []);
      const selectedSet = new Set(selected);
      let hits = 0;
      for (const s of selected) {
        if (correctSet.has(s)) hits++;
      }
      const extras = selected.filter((s) => !correctSet.has(s)).length;
      const denom = correctSet.size || 1;
      const score = Math.max(0, (hits - extras) / denom);
      const allCorrect = hits === correctSet.size && selectedSet.size === correctSet.size;
      return { correct: allCorrect, partialScore: score };
    }
    case "matching": {
      const mapping = userAnswer && typeof userAnswer === "object" ? userAnswer : {};
      const total = Object.keys(question.correct_mapping || {}).length;
      if (total === 0) return { correct: false, partialScore: 0 };
      let hits = 0;
      for (const [item, category] of Object.entries(question.correct_mapping)) {
        if (mapping[item] === category) hits++;
      }
      return { correct: hits === total, partialScore: hits / total };
    }
    case "ordering": {
      const order = Array.isArray(userAnswer) ? userAnswer : [];
      const correctOrder = question.correct_order || [];
      const total = correctOrder.length;
      if (total === 0) return { correct: false, partialScore: 0 };
      let hits = 0;
      for (let i = 0; i < total; i++) {
        if (order[i] === correctOrder[i]) hits++;
      }
      return { correct: hits === total, partialScore: hits / total };
    }
    default:
      return { correct: false, partialScore: 0 };
  }
}

export function calculateTotalScore(questions, answers) {
  let totalCorrect = 0;
  let totalPartial = 0;
  for (const q of questions) {
    const a = answers.get(q.id);
    if (a === undefined) continue;
    const r = scoreQuestion(q, a);
    if (r.correct) totalCorrect++;
    totalPartial += r.partialScore;
  }
  return { totalCorrect, totalPartial, total: questions.length };
}
