// Extracts the old static-HTML course content into the pixel app's COURSES format.
// Run: node scripts/build-pixel-courses.mjs
// Emits: public/pixel/courses-data.js  (window.COURSES.autosys = {...})
//
// Source (auto-sys, static HTML only):
//   public/auto-sys/lecture-NN-quiz.html + the 4 exams  -> embedded `const QUESTIONS = [...]`
//   public/auto-sys/lecture-NN.html                     -> <article> notes HTML
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const AS = join(ROOT, "public/auto-sys");
const LETTERS = "ABCDEFGHIJ".split("");

// --- balanced [..] slice that respects ' " ` strings (template literals carry HTML) ---
function sliceArray(src, openIdx) {
  let depth = 0, str = null, tpl = false;
  for (let i = openIdx; i < src.length; i++) {
    const c = src[i], p = src[i - 1];
    if (str) { if (c === str && p !== "\\") str = null; continue; }
    if (tpl) { if (c === "`" && p !== "\\") tpl = false; continue; }
    if (c === '"' || c === "'") { str = c; continue; }
    if (c === "`") { tpl = true; continue; }
    if (c === "[") depth++;
    else if (c === "]") { if (--depth === 0) return src.slice(openIdx, i + 1); }
  }
  return null;
}
function extractQuestions(html) {
  const m = /const\s+QUESTIONS\s*=\s*\[/.exec(html);
  if (!m) return [];
  const arr = sliceArray(html, m.index + m[0].length - 1);
  if (!arr) return [];
  const ctx = {};
  vm.runInNewContext("out = " + arr, ctx, { timeout: 2000 });
  return Array.isArray(ctx.out) ? ctx.out : [];
}

// --- HTML -> readable plain text (the pixel quiz binds q/options/explain as text) ---
function txt(h) {
  return String(h == null ? "" : h)
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/<\/(p|div|li|h[1-6])>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&nbsp;/g, " ").replace(/&middot;/g, "·").replace(/&times;/g, "×")
    .replace(/&#39;|&rsquo;|&lsquo;/g, "'").replace(/&quot;|&ldquo;|&rdquo;/g, '"')
    .replace(/&hellip;/g, "…").replace(/&mdash;/g, "—").replace(/&ndash;/g, "–")
    .replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
}
function firstTitle(html, fallback) {
  let m = /<h1[^>]*class="[^"]*hero-title[^"]*"[^>]*>([\s\S]*?)<\/h1>/i.exec(html)
       || /<h1[^>]*>([\s\S]*?)<\/h1>/i.exec(html)
       || /<title>([\s\S]*?)<\/title>/i.exec(html);
  return m ? txt(m[1]).replace(/\s*[|–—-].*$/, "").trim() || fallback : fallback;
}

// --- map one source question -> pixel question ---
function mapQuestion(srcQ, n) {
  const opts = Array.isArray(srcQ.options) ? srcQ.options : [];
  const options = {}; const correct = [];
  opts.forEach((o, i) => {
    const L = LETTERS[i]; if (!L) return;
    options[L] = txt(o.html != null ? o.html : o.text != null ? o.text : o);
    if (o.correct === true) correct.push(L);
  });
  return {
    n,
    type: correct.length > 1 ? "multi" : "single",
    q: txt(srcQ.prompt != null ? srcQ.prompt : srcQ.q != null ? srcQ.q : srcQ.question),
    code: false,
    options,
    correct: correct.length > 1 ? correct : (correct[0] || LETTERS[0]),
    explain: txt(srcQ.prof != null ? srcQ.prof : srcQ.explanation != null ? srcQ.explanation : srcQ.explain),
  };
}
function buildLesson(file, { code, id, topic, title, isExam }) {
  const html = readFileSync(join(AS, file), "utf8");
  const qs = extractQuestions(html).map((q, i) => mapQuestion(q, i + 1));
  return {
    code, id,
    topic: topic || firstTitle(html, code),
    title: title || firstTitle(html, code),
    count: qs.length,
    real: true,
    source: "Tilburg · Autonomous Systems",
    ...(isExam ? { isExam: true } : {}),
    questions: qs,
  };
}

// --- lecture <article> -> note html (with slide paths absolutised) ---
function buildNote(file, n) {
  const html = readFileSync(join(AS, file), "utf8");
  const m = /<article[^>]*>([\s\S]*?)<\/article>/i.exec(html);
  let inner = m ? m[1] : "";
  inner = inner
    .replace(/(["'(])\s*\.?\/?(week\d+-slides\/)/g, "$1/auto-sys/$2")
    .replace(/(["'(])\s*\.?\/?(decks\/)/g, "$1/auto-sys/$2");
  return { id: "as-note" + n, title: firstTitle(html, "Lecture " + n), html: inner.trim() };
}

// ---- build auto-sys ----
const N = 11;
const lessons = [], notes = [];
for (let i = 1; i <= N; i++) {
  const nn = String(i).padStart(2, "0");
  const quiz = `lecture-${nn}-quiz.html`;
  if (existsSync(join(AS, quiz))) {
    const lec = `lecture-${nn}.html`;
    const topic = existsSync(join(AS, lec)) ? firstTitle(readFileSync(join(AS, lec), "utf8"), "Lecture " + i) : "Lecture " + i;
    lessons.push(buildLesson(quiz, { code: "L" + i, id: "as-l" + i, topic, title: topic }));
  }
  if (existsSync(join(AS, `lecture-${nn}.html`))) notes.push(buildNote(`lecture-${nn}.html`, i));
}
const examFiles = [
  ["mock-exam.html", "Mock Exam", "as-mock"],
  ["final-exam.html", "Final Exam", "as-final"],
  ["final-exam-2.html", "Final Exam 2", "as-final2"],
  ["final-exam-3.html", "Final Exam 3", "as-final3"],
];
const exams = [];
for (const [file, name, id] of examFiles) {
  if (existsSync(join(AS, file))) exams.push(buildLesson(file, { code: "EX", id, topic: name, title: name, isExam: true }));
}

const autosys = {
  id: "autosys",
  name: "autonomous-systems",
  navIcon: "autonomous",
  live: true,
  lessons, notes, exams,
};

const out =
  "// AUTO-GENERATED by scripts/build-pixel-courses.mjs — do not edit by hand.\n" +
  "window.COURSES = window.COURSES || {};\n" +
  "window.COURSES.autosys = " + JSON.stringify(autosys) + ";\n";
writeFileSync(join(ROOT, "public/pixel/courses-data.js"), out);

console.log(`auto-sys → ${lessons.length} quizzes (${lessons.reduce((a, l) => a + l.count, 0)} Q), ` +
  `${exams.length} exams (${exams.reduce((a, l) => a + l.count, 0)} Q), ${notes.length} notes`);
console.log("quiz titles:", lessons.map(l => l.topic).join(" | "));
console.log("wrote public/pixel/courses-data.js (" + (out.length / 1024).toFixed(1) + " KB)");
