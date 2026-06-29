// Pixel-styled 3D brain quiz — self-contained vanilla port of the React BrainQuizView.
// It mounts itself into a #brain-quiz-host div whenever the pixel app renders one, and
// tears down when that div leaves the DOM. No coupling to the Datacosmos React runtime:
// this module owns the Three.js viewer, question generation, scoring, and its own panel UI.
//
// Loaded as an ES module (see the importmap in index.html). Meshes are same-origin OBJ
// files under /cog-neuro/brain-meshes (Desikan-Killiany atlas, brainder.org CC BY-SA 3.0).
import * as THREE from "three";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { BRAIN_REGIONS, getAllMeshFiles, buildMeshToRegionMap } from "./brain-regions.mjs";

const MESH_BASE = "/cog-neuro/brain-meshes";
const QUESTION_COUNT = 10;
const UNASSIGNED = new THREE.Color(0.88, 0.87, 0.85);

window.BRAIN_REGIONS = BRAIN_REGIONS; // expose for any pixel-side use

function shuffle(arr) {
  const out = [...arr];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}
function genQuestions(count) {
  const cand = BRAIN_REGIONS.filter((r) => r.meshFiles.length > 0);
  return shuffle(cand).slice(0, Math.min(count, cand.length)).map((correct) => {
    const wrong = shuffle(cand.filter((r) => r.id !== correct.id)).slice(0, 3);
    return { correct, options: shuffle([...wrong, correct]) };
  });
}

// tiny DOM helper
function el(tag, style, attrs) {
  const n = document.createElement(tag);
  if (style) n.setAttribute("style", style);
  if (attrs) for (const k in attrs) { if (k === "text") n.textContent = attrs[k]; else if (k === "html") n.innerHTML = attrs[k]; else n.setAttribute(k, attrs[k]); }
  return n;
}

// ---- Three.js viewer (vanilla port of BrainQuizView's useEffect) ----
function createViewer(container, onProgress, onReady) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x141414);
  let width = container.clientWidth || 600;
  let height = container.clientHeight || 520;
  const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
  camera.position.set(0, 20, 250);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 0.7));
  const dir = new THREE.DirectionalLight(0xffffff, 0.8); dir.position.set(50, 80, 100); scene.add(dir);
  const back = new THREE.DirectionalLight(0xffffff, 0.3); back.position.set(-50, -30, -80); scene.add(back);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.dampingFactor = 0.08;
  controls.target.set(0, 20, 0); controls.minDistance = 80; controls.maxDistance = 500;

  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();
  const meshToRegion = buildMeshToRegionMap();
  const meshByFile = new Map();
  const regionMaterials = new Map();
  const meshObjects = [];
  const meshToRegionId = new Map();
  const allFiles = getAllMeshFiles();
  const loader = new OBJLoader();
  let loaded = 0;
  const api = { onRegionClick: null };

  Promise.all(allFiles.map(async (file) => {
    try {
      const obj = await loader.loadAsync(`${MESH_BASE}/${file}`);
      const regionId = meshToRegion.get(file);
      const region = regionId ? BRAIN_REGIONS.find((r) => r.id === regionId) : null;
      obj.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          const color = region
            ? new THREE.Color(region.color[0] / 255, region.color[1] / 255, region.color[2] / 255)
            : UNASSIGNED;
          child.material = new THREE.MeshStandardMaterial({
            color, transparent: true, opacity: region ? 0.85 : 0.55,
            emissive: color, emissiveIntensity: region ? 0.05 : 0, side: THREE.DoubleSide,
          });
          if (region) {
            const list = regionMaterials.get(region.id) || [];
            list.push(child.material); regionMaterials.set(region.id, list);
            meshToRegionId.set(child, region.id);
          }
          meshObjects.push(child);
        }
      });
      meshByFile.set(file, obj);
      scene.add(obj);
    } catch (e) { /* some atlas files may be absent locally — skip */ }
    loaded++;
    onProgress(Math.round((loaded / allFiles.length) * 100));
  })).then(() => onReady());

  scene.position.copy(new THREE.Vector3(0, 20, 0).multiplyScalar(-1)); // approx FreeSurfer offset

  const onClick = (e) => {
    const r = renderer.domElement.getBoundingClientRect();
    mouse.x = ((e.clientX - r.left) / r.width) * 2 - 1;
    mouse.y = -((e.clientY - r.top) / r.height) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    for (const h of raycaster.intersectObjects(meshObjects, false)) {
      const rid = meshToRegionId.get(h.object);
      if (rid && api.onRegionClick) { api.onRegionClick(rid); return; }
    }
  };
  renderer.domElement.addEventListener("click", onClick);

  let frame = 0;
  const animate = () => { controls.update(); renderer.render(scene, camera); frame = requestAnimationFrame(animate); };
  animate();

  const ro = new ResizeObserver(() => {
    width = container.clientWidth; height = container.clientHeight;
    if (!width || !height) return;
    camera.aspect = width / height; camera.updateProjectionMatrix(); renderer.setSize(width, height);
  });
  ro.observe(container);

  // dim/dimU default to the quiz's "hunt for it" levels; the explore mini-viewer passes higher values to keep context
  api.highlightRegion = (region, dim = 0.12, dimU = 0.05) => {
    for (const r of BRAIN_REGIONS) {
      const mats = regionMaterials.get(r.id); if (!mats) continue;
      const on = r.id === region.id;
      for (const m of mats) { m.opacity = on ? 1.0 : dim; m.emissiveIntensity = on ? 0.6 : 0; }
    }
    for (const [file, obj] of meshByFile) {
      if (meshToRegion.get(file)) continue;
      obj.traverse((c) => { if (c instanceof THREE.Mesh) c.material.opacity = dimU; });
    }
  };
  api.reset = () => {
    for (const r of BRAIN_REGIONS) {
      const mats = regionMaterials.get(r.id); if (!mats) continue;
      for (const m of mats) { m.opacity = 0.85; m.emissiveIntensity = 0.05; }
    }
    for (const [file, obj] of meshByFile) {
      if (meshToRegion.get(file)) continue;
      obj.traverse((c) => { if (c instanceof THREE.Mesh) c.material.opacity = 0.55; });
    }
  };
  api.flyToRegion = (region) => {
    const d = 250, az = (region.camera.azimuth * Math.PI) / 180, el2 = (region.camera.elevation * Math.PI) / 180;
    camera.position.set(d * Math.sin(az) * Math.cos(el2), 20 + d * Math.sin(el2), d * Math.cos(az) * Math.cos(el2));
  };
  api.dispose = () => {
    cancelAnimationFrame(frame); ro.disconnect();
    renderer.domElement.removeEventListener("click", onClick);
    controls.dispose(); renderer.dispose();
    if (renderer.domElement.parentElement === container) container.removeChild(renderer.domElement);
  };
  return api;
}

