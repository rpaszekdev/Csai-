# LLM Design Guide — CSAI Hub Lecture Pages

Instructions for AI assistants generating or modifying lecture pages in this project. Read this before writing any HTML, CSS, or JS for a course.

---

## Architecture: Static HTML, Not React

Lecture pages are **self-contained static HTML files** served from `public/`. They are NOT React components. Do not attempt to convert them into JSX or route them through the React app.

```
public/
├── cog-neuro/lectures/m1_l1.html    ← static, self-contained
├── auto-sys/lecture-01.html          ← static, self-contained
└── shared/                           ← drop-in JS/CSS modules
```

The React app (`src/`) only handles the landing page, roadmap, and quiz UIs. It links *out* to these static HTMLs.

---

## The Canonical Template: Cognitive Neuroscience

Every new course page must replicate the structure and visual language of the cog-neuro lectures. The reference file is:

```
public/cog-neuro/lectures/m1_l1.html
```

---

## Design Tokens (CSS Custom Properties)

Every course skin must define these tokens. Copy them from the cog-neuro defaults and override only what changes (e.g., accent color):

```css
:root {
  --paper:       #F2EDE0;    /* page background — cream */
  --paper-2:     #ECE6D6;    /* secondary surface — panels, code blocks */
  --ink:         #1A1A1A;    /* primary text */
  --ink-soft:    #2B2B2B;    /* body text */
  --ink-mute:    #8A8270;    /* labels, eyebrows, secondary text */
  --ink-faint:   #C5BEAE;    /* borders, dividers */
  --ink-faint-2: #A8A29A;    /* very subtle elements */
  --rule:        #1A1A1A;    /* horizontal rules */
  --hair:        #1F1F1F;    /* hairline borders */
  --rust:        #A84F2A;    /* accent — callout labels, badges, active states */
  --rust-soft:   #C46A3F;    /* lighter accent — hover states */
  --highlight:   rgba(168, 79, 42, 0.10);  /* selection/highlight tint */
  --cream:       #F2EDE0;    /* alias for paper */
}
```

**Typography**: `"JetBrains Mono", "IBM Plex Mono", "Söhne Mono", "SF Mono", ui-monospace, monospace` — monospace everywhere, no sans-serif.

**Aesthetic**: Brutalist editorial. No rounded corners, no gradients, no drop shadows (except the brutalist `box-shadow: Npx Npx 0 var(--ink)` on interactive panels). Dense, ink-on-paper feel.

---

## Page Skeleton

Every lecture HTML follows this exact structure. Copy it verbatim for new courses:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>L01 — Lecture Title</title>
  <!-- Option A: cog-neuro has its own CSS -->
  <link rel="stylesheet" href="./cog-neuro.css" />
  <!-- Option B: other courses use shared shell + skin -->
  <link rel="stylesheet" href="/shared/lesson-shell.css" />
  <link rel="stylesheet" href="/your-course/your-course.skin.css" />
  <!-- Always include annotations -->
  <link rel="stylesheet" href="/shared/annotations/annotations.css" />
</head>
<body>

<!-- 1. Rust accent bar (4px tall, full width) -->
<div class="rust-bar"></div>

<!-- 2. Top bar -->
<header class="topbar">
  <a href="/" class="back">← Back</a>
  <span class="brand">
    <span class="mark"></span>          <!-- 14×14 rust square -->
    <span class="name">Course Name</span>
  </span>
  <span class="crumbs">
    <span>University</span>
    <span>Year N</span>
    <span>Sem N</span>
  </span>
</header>

<!-- 3. Tab navigation -->
<nav class="tabs">
  <a href="/courses/your-course/roadmap">Roadmap</a>
  <a href="#" class="active">Lessons</a>
  <a href="./lecture-01-quiz.html">Quizzes</a>
</nav>

<!-- 4. Hero section -->
<section class="hero">
  <div class="hero-left">
    <div class="hero-num">01</div>       <!-- giant outlined number -->
    <div class="hero-title-block">
      <span class="hero-eyebrow">Module 01 · Lecture 01 —</span>
      <h1 class="hero-title">Lecture Title Here</h1>
    </div>
    <div class="hero-meta">
      <span>N sources</span>
      <span>N slides</span>
    </div>
    <div class="hero-tools">
      <!-- Buttons for transcript, book chapter, slide download -->
      <button class="hero-tool" data-toggle-panel="panel-transcript">
        Transcript
      </button>
      <a class="hero-tool hero-tool-pptx" href="/course/decks/file.pptx" download>
        PPTX
      </a>
    </div>
  </div>
  <div class="hero-right">
    <img class="brain-illu" src="/course/mascot.svg" alt="Course illustration" />
  </div>
</section>

<!-- 5. Chip strip (lecture navigation) -->
<div class="chips">
  <a class="chip active" href="./lecture-01.html">L01</a>
  <a class="chip" href="./lecture-02.html">L02</a>
  <!-- ... one chip per lecture, current = .active -->
</div>

