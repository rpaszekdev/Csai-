#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
HTML_FILE="${PROJECT_DIR}/index.html"

# Get events with calendar name for type detection
# Use separate calls per calendar type for clean categorization

EXCLUDED="Święta w Polsce,Birthdays,Przypomnienia,Siri Suggestions,Scheduled Reminders"
DAY="eventsFrom:\"tomorrow\" to:\"tomorrow\""

RAW_WITH_CALS=$(/opt/homebrew/bin/icalBuddy -f -nrd -npn -ea -eed -b "" -ss "" -po "title,calendar,datetime" -iep "title,calendar,datetime" -tf "%H:%M" -ec "$EXCLUDED" eventsToday 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g')

ALL_EVENTS=""
while IFS= read -r line; do
  [ -z "$line" ] && continue
  [[ "$line" =~ ^[[:space:]] ]] && continue

  TITLE=$(echo "$line" | sed 's/ (.*//')
  CAL=$(echo "$line" | grep -o '([^)]*) *$' | tr -d '()')

  [ -z "$TITLE" ] && continue

  case "$CAL" in
    "Study Schedule"|"ignore "|"ignore") TYPE="study" ;;
    "University "|"University"|"Tilburg University"*) TYPE="lecture" ;;
    "Deadline"|"Deadline ") TYPE="deadline" ;;
    "People "|"People") TYPE="meeting" ;;
    "Study"|"Study ") TYPE="exam" ;;
    *) TYPE="other" ;;
  esac

  ALL_EVENTS+="${TYPE}||| ||| ${TITLE}"$'\n'
done <<< "$RAW_WITH_CALS"

# Now get times separately
RAW_TIMES=$(/opt/homebrew/bin/icalBuddy -f -nc -nrd -npn -ea -eed -ps "/ ||| /" -po "datetime,title" -iep "datetime,title" -tf "%H:%M" -b "" -ss "" -ec "$EXCLUDED" eventsToday 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g')

# Build combined: use the calendar-typed list with times from second query
ALL_EVENTS=""
IDX=0
declare -a TYPES_ARR
declare -a TITLES_ARR

while IFS= read -r line; do
  [ -z "$line" ] && continue
  [[ "$line" =~ ^[[:space:]] ]] && continue
  T=$(echo "$line" | sed 's/ (.*//')
  C=$(echo "$line" | grep -o '([^)]*) *$' | tr -d '()')
  [ -z "$T" ] && continue
  case "$C" in
    "Study Schedule"|"ignore "|"ignore") TYPE="study" ;;
    "University "|"University"|"Tilburg University"*) TYPE="lecture" ;;
    "Deadline"|"Deadline ") TYPE="deadline" ;;
    "People "|"People") TYPE="meeting" ;;
    "Study"|"Study ") TYPE="exam" ;;
    *) TYPE="other" ;;
  esac
  TYPES_ARR[$IDX]="$TYPE"
  TITLES_ARR[$IDX]="$T"
  IDX=$((IDX + 1))
done <<< "$RAW_WITH_CALS"

# Get times in order
IDX=0
ALL_EVENTS=""
while IFS= read -r line; do
  [ -z "$line" ] && continue
  [[ "$line" =~ ^[[:space:]] ]] && continue
  TIME=$(echo "$line" | sed 's/ |||.*//' | xargs)
  TITLE=$(echo "$line" | sed 's/.*||| //' | xargs)
  [ -z "$TITLE" ] && continue

  TYPE="${TYPES_ARR[$IDX]:-other}"
  ALL_EVENTS+="${TYPE}|||${TIME} ||| ${TITLE}"$'\n'
  IDX=$((IDX + 1))
done <<< "$RAW_TIMES"

TU="/Users/robertpaszek/Desktop/Tilburg University"

