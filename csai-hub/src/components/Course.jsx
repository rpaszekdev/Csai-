import { useState } from "react";
import { Link } from "react-router-dom";
import CourseIllustration from "./CourseIllustration";

function ResourceLink({ resource }) {
  const isInternal = resource.href.startsWith("/courses/");
  if (isInternal) {
    return (
      <Link to={resource.href} className="resource-link">
        {resource.label}
      </Link>
    );
  }
  return (
    <a href={resource.href} className="resource-link">
      {resource.label}
    </a>
  );
}

export default function Course({ course }) {
  const [open, setOpen] = useState(false);
  const nextExam = course.exams[0];
  const accent = course.color ?? "#E8723A";

  return (
    <div
      className={`course ${open ? "course-open" : ""}`}
      style={{ "--course-color": accent }}
    >
      <button className="course-toggle" onClick={() => setOpen((o) => !o)}>
        <span className="course-swatch" aria-hidden="true" />
        <span className="course-name">{course.name}</span>
        {nextExam && (
          <span className="course-meta">
            {nextExam.type} · {nextExam.date}
          </span>
        )}
        {!nextExam && <span className="course-meta">Project-based</span>}
      </button>

      {open && (
        <div className="course-detail">
          <div className="course-detail-head">
            <CourseIllustration
              shape={course.shape}
              color={accent}
              id={course.id}
            />
            <div className="course-detail-title">
              <span className="course-detail-eyebrow">Course</span>
              <span className="course-detail-name">{course.name}</span>
            </div>
          </div>

          {course.examLinks?.length > 0 && (
            <div className="course-exam-links">
              {course.examLinks.map((e) => (
                <a key={e.label} href={e.href} className="exam-link-btn">
                  {e.label}
                </a>
              ))}
            </div>
          )}

          {course.resources.length > 0 && (
            <div className="course-resources">
              {course.resources.map((r) => (
                <ResourceLink key={r.label} resource={r} />
              ))}
            </div>
          )}

          {course.exams.length > 0 && (
            <div className="course-exams">
              {course.exams.map((e) => (
                <div key={`${e.type}-${e.date}`} className="exam-row">
                  <span className="exam-type">
                    {e.type} <span className="exam-format">({e.format})</span>
                  </span>
                  <span className="exam-weight">{e.weight}</span>
                  <span className="exam-min">min {e.min}</span>
                  <span className="exam-date">{e.date}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