<!-- 6. Hero panels (hidden by default, toggled by hero-tool buttons) -->
<div class="hero-panels">
  <div class="hero-panel" id="panel-transcript" hidden>
    <div class="hero-panel-head">
      <span class="hero-panel-title">Lecture transcript</span>
      <button class="hero-panel-copy" data-copy-target="text-transcript">copy</button>
      <button class="hero-panel-close" data-close="panel-transcript">×</button>
    </div>
    <pre class="hero-panel-text" id="text-transcript"
         data-src="/course/transcripts/lecture-01.txt"></pre>
  </div>
</div>

<!-- 7. Slide strip (horizontal scrollable thumbnail row) -->
<div class="slide-strip">
  <a href="/course/slides/l01_slide-01.png" data-slide="01">
    <img src="/course/slides/l01_slide-01.png" alt="Slide 01" loading="lazy"/>
    <span class="num">01</span>
  </a>
  <!-- ... one per slide -->
</div>

<!-- 8. Article body (the lecture content) -->
<article id="content" data-annot-scope="your-course:lecture-01">
  <!-- Sections are separated by hand-drawn ink dividers (automatic via CSS) -->

  <section>
    <div class="col-slides">
      <!-- Slide thumbnails float right, text wraps around -->
      <figure class="slide-embed">
        <a href="/course/slides/l01_slide-01.png" data-slide="01">
          <img src="/course/slides/l01_slide-01.png" alt="Slide 01" loading="lazy"/>
        </a>
        <figcaption><span class="num">slide 01</span></figcaption>
      </figure>
    </div>
    <div class="col-text">
      <div class="section-eyebrow">1. Section Title</div>
      <p>Body text with <strong>bold key terms</strong>. <span class="badge">Exam</span></p>
    </div>
  </section>

  <section>
    <!-- The ::before pseudo-element auto-inserts the hand-drawn divider -->
    <div class="col-text">
      <div class="section-eyebrow">2. Next Section</div>
      <p>More content here.</p>
    </div>
  </section>

</article>

<!-- 9. Lightbox (one per page, shared JS handles it) -->
<div class="lightbox" id="lightbox" role="dialog" aria-hidden="true">
  <button class="lightbox-close">×</button>
  <button class="lightbox-nav lightbox-prev">‹</button>
  <button class="lightbox-nav lightbox-next">›</button>
  <img class="lightbox-img" id="lightboxImg" alt=""/>
  <div class="lightbox-meta" id="lightboxMeta"></div>
</div>

<!-- 10. Scripts (always at bottom, always defer) -->
<script src="./course-extras.js"></script>
<script src="/shared/lightbox.js" defer></script>
<script src="/shared/annotations/annotations.js" defer></script>
</body>
</html>
```

---

## Component Reference

### Section with slides

Each `<section>` inside `<article>` gets an automatic hand-drawn ink divider between it and the next section (via `section + section::before` in CSS). Sections contain:

- `.col-slides` — floats right (320px wide), holds `figure.slide-embed` elements in a 2-column grid
- `.col-text` — flows left of the slides, contains the section body

```html
<section>
  <div class="col-slides">
    <figure class="slide-embed">
      <a href="/path/to/slide.png" data-slide="05">
        <img src="/path/to/slide.png" alt="Slide 05" loading="lazy"/>
      </a>
      <figcaption><span class="num">slide 05</span> Optional caption</figcaption>
    </figure>
  </div>
  <div class="col-text">
    <div class="section-eyebrow">5. Section Title <span class="badge">Exam</span></div>
    <p>Content goes here.</p>
  </div>
</section>
```

If a section has only 1 slide, the grid collapses to 220px single-column automatically.

### Callouts

Two flavors — professor emphasis and exam-relevant:

```html
<!-- Professor emphasis -->
<div class="callout">
  <div class="callout-label">Prof emphasis <span class="badge prof">Prof</span></div>
  <p>What the professor stressed in class.</p>
</div>

<!-- Exam callout (same structure, different badge) -->
<div class="callout">
  <div class="callout-label">Exam note <span class="badge">Exam</span></div>
  <p>This will be on the exam.</p>
</div>
```

### Inline badges

Use inline badges to mark examinable sentences:

```html
<p>The hippocampus is critical for memory consolidation. <span class="badge">Exam</span></p>
```

### Tables

Standard HTML tables, no extra classes needed. The CSS handles styling:

```html
<table>
  <thead>
    <tr><th>Term</th><th>Definition</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>fMRI</strong></td><td>Measures blood oxygenation as a proxy for neural activity</td></tr>
  </tbody>
</table>
```

### Lists

Use standard `<ul>` or `<ol>`. The CSS replaces default markers with rust-colored dots (unordered) or zero-padded numbers (ordered):

```html
<ul>
  <li><strong>Key term</strong> — explanation of the concept</li>
  <li>Another point</li>
</ul>

<ol>
  <li>First step in a process</li>
  <li>Second step</li>
