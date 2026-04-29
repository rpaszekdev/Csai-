import { useEffect, useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getNote, getSectionImages, listNotes } from "../lib/pregeneratedNotes";
import { detectRegions } from "../data/brain-regions";
import { useMeasuredBody } from "../lib/useMeasuredBody";

const BODY_FONT = '13px "IBM Plex Mono"';
const BODY_LINE_HEIGHT = 22;

// Width reserved on the right of the body for the vertical line separator.
// Kept in sync with `.editorial-body--wrapped { padding-right }` in styles.css.
const LINE_GUTTER = 480;

const TAG_REGEX = /\[(EXAM|PROF EMPHASIS)\]/g;

function renderTaggedText(text) {
  const parts = [];
  let lastIndex = 0;
  let match;
  let index = 0;
  while ((match = TAG_REGEX.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index));
    const isExam = match[1] === "EXAM";
    parts.push(
      <span
        key={`tag-${index++}-${match.index}`}
        className={`exam-badge ${isExam ? "" : "prof"}`}
      >
        {isExam ? "Exam" : "Prof"}
      </span>,
    );
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts;
}

function processChildren(children) {
  if (typeof children === "string") return renderTaggedText(children);
  if (Array.isArray(children)) {
    return children.map((child, i) => {
      if (typeof child === "string") {
        const replaced = renderTaggedText(child);
        if (Array.isArray(replaced)) {
          return replaced.map((part, j) =>
            typeof part === "string" ? part : { ...part, key: `${i}-${j}` },
          );
        }
        return replaced;
      }
      return child;
    });
  }
  return children;
}

function buildMarkdownComponents(slides) {
  // Mutable counter shared across the render; ReactMarkdown walks the tree
  // top-down, so headings are visited in document order — each one consumes
  // the next slide thumbnail.
  let h2Index = 0;

  return {
    p: ({ children }) => <p>{processChildren(children)}</p>,
    li: ({ children }) => <li>{processChildren(children)}</li>,
    strong: ({ children }) => <strong>{processChildren(children)}</strong>,
    h2: ({ children }) => {
      const slide = slides[h2Index++];
      return (
        <div className="editorial-section-head">
          <h2>{processChildren(children)}</h2>
          {slide && (
            <aside className="editorial-slide-aside">
              <a href={slide.url} target="_blank" rel="noreferrer">
                <img src={slide.url} alt={slide.caption} loading="lazy" />
              </a>
              <div className="editorial-slide-cap">Slide {slide.slide}</div>
            </aside>
          )}
        </div>
      );
    },
  };
}

// Keep one thumbnail per slide number — duplicates from the same slide page
// would just stack identical images down the gutter.
function dedupeSlides(images) {
  const seen = new Set();
  const out = [];
  for (const img of images) {
    if (seen.has(img.slide)) continue;
    seen.add(img.slide);
    out.push(img);
  }
  return out;
}

function shortLabel(title) {
  const match = title.match(/Module\s*(\d+)\s*Lecture\s*(\d+)/i);
  if (match) return `M${match[1]}L${match[2]}`;
  if (/midterm/i.test(title)) return "Mid";
  return title.slice(0, 6);
}

function cleanMarkdown(md) {
  if (!md) return md;
  return md
    .replace(/^#\s.+?\n+/, "")
    .replace(/^##\s+Study Notes for Exam Preparation\s*\n+/im, "")
    .replace(/^---\s*\n+/m, "");
}

function parseLectureTitle(title = "") {
  const match = title.match(
    /Module\s*(\d+)\s*[—\-]?\s*Lecture\s*(\d+)\s*[:\-]\s*(.+)/i,
  );
  if (match) {
    return {
      module: match[1].padStart(2, "0"),
      lecture: match[2].padStart(2, "0"),
      name: match[3].trim(),
    };
  }
  return { module: "00", lecture: "00", name: title };
}

const TODAY = new Date().toISOString().slice(0, 10);

export default function NotesView() {
  const { sectionId } = useParams();
  const note = useMemo(() => getNote(sectionId), [sectionId]);
  const cleanedMarkdown = useMemo(
    () => cleanMarkdown(note?.markdown),
    [note?.markdown],
  );
  const slideImages = useMemo(
    () => dedupeSlides(getSectionImages(sectionId, "slide")),
    [sectionId],
  );
  const markdownComponents = useMemo(
    () => buildMarkdownComponents(slideImages),
    [slideImages],
  );
  const notes = useMemo(() => listNotes(), []);
  const detectedRegions = useMemo(
    () => (note ? detectRegions(note.markdown).slice(0, 6) : []),
    [note],
  );
  const meta = note ? parseLectureTitle(note.title) : null;
  const cardIndex = useMemo(
    () => notes.findIndex((n) => n.sectionId === sectionId),
    [notes, sectionId],
  );

  // The vertical line.svg separator reserves a fixed gutter on the right.
  // One width band — pretext just measures against the narrower column.
  const getMaxWidth = useMemo(
    () => (_y, containerWidth) => containerWidth - LINE_GUTTER,
    [],
  );

  const [bodyHeight, , bodyMeasureRef] = useMeasuredBody(cleanedMarkdown, {
    font: BODY_FONT,
    lineHeight: BODY_LINE_HEIGHT,
    getMaxWidth,
  });

  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty("--cog-body-height", `${Math.round(bodyHeight)}px`);
    return () => {
      root.style.removeProperty("--cog-body-height");
    };
  }, [bodyHeight]);

  return (
    <div className="editorial">
      <header className="editorial-hero">
        <div className="editorial-num">{meta ? meta.module : "00"}</div>
        <div>
          <p className="editorial-eyebrow">
            {meta
              ? `Module ${meta.module} · Lecture ${meta.lecture} — ${meta.name}`
              : note?.title || "Lecture"}
          </p>
        </div>
        <p className="editorial-card">
          Card #{cardIndex >= 0 ? cardIndex + 1 : "?"} of {notes.length} ·
          Tilburg University · {TODAY}
        </p>
      </header>

      <nav className="editorial-chips">
        {notes.map((n) => (
          <Link
            key={n.sectionId}
            to={`../notes/${n.sectionId}`}
            className={`editorial-chip ${n.sectionId === sectionId ? "active" : ""}`}
            title={n.title}
          >
            {shortLabel(n.title)}
          </Link>
        ))}
      </nav>

      {detectedRegions.length > 0 && (
        <ul className="editorial-region-list">
          {detectedRegions.map((r) => (
            <li key={r.id}>{r.name}</li>
          ))}
        </ul>
      )}

      <article
        className="editorial-body editorial-body--wrapped"
        ref={bodyMeasureRef}
      >
        {note ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {cleanedMarkdown}
          </ReactMarkdown>
        ) : (
          <p>Note not found for section {sectionId}.</p>
        )}
      </article>
    </div>
  );
}
