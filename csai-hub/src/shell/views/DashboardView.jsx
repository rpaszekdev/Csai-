// DashboardView.jsx — cognitive-neuroscience module overview. Sample content
// for v1 (known gap), but lecture rows deep-link to the real static pages
// under /cog-neuro/lectures where one exists. Faithful port of the prototype's
// `isDashboard` block.

import { DASHBOARD_LECTURES } from "../shellContent.js";

export default function DashboardView({ onOpenFile }) {
  const lectures = DASHBOARD_LECTURES.map((lec) => {
    const locked = lec.status === "LOCKED";
    let onClick = () => {};
    if (lec.fileId) {
      onClick = () => onOpenFile(lec.fileId);
    } else if (lec.href) {
      onClick = () => window.open(lec.href, "_blank", "noopener,noreferrer");
    }
    return { ...lec, fg: locked ? "var(--mute)" : "var(--ink)", onClick };
  });

  return (
    <div style={{ padding: "46px 60px 56px", maxWidth: 940 }}>
      <div
        style={{
          fontSize: 10,
          letterSpacing: 2,
          color: "var(--mute)",
          textTransform: "uppercase",
        }}
      >
        Module Overview · Year 2 · 6 ECTS
      </div>
      <h1
        style={{
          margin: "14px 0 0",
          fontFamily: "'Press Start 2P',monospace",
          fontSize: 21,
          lineHeight: 1.55,
        }}
      >
        COGNITIVE
        <br />
        NEUROSCIENCE
      </h1>

      <div
        style={{
          display: "flex",
          gap: 0,
          marginTop: 40,
          borderTop: "1px dashed var(--line)",
          borderBottom: "1px dashed var(--line)",
        }}
      >
        <div style={{ flex: 1, padding: "22px 24px 22px 0" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontSize: 9,
              letterSpacing: 1,
              color: "var(--mute)",
            }}
          >
            <i
              className="hn hn-check-list"
              style={{ fontSize: 13, color: "var(--ink)" }}
            />
            PROGRESS
          </div>
          <div
            style={{
              fontFamily: "'Press Start 2P',monospace",
              fontSize: 18,
              marginTop: 14,
            }}
          >
            6<span style={{ color: "var(--mute)", fontSize: 11 }}>/11</span>
          </div>
          <div
            style={{
              marginTop: 14,
              height: 14,
              border: "2px solid var(--ink)",
              display: "flex",
            }}
          >
            <div style={{ width: "55%", background: "var(--ink)" }} />
          </div>
        </div>
        <div
          style={{
            flex: 1,
            padding: "22px 24px",
            borderLeft: "1px dashed var(--line)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontSize: 9,
              letterSpacing: 1,
              color: "var(--mute)",
            }}
          >
            <i
              className="hn hn-calendar-alt"
              style={{ fontSize: 13, color: "var(--ink)" }}
            />
            NEXT EXAM
          </div>
          <div
            style={{
              fontFamily: "'Press Start 2P',monospace",
              fontSize: 18,
              marginTop: 14,
            }}
          >
            26 MAY
          </div>
          <div style={{ marginTop: 16, fontSize: 11, color: "var(--mute)" }}>
            17:30 · in 12 days
          </div>
        </div>
        <div
          style={{
            flex: 1,
            padding: "22px 0 22px 24px",
            borderLeft: "1px dashed var(--line)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontSize: 9,
              letterSpacing: 1,
              color: "var(--mute)",
            }}
          >
            <i
              className="hn hn-trophy"
              style={{ fontSize: 13, color: "var(--ink)" }}
            />
            BEST QUIZ
          </div>
          <div
            style={{
              fontFamily: "'Press Start 2P',monospace",
              fontSize: 18,
              marginTop: 14,
            }}
          >
            86<span style={{ color: "var(--mute)", fontSize: 11 }}>%</span>
          </div>
          <div style={{ marginTop: 16, fontSize: 11, color: "var(--mute)" }}>
            Memory Systems
          </div>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          marginTop: 44,
          marginBottom: 6,
        }}
      >
        <span
          style={{ fontFamily: "'Press Start 2P',monospace", fontSize: 11 }}
        >
          LECTURES
        </span>
        <span style={{ flex: 1 }} />
        <span style={{ fontSize: 10, color: "var(--mute)", letterSpacing: 1 }}>
          11 TOTAL
        </span>
      </div>
      <div>
        {lectures.map((lec) => (
          <div
            key={lec.mod}
            onClick={lec.onClick}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 16,
              padding: "16px 4px",
              cursor: "pointer",
              borderBottom: "1px dashed var(--line)",
            }}
          >
            <span
              style={{
                fontFamily: "'Press Start 2P',monospace",
                fontSize: 8,
                minWidth: 48,
                color: "var(--mute)",
              }}
            >
              {lec.mod}
            </span>
            <span
              style={{
                flex: 1,
                fontSize: 13.5,
                fontWeight: 600,
                minWidth: 0,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                color: lec.fg,
              }}
            >
              {lec.title}
            </span>
            <span
              style={{ fontSize: 9, letterSpacing: 1, color: "var(--mute)" }}
            >
              {lec.status}
            </span>
            <i className={`hn ${lec.icon}`} style={{ fontSize: 15, color: lec.fg }} />
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 48, marginTop: 46 }}>
        <div style={{ flex: 1.1 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 9,
              marginBottom: 18,
            }}
          >
            <i className="hn hn-graduation-cap" style={{ fontSize: 14 }} />
            <span
              style={{ fontFamily: "'Press Start 2P',monospace", fontSize: 9 }}
            >
              EXAMS
            </span>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "baseline",
              padding: "10px 0",
              borderBottom: "1px dashed var(--line)",
            }}
          >
            <span style={{ fontSize: 12, fontWeight: 700 }}>FINAL · Digital</span>
            <span
              style={{ fontFamily: "'Press Start 2P',monospace", fontSize: 9 }}
            >
              40%
            </span>
          </div>
          <div
            style={{ fontSize: 10.5, color: "var(--mute)", padding: "8px 0 16px" }}
          >
            26 May · 17:30–19:30 · no min grade
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "baseline",
              padding: "10px 0",
              borderBottom: "1px dashed var(--line)",
            }}
          >
            <span style={{ fontSize: 12, fontWeight: 700 }}>RESIT · Digital</span>
            <span
              style={{ fontFamily: "'Press Start 2P',monospace", fontSize: 9 }}
            >
              80%
            </span>
          </div>
          <div style={{ fontSize: 10.5, color: "var(--mute)", padding: "8px 0 0" }}>
            23 Jun · resit replaces final
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 9,
              marginBottom: 18,
            }}
          >
            <i className="hn hn-pencil-ruler" style={{ fontSize: 14 }} />
            <span
              style={{ fontFamily: "'Press Start 2P',monospace", fontSize: 9 }}
            >
              ASSIGNMENT
            </span>
          </div>
          <div
            style={{
              fontSize: 12,
              fontWeight: 600,
              lineHeight: 1.6,
              marginBottom: 14,
            }}
          >
            4 of 6 practicals + flipped-classroom presentation
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 16,
            }}
          >
            <span
              style={{ fontFamily: "'Press Start 2P',monospace", fontSize: 9 }}
            >
              20%
            </span>
            <span style={{ fontSize: 10.5, color: "var(--mute)" }}>
              throughout semester
            </span>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 9,
              fontSize: 10.5,
              borderTop: "1px dashed var(--line)",
              paddingTop: 16,
              color: "var(--mute)",
            }}
          >
            <i
              className="hn hn-bell"
              style={{ fontSize: 12, marginTop: 1, color: "var(--ink)" }}
            />
            <span>Skip either component → grade becomes 0</span>
          </div>
        </div>
      </div>
    </div>
  );
}