gen_tip() {
  local title="$1"
  local t=$(echo "$title" | tr '[:upper:]' '[:lower:]')

  if [[ "$t" == *"dl:"* ]] || [[ "$t" == *"deep learning"* ]] || [[ "$t" == *"mlp"* ]] || [[ "$t" == *"backprop"* ]] || [[ "$t" == *"cnn"* ]] || [[ "$t" == *"rnn"* ]] || [[ "$t" == *"transformer"* ]] || [[ "$t" == *"regularization"* ]] || [[ "$t" == *"optimizer"* ]] || [[ "$t" == *"computer vision"* ]]; then
    local files=$(ls "$TU/Deep Learning/Lecture Presentations/" 2>/dev/null | head -4 | tr '\n' ', ' | sed 's/,$//')
    local notebooks=$(ls "$TU/Deep Learning/Assignments/" 2>/dev/null | grep -i ".ipynb" | head -2 | tr '\n' ', ' | sed 's/,$//')
    local tip="Course: Introduction to Deep Learning. "
    if [[ "$t" == *"mlp"* ]]; then tip+="Focus on perceptron architecture, activation functions, forward pass. "; fi
    if [[ "$t" == *"backprop"* ]]; then tip+="Focus on chain rule, gradient computation, weight updates. "; fi
    if [[ "$t" == *"cnn"* ]]; then tip+="Focus on convolution, pooling, feature maps, architectures. "; fi
    if [[ "$t" == *"regularization"* ]]; then tip+="Focus on dropout, L1/L2, data augmentation, batch norm. "; fi
    if [[ "$t" == *"optimizer"* ]]; then tip+="Focus on SGD, momentum, Adam, learning rate schedules. "; fi
    if [[ "$t" == *"rnn"* ]] || [[ "$t" == *"recur"* ]]; then tip+="Focus on vanishing gradients, LSTM, GRU, seq2seq. "; fi
    if [[ "$t" == *"transformer"* ]]; then tip+="Focus on self-attention, multi-head, positional encoding. "; fi
    if [[ "$t" == *"vision"* ]] || [[ "$t" == *"cv"* ]]; then tip+="Focus on ResNet, transfer learning, object detection. "; fi
    tip+="Materials: ${files:-check Lecture Presentations folder}. "
    [ -n "$notebooks" ] && tip+="Notebooks: ${notebooks}."
    echo "$tip"
    return
  fi

  if [[ "$t" == *"adv prog"* ]] || [[ "$t" == *"advanced prog"* ]] || [[ "$t" == *"fp review"* ]] || [[ "$t" == *"fp practice"* ]] || [[ "$t" == *"concurrency"* ]] || [[ "$t" == *"oop"* ]] || [[ "$t" == *"design pattern"* ]]; then
    local tip="Course: Advanced Programming for CSAI. "
    if [[ "$t" == *"fp"* ]] || [[ "$t" == *"functional"* ]]; then tip+="Focus on lambda, map/filter/reduce, decorators, currying, generators, comprehensions. Use FP_Exam_Study_Guide.ipynb. "; fi
    if [[ "$t" == *"concurrency"* ]]; then tip+="Focus on threading, multiprocessing, thread safety, locks, GIL. Check AP2526_Concurrency_1_assignment.ipynb. "; fi
    if [[ "$t" == *"oop"* ]]; then tip+="Focus on inheritance, polymorphism, abstract classes, SOLID principles. "; fi
    if [[ "$t" == *"design pattern"* ]]; then tip+="Focus on singleton, factory, observer, strategy, decorator patterns. "; fi
    local files=$(ls "$TU/Advanced Programming/Functional Programming/" 2>/dev/null | grep -i "complete" | head -3 | tr '\n' ', ' | sed 's/,$//')
    [ -n "$files" ] && tip+="Completed notebooks: ${files}."
    echo "$tip"
    return
  fi

  if [[ "$t" == *"auto"* ]] || [[ "$t" == *"autonomous"* ]]; then
    local tip="Course: Autonomous Systems. "
    local lectures=$(ls "$TU/Autonomus Systems/Lectures/" 2>/dev/null | head -3 | tr '\n' ', ' | sed 's/,$//')
    local readings=$(ls "$TU/Autonomus Systems/Readings/" 2>/dev/null | head -3 | tr '\n' ', ' | sed 's/,$//')
    tip+="Topics: Braitenberg vehicles, controllers, embodiment, RL, social robotics, HRI. "
    tip+="Exam: ~50 Qs (T/F, open, fill-in). "
    [ -n "$lectures" ] && tip+="Lectures: ${lectures}. "
    [ -n "$readings" ] && tip+="Readings: ${readings}."
    echo "$tip"
    return
  fi

  if [[ "$t" == *"cog"* ]] || [[ "$t" == *"neuro"* ]]; then
    local tip="Course: Cognitive Neuroscience. "
    tip+="Topics: history, motor control, memory, emotion, executive function, decision making. "
    tip+="Exam: 30 Qs (MC, matching, fill-in), 120 min. "
    tip+="Book: Purves et al. Principles of Cognitive Neuroscience. "
    local ankis=$(ls "$TU/Cognitive Neuroscience/" 2>/dev/null | grep -i "anki" | wc -l | xargs)
    [ "$ankis" -gt 0 ] && tip+="Anki decks available: ${ankis} modules."
    echo "$tip"
    return
  fi

  if [[ "$t" == *"research"* ]] || [[ "$t" == *"rw:"* ]] || [[ "$t" == *"research ws"* ]]; then
    local tip="Course: Research Workshop CSAI. "
    tip+="Project: spatial-reasoning-dsl. Paper deadline: May 30. "
    tip+="Focus on methodology, results interpretation, academic writing."
    echo "$tip"
    return
  fi

  echo ""
}

