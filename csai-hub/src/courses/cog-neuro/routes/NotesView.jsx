import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getNote, getSectionImages, listNotes } from "../lib/pregeneratedNotes";
import { detectRegions } from "../data/brain-regions";
import BrainPreview from "./BrainPreview";

const TAG_REGEX = /\[(EXAM|PROF EMPHASIS)\]/g;

function renderTaggedText(text) {
  const parts = [];
  let lastIndex = 0;
  let match;
  let index = 0;
  while ((match = TAG_REGEX.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
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

function slugify(text) {
  return String(text)
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function flattenChildren(children) {
  if (typeof children === "string") return children;
  if (Array.isArray(children)) return children.map(flattenChildren).join("");
  if (children && children.props) return flattenChildren(children.props.children);
  return "";
}

function buildHeadingComponents() {
  const make = (Tag) =>
    function Heading({ children, ...rest }) {
      const text = flattenChildren(children);
      const id = slugify(text);
      return (
        <Tag id={id} {...rest}>
          {processChildren(children)}
        </Tag>
      );
    };
  return {
    h1: make("h1"),
    h2: make("h2"),
    h3: make("h3"),
    h4: make("h4"),
  };
}

const headingComponents = buildHeadingComponents();

const markdownComponents = {
  ...headingComponents,
  p: ({ children }) => <p>{processChildren(children)}</p>,
  li: ({ children }) => <li>{processChildren(children)}</li>,
  strong: ({ children }) => <strong>{processChildren(children)}</strong>,
};

function shortLabel(title) {
  const match = title.match(/Module\s*(\d+)\s*Lecture\s*(\d+)/i);
  if (match) return `M${match[1]}L${match[2]}`;
  if (/midterm/i.test(title)) return "Midterm";
  return title.slice(0, 12);
}

function cleanMarkdown(md) {
  if (!md) return md;
  return md
    .replace(/^#\s.+?\n+/, "")
    .replace(/^##\s+Study Notes for Exam Preparation\s*\n+/im, "")
    .replace(/^---\s*\n+/m, "");
}

function buildToc(md) {
  if (!md) return [];
  const lines = md.split("\n");
  const items = [];
  for (const line of lines) {
    const m = line.match(/^(#{2,3})\s+(.+?)\s*$/);
    if (!m) continue;
    const level = m[1].length;
    const text = m[2].replace(/\[EXAM\]|\[PROF EMPHASIS\]/g, "").trim();
    if (!text || /study notes for exam preparation/i.test(text)) continue;
    items.push({ level, text, id: slugify(text) });
  }
  return items;
}

export default function NotesView() {
  const { sectionId } = useParams();
  const note = useMemo(() => getNote(sectionId), [sectionId]);
  const cleanedMarkdown = useMemo(() => cleanMarkdown(note?.markdown), [note?.markdown]);
  const slideImages = useMemo(() => getSectionImages(sectionId, "slide"), [sectionId]);
  const notes = useMemo(() => listNotes(), []);
  const detectedRegions = useMemo(
    () => (note ? detectRegions(note.markdown).slice(0, 6) : []),
    [note],
  );
  const toc = useMemo(() => buildToc(cleanedMarkdown), [cleanedMarkdown]);

  return (
    <div className="notes-layout">
      <nav className="notes-lecture-strip">
        {notes.map((n) => (
          <Link
            key={n.sectionId}
            to={`../notes/${n.sectionId}`}
            className={`notes-lecture-chip ${n.sectionId === sectionId ? "active" : ""}`}
            title={n.title}
          >
            {shortLabel(n.title)}
          </Link>
        ))}
      </nav>

      <div className="notes-grid">
        <article className="notes-main">
          {note ? (
            <>
              <header className="notes-main-head">
                <h2 className="notes-main-title">{note.title}</h2>
                <div className="notes-main-meta">
                  <span className="notes-meta-chip">{note.sources.length} sources</span>
                  <span className="notes-meta-chip">{note.images.length} img</span>
                </div>
              </header>

              {slideImages.length > 0 && (
                <div className="notes-image-strip">
                  {slideImages.map((img, i) => (
                    <a
                      key={i}
                      href={img.url}
                      target="_blank"
                      rel="noreferrer"
                      className="notes-image"
                    >
                      <img src={img.url} alt={img.caption} loading="lazy" />
                    </a>
                  ))}
                </div>
              )}

              <div className="notes-body">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {cleanedMarkdown}
                </ReactMarkdown>
              </div>
            </>
          ) : (
            <div style={{ padding: "var(--space-lg)" }}>
              <p>
                Note not found for section <code>{sectionId}</code>.
              </p>
            </div>
          )}
        </article>

        <aside className="notes-side-rail">
          <div className="notes-brain-card">
            <div className="notes-brain-head">Regions in this lecture</div>
            <BrainPreview regions={detectedRegions} />
            {detectedRegions.length > 0 && (
              <ul className="notes-brain-legend">
                {detectedRegions.map((r) => (
                  <li key={r.id}>
                    <span
                      className="notes-brain-dot"
                      style={{
                        background: `rgb(${r.color[0]}, ${r.color[1]}, ${r.color[2]})`,
                      }}
                    />
                    {r.name}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {toc.length > 0 && (
            <nav className="notes-toc">
              <div className="notes-toc-head">On this page</div>
              <ul>
                {toc.map((item, i) => (
                  <li
                    key={`${item.id}-${i}`}
                    className={`notes-toc-item lvl-${item.level}`}
                  >
                    <a href={`#${item.id}`}>{item.text}</a>
                  </li>
                ))}
              </ul>
            </nav>
          )}
        </aside>
      </div>
    </div>
  );
}
