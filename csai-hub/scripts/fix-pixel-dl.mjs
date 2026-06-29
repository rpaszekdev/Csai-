// Refills blank answer options in the pixel app's static bundle from the source
// quiz JSON, and corrects the type/correct of questions the old HTML-scraper
// mangled. Idempotent: re-run anytime to heal drift (run finds 0 blanks -> noop).
//
//   node scripts/fix-pixel-dl.mjs
//
// Reads:  src/courses/deep-learn/data/quizzes/*_multiple_{choice,response}.json
// Writes: public/pixel/dl-data.js   (window.DL_LESSONS = [...])
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import assert from "node:assert";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const QUIZ_DIR = join(ROOT, "src/courses/deep-learn/data/quizzes");
const BUNDLE = join(ROOT, "public/pixel/dl-data.js");

// hard-normalize: text was entity-decoded + whitespace-collapsed by the scraper,
// so match on letters+digits only. ponytail: distinct full stems won't collide.
const normKey = (s) => String(s ?? "").toLowerCase().replace(/[^a-z0-9]+/g, "");
const isBlank = (v) => v == null || String(v).trim() === "";

// --- index every source MC/MR question by its normalized stem ---
const byStem = new Map();
for (const file of readdirSync(QUIZ_DIR)) {
  const isMC = file.endsWith("_multiple_choice.json");
  const isMR = file.endsWith("_multiple_response.json");
  if (!isMC && !isMR) continue;
  const { questions } = JSON.parse(readFileSync(join(QUIZ_DIR, file), "utf8"));
  for (const q of questions ?? []) {
    byStem.set(normKey(q.question), {
      options: q.options,
      correct: isMR ? q.correct_answers ?? [] : q.correct_answer,
      type: isMR ? "multi" : "single",
    });
  }
}

// --- load the bundle, parse the JSON array out of `window.DL_LESSONS = [...]` ---
const raw = readFileSync(BUNDLE, "utf8");
const open = raw.indexOf("["), close = raw.lastIndexOf("]");
const prefix = raw.slice(0, open), suffix = raw.slice(close + 1);
const lessons = JSON.parse(raw.slice(open, close + 1));

// --- patch every question that has a blank option ---
let fixed = 0;
const unmatched = [];
for (const lesson of lessons) {
  for (const q of lesson.questions ?? []) {
    if (!q.options || !Object.values(q.options).some(isBlank)) continue;
    const src = byStem.get(normKey(q.q));
    if (!src) { unmatched.push(`${lesson.code}#${q.n} :: ${String(q.q).slice(0, 60)}`); continue; }
    q.options = { ...src.options };
    q.type = src.type;
    q.correct = Array.isArray(src.correct) ? [...src.correct] : src.correct;
    fixed++;
  }
}

// --- fail loud on anything we couldn't match ---
if (unmatched.length) {
  console.error(`Could not match ${unmatched.length} blank question(s) to source:`);
  for (const u of unmatched) console.error("  " + u);
  process.exit(1);
}

// --- self-check: no blank option may survive ---
for (const lesson of lessons)
  for (const q of lesson.questions ?? [])
    if (q.options)
      for (const [k, v] of Object.entries(q.options))
        assert(!isBlank(v), `still blank after fix: ${lesson.code}#${q.n} option ${k}`);

writeFileSync(BUNDLE, prefix + JSON.stringify(lessons) + suffix);
console.log(fixed ? `fixed ${fixed} questions, unmatched: 0` : "nothing to fix");