EVENTS_JSON="["
FIRST=true
SEEN=""
while IFS= read -r line; do
  [ -z "$line" ] && continue
  TYPE=$(echo "$line" | sed 's/|||.*//')
  REST=$(echo "$line" | sed 's/^[^|]*|||//')
  TIME=$(echo "$REST" | sed 's/ |||.*//' | xargs)
  TITLE=$(echo "$REST" | sed 's/.*||| //' | xargs)
  [ -z "$TITLE" ] && continue
  TITLE=$(echo "$TITLE" | sed 's/^Vak: [0-9A-Z-]*\. //')
  KEY="${TIME}::${TITLE}"
  if echo "$SEEN" | grep -qF "$KEY"; then continue; fi
  SEEN="${SEEN}${KEY}"$'\n'
  TITLE_ESC=$(echo "$TITLE" | sed 's/"/\\"/g' | sed "s/'/\\\\'/g")
  TIME_ESC=$(echo "$TIME" | sed 's/"/\\"/g')
  TIP=$(gen_tip "$TITLE")
  TIP_ESC=$(echo "$TIP" | sed 's/"/\\"/g' | sed "s/'/\\\\'/g")
  if [ "$FIRST" = true ]; then FIRST=false; else EVENTS_JSON+=","; fi
  EVENTS_JSON+="{\"time\":\"${TIME_ESC}\",\"title\":\"${TITLE_ESC}\",\"type\":\"${TYPE}\",\"tip\":\"${TIP_ESC}\"}"
done <<< "$ALL_EVENTS"
EVENTS_JSON+="]"

