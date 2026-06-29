// IdeShell.jsx — the CSAI@LIVE IDE shell. A faithful React port of the
// .design-ref/CSAI-Hub-Pixel-Redesign.dc.html prototype (one DCLogic class
// with a single state object + 4 content views), rewired to real data.
//
// State, handlers, file-tree, tabs and quiz logic mirror the prototype's
// `renderVals()`; the four content views live in ./views/*. The deep-learning
// quiz + lecture tree are driven by ../shell/dlData.js (real exam questions);
// the cognitive-neuroscience branch keeps sample content for v1 but deep-links
// to the real static pages under /cog-neuro/lectures where possible.

import { useState, useRef, useEffect } from "react";
import "./ideShell.css";
import { rootStyle } from "./shellThemes.js";
import { buildFileRows, buildTabs } from "./shellTree.js";
import { applySelection, isAnswerCorrect } from "./shellQuiz.js";
import { COG_NEURO_DOCS } from "./shellContent.js";
import { getLessons, getTopics, DL_LESSONS, DL_TOPICS } from "./dlData.js";
import { listSummaries, getSummary } from "./summaries.js";
import QuizView from "./views/QuizView.jsx";
import DlLectureView from "./views/DlLectureView.jsx";
import DashboardView from "./views/DashboardView.jsx";
import LectureDocView from "./views/LectureDocView.jsx";
import SummaryView from "./views/SummaryView.jsx";

const WALK_MS = 600;
const PROGRESS_KEY = "dlquiz-progress";

function loadProgress() {
  try {
    return JSON.parse(localStorage.getItem(PROGRESS_KEY) || "{}");
  } catch {
    return {};
  }
}