</ol>
```

---

## Shared Assets — What to Reuse

These assets are shared across all courses. Never duplicate them into a course folder:

| Asset | Path | What it does |
|-------|------|-------------|
| Lightbox | `/shared/lightbox.js` | Click-to-zoom for slides. Auto-discovers `.slide-strip a` and `figure.slide-embed > a` |
| Annotations | `/shared/annotations/annotations.js` + `annotations.css` | Drag-select text to save notes. Persists to localStorage |
| Lesson shell CSS | `/shared/lesson-shell.css` | Base layout (topbar, hero, chips, sections, slides, lightbox). Used by all courses except cog-neuro (which has its own CSS) |
| Analytics | `/shared/clarity.js` | Microsoft Clarity tracking snippet |

### Course-specific assets

Each course owns these in its own folder:

| Asset | Example path | Purpose |
|-------|-------------|---------|
| Skin CSS | `/auto-sys/auto-sys.skin.css` | Token overrides, course-specific decoration |
| Mascot SVG | `/cog-neuro/brain.svg` | Hero illustration |
| Slide frame | `/cog-neuro/slide-frame.svg` | Hand-drawn ink frame overlaid on slide thumbnails |
| Section divider | `/cog-neuro/line-horizontal.svg` | Hand-drawn ink stroke between sections |
| Vertical line | `/cog-neuro/line.svg` | Callout left-border decoration |
| Extras JS | `./cog-neuro-extras.js` | Hero panel toggle logic (transcript/chapter) |
| Slides | `/course/slides/` | PNG exports of lecture slides |
| Transcripts | `/course/transcripts/` | Plain text lecture transcripts |
| Decks | `/course/decks/` | Original slide files (PPTX/PDF) |

---

## Creating a New Course

### Step 1: File structure

```
public/your-course/
├── your-course.skin.css       ← token overrides + course decoration
├── your-course-extras.js      ← hero panel logic (copy from cog-neuro-extras.js)
├── mascot.svg                 ← hero illustration
├── lectures/                  ← or put HTMLs directly in the course folder
│   ├── lecture-01.html
│   └── lecture-02.html
├── slides/                    ← slide PNGs
├── decks/                     ← original PPTX/PDF files
└── transcripts/               ← plain text transcripts
```

### Step 2: Skin CSS

Create a skin that overrides only the tokens. Do NOT rewrite layout:

```css
/* your-course.skin.css */
:root {
  --paper:     #F2EDE0;
  --paper-2:   #ECE6D6;
  --ink:       #1A1A1A;
  --ink-soft:  #2B2B2B;
  --ink-mute:  #8A8270;
  --ink-faint: #C5BEAE;
  --rule:      #1A1A1A;
  --hair:      #1F1F1F;
  --rust:      #A84F2A;      /* change this for a different accent */
  --rust-soft: #C46A3F;

  /* Optional decoration overrides */
  --slide-frame: url("/cog-neuro/slide-frame.svg");  /* reuse or replace */
  --section-sep: url("/cog-neuro/line-horizontal.svg");
  --callout-line: url("/cog-neuro/line.svg");
}
```

### Step 3: HTML head

```html
<link rel="stylesheet" href="/shared/lesson-shell.css" />
<link rel="stylesheet" href="/your-course/your-course.skin.css" />
<link rel="stylesheet" href="/shared/annotations/annotations.css" />
```

### Step 4: Annotation scope

Set the `data-annot-scope` attribute on the `<article>` element. This becomes the localStorage key:

```html
<article id="content" data-annot-scope="your-course:lecture-01">
```

The key format is `annot:<course>:<lectureId>`. Never change an existing scope value — it would orphan users' saved notes.

---

## Slide Integration

### Slide strip (top horizontal scroll)

```html
<div class="slide-strip">
  <a href="/course/slides/l01_slide-01.png" data-slide="01">
    <img src="/course/slides/l01_slide-01.png" alt="Slide 01" loading="lazy"/>
    <span class="num">01</span>
  </a>
</div>
```

The slide frame overlay (hand-drawn ink border) is applied via CSS `::after` pseudo-element. If your course skin defines `--slide-frame`, it will be used; otherwise the cog-neuro frame is used.

### In-article slides (float right)

```html
<figure class="slide-embed">
  <a href="/course/slides/l01_slide-05.png" data-slide="05">
    <img src="/course/slides/l01_slide-05.png" alt="Slide 05" loading="lazy"/>
  </a>
  <figcaption><span class="num">slide 05</span> Description</figcaption>
</figure>
```

Both flavors are auto-discovered by `lightbox.js` — no configuration needed.

---

## Rules

1. **Static HTML only** — never convert a lecture page to JSX/React
2. **Copy structure, not style** — reuse the DOM skeleton exactly; override only CSS tokens
3. **Never break annotation keys** — existing `data-annot-scope` values are permanent
4. **No emojis** in code or visible copy
5. **Reuse shared assets** — do not duplicate `lightbox.js`, `annotations.js`, or SVG decorations into course folders
6. **Lazy-load images** — always add `loading="lazy"` to slide `<img>` elements
7. **Monospace only** — no sans-serif or serif fonts anywhere
8. **No rounded corners, no gradients** — the aesthetic is brutalist editorial
9. **Defer all scripts** — use `defer` attribute on `<script>` tags
10. **Keep files small** — one HTML file per lecture, split large lectures into multiple sections within the file