cat > "$HTML_FILE" << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Focus Pilot</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #EDEBE6;
    --card: #F5F4F1;
    --card-hover: #EEEDEA;
    --terra: #8B7355;
    --ink: #2C2824;
    --ink-mid: #4A4640;
    --ink-mute: #8A8680;
    --ink-faint: #C5C2BC;
    --done: #A8B89A;
    --done-bg: rgba(168, 184, 154, 0.18);
    --progress: #C9A84C;
    --progress-bg: rgba(201, 168, 76, 0.12);
    --lecture-bg: rgba(91, 120, 150, 0.06);
    --lecture: #7A8FA0;
    --deadline: #B86B5A;
    --meeting: #8A7AB0;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: "JetBrains Mono", ui-monospace, monospace;
    background: var(--bg);
    color: var(--ink);
    line-height: 1.6;
    min-height: 100vh;
  }

  .page {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 28px 60px;
  }

  .top {
    display: flex;
    align-items: baseline;
    padding: 28px 0 20px;
  }

  .date {
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--ink-mute);
    font-weight: 300;
  }

  .top-right {
    margin-left: auto;
    display: flex;
    align-items: baseline;
    gap: 20px;
  }

  .focus-total {
    font-size: 9px;
    letter-spacing: 0.12em;
    color: var(--ink-faint);
    font-weight: 300;
  }

  .focus-total span { color: var(--ink-mute); font-weight: 500; }

  .target {
    font-size: 9px;
    letter-spacing: 0.12em;
    color: var(--ink-faint);
    font-weight: 300;
  }

  .target span { color: var(--ink-mute); font-weight: 500; }

  .layout {
    display: grid;
    grid-template-columns: 1fr 360px;
    gap: 3px;
    margin-top: 16px;
  }

  .left {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .summary-card {
    background: var(--card);
    padding: 20px 22px;
    display: flex;
    align-items: baseline;
    gap: 18px;
  }

  .s-count {
    font-family: "DM Serif Display", Georgia, serif;
    font-size: 36px;
    line-height: 1;
  }

  .s-meta { display: flex; flex-direction: column; gap: 3px; }

  .s-label {
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--ink-mute);
    font-weight: 400;
  }

  .s-bar { width: 100px; height: 2px; background: var(--ink-faint); margin-top: 3px; }
  .s-bar-fill { height: 100%; background: var(--done); transition: width 0.4s; }

  .grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 3px;
  }

  /* ─── Cell ─── */
  .cell {
    background: var(--card);
    padding: 16px 16px 12px;
    min-height: 90px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    position: relative;
    overflow: hidden;
    user-select: none;
  }

  .cell:hover { background: var(--card-hover); }
  .cell.selected { box-shadow: inset 2px 0 0 var(--terra); }

  .cell.in-progress {
    background: var(--progress-bg);
    box-shadow: inset 2px 0 0 var(--progress);
  }
  .cell.in-progress::after {
    content: ""; position: absolute;
    bottom: 0; left: 0; right: 0; height: 2px;
    background: var(--progress);
  }
  .cell.in-progress .c-dot { background: var(--progress); }

  .cell.done { background: var(--done-bg); }
  .cell.done::after {
    content: ""; position: absolute;
    bottom: 0; left: 0; right: 0; height: 2px;
    background: var(--done);
  }
  .cell.done .c-title {
    text-decoration: line-through;
    text-decoration-color: var(--done);
    text-decoration-thickness: 1px;
    color: var(--ink-mute);
  }
  .cell.done .c-dot { background: var(--done); }

  /* Lecture / non-study cells */
  .cell.is-lecture { background: var(--lecture-bg); cursor: default; }
  .cell.is-lecture .c-dot { background: var(--lecture); }
  .cell.is-lecture:hover { background: var(--lecture-bg); }

  .cell.is-deadline .c-dot { background: var(--deadline); }
  .cell.is-meeting .c-dot { background: var(--meeting); }

  .c-time {
    font-size: 10px;
    letter-spacing: 0.1em;
    color: var(--ink-mute);
    font-weight: 300;
    margin-bottom: 4px;
  }

  .c-title {
    font-size: 12px;
    font-weight: 500;
    line-height: 1.4;
    flex: 1;
  }

  .c-foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 8px;
  }

  .c-dot { width: 5px; height: 5px; background: var(--terra); }

  .c-type {
    font-size: 8px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--ink-faint);
    font-weight: 400;
  }

  .c-type.t-study { color: var(--terra); }
  .c-type.t-lecture { color: var(--lecture); }
  .c-type.t-deadline { color: var(--deadline); }
  .c-type.t-meeting { color: var(--meeting); }
  .c-type.t-exam { color: var(--deadline); }

  .c-status {
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--ink-faint);
    font-weight: 400;
  }

  .c-status.is-done { color: var(--done); font-weight: 500; }
  .c-status.is-running { color: var(--progress); }

  /* ─── Right panel ─── */
  .right-panel {
    background: var(--card);
    padding: 28px 24px;
    display: flex;
    flex-direction: column;
    min-height: 380px;
    position: sticky;
    top: 16px;
    align-self: start;
  }

  .rp-label {
    font-size: 9px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--ink-faint);
    font-weight: 400;
    margin-bottom: 20px;
  }

  .rp-time {
    font-size: 10px;
    letter-spacing: 0.12em;
    color: var(--ink-mute);
    font-weight: 300;
    margin-bottom: 6px;
  }

  .rp-title {
    font-family: "DM Serif Display", Georgia, serif;
    font-size: 20px;
    line-height: 1.3;
    margin-bottom: 6px;
  }

  .rp-type-tag {
    font-size: 8px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--ink-faint);
    margin-bottom: 24px;
  }

  .rp-idle {
    color: var(--ink-faint);
    font-size: 11px;
    letter-spacing: 0.06em;
    line-height: 1.8;
    font-weight: 300;
  }

  .rp-timer { margin-top: auto; display: none; }
  .rp-timer.show { display: block; }

  .rp-display {
    font-family: "DM Serif Display", Georgia, serif;
    font-size: 56px;
    letter-spacing: -0.02em;
    color: var(--ink);
    font-variant-numeric: tabular-nums;
    line-height: 1;
    transition: color 0.3s;
  }

  .rp-display.running { color: var(--progress); }
  .rp-display.on-break { color: var(--done); }

  .rp-mode {
    font-size: 9px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--ink-mute);
    font-weight: 300;
    margin: 4px 0 12px;
  }

  .rp-bar { height: 2px; background: var(--ink-faint); margin-bottom: 16px; }
  .rp-bar-fill { height: 100%; background: var(--progress); transition: width 1s linear; }
  .rp-bar-fill.on-break { background: var(--done); }

  .rp-btns { display: flex; gap: 6px; }

  .rp-btn {
    font-family: inherit; font-size: 9px;
    letter-spacing: 0.18em; text-transform: uppercase;
    font-weight: 500; padding: 8px 16px;
    border: 1px solid var(--ink-mute); background: none;
    color: var(--ink-mid); cursor: pointer;
    transition: all 0.15s; flex: 1;
  }

  .rp-btn:hover { background: var(--ink); color: var(--card); border-color: var(--ink); }
  .rp-btn.go { background: var(--progress); border-color: var(--progress); color: #fff; }
  .rp-btn.brk { background: var(--done); border-color: var(--done); color: #fff; }
  .rp-btn.done-btn { background: var(--done); border-color: var(--done); color: #fff; }

  .rp-done-row { display: none; margin-top: 10px; }
  .rp-done-row.show { display: flex; }

  .rp-notes { margin-top: 16px; display: none; }
  .rp-notes.show { display: block; }

  .rp-notes-label {
    font-size: 9px; letter-spacing: 0.18em;
    text-transform: uppercase; color: var(--ink-faint);
    font-weight: 400; margin-bottom: 4px;
  }

  .rp-notes textarea {
    width: 100%; min-height: 60px; padding: 8px 10px;
    font-family: inherit; font-size: 11px; line-height: 1.5;
    color: var(--ink); background: var(--bg);
    border: 1px solid var(--ink-faint); resize: vertical; outline: none;
  }

  .rp-notes textarea:focus { border-color: var(--ink-mute); }
  .rp-notes textarea::placeholder { color: var(--ink-faint); font-style: italic; }

  .rp-dot { width: 6px; height: 6px; background: var(--terra); margin-bottom: 14px; }
  .rp-dot.running { background: var(--progress); }
  .rp-dot.done { background: var(--done); }

  /* lecture panel — no timer */
  .rp-lecture-msg {
    display: none;
    color: var(--ink-faint);
    font-size: 10px;
    letter-spacing: 0.08em;
    font-weight: 300;
    margin-top: auto;
    font-style: italic;
  }

  .rp-lecture-msg.show { display: block; }

  .rp-tip {
    display: none;
    margin-top: 0;
    margin-bottom: 16px;
    padding: 12px 14px;
    background: var(--bg);
    font-size: 10px;
    line-height: 1.65;
    color: var(--ink-mid);
    font-weight: 300;
    letter-spacing: 0.02em;
  }

  .rp-tip.show { display: block; }

  .rp-tip-label {
    font-size: 8px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--ink-faint);
    font-weight: 400;
    margin-bottom: 4px;
  }

  .stats {
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-top: 14px;
  }

  .stat {
    padding: 8px 14px;
    text-align: center;
    display: flex;
    align-items: baseline;
    gap: 5px;
  }

  .stat-n { font-size: 11px; font-weight: 500; color: var(--ink-mute); }
  .stat-l {
    font-size: 9px; letter-spacing: 0.15em;
    text-transform: uppercase; color: var(--ink-faint); font-weight: 300;
  }
</style>
</head>
<body>
<div class="page">
  <div class="top">
    <span class="date" id="dateEl"></span>
    <div class="top-right">
      <span class="target"><span id="targetH">0h</span> target · <span id="targetP">0</span> pomos</span>
      <span class="focus-total"><span id="focusH">0h 0m</span> focused</span>
    </div>
  </div>

  <div class="layout">
    <div class="left">
      <div class="summary-card">
        <div class="s-count" id="sCount">0</div>
        <div class="s-meta">
          <div class="s-label">Tasks</div>
          <div class="s-label"><span id="sDone">0</span> done</div>
          <div class="s-bar"><div class="s-bar-fill" id="sBar" style="width:0%"></div></div>
        </div>
      </div>
      <div class="grid" id="grid"></div>
    </div>

    <div class="right-panel" id="rightPanel">
      <div class="rp-label">Selected</div>
      <div class="rp-dot" id="rpDot"></div>
      <div class="rp-time" id="rpTime"></div>
      <div class="rp-title" id="rpTitle"></div>
      <div class="rp-type-tag" id="rpType"></div>
      <div class="rp-tip" id="rpTip">
        <div class="rp-tip-label">Details</div>
        <div id="rpTipText"></div>
      </div>
      <div class="rp-idle" id="rpIdle">
        Select a task to begin.
      </div>
      <div class="rp-lecture-msg" id="rpLecture">
        Lecture — no timer needed.
      </div>
      <div class="rp-timer" id="rpTimer">
        <div class="rp-display" id="rpDisp">40:00</div>
        <div class="rp-mode" id="rpMode">Focus</div>
        <div class="rp-bar"><div class="rp-bar-fill" id="rpBar" style="width:100%"></div></div>
        <div class="rp-btns">
          <button class="rp-btn" id="rpStart" onclick="go()">Start</button>
          <button class="rp-btn" onclick="rst()">Reset</button>
        </div>
        <div class="rp-done-row" id="rpDoneRow">
          <button class="rp-btn done-btn" onclick="markDone()">Mark done</button>
        </div>
      </div>
      <div class="rp-notes" id="rpNotes">
        <div class="rp-notes-label">Notes</div>
        <textarea id="rpNotesText" placeholder="..." oninput="saveNote()"></textarea>
      </div>
    </div>
  </div>

  <div class="stats">
    <div class="stat"><div class="stat-n" id="xDone">0</div><div class="stat-l">done</div></div>
    <div class="stat"><div class="stat-n" id="xTotal">0</div><div class="stat-l">total</div></div>
    <div class="stat"><div class="stat-n" id="xPomo">0</div><div class="stat-l">pomos</div></div>
  </div>
</div>

<script>
HTMLEOF

echo "const EV = ${EVENTS_JSON};" >> "$HTML_FILE"

cat >> "$HTML_FILE" << 'HTMLEOF2'
const FOCUS = 40*60, BRK = 10*60;
document.getElementById('dateEl').textContent = new Date().toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'});

const grid = document.getElementById('grid');
let act = null, pomos = 0, tmr = null, focusSec = 0;
const S = [];
const notes = JSON.parse(localStorage.getItem('fp-notes') || '{}');

const STUDY_TYPES = ['study','exam'];
const VIEW_TYPES = ['lecture','meeting','deadline','other'];

const fmt = s => String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');

// Calculate target: each study block = 1 pomodoro (40 min)
const studyCount = EV.filter(e => STUDY_TYPES.includes(e.type)).length;
const targetPomos = studyCount;
const targetHours = Math.round(studyCount * 40 / 60 * 10) / 10;
document.getElementById('targetP').textContent = targetPomos;
document.getElementById('targetH').textContent = targetHours + 'h';

function upd() {
  const studyDone = S.filter((x,i) => x.done && STUDY_TYPES.includes(EV[i].type)).length;
  const total = EV.filter(e => STUDY_TYPES.includes(e.type)).length;
  const allDone = S.filter(x => x.done).length;
  document.getElementById('sCount').textContent = EV.length;
  document.getElementById('sDone').textContent = allDone;
  document.getElementById('sBar').style.width = (total ? studyDone/total*100 : 0) + '%';
  document.getElementById('xDone').textContent = allDone;
  document.getElementById('xTotal').textContent = EV.length;
  document.getElementById('xPomo').textContent = pomos;
}

const TYPE_LABELS = {study:'study',lecture:'lecture',deadline:'deadline',meeting:'meeting',exam:'exam',other:'event'};
const TYPE_CSS = {study:'t-study',lecture:'t-lecture',deadline:'t-deadline',meeting:'t-meeting',exam:'t-exam',other:''};

EV.forEach((e,i) => {
  S.push({done:false, p:0});
  const isView = VIEW_TYPES.includes(e.type);
  const c = document.createElement('div');
  c.className = 'cell' + (isView ? ' is-' + e.type : '');
  c.id = 'c'+i;
  c.innerHTML = `
    <div class="c-time">${e.time}</div>
    <div class="c-title">${e.title}</div>
    <div class="c-foot">
      <div class="c-dot"></div>
      <span class="c-type ${TYPE_CSS[e.type] || ''}">${TYPE_LABELS[e.type] || ''}</span>
      <span class="c-status" id="s${i}">${isView ? '' : 'ready'}</span>
    </div>`;
  c.onclick = () => sel(i);
  grid.appendChild(c);
});
upd();

function sel(i) {
  if (S[i].done && STUDY_TYPES.includes(EV[i].type)) return;
  if (tmr && tmr.on && act !== i) return;
  if (act !== null && act !== i) {
    document.getElementById('c'+act).classList.remove('selected');
  }
  act = i;
  document.getElementById('c'+i).classList.add('selected');
  document.getElementById('rpTime').textContent = EV[i].time;
  document.getElementById('rpTitle').textContent = EV[i].title;
  document.getElementById('rpType').textContent = TYPE_LABELS[EV[i].type] || '';
  document.getElementById('rpIdle').style.display = 'none';
  if (EV[i].tip) {
    document.getElementById('rpTipText').textContent = EV[i].tip;
    document.getElementById('rpTip').classList.add('show');
  } else {
    document.getElementById('rpTip').classList.remove('show');
  }
  document.getElementById('rpNotes').classList.add('show');
  document.getElementById('rpNotesText').value = notes[i] || '';
  document.getElementById('rpDot').className = 'rp-dot';

  const isView = VIEW_TYPES.includes(EV[i].type);

  if (isView) {
    document.getElementById('rpTimer').classList.remove('show');
    document.getElementById('rpDoneRow').classList.remove('show');
    document.getElementById('rpLecture').classList.add('show');
  } else {
    document.getElementById('rpLecture').classList.remove('show');
    document.getElementById('rpTimer').classList.add('show');
    document.getElementById('rpDoneRow').classList.add('show');
    if (!tmr || !tmr.on) {
      document.getElementById('rpDisp').textContent = fmt(FOCUS);
      document.getElementById('rpDisp').className = 'rp-display';
      document.getElementById('rpMode').textContent = 'Focus';
      document.getElementById('rpBar').style.width = '100%';
      document.getElementById('rpBar').className = 'rp-bar-fill';
      document.getElementById('rpStart').textContent = 'Start';
      document.getElementById('rpStart').className = 'rp-btn';
    }
  }
}

function go() {
  if (act === null) return;
  const btn = document.getElementById('rpStart');
  const dsp = document.getElementById('rpDisp');
  if (tmr && tmr.on) {
    clearInterval(tmr.iv); tmr.on = false;
    btn.textContent = 'Resume'; btn.className = 'rp-btn';
    dsp.className = 'rp-display'; return;
  }
  if (!tmr) tmr = {sec:FOCUS, tot:FOCUS, brk:false, on:false};
  tmr.on = true;
  btn.textContent = 'Pause';
  btn.className = tmr.brk ? 'rp-btn brk' : 'rp-btn go';
  dsp.className = tmr.brk ? 'rp-display on-break' : 'rp-display running';
  document.getElementById('rpDot').className = tmr.brk ? 'rp-dot done' : 'rp-dot running';
  document.getElementById('c'+act).classList.add('in-progress');
  document.getElementById('s'+act).textContent = fmt(tmr.sec);
  document.getElementById('s'+act).className = 'c-status is-running';

  tmr.iv = setInterval(() => {
    tmr.sec--;
    dsp.textContent = fmt(tmr.sec);
    document.title = fmt(tmr.sec) + ' \u2014 Focus Pilot';
    document.getElementById('rpBar').style.width = (tmr.sec/tmr.tot*100)+'%';
    if (!tmr.brk) {
      document.getElementById('s'+act).textContent = fmt(tmr.sec);
      focusSec++;
      const fh = Math.floor(focusSec/3600);
      const fm = Math.floor((focusSec%3600)/60);
      document.getElementById('focusH').textContent = fh+'h '+fm+'m';
    }
    if (tmr.sec <= 0) {
      clearInterval(tmr.iv); tmr.on = false;
      if (!tmr.brk) {
        pomos++; S[act].p++; upd(); fin(act);
        new Notification('Done!',{body:EV[act].title+' \u2014 take a break'});
        tmr = {sec:BRK, tot:BRK, brk:true, on:false};
        dsp.textContent = fmt(BRK); dsp.className = 'rp-display on-break';
        document.getElementById('rpMode').textContent = 'Break';
        document.getElementById('rpBar').style.width = '100%';
        document.getElementById('rpBar').className = 'rp-bar-fill on-break';
        document.getElementById('rpDot').className = 'rp-dot done';
        btn.textContent = 'Start break'; btn.className = 'rp-btn';
      } else {
        new Notification('Break over!',{body:'Pick next task'});
        tmr = null;
        document.getElementById('c'+act).classList.remove('selected','in-progress');
        act = null; document.title = 'Focus Pilot';
        document.getElementById('rpTime').textContent = '';
        document.getElementById('rpTitle').textContent = '';
        document.getElementById('rpType').textContent = '';
        document.getElementById('rpIdle').style.display = 'block';
        document.getElementById('rpTimer').classList.remove('show');
        document.getElementById('rpTip').classList.remove('show');
        document.getElementById('rpNotes').classList.remove('show');
        document.getElementById('rpDoneRow').classList.remove('show');
        document.getElementById('rpLecture').classList.remove('show');
        document.getElementById('rpDot').className = 'rp-dot';
      }
    }
  }, 1000);
}

function fin(i) {
  S[i].done = true;
  const c = document.getElementById('c'+i);
  c.classList.remove('selected','in-progress');
  c.classList.add('done');
  document.getElementById('s'+i).textContent = '\u2713 ' + S[i].p + ' pomo';
  document.getElementById('s'+i).className = 'c-status is-done';
  upd();
}

function rst() {
  if (tmr && tmr.iv) clearInterval(tmr.iv);
  tmr = null;
  document.getElementById('rpDisp').textContent = fmt(FOCUS);
  document.getElementById('rpDisp').className = 'rp-display';
  document.getElementById('rpMode').textContent = 'Focus';
  document.getElementById('rpBar').style.width = '100%';
  document.getElementById('rpBar').className = 'rp-bar-fill';
  document.getElementById('rpStart').textContent = 'Start';
  document.getElementById('rpStart').className = 'rp-btn';
  document.getElementById('rpDot').className = 'rp-dot';
  document.title = 'Focus Pilot';
  if (act !== null && !S[act].done) {
    document.getElementById('c'+act).classList.remove('in-progress');
    document.getElementById('s'+act).textContent = 'ready';
    document.getElementById('s'+act).className = 'c-status';
  }
}

function saveNote() {
  if (act === null) return;
  notes[act] = document.getElementById('rpNotesText').value;
  localStorage.setItem('fp-notes', JSON.stringify(notes));
}

function markDone() {
  if (act === null || S[act].done) return;
  if (tmr && tmr.on) { clearInterval(tmr.iv); tmr.on = false; }
  tmr = null; fin(act);
  document.getElementById('c'+act).classList.remove('selected','in-progress');
  document.getElementById('rpDisp').textContent = fmt(FOCUS);
  document.getElementById('rpDisp').className = 'rp-display';
  document.getElementById('rpMode').textContent = 'Done';
  document.getElementById('rpBar').style.width = '0%';
  document.getElementById('rpStart').textContent = 'Start';
  document.getElementById('rpStart').className = 'rp-btn';
  document.getElementById('rpDot').className = 'rp-dot done';
  document.getElementById('rpDoneRow').classList.remove('show');
  document.title = 'Focus Pilot';
}

if ('Notification' in window) Notification.requestPermission();
</script>
</body>
</html>
HTMLEOF2
