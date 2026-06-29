// SummaryView.jsx — renders a visual exam summary (SUMMARY_DATA schema) in the
// CSAI@LIVE pixel style. Faithful React port of the design's "RNNs Summary.dc.html"
// renderer: hollow section numbers, dashed dividers, EXAM tag, light ASCII boxes,
// 44% figure thumbnails, dashed table. Slides resolve to the real lecture PNGs
// under /dl/summaries/slides/<slug>/; web diagrams render grayscale.

import { useState, useEffect } from "react";

const SLIDE_RE = /slide[-_ ]?(\d+)/;

function slideSrc(slug, fig) {
  const m = SLIDE_RE.exec(`${fig.ph || ""} ${fig.slot || ""}`);
  if (!m) return fig.src || "";
  return `/dl/summaries/slides/${slug}/slide-${String(m[1]).padStart(2, "0")}.png`;
}

function Figure({ slug, fig, last, onZoom }) {
  const isWeb = fig.kind === "web";
  const src = isWeb ? fig.src : slideSrc(slug, fig);
  return (
    <div
      style={{
        display: "flex",
        gap: 28,
        padding: "30px 0",
        alignItems: "flex-start",
        borderBottom: last ? "none" : "1px dashed #e4e4e4",
      }}
    >
      <div style={{ flex: "0 0 44%", maxWidth: "44%", minWidth: 0 }}>
        <div
          role="button"
          tabIndex={0}
          title="Click to expand"
          onClick={() => onZoom(src)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") onZoom(src);
          }}
          style={{ display: "block", cursor: "zoom-in" }}
        >
          <img
            src={src}
            alt={fig.cap || ""}
            style={{
              width: "100%",
              display: "block",
              border: "1px solid #e4e4e4",
              background: "#fff",
              filter: isWeb ? "grayscale(1) contrast(1.05)" : "none",
            }}
          />
        </div>
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <span
          style={{
            display: "inline-block",
            border: "1px solid #141414",
            color: "#141414",
            background: "#fff",
            fontFamily: "'Press Start 2P',monospace",
            fontSize: 7,
            letterSpacing: 1,
            padding: "5px 7px",
            whiteSpace: "nowrap",
          }}
        >
          {fig.label || ""}
        </span>
        <div
          style={{
            fontWeight: 700,
            margin: "13px 0 9px",
            fontSize: 14,
            lineHeight: 1.5,
          }}
        >
          {fig.cap || ""}
        </div>
        <p
          style={{ margin: 0, fontSize: 13.5, lineHeight: 1.8, color: "#333" }}
        >
          {fig.desc || ""}
        </p>
      </div>
    </div>
  );
}

