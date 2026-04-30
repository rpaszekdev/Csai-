// brain-link.js — wraps brain-region mentions in <button class="brain-link">
// and opens a mini 3D viewer in the upper-right corner on click. Text
// scanning runs immediately on load with no dependencies. Three.js is
// dynamically imported only when the user actually clicks a region — so
// CDN failures don't break the inline links.

const MESH_BASE = "/cog-neuro/brain-meshes";
const THREE_VERSION = "0.161.0";
const THREE_CDN = `https://unpkg.com/three@${THREE_VERSION}/build/three.module.js`;
const OBJLOADER_CDN = `https://unpkg.com/three@${THREE_VERSION}/examples/jsm/loaders/OBJLoader.js`;

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
  if (!article) {
    console.warn("[brain-link] no <article id=content> on this page");
    return;
  }
  const regex = buildAliasRegex();
  if (!regex) {
    console.warn("[brain-link] no aliases — region data not loaded");
    return;
  }

  const SKIP = new Set(["CODE", "PRE", "BUTTON", "A", "SCRIPT", "STYLE"]);
  const walker = document.createTreeWalker(
    article,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode(node) {
        if (!node.nodeValue || !node.nodeValue.trim()) {
          return NodeFilter.FILTER_REJECT;
        }
        let p = node.parentElement;
        while (p && p !== article) {
          if (SKIP.has(p.tagName)) return NodeFilter.FILTER_REJECT;
          if (p.classList && p.classList.contains("brain-link")) {
            return NodeFilter.FILTER_REJECT;
          }
          p = p.parentElement;
        }
        return NodeFilter.FILTER_ACCEPT;
      },
    },
  );

  const textNodes = [];
  let n;
  while ((n = walker.nextNode())) textNodes.push(n);

  let wrapped = 0;
  for (const node of textNodes) {
    const before = node.parentNode.querySelectorAll(".brain-link").length;
    wrapMatchesInTextNode(node, regex);
    const after = (node.parentNode || article).querySelectorAll(".brain-link")
      .length;
    if (after > before) wrapped += after - before;
  }
  console.info(
    `[brain-link] scanned ${textNodes.length} text nodes, wrapped ${wrapped} matches`,
  );
}

// ── Three.js (lazy) ───────────────────────────────────────────────────────
let threePromise = null;
function loadThree() {
  if (threePromise) return threePromise;
  threePromise = Promise.all([import(THREE_CDN), import(OBJLOADER_CDN)])
    .then(([three, objLoader]) => ({
      THREE: three,
      OBJLoader: objLoader.OBJLoader,
    }))
    .catch((err) => {
      console.error("[brain-link] failed to load Three.js:", err);
      threePromise = null;
      throw err;
    });
  return threePromise;
}

// ── Mini 3D viewer ────────────────────────────────────────────────────────
let viewer = null;

function ensurePanel() {
  let root = document.querySelector(".brain-mini");
  if (root) return root;
  root = document.createElement("aside");
  root.className = "brain-mini";
  root.setAttribute("aria-label", "Brain region 3D preview");
  root.innerHTML = `
    <header class="brain-mini-head">
      <span class="brain-mini-title">Brain region</span>
      <button type="button" class="brain-mini-close" aria-label="Close">×</button>
    </header>
    <div class="brain-mini-canvas"></div>
    <p class="brain-mini-desc">—</p>
  `;
  document.body.appendChild(root);
  root.querySelector(".brain-mini-close").addEventListener("click", () => {
    root.classList.remove("open");
  });
  return root;
}

async function ensureViewer() {
  if (viewer) return viewer;
  const { THREE, OBJLoader } = await loadThree();
  const root = ensurePanel();
  const canvasHost = root.querySelector(".brain-mini-canvas");

  const scene = new THREE.Scene();
  scene.background = null;
  const w = canvasHost.clientWidth || 320;
  const h = canvasHost.clientHeight || 220;
  const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
  camera.position.set(0, 0, 280);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setClearColor(0x000000, 0);
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  canvasHost.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 0.7));
  const dir = new THREE.DirectionalLight(0xffffff, 0.9);
  dir.position.set(60, 80, 100);
  scene.add(dir);

  const group = new THREE.Group();
  scene.add(group);

  const animate = () => {
    group.rotation.y += 0.005;
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
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

  viewer = {
    THREE, OBJLoader, root, scene, group, camera, renderer, resize,
  };
  return viewer;
}

async function showRegion(region) {
  const root = ensurePanel();
  root.classList.add("open");
  root.querySelector(".brain-mini-title").textContent = region.name;
  root.querySelector(".brain-mini-desc").textContent =
    region.description || "Loading…";

  let v;
  try {
    v = await ensureViewer();
  } catch {
    root.querySelector(".brain-mini-desc").textContent =
      "Could not load 3D viewer (Three.js failed to download).";
    return;
  }
  const { THREE, OBJLoader, group } = v;

  // Reset.
  while (group.children.length > 0) {
    const obj = group.children[0];
    group.remove(obj);
    obj.traverse?.((c) => {
      if (c.isMesh) {
        c.geometry?.dispose();
        c.material?.dispose();
      }
    });
  }
  root.querySelector(".brain-mini-desc").textContent = region.description || "";

  if (!region.meshFiles || region.meshFiles.length === 0) {
    root.querySelector(".brain-mini-desc").textContent =
      "No 3D mesh available for this region.";
    return;
  }

  const loader = new OBJLoader();
  const color = region.color
    ? new THREE.Color(
        `rgb(${region.color[0]}, ${region.color[1]}, ${region.color[2]})`,
      )
    : new THREE.Color(0xff6b2b);

  await Promise.all(
    region.meshFiles.map(async (file) => {
      try {
        const obj = await loader.loadAsync(`${MESH_BASE}/${file}`);
        obj.traverse((child) => {
          if (child.isMesh) {
            child.material = new THREE.MeshStandardMaterial({
              color,
              roughness: 0.5,
              metalness: 0.0,
              emissive: color,
              emissiveIntensity: 0.18,
              side: THREE.DoubleSide,
            });
          }
        });
        group.add(obj);
      } catch {
        /* missing mesh — skip silently */
      }
    }),
  );

  const box = new THREE.Box3().setFromObject(group);
  if (!box.isEmpty()) {
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    group.position.sub(center);
    const dist = maxDim / (2 * Math.tan((v.camera.fov * Math.PI) / 360));
    v.camera.position.set(0, 0, dist * 1.7);
    v.camera.lookAt(0, 0, 0);
  }
  v.resize();
}

// ── Init: scan article ASAP, independent of Three.js ──────────────────────
function init() {
  loadRegions().then(scanArticle);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
