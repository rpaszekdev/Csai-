import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  BRAIN_REGIONS,
  getAllMeshFiles,
  buildMeshToRegionMap,
} from "../data/brain-regions";

const MESH_BASE = "/cog-neuro/brain-meshes";
const QUESTION_COUNT = 10;
const UNASSIGNED_COLOR = new THREE.Color(0.88, 0.87, 0.85);

function shuffle(arr) {
  const out = [...arr];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function generateQuestions(count) {
  const candidates = BRAIN_REGIONS.filter((r) => r.meshFiles.length > 0);
  const picked = shuffle(candidates).slice(0, Math.min(count, candidates.length));
  return picked.map((correct) => {
    const wrong = shuffle(candidates.filter((r) => r.id !== correct.id)).slice(0, 3);
    const options = shuffle([...wrong, correct]);
    return { correct, options };
  });
}

export default function BrainQuizView() {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const [phase, setPhase] = useState("setup"); // setup | playing | result
  const [mode, setMode] = useState("identify"); // identify | locate
  const [questions, setQuestions] = useState([]);
  const [index, setIndex] = useState(0);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(false);
  const [picked, setPicked] = useState(null);
  const [loadProgress, setLoadProgress] = useState(0);
  const [viewerReady, setViewerReady] = useState(false);

  const current = phase === "playing" ? questions[index] : null;

  // Three.js setup runs once
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a);
    const width = container.clientWidth;
    const height = container.clientHeight;
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.set(0, 20, 250);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(50, 80, 100);
    scene.add(dirLight);
    const back = new THREE.DirectionalLight(0xffffff, 0.3);
    back.position.set(-50, -30, -80);
    scene.add(back);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.target.set(0, 20, 0);
    controls.minDistance = 80;
    controls.maxDistance = 500;

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

    Promise.all(
      allFiles.map(async (file) => {
        try {
          const obj = await loader.loadAsync(`${MESH_BASE}/${file}`);
          const regionId = meshToRegion.get(file);
          const region = regionId ? BRAIN_REGIONS.find((r) => r.id === regionId) : null;

          obj.traverse((child) => {
            if (child instanceof THREE.Mesh) {
              const color = region
                ? new THREE.Color(region.color[0] / 255, region.color[1] / 255, region.color[2] / 255)
                : UNASSIGNED_COLOR;
              const mat = new THREE.MeshStandardMaterial({
                color,
                transparent: true,
                opacity: region ? 0.85 : 0.55,
                emissive: color,
                emissiveIntensity: region ? 0.05 : 0,
                side: THREE.DoubleSide,
              });
              child.material = mat;
              if (region) {
                const list = regionMaterials.get(region.id) || [];
                list.push(mat);
                regionMaterials.set(region.id, list);
                meshToRegionId.set(child, region.id);
              }
              meshObjects.push(child);
            }
          });

          meshByFile.set(file, obj);
          scene.add(obj);
        } catch (err) {
          // Skip missing meshes silently — some atlas files may not exist locally.
        }
        loaded++;
        setLoadProgress(Math.round((loaded / allFiles.length) * 100));
      }),
    ).then(() => setViewerReady(true));

    // Center the brain (approximate FreeSurfer offset)
    const centerOffset = new THREE.Vector3(0, 20, 0);
    scene.position.copy(centerOffset.clone().multiplyScalar(-1));

    const onClick = (event) => {
      const r = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - r.left) / r.width) * 2 - 1;
      mouse.y = -((event.clientY - r.top) / r.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(meshObjects, false);
      for (const h of hits) {
        const rid = meshToRegionId.get(h.object);
        if (rid && sceneRef.current?.onRegionClick) {
          sceneRef.current.onRegionClick(rid);
          return;
        }
      }
    };
    renderer.domElement.addEventListener("click", onClick);

    let frame = 0;
    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
      frame = requestAnimationFrame(animate);
    };
    animate();

    const handleResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    sceneRef.current = {
      highlightRegion: (region) => {
        for (const r of BRAIN_REGIONS) {
          const mats = regionMaterials.get(r.id);
          if (!mats) continue;
          const isTarget = r.id === region.id;
          for (const mat of mats) {
            mat.opacity = isTarget ? 1.0 : 0.12;
            mat.emissiveIntensity = isTarget ? 0.5 : 0;
          }
        }
        for (const [file, obj] of meshByFile) {
          if (meshToRegion.get(file)) continue;
          obj.traverse((c) => {
            if (c instanceof THREE.Mesh) c.material.opacity = 0.05;
          });
        }
      },
      reset: () => {
        for (const r of BRAIN_REGIONS) {
          const mats = regionMaterials.get(r.id);
          if (!mats) continue;
          for (const mat of mats) {
            mat.opacity = 0.85;
            mat.emissiveIntensity = 0.05;
          }
        }
        for (const [file, obj] of meshByFile) {
          if (meshToRegion.get(file)) continue;
          obj.traverse((c) => {
            if (c instanceof THREE.Mesh) c.material.opacity = 0.55;
          });
        }
      },
      flyToRegion: (region) => {
        const dist = 250;
        const az = (region.camera.azimuth * Math.PI) / 180;
        const el = (region.camera.elevation * Math.PI) / 180;
        camera.position.set(
          dist * Math.sin(az) * Math.cos(el),
          20 + dist * Math.sin(el),
          dist * Math.cos(az) * Math.cos(el),
        );
      },
      onRegionClick: null,
    };

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", handleResize);
      renderer.domElement.removeEventListener("click", onClick);
      controls.dispose();
      renderer.dispose();
      if (renderer.domElement.parentElement === container) {
        container.removeChild(renderer.domElement);
      }
      sceneRef.current = null;
    };
  }, []);

  // React to question changes
  useEffect(() => {
    if (phase !== "playing" || !current || !sceneRef.current) return;
    if (mode === "identify") {
      sceneRef.current.highlightRegion(current.correct);
      sceneRef.current.flyToRegion(current.correct);
    } else {
      sceneRef.current.reset();
    }
  }, [current, phase, mode]);

  // Wire mesh-click handler for locate mode
  useEffect(() => {
    if (!sceneRef.current) return;
    sceneRef.current.onRegionClick = (regionId) => {
      if (mode !== "locate" || answered || !current) return;
      setAnswered(true);
      setPicked(regionId);
      if (regionId === current.correct.id) setScore((s) => s + 1);
      sceneRef.current?.highlightRegion(current.correct);
      sceneRef.current?.flyToRegion(current.correct);
    };
  }, [mode, answered, current]);

  const start = () => {
    setQuestions(generateQuestions(QUESTION_COUNT));
    setIndex(0);
    setScore(0);
    setAnswered(false);
    setPicked(null);
    setPhase("playing");
  };

  const pickOption = (regionId) => {
    if (answered || !current) return;
    setAnswered(true);
    setPicked(regionId);
    if (regionId === current.correct.id) setScore((s) => s + 1);
    if (mode === "locate") sceneRef.current?.highlightRegion(current.correct);
  };

  const next = () => {
    if (index + 1 >= questions.length) {
      setPhase("result");
      sceneRef.current?.reset();
      return;
    }
    setIndex((i) => i + 1);
    setAnswered(false);
    setPicked(null);
  };

  return (
    <>
      <header className="roadmap-header">
        <span className="roadmap-eyebrow">Brain Quiz</span>
        <h2 className="roadmap-title">3D anatomy practice</h2>
        <p className="roadmap-meta">
          Powered by Three.js · Desikan-Killiany atlas (brainder.org, CC BY-SA 3.0)
        </p>
      </header>

      <div className="brain-layout">
        <div className="brain-canvas-wrap" ref={containerRef}>
          {!viewerReady && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--cream)",
                fontFamily: "var(--font-display)",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
                pointerEvents: "none",
              }}
            >
              Loading meshes… {loadProgress}%
            </div>
          )}
        </div>

        <div className="brain-side">
          <div className="brain-card">
            <div className="brain-mode-row">
              <button
                type="button"
                className={`brain-mode-btn ${mode === "identify" ? "active" : ""}`}
                onClick={() => phase === "setup" && setMode("identify")}
                disabled={phase !== "setup"}
              >
                Identify
              </button>
              <button
                type="button"
                className={`brain-mode-btn ${mode === "locate" ? "active" : ""}`}
                onClick={() => phase === "setup" && setMode("locate")}
                disabled={phase !== "setup"}
              >
                Locate
              </button>
            </div>
            <p style={{ fontSize: 12, color: "var(--ink-light)", lineHeight: 1.5 }}>
              {mode === "identify"
                ? "We highlight a region — you pick its name from 4 options."
                : "We name a region — you click it on the brain."}
            </p>
          </div>

          {phase === "setup" && (
            <div className="brain-card">
              <p style={{ fontSize: 13 }}>
                {QUESTION_COUNT} questions, randomised. Pick a mode and start when the brain finishes loading.
              </p>
              <button
                type="button"
                className="quiz-button"
                onClick={start}
                disabled={!viewerReady}
              >
                Start
              </button>
            </div>
          )}

          {phase === "playing" && current && (
            <div className="brain-card">
              <span className="quiz-result-badge" style={{ background: "var(--cream)" }}>
                {index + 1} / {questions.length} · score {score}
              </span>
              <p className="brain-question">
                {mode === "identify"
                  ? "Which region is highlighted?"
                  : `Click on: ${current.correct.name}`}
              </p>

              {mode === "identify" && (
                <div className="brain-options">
                  {current.options.map((opt) => {
                    let cls = "quiz-option";
                    if (answered) {
                      if (opt.id === current.correct.id) cls += " correct";
                      else if (opt.id === picked) cls += " wrong";
                    } else if (opt.id === picked) {
                      cls += " selected";
                    }
                    return (
                      <button
                        type="button"
                        key={opt.id}
                        className={cls}
                        onClick={() => pickOption(opt.id)}
                        disabled={answered}
                      >
                        {opt.name}
                      </button>
                    );
                  })}
                </div>
              )}

              {answered && (
                <>
                  <p style={{ fontSize: 13, marginTop: 4 }}>
                    {picked === current.correct.id
                      ? "✓ correct"
                      : `✗ correct: ${current.correct.name}`}
                  </p>
                  {current.correct.description && (
                    <p style={{ fontSize: 12, color: "var(--ink-light)", lineHeight: 1.5 }}>
                      {current.correct.description}
                    </p>
                  )}
                  <button type="button" className="quiz-button" onClick={next}>
                    {index + 1 >= questions.length ? "Finish" : "Next"}
                  </button>
                </>
              )}
            </div>
          )}

          {phase === "result" && (
            <div className="brain-card">
              <div className="quiz-summary-score" style={{ alignSelf: "center" }}>
                {score}/{questions.length}
              </div>
              <button type="button" className="quiz-button" onClick={() => setPhase("setup")}>
                Try again
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
