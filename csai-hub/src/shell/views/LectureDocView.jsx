// LectureDocView.jsx — cog-neuro lecture/doc reader. Sample copy for v1, but
// "OPEN SLIDES" deep-links to the real static lecture page under
// /cog-neuro/lectures when one exists for the doc. Faithful port of the
// prototype's `isLecture` block.

export default function LectureDocView({ doc }) {
  const openReal = () => {
    if (doc.href) {
      window.open(doc.href, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <div style={{ padding: "46px 60px 56px", maxWidth: 820 }}>
      <div
        style={{
          fontSize: 10,
          letterSpacing: 2,
          color: "var(--mute)",
          textTransform: "uppercase",
        }}
      >
        {doc.eyebrow}
      </div>
      <h1
        style={{
          margin: "14px 0 0",
          fontFamily: "'Press Start 2P',monospace",
          fontSize: 18,
          lineHeight: 1.6,
        }}
      >
        {doc.title}
      </h1>

      <div
        style={{
          display: "flex",
          gap: 26,
          marginTop: 24,
          fontSize: 11,
          color: "var(--mute)",
          letterSpacing: 0.5,
        }}
      >
        <span style={{ display: "inline-flex", alignItems: "center", gap: 7 }}>
          <i
            className="hn hn-file-import"
            style={{ fontSize: 13, color: "var(--ink)" }}
          />
          6 SOURCES
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 7 }}>
          <i className="hn hn-grid" style={{ fontSize: 13, color: "var(--ink)" }} />
          24 SLIDES
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 7 }}>
          <i
            className="hn hn-clock"
            style={{ fontSize: 13, color: "var(--ink)" }}
          />
          45 MIN
        </span>
      </div>

      <div style={{ borderTop: "1px dashed var(--line)", margin: "30px 0 0" }} />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 9,
          marginTop: 30,
          marginBottom: 10,
        }}
      >
        <i className="hn hn-check-list" style={{ fontSize: 14 }} />
        <span style={{ fontFamily: "'Press Start 2P',monospace", fontSize: 9 }}>
          LEARNING GOALS
        </span>
      </div>
      {doc.goals.map((text) => (
        <div
          key={text}
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 12,
            padding: "9px 0",
            fontSize: 13,
            lineHeight: 1.5,
            borderBottom: "1px dashed var(--line)",
          }}
        >
          <i
            className="hn hn-angle-right"
            style={{ fontSize: 12, marginTop: 3, color: "var(--mute)" }}
          />
          <span>{text}</span>
        </div>
      ))}

      <p style={{ fontSize: 13.5, lineHeight: 1.8, margin: "26px 0 16px" }}>
        {doc.body1}
      </p>
      <p style={{ fontSize: 13.5, lineHeight: 1.8, margin: "0 0 30px" }}>
        {doc.body2}
      </p>

      <div style={{ display: "flex", gap: 14 }}>
        <div
          onClick={openReal}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: 1,
            padding: "14px 22px",
            background: "var(--fill)",
            color: "var(--onFill)",
            cursor: doc.href ? "pointer" : "default",
            opacity: doc.href ? 1 : 0.5,
          }}
        >
          <i className="hn hn-play" style={{ fontSize: 13 }} />
          OPEN SLIDES
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: 1,
            padding: "14px 22px",
            border: "2px solid var(--ink)",
            cursor: "pointer",
          }}
        >
          <i className="hn hn-bookmark" style={{ fontSize: 13 }} />
          SAVE
        </div>
      </div>
    </div>
  );
}
