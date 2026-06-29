// DlLectureView.jsx — deep-learning lecture shell. The topic is driven by real
// data; the material panels (PPTX / TRANSCRIPT / CHAPTER / NOTES / PODCAST) are
// placeholders for v1 (known gap — see fidelity notes). Faithful port of the
// prototype's `isDl` block.

import { DL_MATERIALS, buildPodcastBars } from "../shellContent.js";

export default function DlLectureView({
  topic,
  dlLesson,
  material,
  onSetMaterial,
  podcast,
  podPlaying,
  onTogglePodcast,
  onTogglePlay,
  onClosePodcast,
}) {
  const topicUpper = topic.toUpperCase();
  const materials = DL_MATERIALS.map((m) => {
    const isPod = m.key === "podcast";
    const active = isPod ? podcast : material === m.key;
    return {
      key: m.key,
      label: m.label,
      icon: m.icon,
      onClick: isPod ? onTogglePodcast : () => onSetMaterial(m.key),
      bg: active ? "var(--fill)" : "var(--bg)",
      fg: active ? "var(--onFill)" : "var(--ink)",
      shadow: active ? "none" : "3px 3px 0 var(--line)",
    };
  });
  const bars = buildPodcastBars();

  return (
    <div style={{ minHeight: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: 0 }}>
        <div style={{ flex: 1, padding: "34px 40px 54px", maxWidth: 1000 }}>
          <div
            style={{
              fontSize: 10,
              letterSpacing: 2,
              color: "var(--mute)",
              textTransform: "uppercase",
            }}
          >
            {`Deep Learning · Lesson ${dlLesson + 1}`}
          </div>
          <h1
            style={{
              margin: "12px 0 0",
              fontFamily: "'Press Start 2P',monospace",
              fontSize: 20,
              lineHeight: 1.5,
            }}
          >
            {topicUpper}
          </h1>

          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 12,
              marginTop: 26,
            }}
          >
            {materials.map((m) => (
              <div
                key={m.key}
                onClick={m.onClick}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 9,
                  padding: "11px 16px",
                  cursor: "pointer",
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: 1,
                  background: m.bg,
                  color: m.fg,
                  border: "2px solid var(--ink)",
                  boxShadow: m.shadow,
                }}
              >
                <i className={`hn ${m.icon}`} style={{ fontSize: 14 }} />
                {m.label}
              </div>
            ))}
          </div>

          <div style={{ borderTop: "1px dashed var(--line)", margin: "30px 0 0" }} />

          <div style={{ marginTop: 30 }}>
            {material === "pptx" && (
              <div
                style={{
                  display: "flex",
                  gap: 28,
                  alignItems: "flex-start",
                  flexWrap: "wrap",
                }}
              >
                <div
                  style={{
                    position: "relative",
                    width: 380,
                    maxWidth: "100%",
                    aspectRatio: "16/9",
                    border: "2px solid var(--ink)",
                    boxShadow: "7px 7px 0 var(--line)",
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      zIndex: 2,
                      background: "var(--ink)",
                      color: "var(--onFill)",
                      fontFamily: "'Press Start 2P',monospace",
                      fontSize: 10,
                      padding: "6px 9px",
                    }}
                  >
                    01
                  </div>
                  <div
                    style={{
                      width: "100%",
                      height: "100%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 10,
                      letterSpacing: 1,
                      color: "var(--mute)",
                    }}
                  >
                    DROP SLIDE 01
                  </div>
                </div>
                <div style={{ flex: 1, minWidth: 220 }}>
                  <div
                    style={{
                      fontFamily: "'Press Start 2P',monospace",
                      fontSize: 10,
                    }}
                  >
                    SLIDE DECK
                  </div>
                  <div
                    style={{
                      fontSize: 12.5,
                      lineHeight: 1.75,
                      color: "var(--mute)",
                      marginTop: 14,
                    }}
                  >
                    Placeholder — the real PPTX wires in here, one framed
                    thumbnail per slide.
                  </div>
                  <div
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 9,
                      marginTop: 18,
                      padding: "11px 16px",
                      border: "2px solid var(--ink)",
                      fontSize: 11,
                      fontWeight: 700,
                      letterSpacing: 1,
                      cursor: "pointer",
                    }}
                  >
                    <i className="hn hn-grid" style={{ fontSize: 13 }} />
                    OPEN DECK
                  </div>
                </div>
              </div>
            )}

            {material === "transcript" && (
              <div style={{ maxWidth: 760 }}>
                <div
                  style={{
                    fontFamily: "'Press Start 2P',monospace",
                    fontSize: 10,
                  }}
                >
                  TRANSCRIPT
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: 16,
                    marginTop: 20,
                    paddingBottom: 16,
                    borderBottom: "1px dashed var(--line)",
                  }}
                >
                  <span
                    style={{ fontSize: 11, color: "var(--mute)", minWidth: 46 }}
                  >
                    00:00
                  </span>
                  <span style={{ fontSize: 13, lineHeight: 1.75 }}>
                    Placeholder transcript segment — the lesson's auto-synced
                    transcript appears here, one timestamped block per paragraph.
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--mute)",
                    letterSpacing: 1,
                    marginTop: 18,
                  }}
                >
                  ··· full transcript wires in here ···
                </div>
              </div>
            )}

            {material === "chapter" && (
              <div style={{ maxWidth: 760 }}>
                <div
                  style={{
                    fontFamily: "'Press Start 2P',monospace",
                    fontSize: 10,
                  }}
                >
                  CHAPTER
                </div>
                <div style={{ fontSize: 14, fontWeight: 700, marginTop: 18 }}>
                  Chapter 1 — {topicUpper}
                </div>
                <p
                  style={{
                    fontSize: 13,
                    lineHeight: 1.85,
                    color: "var(--mute)",
                    marginTop: 12,
                  }}
                >
                  Placeholder chapter excerpt. The matching textbook chapter
                  renders here for reading alongside the lecture and slides.
                </p>
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 9,
                    marginTop: 8,
                    padding: "11px 16px",
                    border: "2px solid var(--ink)",
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: 1,
                    cursor: "pointer",
                  }}
                >
                  <i className="hn hn-book" style={{ fontSize: 13 }} />
                  OPEN FULL CHAPTER
                </div>
              </div>
            )}

            {material === "notes" && (
              <div style={{ maxWidth: 680 }}>
                <div
                  style={{ display: "flex", alignItems: "center", gap: 9 }}
                >
                  <i className="hn hn-copy" style={{ fontSize: 15 }} />
                  <span
                    style={{
                      fontFamily: "'Press Start 2P',monospace",
                      fontSize: 10,
                    }}
                  >
                    NOTES
                  </span>
                </div>
                <div
                  style={{
                    marginTop: 18,
                    border: "2px solid var(--ink)",
                    boxShadow: "7px 7px 0 var(--line)",
                    padding: 20,
                    fontSize: 13,
                    lineHeight: 2,
                    color: "var(--mute)",
                  }}
                >
                  — Placeholder note line
                  <br />— Add your own notes for this lesson
                  <br />— Saved alongside the lecture materials
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {podcast && (
        <div
          style={{
            position: "sticky",
            bottom: 0,
            zIndex: 6,
            background: "var(--bg)",
            borderTop: "1px dashed var(--line)",
            padding: "13px 40px",
            display: "flex",
            alignItems: "center",
            gap: 16,
          }}
        >
          <div
            onClick={onTogglePlay}
            style={{
              flex: "none",
              width: 40,
              height: 40,
              background: "var(--fill)",
              color: "var(--onFill)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
            }}
          >
            <i
              className={`hn ${podPlaying ? "hn-pause" : "hn-play"}`}
              style={{ fontSize: 15 }}
            />
          </div>
          <div style={{ flex: "none", fontSize: 11, fontWeight: 700, whiteSpace: "nowrap" }}>
            {topicUpper}
            <span style={{ color: "var(--mute)", fontWeight: 400 }}>
              {" "}
              · podcast
            </span>
          </div>
          <div
            style={{
              flex: 1,
              minWidth: 0,
              display: "flex",
              alignItems: "flex-end",
              gap: 2,
              height: 22,
            }}
          >
            {bars.map((bar, i) => (
              <span
                key={i}
                style={{ flex: 1, height: bar.h, background: bar.bg }}
              />
            ))}
          </div>
          <span style={{ flex: "none", fontSize: 11, color: "var(--mute)" }}>
            03:12 / 18:24
          </span>
          <i
            onClick={onClosePodcast}
            className="hn hn-times"
            style={{
              flex: "none",
              fontSize: 15,
              color: "var(--mute)",
              cursor: "pointer",
            }}
          />
        </div>
      )}
    </div>
  );
}
