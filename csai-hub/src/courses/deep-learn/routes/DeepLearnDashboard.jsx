import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import "../../cog-neuro/styles.css";

const TABS = [
  { external: "/lesson.html", label: "Lessons" },
  { to: "quiz", label: "Quizzes" },
];

function detectTab(pathname) {
  const segs = pathname.split("/").filter(Boolean);
  const idx = segs.indexOf("deep-learn");
  return idx >= 0 ? (segs[idx + 1] ?? "quiz") : "quiz";
}

export default function DeepLearnDashboard() {
  const location = useLocation();
  const tab = detectTab(location.pathname);

  return (
    <div className="cog-neuro" style={{ "--coral": "#FF4521" }}>
      <div className="cog-neuro-bar">
        <Link to="/" className="cog-neuro-back">
          ← Back
        </Link>
        <span className="cog-neuro-swatch" aria-hidden="true" />
        <h1 className="cog-neuro-title">Introduction to Deep Learning</h1>
        <span className="cog-neuro-subtitle">Tilburg · Year 2 · Sem 4</span>
      </div>

      <nav className="cog-neuro-tabs">
        {TABS.map((t) =>
          t.external ? (
            <a key={t.label} href={t.external} className="cog-neuro-tab">
              {t.label}
            </a>
          ) : (
            <NavLink
              key={t.to}
              to={t.to}
              className={({ isActive }) =>
                `cog-neuro-tab ${isActive ? "active" : ""}`
              }
            >
              {t.label}
            </NavLink>
          ),
        )}
      </nav>

      <div className="cog-neuro-content">
        <main className="cog-neuro-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
