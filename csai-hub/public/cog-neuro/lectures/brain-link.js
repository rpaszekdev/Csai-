// brain-link.js — wraps brain-region mentions in <button class="brain-link">
// and opens a mini 3D viewer in the upper-right corner showing the full
// brain with the selected region highlighted. The viewer is fully
// interactive — drag to rotate, scroll to zoom, right-drag to pan.

const MESH_BASE = "/cog-neuro/brain-meshes";
const THREE_URL = "/cog-neuro/lectures/vendor/three.module.js";
const OBJLOADER_URL = "/cog-neuro/lectures/vendor/OBJLoader.js";
const ORBITCONTROLS_URL = "/cog-neuro/lectures/vendor/OrbitControls.js";

// Whole-brain mesh list. Drawn dimmed by default; the selected region
// gets pulled forward and recolored.
const CORTICAL_REGIONS = [
  "bankssts", "caudalanteriorcingulate", "caudalmiddlefrontal", "cuneus",
  "entorhinal", "frontalpole", "fusiform", "inferiorparietal",
  "inferiortemporal", "insula", "isthmuscingulate", "lateraloccipital",
  "lateralorbitofrontal", "lingual", "medialorbitofrontal", "middletemporal",
  "paracentral", "parahippocampal", "parsopercularis", "parsorbitalis",
  "parstriangularis", "pericalcarine", "postcentral", "posteriorcingulate",
  "precentral", "precuneus", "rostralanteriorcingulate", "rostralmiddlefrontal",
  "superiorfrontal", "superiorparietal", "superiortemporal", "supramarginal",
  "temporalpole", "transversetemporal",
];
const SUBCORTICAL = [
  "Brain-Stem", "Left-Hippocampus", "Right-Hippocampus",
  "Left-Amygdala", "Right-Amygdala",
  "Left-Thalamus-Proper", "Right-Thalamus-Proper",
  "Left-Caudate", "Right-Caudate",
  "Left-Putamen", "Right-Putamen",
  "Left-Pallidum", "Right-Pallidum",
  "Left-Accumbens-area", "Right-Accumbens-area",
  "Left-Cerebellum-Cortex", "Right-Cerebellum-Cortex",
  "CC_Posterior", "CC_Mid_Posterior", "CC_Central",
  "CC_Mid_Anterior", "CC_Anterior",
];

function allMeshFiles() {
  const files = [];
  for (const r of CORTICAL_REGIONS) {
    files.push(`cortical/lh.pial.DK.${r}.obj`);
    files.push(`cortical/rh.pial.DK.${r}.obj`);
  }
  for (const s of SUBCORTICAL) files.push(`subcortical/${s}.obj`);
  return files;
}

// ── Region data ───────────────────────────────────────────────────────────
let REGIONS = [];
const aliasMap = new Map();

async function loadRegions() {
  try {
    const res = await fetch("./brain-regions.json");
    if (!res.ok) throw new Error("HTTP " + res.status);
    REGIONS = await res.json();
    for (const r of REGIONS) {
      for (const a of r.aliases) aliasMap.set(a.toLowerCase(), r);
    }
  } catch (err) {
    console.warn("[brain-link] could not load brain-regions.json:", err);
  }
}

function buildAliasRegex() {
  const aliases = Array.from(aliasMap.keys())
    .sort((a, b) => b.length - a.length)
    .map((a) => a.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  if (aliases.length === 0) return null;
  return new RegExp("\\b(" + aliases.join("|") + ")\\b", "gi");
}

function wrapMatchesInTextNode(node, regex) {
  const text = node.nodeValue;
  if (!text) return;
  regex.lastIndex = 0;
  const matches = [];
  let m;
  while ((m = regex.exec(text)) !== null) {
    matches.push({ index: m.index, length: m[0].length, raw: m[0] });
  }
  if (matches.length === 0) return;

  const frag = document.createDocumentFragment();
  let cursor = 0;
  for (const match of matches) {
    if (match.index > cursor) {
      frag.appendChild(document.createTextNode(text.slice(cursor, match.index)));
    }
    const region = aliasMap.get(match.raw.toLowerCase());
    if (region) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "brain-link";
      btn.textContent = match.raw;
      btn.dataset.regionId = region.id;
      btn.title = `View ${region.name} in 3D`;
      btn.addEventListener("click", () => showRegion(region));
      frag.appendChild(btn);
    } else {
      frag.appendChild(document.createTextNode(match.raw));
    }
    cursor = match.index + match.length;
  }
  if (cursor < text.length) {
    frag.appendChild(document.createTextNode(text.slice(cursor)));
  }
  node.parentNode.replaceChild(frag, node);
}

