// Extracts the old static-HTML course content into the pixel app's COURSES format.
// Run: node scripts/build-pixel-courses.mjs
// Emits: public/pixel/courses-data.js  (window.COURSES.autosys = {...})
//
// Source (auto-sys, static HTML only):
//   public/auto-sys/lecture-NN-quiz.html + the 4 exams  -> embedded `const QUESTIONS = [...]`
//   public/auto-sys/lecture-NN.html                     -> <article> notes HTML
import { readFileSync, writeFileSync, existsSync, readdirSync } from "node:fs";
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

// ===================== cog-neuro (structured JSON + markdown notes) =====================
const COG = join(ROOT, "src/courses/cog-neuro/data");
function readJSON(p) { return existsSync(p) ? JSON.parse(readFileSync(p, "utf8")) : null; }
function clean(s) { return String(s == null ? "" : s).trim(); }  // cog-neuro text is already plain (may contain '<'), so don't strip tags

// one cog-neuro quiz question -> pixel question
function cogQuestion(rawQ, type, n) {
  if (type === "review") { // fill_in_blank: no option pool -> self-graded reveal
    return { n, type: "review", q: clean(rawQ.question || rawQ.blank_sentence), code: false, options: {},
      correct: "", explain: "Answer: " + clean(rawQ.correct_answer) + (rawQ.explanation ? " — " + clean(rawQ.explanation) : "") };
  }
  const options = {};
  Object.keys(rawQ.options || {}).forEach((k) => { options[k] = clean(rawQ.options[k]); });
  return { n, type, q: clean(rawQ.question), code: false, options,
    correct: type === "multi" ? [...(rawQ.correct_answers || [])] : clean(rawQ.correct_answer),
    explain: clean(rawQ.explanation) };
}

