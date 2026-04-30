import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { STATIC_ROADMAP } from "../data/roadmap";

const STORAGE_KEY = "cog-neuro:roadmap:done";

function loadDone() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
}

function saveDone(set) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...set]));
}

// Module title in roadmap data: "Module 1: History & Methodology" → split into
// numeral ("01") and short title ("History & Methodology").
function splitModuleName(name = "") {
  const m = name.match(/Module\s*(\d+)\s*:\s*(.+)/i);
  if (!m) return { num: "··", title: name };
  return { num: m[1].padStart(2, "0"), title: m[2].trim() };
}

// Lecture title in roadmap data: "Module 1 Lecture 1: Methods" → code "M1·L1"
// and short title "Methods".
function splitLectureTitle(title = "") {
  const m = title.match(/Module\s*(\d+)\s*Lecture\s*(\d+)\s*:\s*(.+)/i);
  if (!m) return { code: "L?", name: title };
  return { code: `M${m[1]}·L${m[2]}`, name: m[3].trim() };
}

// "Weeks 3-4 — Ch. 5" → "wk 3–4". Strip the chapter portion since chapter
// references are already shown per-lecture.
function shortWeeks(weeks = "") {
  const m = weeks.match(/Weeks?\s*(\d+(?:\s*[-–]\s*\d+)?)/i);
  if (!m) return weeks.toLowerCase();
  return `wk ${m[1].replace(/\s*-\s*/, "–")}`;
}

function daysUntil(dateStr) {
  if (!dateStr) return null;
  const target = new Date(dateStr + "T00:00:00");
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diff = Math.round((target - today) / (1000 * 60 * 60 * 24));
  return diff;
}

export default function RoadmapView() {
  const [done, setDone] = useState(() => loadDone());

  const allLectureIds = useMemo(() => {
    const ids = [];
    for (const phase of STATIC_ROADMAP.phases) {
      for (const lecture of phase.lectures ?? []) ids.push(lecture.id);
    }
    return ids;
  }, []);

  const completed = allLectureIds.filter((id) => done.has(id)).length;
  const total = allLectureIds.length;
  const pct = total === 0 ? 0 : Math.round((completed / total) * 100);
  const daysLeft = daysUntil(STATIC_ROADMAP.exam_date);

  useEffect(() => {
    saveDone(done);
  }, [done]);

  const toggle = (lectureId) => {
    setDone((prev) => {
      const next = new Set(prev);
      if (next.has(lectureId)) next.delete(lectureId);
      else next.add(lectureId);
      return next;
    });
  };

  return (
    <div className="roadmap-list">
      <header className="roadmap-list-head">
        <p className="roadmap-list-eyebrow">Study Roadmap</p>
        <h1 className="roadmap-list-title">{STATIC_ROADMAP.name}</h1>
        <p className="roadmap-list-meta">
          <span>Exam {STATIC_ROADMAP.exam_date}</span>
          {daysLeft !== null && daysLeft >= 0 && (
            <>
              <span className="roadmap-list-dot">·</span>
              <span>{daysLeft} days remaining</span>
            </>
          )}
          <span className="roadmap-list-dot">·</span>
          <span>{pct}% complete</span>
        </p>
      </header>

      <div className="roadmap-list-rule" aria-hidden="true" />

      {STATIC_ROADMAP.phases.map((phase) => {
        const { num, title } = splitModuleName(phase.name);
        return (
          <section key={phase.name} className="roadmap-mod">
            <div className="roadmap-mod-head">
              <span className="roadmap-mod-num">{num}</span>
              <h2 className="roadmap-mod-title">{title}</h2>
              <span className="roadmap-mod-meta">
                <span
                  className={`roadmap-mod-priority ${phase.priority || ""}`}
                >
                  {(phase.priority || "—").toUpperCase()}
                </span>
                <span className="roadmap-mod-dot">·</span>
                <span>{phase.exam_weight}% exam</span>
                <span className="roadmap-mod-dot">·</span>
                <span>{shortWeeks(phase.weeks)}</span>
              </span>
            </div>

            {phase.topics?.length > 0 && (
              <p className="roadmap-mod-topics">
                {phase.topics.join(" · ")}
              </p>
            )}

            <ul className="roadmap-lect-list">
              {phase.lectures?.map((lecture) => {
                const isDone = done.has(lecture.id);
                const { code, name } = splitLectureTitle(lecture.title);
                return (
                  <li key={lecture.id} className="roadmap-lect">
                    <div className="roadmap-lect-row">
                      <button
                        type="button"
                        className={`roadmap-lect-check ${isDone ? "checked" : ""}`}
                        onClick={() => toggle(lecture.id)}
                        aria-pressed={isDone}
                        aria-label={`Mark ${lecture.title} as ${isDone ? "incomplete" : "done"}`}
                      >
                        {isDone ? "✓" : ""}
                      </button>
                      <span className="roadmap-lect-code">{code}</span>
                      <span className="roadmap-lect-name">{name}</span>
                      <span className="roadmap-lect-spacer" />
                      {lecture.readings?.length > 0 && (
                        <span className="roadmap-lect-chapter">
                          {lecture.readings[0]}
                        </span>
                      )}
                    </div>

                    <div className="roadmap-lect-sub">
                      <span className="roadmap-lect-concepts">
                        {(lecture.key_concepts || []).join(" · ")}
                      </span>
                      <span className="roadmap-lect-actions">
                        {lecture.sectionId && (
                          <Link
                            className="roadmap-lect-action"
                            to={`../notes/${lecture.sectionId}`}
                          >
                            notes
                          </Link>
                        )}
                        {lecture.sectionId && (
                          <Link
                            className="roadmap-lect-action"
                            to={`../quiz/${lecture.sectionId}/multiple_choice`}
                          >
                            quiz
                          </Link>
                        )}
                      </span>
                    </div>
                  </li>
                );
              })}
            </ul>

            <div className="roadmap-list-rule" aria-hidden="true" />
          </section>
        );
      })}

      <footer className="roadmap-list-footer">
        {completed} of {total} lectures complete · Tilburg University ·{" "}
        {STATIC_ROADMAP.exam_date}
      </footer>
    </div>
  );
}
