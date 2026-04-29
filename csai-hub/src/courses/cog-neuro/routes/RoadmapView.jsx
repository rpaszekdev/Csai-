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

export default function RoadmapView() {
  const [done, setDone] = useState(() => loadDone());

  const allLectureIds = useMemo(() => {
    const ids = [];
    for (const phase of STATIC_ROADMAP.phases) {
      for (const lecture of phase.lectures ?? []) {
        ids.push(lecture.id);
      }
    }
    return ids;
  }, []);

  const completed = allLectureIds.filter((id) => done.has(id)).length;
  const total = allLectureIds.length;
  const pct = total === 0 ? 0 : Math.round((completed / total) * 100);

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
    <>
      <header className="roadmap-header">
        <span className="roadmap-eyebrow">Study Roadmap</span>
        <h2 className="roadmap-title">{STATIC_ROADMAP.name}</h2>
        <p className="roadmap-meta">Exam: {STATIC_ROADMAP.exam_date}</p>
      </header>

      <div className="roadmap-progress">
        <span className="roadmap-progress-label">Overall progress</span>
        <div className="roadmap-progress-bar">
          <div className="roadmap-progress-fill" style={{ width: `${pct}%` }} />
        </div>
        <span className="roadmap-progress-pct">{pct}%</span>
      </div>

      {STATIC_ROADMAP.phases.map((phase) => (
        <section key={phase.name} className="phase-card">
          <header className="phase-card-head">
            <div>
              <h3 className="phase-name">{phase.name}</h3>
              <p className="phase-weeks">{phase.weeks}</p>
            </div>
            <div className="phase-tags">
              <span className={`phase-priority ${phase.priority}`}>{phase.priority}</span>
              <span className="phase-weight">{phase.exam_weight}% exam</span>
            </div>
          </header>

          {phase.topics?.length > 0 && (
            <div className="phase-topics">
              {phase.topics.map((t) => (
                <span key={t} className="topic-chip">{t}</span>
              ))}
            </div>
          )}

          {phase.lectures?.map((lecture) => {
            const isDone = done.has(lecture.id);
            return (
              <article key={lecture.id} className="lecture-card">
                <div className="lecture-row">
                  <button
                    type="button"
                    className={`lecture-checkbox ${isDone ? "checked" : ""}`}
                    onClick={() => toggle(lecture.id)}
                    aria-pressed={isDone}
                    aria-label={`Mark ${lecture.title} as ${isDone ? "incomplete" : "done"}`}
                  >
                    {isDone ? "✓" : ""}
                  </button>
                  <span className="lecture-title">{lecture.title}</span>
                  <div className="lecture-actions">
                    {lecture.sectionId && (
                      <Link to={`../notes/${lecture.sectionId}`} className="lecture-action">Notes</Link>
                    )}
                    {lecture.sectionId && (
                      <Link
                        to={`../quiz/${lecture.sectionId}/multiple_choice`}
                        className="lecture-action"
                      >
                        Quiz
                      </Link>
                    )}
                  </div>
                </div>
                {(lecture.key_concepts?.length || lecture.readings?.length) > 0 && (
                  <div className="lecture-meta">
                    {lecture.key_concepts?.map((c) => (
                      <span key={c} className="lecture-concept">{c}</span>
                    ))}
                    {lecture.readings?.map((r) => (
                      <span key={r} className="lecture-reading">{r}</span>
                    ))}
                  </div>
                )}
              </article>
            );
          })}
        </section>
      ))}
    </>
  );
}