function SummaryTable({ table }) {
  return (
    <table
      style={{
        borderCollapse: "collapse",
        width: "100%",
        margin: "34px 0",
        fontSize: 13,
      }}
    >
      <tbody>
        <tr>
          {(table.head || []).map((h, i) => (
            <th
              key={i}
              style={{
                borderBottom: "2px solid #141414",
                padding: "12px 10px 12px 0",
                textAlign: "left",
                fontWeight: 700,
                letterSpacing: 0.5,
                lineHeight: 1.6,
              }}
            >
              {h}
            </th>
          ))}
        </tr>
        {(table.rows || []).map((r, ri) => (
          <tr key={ri}>
            {(r || []).map((c, ci) => (
              <td
                key={ci}
                style={{
                  borderBottom: "1px dashed #e4e4e4",
                  padding: "12px 10px 12px 0",
                  textAlign: "left",
                  lineHeight: 1.6,
                  verticalAlign: "top",
                }}
              >
                {c}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function SummaryView({ data, slug, onPlayPodcast }) {
  const [zoom, setZoom] = useState(null);
  const play = onPlayPodcast || (() => {});

  // Close the lightbox on Escape.
  useEffect(() => {
    if (!zoom) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") setZoom(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [zoom]);

  if (!data) {
    return (
      <div
        style={{
          padding: 60,
          fontFamily: "'JetBrains Mono',monospace",
          color: "#9c9c9c",
        }}
      >
        Loading summary…
      </div>
    );
  }
  const audioSrc = `/dl/summaries/audio/${data.slug || slug}.mp3`;
  const podLabel = data.podcast?.label || "LISTEN";

  return (
    <div
      style={{
        minHeight: "100%",
        background: "#fff",
        color: "#141414",
        fontFamily: "'JetBrains Mono',ui-monospace,monospace",
      }}
    >
      <div
        style={{
          maxWidth: 760,
          margin: "0 auto",
          padding: "64px 30px 150px",
          fontSize: 14.5,
          lineHeight: 1.9,
        }}
      >
        <div
          style={{
            fontSize: 10,
            letterSpacing: 2.5,
            color: "#9c9c9c",
            marginBottom: 8,
          }}
        >
          {data.eyebrow}
        </div>
        <h1
          style={{
            fontFamily: "'Press Start 2P',monospace",
            fontSize: 23,
            lineHeight: 1.65,
            margin: "14px 0 16px",
          }}
        >
          {data.title}
        </h1>
        <p
          style={{
            color: "#9c9c9c",
            margin: 0,
            lineHeight: 1.7,
            maxWidth: "58ch",
          }}
        >
          {data.sub}
        </p>

        <div style={{ margin: "28px 0 0" }}>
          <button
            type="button"
            onClick={() => play(audioSrc, podLabel)}
            style={{
              display: "inline-block",
              background: "#141414",
              color: "#fff",
              border: "none",
              fontFamily: "'Press Start 2P',monospace",
              fontSize: 9,
              letterSpacing: 1,
              padding: "14px 18px",
              cursor: "pointer",
            }}
          >
            ▶ {podLabel}
          </button>
        </div>

        {(data.sections || []).map((s) => {
          const figs = s.figures || [];
          return (
            <div
              key={s.n}
              style={{
                margin: "92px 0 0",
                borderTop: "1px dashed #141414",
                paddingTop: 44,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 24,
                  marginBottom: 28,
                }}
              >
                <span
                  style={{
                    fontFamily: "'Press Start 2P',monospace",
                    fontSize: 40,
                    lineHeight: 1,
                    color: "transparent",
                    WebkitTextStroke: "2px #141414",
                    flex: "none",
                  }}
                >
                  {s.n}
                </span>
                <span
                  style={{
                    fontFamily: "'Press Start 2P',monospace",
                    fontSize: 13,
                    lineHeight: 1.75,
                    letterSpacing: 0.5,
                    margin: "7px 0 0",
                  }}
                >
                  {s.title}
                </span>
              </div>

              <div
                style={{ margin: "0 0 36px", lineHeight: 1.85, fontSize: 15 }}
              >
                <span
                  style={{
                    display: "inline-block",
                    border: "1.5px solid #141414",
                    color: "#141414",
                    fontFamily: "'Press Start 2P',monospace",
                    fontSize: 8,
                    letterSpacing: 1,
                    padding: "5px 8px",
                    marginRight: 13,
                    whiteSpace: "nowrap",
                  }}
                >
                  EXAM
                </span>
                {s.exam}
              </div>

              {s.ascii ? (
                <pre
                  style={{
                    background: "#fafafa",
                    color: "#141414",
                    padding: "24px 26px",
                    overflow: "auto",
                    margin: "34px 0",
                    fontFamily: "'JetBrains Mono',ui-monospace,monospace",
                    fontSize: 13,
                    lineHeight: 1.65,
                    border: "1px solid #e4e4e4",
                    whiteSpace: "pre",
                  }}
                >
                  {s.ascii}
                </pre>
              ) : null}

              {figs.length > 0 ? (
                <div style={{ margin: "36px 0 0" }}>
                  {figs.map((f, i) => (
                    <Figure
                      key={i}
                      slug={data.slug || slug}
                      fig={f}
                      last={i === figs.length - 1}
                      onZoom={setZoom}
                    />
                  ))}
                </div>
              ) : null}

              {s.table ? <SummaryTable table={s.table} /> : null}
            </div>
          );
        })}

        <div
          style={{
            marginTop: 100,
            borderTop: "1px dashed #141414",
            paddingTop: 20,
            color: "#9c9c9c",
            fontSize: 11,
            letterSpacing: 1,
          }}
        >
          {data.source}
        </div>
      </div>

      {zoom ? (
        <div
          onClick={() => setZoom(null)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 60,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(20,20,20,.5)",
            backdropFilter: "blur(6px)",
            WebkitBackdropFilter: "blur(6px)",
            cursor: "zoom-out",
          }}
        >
          <img
            src={zoom}
            alt=""
            onClick={(e) => e.stopPropagation()}
            style={{
              maxWidth: "72vw",
              maxHeight: "86vh",
              border: "2px solid #141414",
              background: "#fff",
              boxShadow: "0 12px 48px rgba(0,0,0,.45)",
              cursor: "default",
            }}
          />
        </div>
      ) : null}
    </div>
  );
}
