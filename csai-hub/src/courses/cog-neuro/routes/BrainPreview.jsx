import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";

const MESH_BASE = "/cog-neuro/brain-meshes";

export default function BrainPreview({ regions }) {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a);
    const width = container.clientWidth;
    const height = container.clientHeight;
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 20, 280);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const dir = new THREE.DirectionalLight(0xffffff, 0.85);
    dir.position.set(60, 80, 100);
    scene.add(dir);

    const group = new THREE.Group();
    scene.add(group);

    sceneRef.current = { renderer, camera, scene, group, container };

    let frame;
    const animate = () => {
      group.rotation.y += 0.0035;
      renderer.render(scene, camera);
      frame = requestAnimationFrame(animate);
    };
    animate();

    const onResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      if (renderer.domElement.parentElement === container) {
        container.removeChild(renderer.domElement);
      }
      sceneRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!sceneRef.current) return;
    const { group } = sceneRef.current;

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

    if (!regions || regions.length === 0) {
      setLoading(false);
      return;
    }

    setLoading(true);
    const loader = new OBJLoader();
    const files = regions.flatMap((r) =>
      r.meshFiles.map((f) => ({ file: f, region: r })),
    );

    let active = true;
    let loaded = 0;

    Promise.all(
      files.map(async ({ file, region }) => {
        try {
          const obj = await loader.loadAsync(`${MESH_BASE}/${file}`);
          if (!active) return;
          obj.traverse((child) => {
            if (child.isMesh) {
              const c = region.color;
              const color = new THREE.Color(c[0] / 255, c[1] / 255, c[2] / 255);
              child.material = new THREE.MeshStandardMaterial({
                color,
                emissive: color,
                emissiveIntensity: 0.4,
                transparent: true,
                opacity: 0.95,
                side: THREE.DoubleSide,
              });
            }
          });
          group.add(obj);
        } catch {
          // ignore missing meshes
        }
        loaded++;
      }),
    ).then(() => {
      if (active) setLoading(false);
    });

    return () => {
      active = false;
    };
  }, [regions]);

  return (
    <div className="notes-brain-canvas" ref={containerRef}>
      {loading && (
        <div className="notes-brain-loading">
          {regions.length === 0 ? "No regions detected" : "Loading…"}
        </div>
      )}
    </div>
  );
}
