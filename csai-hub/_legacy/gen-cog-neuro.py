#!/usr/bin/env python3
"""Generate static HTML cog-neuro lectures from existing markdown.

Reads csai-hub/src/courses/cog-neuro/data/notes/*.md, applies the auto-sys
brutalist editorial template, swaps the slide border for cog-neuro's
hand-drawn frame, and wires up the annotation panel + lightbox.

Run once. Throwaway.
"""
import json
import re
from pathlib import Path

import markdown

REPO = Path(__file__).resolve().parent
NOTES = REPO / "csai-hub" / "src" / "courses" / "cog-neuro" / "data" / "notes"
IMAGES_JSON = REPO / "csai-hub" / "src" / "courses" / "cog-neuro" / "data" / "images.json"
SLIDES_DIR = REPO / "csai-hub" / "public" / "cog-neuro" / "slides"
OUT = REPO / "csai-hub" / "public" / "cog-neuro" / "lectures"

SECTIONS = [
    ("m1_l1",  1, 1, False),
    ("m1_l2",  1, 2, False),
    ("m2_l1",  2, 1, False),
    ("m2_l2",  2, 2, False),
    ("m3_l1",  3, 1, False),
    ("m3_l2",  3, 2, False),
    ("m4_l1",  4, 1, False),
    ("m4_l2",  4, 2, False),
    ("m5_l1",  5, 1, False),
    ("m5_l2",  5, 2, False),
    ("midterm", 0, 0, True),
]


def chip_label(sid):
    if sid == "midterm":
        return "MID"
    m = re.match(r"m(\d)_l(\d)", sid)
    return f"M{m.group(1)}L{m.group(2)}" if m else sid.upper()


def render_chips(active_sid):
    parts = []
    for sid, _, _, _ in SECTIONS:
        cls = "chip active" if sid == active_sid else "chip"
        parts.append(f'  <a class="{cls}" href="./{sid}.html">{chip_label(sid)}</a>')
    return "\n".join(parts)


def hero_num(module, lecture, is_midterm):
    if is_midterm:
        return "MID"
    return f"{module}{lecture:02d}"  # e.g. "101" → we want "01"


def render_hero_num(module, lecture, is_midterm):
    """Big outlined numeral in the hero."""
    if is_midterm:
        return '<div class="hero-num">M</div>'
    # Use lecture as the displayed number — closer match to auto-sys "01..11"
    # cog-neuro original used module number; keeping module-major to match cog-neuro
    return f'<div class="hero-num">{module:02d}</div>'


def parse_meta_title(title):
    """'Module 4 Lecture 1: Emotion and Social Cognition' →
    ('Module 04 · Lecture 01 —', 'Emotion and Social Cognition')."""
    m = re.match(r"Module\s+(\d)\s+Lecture\s+(\d):\s*(.+)", title)
    if m:
        eyebrow = f"Module 0{m.group(1)} · Lecture 0{m.group(2)} —"
        return eyebrow, m.group(3).strip()
    if title.lower().startswith("midterm"):
        return "Module 03 · Recap —", "Midterm Review"
    return "Lecture —", title


# ─── markdown post-processing ─────────────────────────────────────────────

EXAM_INLINE = re.compile(r"\[EXAM\]")
PROF_INLINE = re.compile(r"\[PROF EMPHASIS\]")


def post_process_html(html):
    """Apply editorial transforms to the rendered HTML.

    1. drop the H1 (page title is in the hero) and any "Study Notes for Exam Preparation" subtitle
    2. wrap each top-level H2 + following content into a <section>
    3. blockquotes that begin with "[PROF EMPHASIS]" → .callout with prof badge
    4. inline [EXAM] / [PROF EMPHASIS] strings → badge spans
    5. <h2> → <div class="section-eyebrow">…</div>; collapse into the section opener
    """
    # 1. Drop top H1 (renders only the first one — there's just one in our notes)
    html = re.sub(r"<h1>.*?</h1>\s*", "", html, count=1, flags=re.DOTALL)
    # Drop "Study Notes for Exam Preparation" H2 boilerplate
    html = re.sub(
        r"<h2>\s*Study Notes for Exam Preparation\s*</h2>\s*",
        "",
        html,
        count=1,
        flags=re.IGNORECASE,
    )
    # Drop standalone <hr/> separators (markdown emits these for `---`)
    html = re.sub(r"<hr\s*/?>\s*", "", html)

    # 2. Convert blockquotes starting with [PROF EMPHASIS] into callouts
    def prof_callout(match):
        inner = match.group(1).strip()
        # Strip the leading [PROF EMPHASIS] tag from the inner content
        inner = re.sub(r"^\s*<p>\s*\[PROF EMPHASIS\]\s*", "<p>", inner, count=1)
        return (
            '<div class="callout">'
            '<div class="callout-label">Prof emphasis '
            '<span class="badge prof">Prof</span></div>'
            f"{inner}"
            "</div>"
        )

    html = re.sub(
        r"<blockquote>\s*(.*?)\s*</blockquote>",
        prof_callout,
        html,
        flags=re.DOTALL,
    )

    # 3. Inline [EXAM] / [PROF EMPHASIS] → badge spans
    html = EXAM_INLINE.sub('<span class="badge">Exam</span>', html)
    html = PROF_INLINE.sub('<span class="badge prof">Prof</span>', html)

    # 4. Wrap H2-delimited blocks in <section> with the eyebrow style
    # Strategy: split on <h2>...</h2>, then rebuild, wrapping each chunk.
    parts = re.split(r"(<h2>.*?</h2>)", html, flags=re.DOTALL)
    # parts: [pre_h2_content, h2_1, between_1, h2_2, between_2, …]
    sections = []
    if parts and parts[0].strip():
        # any content before the first H2 stays at the top
        sections.append(parts[0])
    i = 1
    while i < len(parts):
        h2 = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        eyebrow_text = re.sub(r"<h2>(.*?)</h2>", r"\1", h2, flags=re.DOTALL).strip()
        # detect [EXAM] flag on the heading itself (already converted to badge)
        sections.append(
            '<section>\n'
            '<div class="col-text">\n'
            f'<div class="section-eyebrow">{eyebrow_text}</div>\n'
            f'{body}\n'
            '</div>\n'
            '</section>'
        )
        i += 2
    return "\n\n".join(sections)