function scanArticle() {
  const article = document.querySelector("article#content");
  if (!article) return;
  const regex = buildAliasRegex();
  if (!regex) return;

  const SKIP = new Set(["CODE", "PRE", "BUTTON", "A", "SCRIPT", "STYLE"]);
  const walker = document.createTreeWalker(article, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
      let p = node.parentElement;
      while (p && p !== article) {
        if (SKIP.has(p.tagName)) return NodeFilter.FILTER_REJECT;
        if (p.classList && p.classList.contains("brain-link")) return NodeFilter.FILTER_REJECT;
        p = p.parentElement;
      }
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const textNodes = [];
  let n;
  while ((n = walker.nextNode())) textNodes.push(n);
  for (const node of textNodes) wrapMatchesInTextNode(node, regex);
  console.info(`[brain-link] scanned ${textNodes.length} text nodes`);
}

// ── Three.js (lazy) ───────────────────────────────────────────────────────
let threePromise = null;
function loadThree() {
  if (threePromise) return threePromise;
  threePromise = Promise.all([
    import(THREE_URL),
    import(OBJLOADER_URL),
    import(ORBITCONTROLS_URL),
  ])
    .then(([three, loader, controls]) => ({
      THREE: three,
      OBJLoader: loader.OBJLoader,
      OrbitControls: controls.OrbitControls,
    }))
    .catch((err) => {
      console.error("[brain-link] failed to load Three.js:", err);
      threePromise = null;
      throw err;
    });
  return threePromise;
}

// ── Viewer ────────────────────────────────────────────────────────────────
let viewer = null;

function ensurePanel() {
  let root = document.querySelector(".brain-mini");
  if (root) return root;
  root = document.createElement("aside");
  root.className = "brain-mini";
  root.innerHTML = `
    <header class="brain-mini-head">
      <span class="brain-mini-title">Brain region</span>
      <button type="button" class="brain-mini-close" aria-label="Close">×</button>
    </header>
    <div class="brain-mini-canvas"></div>
    <p class="brain-mini-desc">—</p>
    <p class="brain-mini-hint">Drag to rotate · scroll to zoom · right-drag to pan</p>
  `;
  document.body.appendChild(root);
  root.querySelector(".brain-mini-close").addEventListener("click", () => {
    root.classList.remove("open");
  });
  return root;
}

async function ensureViewer() {
  if (viewer) return viewer;
  const { THREE, OBJLoader, OrbitControls } = await loadThree();
  const root = ensurePanel();
  const canvasHost = root.querySelector(".brain-mini-canvas");

  const scene = new THREE.Scene();
  scene.background = null;
  const w = canvasHost.clientWidth || 360;
  const h = canvasHost.clientHeight || 280;
  const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 2000);
  camera.position.set(0, 30, 320);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setClearColor(0x000000, 0);
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  canvasHost.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const dir = new THREE.DirectionalLight(0xffffff, 1.0);
  dir.position.set(60, 80, 100);
  scene.add(dir);
  const dir2 = new THREE.DirectionalLight(0xffffff, 0.3);
  dir2.position.set(-60, -40, -80);
  scene.add(dir2);

  const group = new THREE.Group();
  scene.add(group);

  // OrbitControls — drag rotate, scroll zoom, right-drag pan.
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.rotateSpeed = 0.7;
  controls.zoomSpeed = 0.7;
  controls.minDistance = 40;
  controls.maxDistance = 800;

  // Track which meshes belong to which mesh-file path so we can
  // selectively re-color the active region without rebuilding the scene.
  const meshIndex = new Map(); // file → THREE.Mesh[]

  function makeMaterial(THREE, baseColor, opacity, emissive, emissiveIntensity) {
    return new THREE.MeshStandardMaterial({
      color: baseColor,
      roughness: 0.7,
      metalness: 0.0,
      transparent: opacity < 1,
      opacity,
      emissive,
      emissiveIntensity,
      side: THREE.DoubleSide,
      depthWrite: opacity > 0.5,
    });
  }

  // Load all meshes once. Done in parallel; total = 92 OBJs.
  const baseColor = new THREE.Color("#bcb6a4");
  const loader = new OBJLoader();
  const all = allMeshFiles();
  await Promise.all(
    all.map(async (file) => {
      try {
        const obj = await loader.loadAsync(`${MESH_BASE}/${file}`);
        const meshes = [];
        obj.traverse((child) => {
          if (child.isMesh) {
            child.material = makeMaterial(
              THREE,
              baseColor,
              0.18,
              new THREE.Color(0x000000),
              0.0,
            );
            child.userData.meshFile = file;
            meshes.push(child);
          }
        });
        meshIndex.set(file, meshes);
        group.add(obj);
      } catch {
        /* missing mesh — silently skip */
      }
    }),
  );

  // Center group on its own bounding box and back the camera off so the
  // whole brain fits inside the canvas.
  const box = new THREE.Box3().setFromObject(group);
  if (!box.isEmpty()) {
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    group.position.sub(center);
    const dist = maxDim / (2 * Math.tan((camera.fov * Math.PI) / 360));
    camera.position.set(0, size.y * 0.2, dist * 1.6);
    controls.target.set(0, 0, 0);
    controls.update();
  }

  let frame;
  const animate = () => {
    controls.update();
    renderer.render(scene, camera);
    frame = requestAnimationFrame(animate);
  };
  animate();

  const resize = () => {
    const w2 = canvasHost.clientWidth;
    const h2 = canvasHost.clientHeight;
    if (w2 <= 0 || h2 <= 0) return;
    camera.aspect = w2 / h2;
    camera.updateProjectionMatrix();
    renderer.setSize(w2, h2);
  };
  window.addEventListener("resize", resize);
  // Also handle panel resize via ResizeObserver.
  const ro = new ResizeObserver(resize);
  ro.observe(canvasHost);

  viewer = {
    THREE, root, scene, group, camera, renderer, controls,
    meshIndex, makeMaterial, resize,
  };
  return viewer;
}

