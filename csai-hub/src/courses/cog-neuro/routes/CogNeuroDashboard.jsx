import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import "../styles.css";

const TABS = [
  { to: "roadmap", label: "Roadmap" },
  { external: "/cog-neuro/lectures/m1_l1.html", label: "Lessons" },
  { to: "quiz", label: "Quizzes" },
  { to: "brain-quiz", label: "Brain Quiz" },
];

// Tabs that suppress the persistent brain corner (Brain Quiz already runs a 3D viewer).
const FULL_BLEED_TABS = new Set(["brain-quiz"]);

function detectTab(pathname) {
  const segs = pathname.split("/").filter(Boolean);
  // /courses/cog-neuro/<tab>/<...>
  const idx = segs.indexOf("cog-neuro");
  return idx >= 0 ? (segs[idx + 1] ?? "roadmap") : "roadmap";
}

export default function CogNeuroDashboard() {
  const location = useLocation();
  const tab = detectTab(location.pathname);

  return (
    <div className="cog-neuro">
      <div className="cog-neuro-bar">
        <Link to="/" className="cog-neuro-back">
          ← Back
        </Link>
        <span className="cog-neuro-swatch" aria-hidden="true" />
        <h1 className="cog-neuro-title">Cognitive Neuroscience</h1>
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
              end={t.to === "roadmap"}
            >
              {t.label}
            </NavLink>
          ),
        )}
      </nav>

      {!FULL_BLEED_TABS.has(tab) && (
        <>
          <img
            className="cog-neuro-brain-corner"
            src="/cog-neuro/brain.svg"
            alt=""
            aria-hidden="true"
          />
          <img
            className="editorial-line"
            src="/cog-neuro/linev2.svg"
            alt=""
            aria-hidden="true"
          />
        </>
      )}

      <div className="cog-neuro-content">
        <main className="cog-neuro-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