def inject_slide_clusters(sections_html, image_urls):
    """Distribute slide thumbnails across sections.

    image_urls is the ordered list of slide URLs from images.json. We split
    them ~evenly across sections and insert a `<div class="col-slides">` at
    the top of each section's <div class="col-text"> sibling.
    """
    section_starts = list(re.finditer(r"<section>\s*<div class=\"col-text\">", sections_html))
    n_sections = len(section_starts)
    if n_sections == 0 or not image_urls:
        return sections_html

    # Distribute slides across sections, capped at MAX_PER_SECTION per cluster.
    # If we'd overflow, prefer evenness over completeness — extra slides fall
    # off the right margin gracefully (the user can always open the slide PDF
    # for the full deck).
    MAX_PER_SECTION = 4
    n_slides = len(image_urls)
    base = min(MAX_PER_SECTION, max(1, n_slides // n_sections))
    distribution = []
    cursor = 0
    for s_idx in range(n_sections):
        take = min(MAX_PER_SECTION, base, len(image_urls) - cursor)
        if take < 0:
            take = 0
        distribution.append(image_urls[cursor : cursor + take])
        cursor += take
    # Any leftover slides go onto the last section's cluster (capped to 6 there)
    if cursor < n_slides and distribution:
        spare = image_urls[cursor:]
        distribution[-1] = (distribution[-1] + spare)[:6]

    # Build a new HTML by inserting col-slides at each section start
    out = []
    last = 0
    for s_idx, sect_match in enumerate(section_starts):
        out.append(sections_html[last : sect_match.start()])
        slides = distribution[s_idx]
        cluster = ""
        if slides:
            figs = []
            for url in slides:
                # Extract slide number from either:
                #   /cog-neuro/slides/m1_l1_slide-04.png       (dashed)
                #   /cog-neuro/study-images/.../slide04_img006.png  (no dash)
                num_match = re.search(r"slide[-_]?(\d+)", url)
                slide_n = num_match.group(1).zfill(2) if num_match else ""
                figs.append(
                    '<figure class="slide-embed">'
                    f'<a href="{url}" data-slide="{slide_n}"><img src="{url}" alt="Slide {slide_n}" loading="lazy"/></a>'
                    f'<figcaption><span class="num">slide {slide_n}</span></figcaption>'
                    '</figure>'
                )
            cluster = '<div class="col-slides">\n' + "\n".join(figs) + "\n</div>\n"
        # Replace the matched `<section>\n<div class="col-text">` with our
        # version that includes the cluster before the col-text wrapper.
        out.append("<section>\n" + cluster)
        out.append('<div class="col-text">')
        last = sect_match.end()
    out.append(sections_html[last:])
    return "".join(out)


# ─── template ──────────────────────────────────────────────────────────────

TEMPLATE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{chip_label} — {hero_title}</title>
<link rel="stylesheet" href="./cog-neuro.css" />
</head>
<body>
<div class="rust-bar"></div>

<header class="topbar">
  <a href="/" class="back">← Back</a>
  <span class="brand">
    <span class="mark"></span>
    <span class="name">Cognitive Neuroscience</span>
  </span>
  <span class="crumbs">
    <span>Tilburg</span>
    <span>Year 2</span>
    <span>Sem 4</span>
  </span>
</header>

<nav class="tabs">
  <a href="/courses/cog-neuro/roadmap">Roadmap</a>
  <a href="#" class="active">Lessons</a>
  <a href="/courses/cog-neuro/quiz">Quizzes</a>
  <a href="/courses/cog-neuro/brain-quiz">Brain Quiz</a>
</nav>

<section class="hero">
  <div class="hero-left">
    {hero_num_html}
    <div class="hero-title-block">
      <span class="hero-eyebrow">{hero_eyebrow}</span>
      <h1 class="hero-title">{hero_title}</h1>
    </div>
    <div class="hero-meta">
      {meta_pills}
    </div>
  </div>
  <div class="hero-right">
    <img class="brain-illu" src="/cog-neuro/brain.svg" alt="Cognitive Neuroscience brain illustration" />
  </div>
</section>

<div class="chips">
{chip_strip}
</div>

<div class="slide-strip">
{slide_strip}
</div>

<article id="content">

{body}

</article>

<!-- Annotation panel -->
<aside class="annot-panel" aria-label="Saved annotations" id="annotPanel">
  <button type="button" class="annot-panel-toggle">
    <span class="annot-panel-icon">✎</span>
    <span class="annot-panel-count">0</span>
    <span class="annot-panel-label">notes</span>
  </button>
  <div class="annot-panel-list"></div>
</aside>

<!-- Lightbox -->
<div class="lightbox" id="lightbox" role="dialog" aria-hidden="true" aria-label="Slide viewer">
  <button class="lightbox-close" id="lightboxClose" aria-label="Close">×</button>
  <button class="lightbox-nav lightbox-prev" id="lightboxPrev" aria-label="Previous slide">‹</button>
  <button class="lightbox-nav lightbox-next" id="lightboxNext" aria-label="Next slide">›</button>
  <img class="lightbox-img" id="lightboxImg" alt=""/>
  <div class="lightbox-meta" id="lightboxMeta"></div>
</div>

<script src="./lightbox.js"></script>
<script src="./cog-neuro-annot.js"></script>
<script>
  window.cogAnnot.mount({{
    sectionId: "{section_id}",
    contentEl: document.getElementById("content"),
    panelEl: document.getElementById("annotPanel"),
  }});
</script>
</body>
</html>
"""


def main():
    images_json = json.loads(IMAGES_JSON.read_text())
    OUT.mkdir(parents=True, exist_ok=True)

    md_converter = markdown.Markdown(extensions=["tables", "fenced_code"])

    for sid, module, lecture, is_midterm in SECTIONS:
        md_path = NOTES / f"{sid}.md"
        meta_path = NOTES / f"{sid}.meta.json"
        if not md_path.exists():
            print(f"  skip {sid} — no .md file")
            continue
        md_text = md_path.read_text()
        meta = json.loads(meta_path.read_text())

        eyebrow, hero_title = parse_meta_title(meta["title"])
        sources = meta.get("sources", [])

        # Prefer full slide pages from /cog-neuro/slides/ — one image per slide,
        # cleaner thumbnails for the brutalist editorial cluster. Fall back to
        # the in-slide figure extracts in images.json when no slide pages exist.
        slide_files = sorted(SLIDES_DIR.glob(f"{sid}_slide-*.png"))
        if slide_files:
            image_urls = [f"/cog-neuro/slides/{p.name}" for p in slide_files]
        else:
            section_images = images_json.get(sid, [])
            image_urls = [img["url"] for img in section_images if img.get("type") == "slide"]
        section_image_count = len(image_urls)

        # 1. md → html
        md_converter.reset()
        body_html = md_converter.convert(md_text)
        # 2. post-process
        body_html = post_process_html(body_html)
        # 3. inject slide clusters
        body_html = inject_slide_clusters(body_html, image_urls)

        # 4. render template
        meta_pills_html = (
            f"<span>{len(sources)} source{'s' if len(sources) != 1 else ''}</span>\n"
            f"      <span>{section_image_count} slides</span>"
        )

        # Top slide strip — every slide for the lecture, in order
        slide_strip_items = []
        for url in image_urls:
            num_match = re.search(r"slide[-_]?(\d+)", url)
            slide_n = num_match.group(1).zfill(2) if num_match else ""
            slide_strip_items.append(
                f'<a href="{url}" data-slide="{slide_n}">'
                f'<img src="{url}" alt="Slide {slide_n}" loading="lazy"/>'
                f'<span class="num">{slide_n}</span>'
                '</a>'
            )
        slide_strip_html = "\n".join(slide_strip_items)
        html = TEMPLATE.format(
            chip_label=chip_label(sid),
            hero_title=hero_title.replace("&", "&amp;"),
            hero_num_html=render_hero_num(module, lecture, is_midterm),
            hero_eyebrow=eyebrow,
            meta_pills=meta_pills_html,
            chip_strip=render_chips(sid),
            slide_strip=slide_strip_html,
            section_id=sid,
            body=body_html,
        )

        out_path = OUT / f"{sid}.html"
        out_path.write_text(html)
        print(f"  ✓ {sid}.html — {len(image_urls)} slides")

    print(f"\nWrote 11 lectures to {OUT}")


if __name__ == "__main__":
    main()