function highlightRegion(v, region) {
  const { THREE, meshIndex, makeMaterial } = v;
  const baseColor = new THREE.Color("#bcb6a4");
  const dimMat = makeMaterial(THREE, baseColor, 0.13, new THREE.Color(0), 0);
  const highlightColor = region?.color
    ? new THREE.Color(
        `rgb(${region.color[0]}, ${region.color[1]}, ${region.color[2]})`,
      )
    : new THREE.Color("#a84f2a");
  const hiMat = makeMaterial(THREE, highlightColor, 1.0, highlightColor, 0.25);

  const activeFiles = new Set(region?.meshFiles || []);
  for (const [file, meshes] of meshIndex.entries()) {
    const isActive = activeFiles.has(file);
    for (const mesh of meshes) {
      mesh.material = isActive ? hiMat : dimMat;
      mesh.renderOrder = isActive ? 1 : 0;
    }
  }
}

async function showRegion(region) {
  const root = ensurePanel();
  root.classList.add("open");
  root.querySelector(".brain-mini-title").textContent = region.name;
  root.querySelector(".brain-mini-desc").textContent =
    region.description || "Loading 3D brain…";

  let v;
  try {
    v = await ensureViewer();
  } catch {
    root.querySelector(".brain-mini-desc").textContent =
      "Could not load 3D viewer.";
    return;
  }
  highlightRegion(v, region);
  root.querySelector(".brain-mini-desc").textContent = region.description || "";
}

// ── Init ──────────────────────────────────────────────────────────────────
function init() { loadRegions().then(scanArticle); }
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
