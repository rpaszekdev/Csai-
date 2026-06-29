// QuizView.jsx — the quiz view with the walking-Vader progress indicator and
// the right-side explanation drawer. Faithful port of the v3 design's `isQuiz`
// block, wired to real deep-learning questions.
//
// Scroll model (from the design): the L-tabs row and the lesson header live
// inside a scrollable column; as you scroll down they collapse/scroll away and
// the question number + question text "stick" to the top (pinned) with a shadow
// while the options scroll under them. The nav row stays fixed at the bottom.

import { useRef, useEffect } from "react";
import {
  buildOptions,
  isAnswerCorrect,
  typeLabel,
  answerLabel,
  paddedNumber,
} from "../shellQuiz.js";

const VADER_SPRITE = "/pixel/assets/vader_walk_right.png";

export default function QuizView({
  topics,
  dlLesson,
  onSelectLesson,
  lesson,
  qIndex,
  qcount,
  q,
  selected,
  revealed,
  walking,
  explOpen,
  onSelectOption,
  onCheck,
  onPrev,
  onNext,
  onNextQuiz,
  lessonCount,
  onToggleExpl,
  onCloseExpl,
}) {
  const total = qcount;
  const atLast = qIndex === total - 1;
  const hasNextLesson = lessonCount != null && dlLesson < lessonCount - 1;
  const nextEnabled = !atLast || hasNextLesson;
  const nextLabel = atLast ? (hasNextLesson ? "NEXT QUIZ" : "DONE") : "NEXT";
  const handleNextClick = () => {
    if (!atLast) onNext();
    else if (hasNextLesson && onNextQuiz) onNextQuiz();
  };

  // ---- sticky-on-scroll refs + behavior (mirrors the design's onQScroll) ----
  const qScrollRef = useRef(null);
  const qLessonRef = useRef(null);
  const qStickyRef = useRef(null);
  const qNumRowRef = useRef(null);
  const qTextRef = useRef(null);
  const qTabsRef = useRef(null);
  const stuckRef = useRef(false);

  const applyStuck = (stuck) => {
    const head = qStickyRef.current;
    const num = qNumRowRef.current;
    const txt = qTextRef.current;
    const tabs = qTabsRef.current;
    if (head) {
      head.style.borderBottomColor = stuck ? "var(--line)" : "transparent";
      head.style.boxShadow = stuck ? "0 8px 12px -10px rgba(0,0,0,.3)" : "none";
      head.style.paddingBottom = stuck ? "10px" : "0px";
    }
    if (num) {
      num.style.maxHeight = stuck ? "0px" : "48px";
      num.style.opacity = stuck ? "0" : "1";
    }
    if (txt) {
      txt.style.fontSize = stuck ? "12.5px" : "clamp(13px,1.35vw,15px)";
      txt.style.marginTop = stuck ? "2px" : "12px";
      txt.style.fontWeight = stuck ? "700" : "600";
    }
    if (tabs) {
      tabs.style.maxHeight = stuck ? "0px" : "64px";
      tabs.style.opacity = stuck ? "0" : "1";
    }
  };

  const onQScroll = (e) => {
    const sc = e.currentTarget;
    const lead = qLessonRef.current;
    const thr = lead ? Math.max(20, lead.offsetHeight - 12) : 40;
    const stuck = sc.scrollTop > thr;
    if (stuck !== stuckRef.current) {
      stuckRef.current = stuck;
      applyStuck(stuck);
    }
  };

  // Reset scroll to top and un-stick whenever the question or lesson changes.
  useEffect(() => {
    const sc = qScrollRef.current;
    if (sc) sc.scrollTop = 0;
    stuckRef.current = false;
    applyStuck(false);
  }, [qIndex, dlLesson]);

  const dlTabs = topics.map((t, i) => ({
    code: t.code || `L${i + 1}`,
    active: i === dlLesson,
    fg: i === dlLesson ? "var(--ink)" : "var(--mute)",
    weight: i === dlLesson ? 700 : 400,
    selBd: i === dlLesson ? "var(--ink)" : "var(--line)",
  }));

  const blocks = Array.from({ length: total }, (_, i) => ({
    fill: i <= qIndex ? "var(--ink)" : "var(--line)",
  }));

  const options = buildOptions(q, selected, revealed);
  const sel = selected.length > 0;
  const rev = revealed;
  const wasCorrect = rev && isAnswerCorrect(q, selected);
  const enabled = rev || sel;
  const sourceTag =
    q && q.source === "lecturer"
      ? "LECTURER"
      : q && q.source === "exam"
        ? "EXAM"
        : null;
  const provenance =
    q && q.source === "lecturer"
      ? "LECTURER QUIZ"
      : q && q.source === "exam"
        ? "EXAM-STYLE QUESTION"
        : "AI TUTOR · auto-generated";
  const provenanceIcon =
    q && (q.source === "lecturer" || q.source === "exam")
      ? "hn-book"
      : "hn-robot";

  const vaderLeft = `${((qIndex + 0.5) / Math.max(total, 1)) * 100}%`;

  const centerLabel = rev
    ? wasCorrect
      ? "CORRECT"
      : "INCORRECT"
    : "CHECK ANSWER";
  const centerIcon = rev
    ? wasCorrect
      ? "hn-check"
      : "hn-times"
    : "hn-check-box";

  return (
    <div style={{ height: "100%", display: "flex", minHeight: 0 }}>
      {/* quiz column */}
      <div
        style={{
          flex: 1,
          minWidth: 0,
          height: "100%",
          boxSizing: "border-box",
          display: "flex",
          flexDirection: "column",
          padding: "clamp(10px,2vh,20px) 44px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: 680,
            margin: "0 auto",
            flex: 1,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* L-tabs (collapse away when the header sticks) */}
          <div
            ref={qTabsRef}
            style={{
              flex: "none",
              overflow: "hidden",
              maxHeight: 64,
              opacity: 1,
              transition: "max-height .28s ease, opacity .2s ease",
            }}
          >
            <div
              style={{
                display: "flex",
                gap: 5,
                justifyContent: "center",
                flexWrap: "wrap",
              }}
            >
              {dlTabs.map((t, i) => (
                <div
                  key={t.code}
                  onClick={() => onSelectLesson(i)}
                  style={{
                    padding: "5px 9px",
                    cursor: "pointer",
                    fontSize: 10,
                    fontWeight: t.weight,
                    color: t.fg,
                    border: `1.5px solid ${t.selBd}`,
                  }}
                >
                  {t.code}
                </div>
              ))}
            </div>
          </div>

          {/* scrollable question area */}
          <div
            ref={qScrollRef}
            onScroll={onQScroll}
            style={{
              flex: 1,
              minHeight: 0,
              overflowY: "auto",
              position: "relative",
              paddingRight: 6,
              marginTop: "clamp(10px,1.6vh,16px)",
            }}
          >
            {/* lesson header (scrolls away) */}
            <div
              ref={qLessonRef}
              style={{
                textAlign: "center",
                paddingBottom: "clamp(10px,1.7vh,16px)",
              }}
            >
              <div
                style={{ fontSize: 9, letterSpacing: 3, color: "var(--mute)" }}
              >
                {lesson
                  ? `DEEP LEARNING · ${
                      lesson.code === "EX"
                        ? "EXAM SET"
                        : `LESSON ${dlLesson + 1}`
                    }`
                  : "DEEP LEARNING"}
              </div>
              <h1
                style={{
                  margin: "10px 0 0",
                  fontFamily: "'Press Start 2P',monospace",
                  fontSize: "clamp(13px,1.5vw,16px)",
                  lineHeight: 1.5,
                  letterSpacing: 1,
                }}
              >
                {lesson
                  ? lesson.code === "EX"
                    ? lesson.topic.toUpperCase()
                    : `${lesson.code}: ${lesson.topic.toUpperCase()}`
                  : "LOADING…"}
              </h1>
              <div
                style={{
                  fontSize: 10,
                  letterSpacing: 2,
                  color: "var(--mute)",
                  marginTop: 11,
                }}
              >
                {`QUESTION ${qIndex + 1} OF ${total} · ${total} TOTAL`}
              </div>

              {/* minimal progress + small vader */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  marginTop: 14,
                }}
              >
                <div
                  style={{ position: "relative", width: 230, paddingTop: 23 }}
                >
                  <div
                    style={{
                      position: "absolute",
                      left: vaderLeft,
                      bottom: 8,
                      width: 30,
                      height: 30,
                      background: `url('${VADER_SPRITE}') left center / 330px 30px no-repeat`,
                      imageRendering: "pixelated",
                      animation: walking
                        ? "vaderwalk .55s steps(11) infinite"
                        : "none",
                      backgroundPositionX: walking ? undefined : "0px",
                      transform: "translateX(-50%)",
                      transition: "left .55s cubic-bezier(.4,.06,.2,1)",
                      pointerEvents: "none",
                    }}
                  />
                  <div style={{ display: "flex", gap: 5 }}>
                    {blocks.map((b, i) => (
                      <span
                        key={i}
                        style={{ flex: 1, height: 3, background: b.fill }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* sticky header: number + type (+ source tag) and question text */}
            <div
              ref={qStickyRef}
              style={{
                position: "sticky",
                top: 0,
                zIndex: 3,
                background: "var(--bg)",
                paddingTop: "clamp(8px,1.4vh,14px)",
                paddingBottom: 0,
                borderBottom: "1px dashed transparent",
                transition:
                  "border-color .25s ease, box-shadow .25s ease, padding-bottom .25s ease",
              }}
            >
              <div
                ref={qNumRowRef}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  justifyContent: "space-between",
                  gap: 20,
                  overflow: "hidden",
                  maxHeight: 48,
                  opacity: 1,
                  transition: "max-height .28s ease, opacity .2s ease",
                }}
              >
                <span
                  style={{
                    fontFamily: "'Press Start 2P',monospace",
                    fontSize: 26,
                    lineHeight: 1,
                    WebkitTextStroke: "2px var(--ink)",
                    color: "transparent",
                  }}
                >
                  {paddedNumber(qIndex)}
                </span>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "flex-end",
                    gap: 6,
                    marginTop: 4,
                  }}
                >
                  <span
                    style={{
                      fontSize: 9,
                      letterSpacing: 2,
                      color: "var(--mute)",
                    }}
                  >
                    {typeLabel(q)}
                  </span>
                  {sourceTag && (
                    <span
                      style={{
                        fontSize: 8,
                        letterSpacing: 1,
                        fontWeight: 700,
                        color: "var(--ink)",
                        border: "1.5px solid var(--ink)",
                        padding: "2px 6px",
                      }}
                    >
                      {sourceTag}
                    </span>
                  )}
                </div>
              </div>
              <div
                ref={qTextRef}
                style={{
                  fontSize: "clamp(13px,1.35vw,15px)",
                  fontWeight: 600,
                  lineHeight: 1.6,
                  marginTop: 12,
                  transition: "font-size .25s ease, margin-top .25s ease",
                }}
              >
                {q.q}
              </div>
            </div>

            {/* options */}
            <div style={{ marginTop: 14 }}>
              {options.map((opt) => (
                <div
                  key={opt.letter}
                  onClick={() => onSelectOption(opt.letter)}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 14,
                    padding: "12px 2px",
                    cursor: "pointer",
                    borderBottom: "1px dashed var(--line)",
                  }}
                >
                  <span
                    style={{
                      flex: "none",
                      marginTop: 1,
                      width: 16,
                      height: 16,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      border: `1.5px solid ${opt.boxBd}`,
                      background: opt.boxBg,
                    }}
                  >
                    <i
                      className={`hn ${opt.checkIcon}`}
                      style={{
                        fontSize: 9,
                        color: opt.checkColor,
                        opacity: opt.checkOp,
                        animation: opt.tickAnim,
                      }}
                    />
                  </span>
                  <span
                    style={{
                      flex: "none",
                      fontWeight: 700,
                      fontSize: 13.5,
                      minWidth: 18,
                      color: opt.dim,
                    }}
                  >
                    {opt.letter}.
                  </span>
                  <span
                    style={{
                      flex: 1,
                      fontSize: 13.5,
                      lineHeight: 1.55,
                      fontWeight: opt.textWeight,
                      color: opt.dim,
                    }}
                  >
                    {opt.text}
                  </span>
                  <span
                    style={{
                      flex: "none",
                      marginTop: 1,
                      fontSize: 8,
                      letterSpacing: 1,
                      color: opt.tagColor,
                      opacity: opt.tagOp,
                    }}
                  >
                    {opt.tag}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* nav row: PREV · CHECK · NEXT — spacer — EXPLANATION (v3 design) */}
          <div
            style={{
              flex: "none",
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginTop: "clamp(10px,1.6vh,16px)",
              paddingTop: 14,
              borderTop: "1px dashed var(--line)",
            }}
          >
            <div
              onClick={onPrev}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1,
                padding: "10px 15px",
                border: `2px solid ${qIndex === 0 ? "var(--line)" : "var(--ink)"}`,
                color: qIndex === 0 ? "var(--mute)" : "var(--ink)",
                cursor: qIndex === 0 ? "default" : "pointer",
              }}
            >
              <i className="hn hn-arrow-left" style={{ fontSize: 12 }} />
              PREV
            </div>

            <div
              onClick={onCheck}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1,
                padding: "10px 18px",
                background: rev
                  ? wasCorrect
                    ? "var(--good)"
                    : "var(--bad)"
                  : enabled
                    ? "var(--fill)"
                    : "transparent",
                color: rev ? "#ffffff" : enabled ? "var(--onFill)" : "var(--mute)",
                border: `2px solid ${
                  rev
                    ? wasCorrect
                      ? "var(--good)"
                      : "var(--bad)"
                    : enabled
                      ? "var(--fill)"
                      : "var(--line)"
                }`,
                animation: rev && wasCorrect ? "btnpop .45s ease-out" : "none",
                cursor: !rev && sel ? "pointer" : "default",
              }}
            >
              {centerLabel}{" "}
              <i className={`hn ${centerIcon}`} style={{ fontSize: 12 }} />
            </div>

            <div
              onClick={handleNextClick}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1,
                padding: "10px 15px",
                border: `2px solid ${nextEnabled ? "var(--ink)" : "var(--line)"}`,
                color: nextEnabled ? "var(--ink)" : "var(--mute)",
                cursor: nextEnabled ? "pointer" : "default",
              }}
            >
              {nextLabel}
              <i className="hn hn-arrow-right" style={{ fontSize: 12 }} />
            </div>

            <div style={{ flex: 1 }} />

            <div
              onClick={onToggleExpl}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 1,
                padding: "10px 15px",
                color: "var(--ink)",
                cursor: "pointer",
              }}
            >
              EXPLANATION{" "}
              <i
                className={`hn ${
                  explOpen ? "hn-side-nav-collapse" : "hn-side-nav-expand"
                }`}
                style={{ fontSize: 12, opacity: 1 }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* explanation drawer (slides from right) */}
      <div
        style={{
          flex: "none",
          width: explOpen ? 280 : 0,
          height: "100%",
          borderLeft: "1px dashed var(--line)",
          overflow: "hidden",
          transition: "width .3s ease",
          background: "var(--bg)",
        }}
      >
        <div
          style={{
            width: 280,
            height: "100%",
            boxSizing: "border-box",
            display: "flex",
            flexDirection: "column",
            padding: "22px 22px 26px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <span
              style={{
                fontFamily: "'Press Start 2P',monospace",
                fontSize: 10,
                letterSpacing: 1,
              }}
            >
              EXPLANATION
            </span>
            <i
              onClick={onCloseExpl}
              className="hn hn-times"
              style={{ fontSize: 16, color: "var(--mute)", cursor: "pointer" }}
            />
          </div>

          {rev ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                flex: 1,
                minHeight: 0,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 9,
                  marginTop: 18,
                }}
              >
                <span
                  style={{
                    flex: "none",
                    width: 22,
                    height: 22,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: wasCorrect ? "var(--good)" : "var(--bad)",
                    color: "#ffffff",
                    animation: "fbpop .4s ease-out",
                  }}
                >
                  <i
                    className={`hn ${wasCorrect ? "hn-check" : "hn-times"}`}
                    style={{ fontSize: 11 }}
                  />
                </span>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: 1,
                    color: wasCorrect ? "var(--good)" : "var(--bad)",
                  }}
                >
                  {wasCorrect ? "CORRECT!" : "NOT QUITE"}
                </span>
              </div>
              <div
                style={{
                  display: "inline-flex",
                  alignSelf: "flex-start",
                  alignItems: "center",
                  gap: 8,
                  marginTop: 18,
                  padding: "8px 12px",
                  border: "2px solid var(--ink)",
                }}
              >
                <i className="hn hn-check" style={{ fontSize: 12 }} />
                <span style={{ fontSize: 12, fontWeight: 700 }}>
                  {answerLabel(q)}
                </span>
              </div>
              <div
                style={{
                  fontSize: 9,
                  letterSpacing: 2,
                  color: "var(--mute)",
                  marginTop: 26,
                }}
              >
                WHY
              </div>
              <div
                style={{
                  fontSize: 13,
                  lineHeight: 1.75,
                  marginTop: 12,
                  overflowY: "auto",
                }}
              >
                {q.explain}
              </div>
              <div style={{ flex: 1 }} />
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 9,
                  fontSize: 10,
                  color: "var(--mute)",
                  letterSpacing: 1,
                  borderTop: "1px dashed var(--line)",
                  paddingTop: 16,
                }}
              >
                <i
                  className={`hn ${provenanceIcon}`}
                  style={{ fontSize: 13, color: "var(--ink)" }}
                />
                {provenance}
              </div>
            </div>
          ) : (
            <div
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                textAlign: "center",
                gap: 16,
                color: "var(--mute)",
              }}
            >
              <i className="hn hn-lock" style={{ fontSize: 24 }} />
              <div style={{ fontSize: 10, letterSpacing: 1.5, lineHeight: 1.9 }}>
                ANSWER THE QUESTION
                <br />
                TO REVEAL THE EXPLANATION
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