// ---- the quiz UI (pixel-styled vanilla DOM) ----
const PSS = "'Press Start 2P',monospace";
const BTN = `font-family:${PSS};font-size:9px;letter-spacing:1px;padding:11px 14px;border:2px solid var(--ink);background:transparent;color:var(--ink);cursor:pointer;text-align:left;width:100%;`;
const PRIMARY = `font-family:${PSS};font-size:9px;letter-spacing:1px;padding:13px 16px;border:2px solid var(--ink);background:var(--fill);color:var(--onFill);cursor:pointer;width:100%;`;

function mountQuiz(host) {
  host.innerHTML = "";
  const wrap = el("div", "padding:34px 40px 120px;max-width:1040px;");
  host.appendChild(wrap);
  wrap.appendChild(el("div", "font-size:10px;letter-spacing:2px;color:var(--mute);text-transform:uppercase;", { text: "Cognitive Neuroscience · Brain Quiz" }));
  wrap.appendChild(el("h1", `margin:13px 0 4px;font-family:${PSS};font-size:18px;line-height:1.6;`, { text: "3D ANATOMY PRACTICE" }));
  wrap.appendChild(el("div", "font-size:10px;color:var(--mute);letter-spacing:.5px;margin-bottom:26px;", { text: "Three.js · Desikan-Killiany atlas (brainder.org, CC BY-SA 3.0) · drag to rotate, scroll to zoom" }));

  const row = el("div", "display:flex;gap:26px;align-items:stretch;flex-wrap:wrap;");
  wrap.appendChild(row);

  const canvasWrap = el("div", "flex:1 1 460px;min-width:300px;height:560px;position:relative;border:2px solid var(--ink);box-shadow:6px 6px 0 var(--line);background:#141414;overflow:hidden;");
  const loadingEl = el("div", `position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#e8e6e2;font-family:${PSS};font-size:10px;letter-spacing:1px;pointer-events:none;`, { text: "LOADING MESHES… 0%" });
  canvasWrap.appendChild(loadingEl);
  row.appendChild(canvasWrap);

  const panel = el("div", "flex:0 0 300px;max-width:340px;display:flex;flex-direction:column;gap:16px;");
  row.appendChild(panel);

  // ---- state ----
  let phase = "setup", mode = "identify", questions = [], index = 0, score = 0, answered = false, picked = null, ready = false;
  let viewer = null;

  const setProgress = (p) => { loadingEl.textContent = "LOADING MESHES… " + p + "%"; };
  const setReady = () => { ready = true; loadingEl.style.display = "none"; render(); };
  viewer = createViewer(canvasWrap, setProgress, setReady);
  viewer.onRegionClick = (rid) => {
    if (mode !== "locate" || phase !== "playing" || answered) return;
    const cur = questions[index];
    answered = true; picked = rid;
    if (rid === cur.correct.id) score++;
    viewer.highlightRegion(cur.correct); viewer.flyToRegion(cur.correct);
    render();
  };

  // ---- per-phase render of the side panel ----
  function card(children) {
    const c = el("div", "border:2px solid var(--ink);padding:16px;display:flex;flex-direction:column;gap:12px;background:var(--bg);");
    children.forEach((ch) => c.appendChild(ch));
    return c;
  }
  function modeRow() {
    const r = el("div", "display:flex;gap:8px;");
    ["identify", "locate"].forEach((m) => {
      const active = mode === m;
      const b = el("button", `${BTN}flex:1;text-align:center;${active ? "background:var(--fill);color:var(--onFill);" : ""}${phase !== "setup" ? "opacity:.45;cursor:default;" : ""}`, { text: m.toUpperCase() });
      if (phase === "setup") b.onclick = () => { mode = m; render(); };
      r.appendChild(b);
    });
    return r;
  }

  function render() {
    panel.innerHTML = "";
    // mode card (always)
    const hint = el("div", "font-size:11px;color:var(--mute);line-height:1.6;", {
      text: mode === "identify" ? "We highlight a region — you pick its name from 4 options." : "We name a region — you click it on the 3D brain.",
    });
    panel.appendChild(card([modeRow(), hint]));

    if (phase === "setup") {
      const msg = el("div", "font-size:12px;line-height:1.6;", { text: QUESTION_COUNT + " questions, randomised. Pick a mode, then start once the brain has loaded." });
      const start = el("button", `${PRIMARY}${ready ? "" : "opacity:.45;cursor:default;"}`, { text: ready ? "START" : "LOADING…" });
      if (ready) start.onclick = () => {
        questions = genQuestions(QUESTION_COUNT); index = 0; score = 0; answered = false; picked = null; phase = "playing";
        applyQuestion(); render();
      };
      panel.appendChild(card([msg, start]));
    } else if (phase === "playing") {
      const cur = questions[index];
      const badge = el("div", `font-family:${PSS};font-size:8px;letter-spacing:1px;border:1.5px solid var(--ink);padding:5px 8px;align-self:flex-start;`, { text: (index + 1) + " / " + questions.length + " · SCORE " + score });
      const q = el("div", "font-size:13px;font-weight:700;line-height:1.5;", { text: mode === "identify" ? "Which region is highlighted?" : ("Click on: " + cur.correct.name) });
      const kids = [badge, q];

      if (mode === "identify") {
        const opts = el("div", "display:flex;flex-direction:column;gap:8px;");
        cur.options.forEach((opt) => {
          let s = BTN;
          if (answered) {
            if (opt.id === cur.correct.id) s += "border-color:var(--good);color:var(--good);";
            else if (opt.id === picked) s += "border-color:var(--bad);color:var(--bad);";
          } else if (opt.id === picked) s += "background:var(--sel);";
          const b = el("button", s, { text: opt.name });
          if (!answered) b.onclick = () => {
            answered = true; picked = opt.id;
            if (opt.id === cur.correct.id) score++;
            render();
          };
          opts.appendChild(b);
        });
        kids.push(opts);
      }

      if (answered) {
        kids.push(el("div", "font-size:12px;font-weight:700;" + (picked === cur.correct.id ? "color:var(--good);" : "color:var(--bad);"), { text: picked === cur.correct.id ? "✓ CORRECT" : ("✗ CORRECT: " + cur.correct.name) }));
        if (cur.correct.description) kids.push(el("div", "font-size:11px;color:var(--mute);line-height:1.6;", { text: cur.correct.description }));
        const next = el("button", PRIMARY, { text: index + 1 >= questions.length ? "FINISH" : "NEXT" });
        next.onclick = () => {
          if (index + 1 >= questions.length) { phase = "result"; viewer.reset(); render(); return; }
          index++; answered = false; picked = null; applyQuestion(); render();
        };
        kids.push(next);
      }
      panel.appendChild(card(kids));
    } else if (phase === "result") {
      const big = el("div", `font-family:${PSS};font-size:26px;text-align:center;`, { text: score + "/" + questions.length });
      const again = el("button", PRIMARY, { text: "TRY AGAIN" });
      again.onclick = () => { phase = "setup"; render(); };
      panel.appendChild(card([big, again]));
    }
  }

  // identify: highlight + fly to the target; locate: clear so the user must find it
  function applyQuestion() {
    if (phase !== "playing" || !viewer) return;
    const cur = questions[index];
    if (mode === "identify") { viewer.highlightRegion(cur.correct); viewer.flyToRegion(cur.correct); }
    else viewer.reset();
  }

  render();

  return function teardown() { try { viewer && viewer.dispose(); } catch (e) {} host.innerHTML = ""; };
}