export default function IdeShell() {
  // Real data (built synchronously at module load — no polling needed).
  const lessons = getLessons();
  const topics = getTopics();
  const summaries = listSummaries();

  // ---- view state (mirrors the prototype's single state object) ----
  const [open, setOpen] = useState("quiz");
  const [docId, setDocId] = useState("m3l1");
  const [theme, setTheme] = useState("light");
  const [collapsed, setCollapsed] = useState(false);
  const [material, setMaterial] = useState("pptx");
  const [dlLesson, setDlLesson] = useState(0);
  const [podcast, setPodcast] = useState(false);
  const [podPlaying, setPodPlaying] = useState(false);
  const [summarySlug, setSummarySlug] = useState(summaries[0]?.slug || "rnns");
  const [expanded, setExpanded] = useState({
    deeplearn: true,
    dlquizzes: true,
    dllectures: false,
    dlsummaries: true,
    cogneuro: false,
    m3: true,
    m4: false,
  });
  const [tabs, setTabs] = useState(["quiz", "dllecture"]);
  const [qIndex, setQIndex] = useState(0);
  const [selected, setSelected] = useState([]); // option keys (0..1 for MC)
  const [revealed, setRevealed] = useState(false);
  const [walking, setWalking] = useState(false);
  const [explOpen, setExplOpen] = useState(false);
  const [progress, setProgress] = useState(loadProgress);
  // Persistent podcast player: lives at the shell root so it keeps playing
  // when the user switches tabs/views. { src, label } or null.
  const [nowPlaying, setNowPlaying] = useState(null);

  const scrollRef = useRef(null);
  const walkTimer = useRef(null);
  const dragTab = useRef(null);

  // Expose the frozen data for parity with the prototype (`window.DL_LESSONS`).
  useEffect(() => {
    window.DL_LESSONS = DL_LESSONS;
    window.DL_TOPICS = DL_TOPICS;
  }, []);

  // Reset scroll to top whenever the visible document/view changes.
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [open, docId, dlLesson, summarySlug]);

  // Clear any pending walk timer on unmount.
  useEffect(() => () => clearTimeout(walkTimer.current), []);

  // ---- derived quiz values ----
  const lesson = lessons[dlLesson] || null;
  const questions = lesson ? lesson.questions : [];
  const qcount = Math.max(questions.length, 1);
  const qIndexClamped = Math.min(qIndex, qcount - 1);
  const q = questions[qIndexClamped] || {
    id: "loading",
    type: "multiple_choice",
    q: "Loading questions…",
    options: { A: "…" },
    correct: "A",
    explain: "",
    source: "generated",
  };

  // ---- handlers ----
  const handleOpenFile = (id) => {
    setOpen(id);
    if (id !== "dashboard" && id !== "quiz") setDocId(id);
    setTabs((prev) => (prev.includes(id) ? prev : [...prev, id]));
  };

  const handleToggleFolder = (key) =>
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));

  const handleReorderTabs = (from, to) => {
    if (!from || from === to) return;
    setTabs((prev) => {
      const next = prev.filter((x) => x !== from);
      const ti = next.indexOf(to);
      next.splice(ti < 0 ? next.length : ti, 0, from);
      return next;
    });
  };

  // Close a tab; if it was the active one, fall back to a neighbouring tab.
  const handleCloseTab = (id) => {
    const idx = tabs.indexOf(id);
    const remaining = tabs.filter((x) => x !== id);
    setTabs(remaining);
    if (open === id && remaining.length) {
      const fallback = remaining[Math.min(idx, remaining.length - 1)];
      setOpen(fallback);
      if (
        fallback !== "dashboard" &&
        fallback !== "quiz" &&
        fallback !== "dllecture" &&
        fallback !== "summary"
      ) {
        setDocId(fallback);
      }
    }
  };

  const handleToggleSidebar = () => setCollapsed((c) => !c);
  const handleToggleTheme = () =>
    setTheme((t) => (t === "light" ? "dark" : "light"));
  const handleSetMaterial = (m) => setMaterial(m);

  const resetQuiz = () => {
    setQIndex(0);
    setSelected([]);
    setRevealed(false);
    setWalking(false);
    setExplOpen(false);
  };

  const handleSelectLesson = (i) => {
    clearTimeout(walkTimer.current);
    setDlLesson(i);
    resetQuiz();
  };

  // Open a quiz lesson from the tree (sets the quiz view + the lesson + resets).
  const handleOpenQuizLesson = (i) => {
    clearTimeout(walkTimer.current);
    setOpen("quiz");
    setDlLesson(i);
    resetQuiz();
    setTabs((prev) => (prev.includes("quiz") ? prev : [...prev, "quiz"]));
  };

  // Advance to the next quiz lesson (NEXT QUIZ button at the last question).
  const handleNextQuiz = () => {
    const n = Math.min(lessons.length - 1, dlLesson + 1);
    if (n !== dlLesson) handleOpenQuizLesson(n);
  };

  const handleTogglePodcast = () => {
    if (podcast) {
      setPodcast(false);
      setPodPlaying(false);
    } else {
      setPodcast(true);
      setPodPlaying(true);
    }
  };
  const handleTogglePlay = () => setPodPlaying((p) => !p);
  const handleClosePodcast = () => {
    setPodcast(false);
    setPodPlaying(false);
  };

  const handleOpenDlLesson = (i) => {
    setOpen("dllecture");
    setDlLesson(i);
    setTabs((prev) =>
      prev.includes("dllecture") ? prev : [...prev, "dllecture"],
    );
  };

  const handleOpenSummary = (slug) => {
    setOpen("summary");
    setSummarySlug(slug);
    setTabs((prev) => (prev.includes("summary") ? prev : [...prev, "summary"]));
  };

  const handlePlayPodcast = (src, label) => setNowPlaying({ src, label });
  const handleStopPodcast = () => setNowPlaying(null);

  const handleSelectOption = (letter) => {
    if (revealed) return;
    setSelected((prev) => applySelection(q, prev, letter));
  };
  const handleCheck = () => {
    if (selected.length === 0 || revealed) return;
    const wasCorrect = isAnswerCorrect(q, selected);
    setProgress((prev) => {
      const next = {
        ...prev,
        [dlLesson]: { ...(prev[dlLesson] || {}), [qIndexClamped]: wasCorrect },
      };
      try {
        localStorage.setItem(PROGRESS_KEY, JSON.stringify(next));
      } catch {
        // ignore storage failures (private mode, quota) — progress is non-critical
      }
      return next;
    });
    setRevealed(true);
    setExplOpen(true);
  };
  const handleToggleExpl = () => setExplOpen((o) => !o);
  const handleCloseExpl = () => setExplOpen(false);

  const walkTo = (next) => {
    clearTimeout(walkTimer.current);
    setQIndex(next);
    setSelected([]);
    setRevealed(false);
    setWalking(true);
    walkTimer.current = setTimeout(() => setWalking(false), WALK_MS);
  };
  const handleNext = () => {
    const n = Math.min(qcount - 1, qIndex + 1);
    if (n !== qIndex) walkTo(n);
  };
  const handlePrev = () => {
    const n = Math.max(0, qIndex - 1);
    if (n !== qIndex) walkTo(n);
  };

  // ---- view-model: tree, tabs, routing ----
  const rows = buildFileRows(
    { open, expanded, dlLesson, topics, progress, summaries, summarySlug },
    {
      onToggle: handleToggleFolder,
      onOpenFile: handleOpenFile,
      onOpenDlLesson: handleOpenDlLesson,
      onOpenQuizLesson: handleOpenQuizLesson,
      onOpenSummary: handleOpenSummary,
    },
  );

  const tabModels = buildTabs(tabs, open);

  const isQuiz = open === "quiz";
  const isDashboard = open === "dashboard";
  const isDl = open === "dllecture";
  const isSummary = open === "summary";
  const isLecture = !isQuiz && !isDashboard && !isDl && !isSummary;
  const doc = COG_NEURO_DOCS[docId] || COG_NEURO_DOCS.m3l1;

  const sidebarWidth = collapsed ? "0px" : "274px";

  return (
    <div className="ide-shell" style={rootStyle(theme)}>
      {/* ===================== SIDEBAR ===================== */}
      <div
        style={{
          flex: "none",
          width: sidebarWidth,
          minWidth: sidebarWidth,
          display: "flex",
          flexDirection: "column",
          background: "var(--bg)",
          borderRight: "1px dashed var(--line)",
          overflow: "hidden",
          transition: "width .22s ease, min-width .22s ease",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 13,
            padding: "24px 18px 20px",
          }}
        >
          <span
            style={{
              fontFamily: "'Press Start 2P',monospace",
              fontSize: 13,
              letterSpacing: 1,
              whiteSpace: "nowrap",
              display: "inline-flex",
              alignItems: "center",
            }}
          >
            CSAI
            <span
              style={{ fontSize: 13, margin: "0 2px", color: "var(--accent)" }}
            >
              @
            </span>
            LIVE
          </span>
          <span style={{ flex: 1 }} />
          <i
            onClick={handleToggleSidebar}
            className="hn hn-side-nav-collapse"
            style={{ fontSize: 21, color: "var(--ink)", cursor: "pointer" }}
          />
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            padding: "6px 22px 14px",
          }}
        >
          <span
            style={{
              fontFamily: "'Press Start 2P',monospace",
              fontSize: 8,
              letterSpacing: 1,
              color: "var(--mute)",
            }}
          >
            FILES
          </span>
          <span style={{ flex: 1 }} />
          <i
            className="hn hn-plus"
            style={{
              fontSize: 15,
              color: "var(--mute)",
              cursor: "pointer",
              marginRight: 14,
            }}
          />
          <i
            className="hn hn-folder"
            style={{ fontSize: 15, color: "var(--mute)", cursor: "pointer" }}
          />
        </div>

        <div
          style={{
            flex: 1,
            minHeight: 0,
            overflow: "auto",
            padding: "2px 12px 12px",
          }}
        >
          {rows.map((row) => (
            <div
              key={row.key}
              onClick={row.onClick}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 11,
                height: 36,
                paddingRight: 10,
                paddingLeft: row.pad,
                cursor: "pointer",
                fontSize: 12.5,
                color: row.fg,
                fontWeight: row.weight,
                background: row.bg,
                borderLeft: `3px solid ${row.mark}`,
              }}
            >
              <i
                className={`hn ${row.chev}`}
                style={{
                  fontSize: 9,
                  width: 9,
                  textAlign: "center",
                  color: "var(--mute)",
                  opacity: row.chevOp,
                }}
              />
              <i
                className={`hn ${row.icon}`}
                style={{ fontSize: 15, color: row.iconColor }}
              />
              <span
                style={{
                  flex: 1,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {row.label}
              </span>
              {row.prog ? (
                <span
                  style={{
                    flex: "none",
                    fontSize: 8,
                    letterSpacing: 1,
                    color: "var(--mute)",
                  }}
                >
                  {row.prog}
                </span>
              ) : null}
              {row.tagIcon ? (
                <i
                  className={`hn ${row.tagIcon}`}
                  style={{ flex: "none", fontSize: 11, color: "var(--ink)" }}
                />
              ) : null}
            </div>
          ))}
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
            padding: "18px 24px",
            borderTop: "1px dashed var(--line)",
          }}
        >
          <a
            href="https://github.com/rpaszekdev/Csai-"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: "var(--ink)",
              textDecoration: "none",
              display: "flex",
            }}
          >
            <i className="hn hn-github" style={{ fontSize: 19 }} />
          </a>
          <i
            onClick={handleToggleTheme}
            className={`hn ${theme === "light" ? "hn-moon" : "hn-sun"}`}
            style={{ fontSize: 19, cursor: "pointer" }}
          />
        </div>
      </div>

      {/* ===================== MAIN ===================== */}
      <div
        style={{
          flex: 1,
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
          background: "var(--bg)",
        }}
      >
        {/* tab bar */}
        <div
          style={{
            flex: "none",
            display: "flex",
            alignItems: "stretch",
            height: 52,
            borderBottom: "1px dashed var(--line)",
          }}
        >
          {collapsed && (
            <div
              onClick={handleToggleSidebar}
              style={{
                flex: "none",
                width: 52,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                borderRight: "1px dashed var(--line)",
                color: "var(--ink)",
              }}
            >
              <i className="hn hn-side-nav-expand" style={{ fontSize: 19 }} />
            </div>
          )}
          <div
            style={{
              flex: 1,
              minWidth: 0,
              display: "flex",
              alignItems: "stretch",
              overflowX: "auto",
            }}
          >
            {tabModels.map((tab) => (
              <div
                key={tab.id}
                onClick={() => handleOpenFile(tab.id)}
                draggable="true"
                onDragStart={() => {
                  dragTab.current = tab.id;
                }}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  handleReorderTabs(dragTab.current, tab.id);
                }}
                style={{
                  flex: "none",
                  display: "flex",
                  alignItems: "center",
                  gap: 9,
                  padding: "0 18px",
                  cursor: "pointer",
                  fontSize: 12,
                  color: tab.fg,
                  fontWeight: tab.weight,
                  borderRight: "1px dashed var(--line)",
                  borderBottom: `2px solid ${tab.ind}`,
                  position: "relative",
                  top: 1,
                }}
              >
                <i
                  className={`hn ${tab.icon}`}
                  style={{ fontSize: 13, color: tab.iconColor }}
                />
                <span style={{ whiteSpace: "nowrap" }}>{tab.label}</span>
                <i
                  className="hn hn-times"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCloseTab(tab.id);
                  }}
                  style={{
                    fontSize: 10,
                    color: "var(--mute)",
                    marginLeft: 6,
                    cursor: "pointer",
                  }}
                />
              </div>
            ))}
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 16,
              padding: "0 22px",
              color: "var(--mute)",
              fontSize: 10,
              letterSpacing: 1,
            }}
          >
            <span>UTF-8</span>
            <i className="hn hn-eye" style={{ fontSize: 15 }} />
          </div>
        </div>

        {/* content */}
        <div
          ref={scrollRef}
          style={{
            flex: 1,
            minHeight: 0,
            overflowX: "hidden",
            overflowY: isQuiz ? "hidden" : "auto",
          }}
        >
          {isQuiz && (
            <QuizView
              topics={topics}
              dlLesson={dlLesson}
              onSelectLesson={handleSelectLesson}
              lesson={lesson}
              qIndex={qIndexClamped}
              qcount={qcount}
              q={q}
              selected={selected}
              revealed={revealed}
              walking={walking}
              explOpen={explOpen}
              onSelectOption={handleSelectOption}
              onCheck={handleCheck}
              onPrev={handlePrev}
              onNext={handleNext}
              onNextQuiz={handleNextQuiz}
              lessonCount={lessons.length}
              onToggleExpl={handleToggleExpl}
              onCloseExpl={handleCloseExpl}
            />
          )}

          {isDl && (
            <DlLectureView
              topic={lesson ? lesson.topic : DL_TOPICS[dlLesson].topic}
              dlLesson={dlLesson}
              material={material}
              onSetMaterial={handleSetMaterial}
              podcast={podcast}
              podPlaying={podPlaying}
              onTogglePodcast={handleTogglePodcast}
              onTogglePlay={handleTogglePlay}
              onClosePodcast={handleClosePodcast}
            />
          )}

          {isSummary && (
            <SummaryView
              data={getSummary(summarySlug)}
              slug={summarySlug}
              onPlayPodcast={handlePlayPodcast}
            />
          )}

          {isDashboard && <DashboardView onOpenFile={handleOpenFile} />}

          {isLecture && <LectureDocView doc={doc} />}
        </div>

        {/* persistent podcast player — stays mounted across tab/view switches */}
        {nowPlaying && (
          <div
            style={{
              flex: "none",
              display: "flex",
              alignItems: "center",
              gap: 14,
              padding: "11px 20px",
              borderTop: "1px dashed var(--line)",
              background: "var(--bg)",
            }}
          >
            <span
              style={{
                fontFamily: "'Press Start 2P',monospace",
                fontSize: 8,
                letterSpacing: 1,
                color: "var(--ink)",
                whiteSpace: "nowrap",
              }}
            >
              ▶ {nowPlaying.label}
            </span>
            <audio
              key={nowPlaying.src}
              src={nowPlaying.src}
              controls
              autoPlay
              style={{ flex: 1, height: 36 }}
            />
            <i
              onClick={handleStopPodcast}
              className="hn hn-times"
              style={{ fontSize: 15, color: "var(--mute)", cursor: "pointer" }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
