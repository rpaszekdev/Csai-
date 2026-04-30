# CLAUDE.md — csai-hub

Repo-level guidance for Claude Code. Read first before editing.

---

## Ground-truth lecture template: Cognitive Neuroscience

**The cog-neuro lecture pages are the canonical reference for how every
course's lecture/section pages should look in this project.** When building
pages for any other course (auto-sys, deep-learn, comp-ling, adv-prog, etc.),
match the cog-neuro look, layout, and interaction patterns unless the user
explicitly asks for something different.

### Reference files (do not change without an explicit request)

| Path | What it is |
|---|---|
| `public/cog-neuro/lectures/m1_l1.html` … `midterm.html` | 11 self-contained static lecture HTMLs — the visual + structural template |
| `public/cog-neuro/lectures/cog-neuro.css` | Shared editorial stylesheet — fonts, colour tokens, hero, chip strip, callouts, slide-frame, divider, annotation panel |
| `public/cog-neuro/lectures/cog-neuro-extras.js` | Hero-tool toggles (transcript / book chapter panels) |
| `public/cog-neuro/lectures/brain-link.js` | Inline brain-region viewer hook |
| `public/cog-neuro/line-horizontal.svg` | Hand-drawn rotated line.svg used as the section divider (`article section + section::before`) |
| `public/cog-neuro/slide-frame.svg` | Hand-drawn ink frame overlay for slide thumbnails |
| `/shared/lightbox.js`, `/shared/annotations/annotations.js` | Drop-in lightbox + drag-select annotation layer used by every cog-neuro lecture |

### What "the cog-neuro look" means

- **Brutalist editorial palette**: cream paper `#F2EDE0`, ink `#1A1A1A`, rust accent `#A84F2A`, monospace body (JetBrains Mono → IBM Plex Mono fallback)
- **Hero block** with outlined number, eyebrow, title, and tool buttons (transcript / chapter)
- **Chip strip** linking sibling lectures, current one marked active
- **Section structure**: each numbered section has a `.section-eyebrow` heading, body text in the left column, and a `.col-slides` cluster floating on the right with hand-drawn ink-framed slide thumbnails (lightbox on click)
- **Section divider**: thin, wide horizontal hand-drawn ink stroke (`line-horizontal.svg` stretched via `preserveAspectRatio="none"`), generous vertical margin (~96px) above and below
- **Callouts**: `.callout` with `[Prof]` badge for emphasis, `.callout.exam` with `[Exam]` badge for examinable points; small inline `<span class="badge">Exam</span>` after sentences
- **Annotation layer**: drag-select text → save note popover in the right gutter → highlights persist via `localStorage` key `cog-neuro:annot:<sectionId>`; `0 NOTES` pill in the hero opens a side drawer
- **No React route for lectures** — they are static HTML served from `public/`. The React side (`/courses/cog-neuro/...`) only renders Roadmap, Quizzes, Brain Quiz tabs and links out to the static HTMLs

### When adapting to another course

1. Copy `cog-neuro.css` as the starting stylesheet — only override course-specific tokens (palette accent, hero illustration). Do **not** rewrite layout primitives.
2. Reuse `slide-frame.svg`, `line-horizontal.svg`, `/shared/lightbox.js`, `/shared/annotations/annotations.js` directly.
3. Keep the same DOM structure for sections, callouts, slide clusters, and the hero so cross-course visuals stay coherent.
4. New annotation `localStorage` keys follow the pattern `<course>:annot:<sectionId>`.
5. If the user shows a screenshot of a cog-neuro lecture and asks to "match this style" for another course, the answer is always yes — replicate verbatim.

---

## Landing page

- `src/App.jsx` is data-driven from `src/data/courses.js` (`PROGRAM`). Adding a course = appending to the appropriate semester's `courses` array — no component edits required.
- `ALL_EXAMS` and `ALL_ASSIGNMENTS` are flat aggregations over `PROGRAM`; the Exam Schedule table filters to `type === "Final"`, the Required-Work table shows every entry.
- Introduction component (`src/components/Introduction.jsx`) is the page's intro block: short copy, WhatsApp contact pill, `— Robert` signoff in display font. Don't add Notion or other external links here unless explicitly asked.

---

## Conventions

- **Pages over routes**: lecture content is static HTML in `public/`, not React routes. Resist the temptation to "Reactify" a working static page.
- **Annotation contract**: never break the `localStorage` key shape `<course>:annot:<sectionId>`. Existing user notes must keep working.
- **Slide URLs**: cog-neuro slides live under `/cog-neuro/study-images/M0X_LX_images/M0X_LX_slideNN_imgNNN.{jpg,png}`; references are pre-baked into the HTML at generation time.
- **No emojis** in code or copy unless the user asks.
- **No backwards-compat shims** when removing code — delete cleanly.
