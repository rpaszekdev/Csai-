import { useState } from "react";
import Course from "./Course";

export default function Semester({ number, courses, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen);
  const empty = courses.length === 0;

  return (
    <div className="semester">
      <button
        className={`semester-toggle ${open ? "open" : ""}`}
        onClick={() => !empty && setOpen((o) => !o)}
        disabled={empty}
      >
        <span className="semester-arrow">{empty ? "·" : open ? "▾" : "▸"}</span>
        <span className="semester-label">Semester {number}</span>
        <span className="semester-count">
          {empty ? "—" : `${courses.length} course${courses.length !== 1 ? "s" : ""}`}
        </span>
      </button>

      {open && (
        <div className="semester-courses">
          {courses.map((c) => (
            <Course key={c.id} course={c} />
          ))}
        </div>
      )}
    </div>
  );
}