// --- tiny markdown -> html for the study notes (only the subset the notes use) ---
function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
function mdInline(s) {
  return esc(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[EXAM\]/g, '<span class="badge">EXAM</span>')
    .replace(/\[PROF EMPHASIS\]/g, '<span class="badge prof">PROF</span>')
    .replace(/ -- /g, " — ");
}
function mdToHtml(md) {
  const lines = md.replace(/\r/g, "").split("\n");
  const out = [];
  let i = 0, sawTitle = false;
  const isBullet = (l) => /^\s*[-*] +/.test(l);
  const isOrdered = (l) => /^\s*\d+\. +/.test(l);
  const isRow = (l) => /^\s*\|.*\|\s*$/.test(l);
  const isSep = (l) => /^\s*\|?[\s:|-]+\|?\s*$/.test(l) && l.includes("-");
  const isBlock = (l) => /^#{1,6} /.test(l) || isBullet(l) || isOrdered(l) || isRow(l) || /^\s*> ?/.test(l) || /^\s*---+\s*$/.test(l);
  while (i < lines.length) {
    const l = lines[i];
    if (!l.trim()) { i++; continue; }
    const h = /^(#{1,6}) +(.*)$/.exec(l);
    if (h) {
      const lvl = h[1].length;
      if (lvl === 1 && !sawTitle) { sawTitle = true; i++; continue; } // title rendered by buildNote
      sawTitle = true;
      const tag = lvl <= 2 ? "h2" : lvl === 3 ? "h3" : "h4";
      out.push(`<${tag}>${mdInline(h[2])}</${tag}>`); i++; continue;
    }
    sawTitle = true;
    if (/^\s*---+\s*$/.test(l)) { out.push("<hr>"); i++; continue; }
    if (isRow(l) && i + 1 < lines.length && isSep(lines[i + 1])) {
      const cells = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      const head = cells(l); i += 2; const body = [];
      while (i < lines.length && isRow(lines[i])) { body.push(cells(lines[i])); i++; }
      out.push("<table><thead><tr>" + head.map((c) => `<th>${mdInline(c)}</th>`).join("") + "</tr></thead><tbody>" +
        body.map((r) => "<tr>" + r.map((c) => `<td>${mdInline(c)}</td>`).join("") + "</tr>").join("") + "</tbody></table>");
      continue;
    }
    if (/^\s*> ?/.test(l)) {
      const buf = [];
      while (i < lines.length && /^\s*> ?/.test(lines[i])) { buf.push(lines[i].replace(/^\s*> ?/, "")); i++; }
      out.push(`<blockquote>${mdInline(buf.join(" "))}</blockquote>`); continue;
    }
    if (isBullet(l) || isOrdered(l)) {
      const tag = isOrdered(l) ? "ol" : "ul";
      out.push(`<${tag}>`); let nested = false;
      while (i < lines.length && (isBullet(lines[i]) || isOrdered(lines[i]))) {
        const indent = (/^(\s*)/.exec(lines[i])[1] || "").length;
        const text = lines[i].replace(/^\s*(?:[-*]|\d+\.) +/, "");
        // ponytail: one nesting level via indent; a bare <ul> sibling renders indented in browsers (upgrade to proper <li>-nesting only if notes go deeper)
        if (indent >= 2 && !nested) { out.push("<ul>"); nested = true; }
        else if (indent < 2 && nested) { out.push("</ul>"); nested = false; }
        out.push(`<li>${mdInline(text)}</li>`); i++;
      }
      if (nested) out.push("</ul>");
      out.push(`</${tag}>`); continue;
    }
    const buf = [];
    while (i < lines.length && lines[i].trim() && !isBlock(lines[i])) { buf.push(lines[i]); i++; }
    out.push(`<p>${mdInline(buf.join(" "))}</p>`);
  }
  return out.join("\n");
}

// --- brain-region word linking (reuse the old site's per-region aliases) ---
const BRAIN_JSON = join(ROOT, "public/cog-neuro/lectures/brain-regions.json");
const brainRegions = existsSync(BRAIN_JSON) ? JSON.parse(readFileSync(BRAIN_JSON, "utf8")) : [];
const aliasToId = new Map();
for (const r of brainRegions) for (const a of (r.aliases || [])) aliasToId.set(a.toLowerCase(), r.id);
const aliasList = [...aliasToId.keys()].sort((a, b) => b.length - a.length).map((a) => a.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
const aliasRe = aliasList.length ? new RegExp("\\b(" + aliasList.join("|") + ")\\b", "gi") : null;

// wrap the FIRST mention of each region in a clickable button; never touch text inside HTML tags
function wrapBrainLinks(html) {
  if (!aliasRe) return html;
  const linked = new Set();
  return html.split(/(<[^>]+>)/).map((tok) => {
    if (tok.startsWith("<")) return tok; // a tag — leave untouched
    return tok.replace(aliasRe, (m) => {
      const id = aliasToId.get(m.toLowerCase());
      if (!id || linked.has(id)) return m;
      linked.add(id);
      return `<button type="button" class="brain-link" data-region="${id}">${m}</button>`;
    });
  }).join("");
}

// --- per-lesson presentation slides -> a zoomable grid section ---
const SLIDES_DIR = join(ROOT, "public/cog-neuro/slides");
function slidesSection(id) {
  if (!existsSync(SLIDES_DIR)) return "";
  const files = readdirSync(SLIDES_DIR).filter((f) => f.startsWith(id + "_slide-") && f.endsWith(".png"))
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  if (!files.length) return "";
  const figs = files.map((f) => {
    const num = (f.match(/slide-(\d+)/) || [])[1] || "";
    return `<figure class="slide-embed"><img src="/cog-neuro/slides/${f}" alt="slide ${num}" loading="lazy"><figcaption><span class="num">${num}</span></figcaption></figure>`;
  }).join("");
  return `<section class="note-slides"><span class="section-eyebrow">PRESENTATION SLIDES · ${files.length}</span><div class="slide-grid">${figs}</div></section>`;
}

function cogTopic(id) {
  const meta = readJSON(join(COG, "notes", id + ".meta.json"));
  if (meta && meta.title) { const t = meta.title.split(":").pop().trim(); return t || meta.title; }
  return id;
}
function buildCogNeuro() {
  const ids = ["m1_l1", "m1_l2", "m2_l1", "m2_l2", "m3_l1", "m3_l2", "m4_l1", "m4_l2", "m5_l1", "m5_l2", "midterm"];
  const lessons = ids.map((id, idx) => {
    const mc = readJSON(join(COG, "quizzes", id + "_multiple_choice.json"));
    const mr = readJSON(join(COG, "quizzes", id + "_multiple_response.json"));
    const fib = readJSON(join(COG, "quizzes", id + "_fill_in_blank.json"));
    const qs = [];
    if (mc) mc.questions.forEach((q) => qs.push(cogQuestion(q, "single", qs.length + 1)));
    if (mr) mr.questions.forEach((q) => qs.push(cogQuestion(q, "multi", qs.length + 1)));
    if (fib) fib.questions.forEach((q) => qs.push(cogQuestion(q, "review", qs.length + 1)));
    const topic = cogTopic(id);
    return { code: id === "midterm" ? "MID" : "L" + (idx + 1), id: "cog-" + id, topic, title: topic,
      count: qs.length, real: true, source: "Tilburg · Cognitive Neuroscience", questions: qs };
  });
  const notes = ids.map((id) => {
    const mdPath = join(COG, "notes", id + ".md");
    if (!existsSync(mdPath)) return null;
    const meta = readJSON(join(COG, "notes", id + ".meta.json"));
    const html = wrapBrainLinks(mdToHtml(readFileSync(mdPath, "utf8"))) + slidesSection(id);
    return { id: "cog-" + id, title: (meta && meta.title) || cogTopic(id), html };
  }).filter(Boolean);
  return { id: "cogneuro", name: "cognitive-neuroscience", navIcon: "cogneuro", live: true, lessons, notes, exams: [] };
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

const cogneuro = buildCogNeuro();

// self-test: the markdown renderer must survive every block the notes use
(function selftest() {
  const html = mdToHtml("# Title\n## Head\nA **bold** word [EXAM]\n\n- one\n  - nested\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n> quote");
  const need = ["<h2>Head</h2>", "<strong>bold</strong>", 'class="badge">EXAM', "<ul>", "<table>", "<th>A</th>", "<blockquote>"];
  for (const s of need) if (!html.includes(s)) throw new Error("mdToHtml self-test failed, missing: " + s);
  if (html.includes("<h1>") || html.includes("Title")) throw new Error("mdToHtml should drop the leading H1 title");
  if (aliasRe) { // brain-link: wrap first mention only, never inside a tag
    const w = wrapBrainLinks("<p>The hippocampus and amygdala. The hippocampus again.</p>");
    const links = (w.match(/class="brain-link"/g) || []).length;
    if (links !== 2) throw new Error("wrapBrainLinks should link first mention per region (got " + links + ")");
    if (!/data-region="hippocampus"/.test(w) || !/data-region="amygdala"/.test(w)) throw new Error("wrapBrainLinks missing region ids");
  }
})();

const out =
  "// AUTO-GENERATED by scripts/build-pixel-courses.mjs — do not edit by hand.\n" +
  "window.COURSES = window.COURSES || {};\n" +
  "window.COURSES.autosys = " + JSON.stringify(autosys) + ";\n" +
  "window.COURSES.cogneuro = " + JSON.stringify(cogneuro) + ";\n";
writeFileSync(join(ROOT, "public/pixel/courses-data.js"), out);

console.log(`auto-sys → ${lessons.length} quizzes (${lessons.reduce((a, l) => a + l.count, 0)} Q), ` +
  `${exams.length} exams (${exams.reduce((a, l) => a + l.count, 0)} Q), ${notes.length} notes`);
console.log(`cog-neuro → ${cogneuro.lessons.length} quizzes (${cogneuro.lessons.reduce((a, l) => a + l.count, 0)} Q), ${cogneuro.notes.length} notes`);
console.log("cog-neuro titles:", cogneuro.lessons.map(l => l.topic).join(" | "));
console.log("wrote public/pixel/courses-data.js (" + (out.length / 1024).toFixed(1) + " KB)");
