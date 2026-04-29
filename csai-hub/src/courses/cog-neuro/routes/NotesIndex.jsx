import { Link } from "react-router-dom";
import { listNotes } from "../lib/pregeneratedNotes";

export default function NotesIndex() {
  const notes = listNotes();

  return (
    <>
      <header className="roadmap-header">
        <span className="roadmap-eyebrow">Lessons</span>
        <h2 className="roadmap-title">Pre-generated study notes</h2>
        <p className="roadmap-meta">{notes.length} lecture summaries with embedded slide images.</p>
      </header>

      <div className="notes-index-grid">
        {notes.map((note) => (
          <Link
            key={note.sectionId}
            to={note.sectionId}
            className="notes-index-card"
          >
            <div className="notes-index-eyebrow">{note.sectionId.toUpperCase()}</div>
            <div className="notes-index-title">{note.title}</div>
          </Link>
        ))}
      </div>
    </>
  );
}
