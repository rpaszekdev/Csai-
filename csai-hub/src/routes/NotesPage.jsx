import { useState, useMemo } from "react";
import { useCreateBlockNote } from "@blocknote/react";
import { BlockNoteView } from "@blocknote/mantine";
import { Link } from "react-router-dom";
import "@blocknote/core/fonts/inter.css";
import "@blocknote/mantine/style.css";

const COURSES = [
  { id: "cog-neuro", name: "Cog Neuro" },
  { id: "auto-sys", name: "Auto Sys" },
  { id: "deep-learn", name: "Deep Learning" },
  { id: "adv-prog", name: "Adv Prog" },
  { id: "research", name: "Research WS" },
  { id: "general", name: "General" },
];

const STORAGE_KEY = (id) => `csai-notes:${id}`;

function loadContent(courseId) {
  try {
    const raw = localStorage.getItem(STORAGE_KEY(courseId));
    return raw ? JSON.parse(raw) : undefined;
  } catch {
    return undefined;
  }
}

function saveContent(courseId, content) {
  localStorage.setItem(STORAGE_KEY(courseId), JSON.stringify(content));
}

function NoteEditor({ courseId }) {
  const initial = useMemo(() => loadContent(courseId), [courseId]);

  const editor = useCreateBlockNote({
    initialContent: initial,
  });

  return (
    <div className="notes-editor">
      <BlockNoteView
        editor={editor}
        onChange={() => {
          saveContent(courseId, editor.document);
        }}
        theme="light"
      />
    </div>
  );
}

export default function NotesPage() {
  const [activeCourse, setActiveCourse] = useState("general");

  return (
    <div className="notes-page">
      <div className="notes-rust-bar" />

      <header className="notes-topbar">
        <Link to="/" className="notes-back">
          &larr; CSAI HUB
        </Link>
        <div className="notes-brand">
          <span className="notes-mark" />
          <span className="notes-brand-name">NOTES</span>
        </div>
      </header>

      <nav className="notes-tabs">
        {COURSES.map((c) => (
          <button
            key={c.id}
            className={`notes-tab ${activeCourse === c.id ? "active" : ""}`}
            onClick={() => setActiveCourse(c.id)}
          >
            {c.name}
          </button>
        ))}
      </nav>

      <div className="notes-body">
        <NoteEditor key={activeCourse} courseId={activeCourse} />
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        .notes-page {
          --paper: #F2EDE0;
          --paper-2: #ECE6D6;
          --ink: #1A1A1A;
          --ink-soft: #2B2B2B;
          --ink-mute: #8A8270;
          --ink-faint: #C5BEAE;
          --rust: #A84F2A;

          min-height: 100vh;
          background: var(--paper);
          color: var(--ink);
          font-family: "JetBrains Mono", "IBM Plex Mono", "SF Mono", ui-monospace, monospace;
          display: flex;
          flex-direction: column;
        }

        .notes-rust-bar {
          height: 4px;
          width: 100%;
          background: var(--rust);
        }

        .notes-topbar {
          display: flex;
          align-items: center;
          padding: 22px 36px 18px;
          border-bottom: 1px solid var(--ink-faint);
          gap: 28px;
        }

        .notes-back {
          color: var(--ink);
          text-decoration: none;
          font-size: 12px;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          font-weight: 500;
          font-family: inherit;
        }

        .notes-back:hover {
          color: var(--rust);
        }

        .notes-brand {
          display: flex;
          align-items: center;
          gap: 14px;
        }

        .notes-mark {
          width: 14px;
          height: 14px;
          background: var(--rust);
          display: inline-block;
        }

        .notes-brand-name {
          font-size: 13px;
          letter-spacing: 0.22em;
          text-transform: uppercase;
          font-weight: 600;
        }

        .notes-tabs {
          display: flex;
          gap: 38px;
          padding: 16px 36px 0;
          border-bottom: 1px solid var(--ink-faint);
          overflow-x: auto;
        }

        .notes-tab {
          position: relative;
          padding: 10px 0 14px;
          border: none;
          background: none;
          cursor: pointer;
          color: var(--ink-mute);
          font-family: inherit;
          font-size: 12px;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          font-weight: 500;
          white-space: nowrap;
          transition: color 0.15s;
        }

        .notes-tab:hover {
          color: var(--ink);
        }

        .notes-tab.active {
          color: var(--ink);
          font-weight: 700;
        }

        .notes-tab.active::after {
          content: "";
          position: absolute;
          bottom: -1px;
          left: 0;
          right: 0;
          height: 2px;
          background: var(--ink);
        }

        .notes-body {
          flex: 1;
          max-width: 780px;
          width: 100%;
          margin: 0 auto;
          padding: 48px 36px;
        }

        .notes-editor {
          min-height: 70vh;
        }

        /* ─── BlockNote theme overrides ─── */
        .notes-editor .bn-container {
          font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
          --bn-colors-editor-background: var(--paper);
          --bn-colors-editor-text: var(--ink);
          --bn-colors-menu-background: var(--paper-2);
          --bn-colors-menu-text: var(--ink);
          --bn-colors-hovered-background: var(--paper-2);
          --bn-colors-selected-background: rgba(168, 79, 42, 0.10);
          --bn-colors-highlights-default-background: rgba(168, 79, 42, 0.10);
          --bn-colors-highlights-default-text: var(--ink);
          --bn-font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
          --bn-border-radius: 0px;
        }

        .notes-editor .bn-container [class*="blockContent"] {
          font-size: 14px;
          line-height: 1.65;
        }

        .notes-editor .bn-container h1,
        .notes-editor .bn-container h2,
        .notes-editor .bn-container h3 {
          font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--ink-mute);
          font-weight: 500;
        }

        .notes-editor .bn-container h1 {
          font-size: 14px;
          margin-top: 32px;
        }

        .notes-editor .bn-container h2 {
          font-size: 13px;
          margin-top: 24px;
        }

        .notes-editor .bn-container h3 {
          font-size: 12px;
          margin-top: 16px;
        }

        .notes-editor .bn-container [class*="sideMenu"] {
          opacity: 0.3;
        }

        .notes-editor .bn-container [class*="sideMenu"]:hover {
          opacity: 0.7;
        }
      `}</style>
    </div>
  );
}
