import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";

function NaoInner({ target }) {
  const { scene } = useGLTF("/nao.glb");
  const ref = useRef();

  useFrame(() => {
    if (!ref.current) return;
    ref.current.rotation.y = THREE.MathUtils.lerp(
      ref.current.rotation.y,
      target.current.x * 0.5,
      0.05,
    );
    ref.current.rotation.x = THREE.MathUtils.lerp(
      ref.current.rotation.x,
      -target.current.y * 0.15,
      0.05,
    );
  });

  return (
    <group ref={ref}>
      <primitive object={scene} scale={0.9} position={[0, -0.8, 0]} />
    </group>
  );
}

function Tracker({ target }) {
  useFrame(({ pointer }) => {
    target.current.x = pointer.x;
    target.current.y = pointer.y;
  });
  return null;
}

export default function NaoModel() {
  const target = useRef(new THREE.Vector2(0, 0));

  return (
    <div className="nao-canvas">
      <Canvas
        camera={{ position: [0, 0, 8], fov: 35 }}
        gl={{ alpha: true, antialias: true }}
      >
        <ambientLight intensity={0.8} />
        <directionalLight position={[5, 5, 5]} intensity={1.2} />
        <directionalLight position={[-3, 2, 4]} intensity={0.4} />
        <NaoInner target={target} />
        <Tracker target={target} />
      </Canvas>
    </div>
  );
}

useGLTF.preload("/nao.glb");