// ---- lifecycle: watch for the host the pixel app renders ----
let active = null; // { host, teardown }
function sync() {
  const host = document.getElementById("brain-quiz-host");
  if (host && (!active || active.host !== host)) {
    if (active) active.teardown();
    active = { host, teardown: mountQuiz(host) };
  } else if (!host && active) {
    active.teardown(); active = null;
  }
}
const mo = new MutationObserver(sync);
mo.observe(document.body, { childList: true, subtree: true });
sync();

// ---- corner mini-viewer for brain-link words inside notes ----
// Clicking a region word (baked into note HTML as <button class="brain-link" data-region=...>)
// pops a small interactive 3D brain in the top-right with that region highlighted.
let mini = null; // lazily built on first click; reused after that
function ensureMini() {
  if (mini) return mini;
  const wrap = el("div", `position:fixed;top:74px;right:18px;z-index:120;width:330px;background:var(--bg);border:2px solid var(--ink);box-shadow:7px 7px 0 var(--line);display:flex;flex-direction:column;font-family:'JetBrains Mono',monospace;`);
  const head = el("div", "display:flex;align-items:center;gap:8px;padding:9px 8px 9px 12px;border-bottom:2px solid var(--ink);");
  const title = el("div", `font-family:${PSS};font-size:8px;letter-spacing:1px;flex:1;line-height:1.5;`, { text: "BRAIN" });
  const close = el("button", `font-family:${PSS};font-size:9px;border:2px solid var(--ink);background:transparent;color:var(--ink);cursor:pointer;padding:4px 8px;`, { text: "✕" });
  close.onclick = () => { wrap.style.display = "none"; };
  head.appendChild(title); head.appendChild(close);
  const canvas = el("div", "height:270px;position:relative;background:#141414;cursor:grab;");
  const loading = el("div", `position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#e8e6e2;font-family:${PSS};font-size:9px;letter-spacing:1px;pointer-events:none;`, { text: "LOADING…" });
  canvas.appendChild(loading);
  const desc = el("div", "font-size:11px;color:var(--mute);line-height:1.55;padding:10px 12px;border-top:1px dashed var(--line);max-height:120px;overflow:auto;", { text: "" });
  wrap.appendChild(head); wrap.appendChild(canvas); wrap.appendChild(desc);
  document.body.appendChild(wrap);
  mini = { wrap, title, desc, loading, ready: false, pending: null, viewer: null };
  mini.viewer = createViewer(canvas, () => {}, () => { mini.ready = true; loading.style.display = "none"; if (mini.pending) { show(mini.pending); mini.pending = null; } });
  return mini;
}
function show(region) {
  mini.title.textContent = region.name.toUpperCase();
  mini.desc.textContent = region.description || "";
  if (mini.ready) { mini.viewer.highlightRegion(region, 0.34, 0.14); mini.viewer.flyToRegion(region); }
  else mini.pending = region;
}
function openMiniBrain(regionId) {
  const region = BRAIN_REGIONS.find((r) => r.id === regionId);
  if (!region) return;
  const m = ensureMini();
  m.wrap.style.display = "flex";
  show(region);
}
document.addEventListener("click", (e) => {
  const btn = e.target.closest && e.target.closest(".brain-link");
  if (btn && btn.dataset.region) { e.preventDefault(); openMiniBrain(btn.dataset.region); }
});
