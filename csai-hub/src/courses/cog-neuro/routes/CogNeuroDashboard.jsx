import { Link, NavLink, Outlet } from "react-router-dom";
import "../styles.css";

const TABS = [
  { to: "roadmap", label: "Roadmap" },
  { to: "notes", label: "Lessons" },
  { to: "quiz", label: "Quizzes" },
  { to: "brain-quiz", label: "Brain Quiz" },
];

export default function CogNeuroDashboard() {
  return (
    <div className="cog-neuro">
      <div className="cog-neuro-bar">
        <Link to="/" className="cog-neuro-back">← Back</Link>
        <span className="cog-neuro-swatch" aria-hidden="true" />
        <h1 className="cog-neuro-title">Cognitive Neuroscience</h1>
        <span className="cog-neuro-subtitle">Tilburg · Year 2 · Sem 4</span>
      </div>

      <nav className="cog-neuro-tabs">
        {TABS.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            className={({ isActive }) =>
              `cog-neuro-tab ${isActive ? "active" : ""}`
            }
            end={t.to === "roadmap"}
          >
            {t.label}
          </NavLink>
        ))}
      </nav>

      <div className="cog-neuro-content">
        <Outlet />
      </div>
    </div>
  );
}
