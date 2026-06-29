import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import "../../cog-neuro/styles.css";

const TABS = [{ to: "quiz", label: "Quizzes" }];

function detectTab(pathname) {
  const segs = pathname.split("/").filter(Boolean);
  const idx = segs.indexOf("rw");
  return idx >= 0 ? (segs[idx + 1] ?? "quiz") : "quiz";
}

export default function RWDashboard() {
  const location = useLocation();
  detectTab(location.pathname);

  return (
    <div className="cog-neuro" style={{ "--coral": "#F5C518" }}>
      <div className="cog-neuro-bar">
        <Link to="/" className="cog-neuro-back">
          ← Back
        </Link>
        <span className="cog-neuro-swatch" aria-hidden="true" />
        <h1 className="cog-neuro-title">Research Workshop CSAI</h1>
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
          >
            {t.label}
          </NavLink>
        ))}
      </nav>

      <div className="cog-neuro-content">
        <main className="cog-neuro-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
