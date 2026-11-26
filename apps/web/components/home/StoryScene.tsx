"use client";

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useMemo, useRef, type MutableRefObject } from "react";
import { BufferGeometry, Float32BufferAttribute, type Group, type Mesh, type MeshStandardMaterial, type Points } from "three";
import type { Tier } from "@/lib/tier";

const N = 7;
const ring = Array.from({ length: N }, (_, i) => {
  const a = (i / N) * Math.PI * 2;
  return { x: Math.cos(a) * 3.2, z: Math.sin(a) * 3.2 - 2, h: 0.8 + ((i * 37) % 10) / 10 };
});

function Structures({ active, progress }: { active: number; progress: MutableRefObject<number> }) {
  const g = useRef<Group>(null);
  const meshes = useRef<(Mesh | null)[]>([]);
  const lines = useRef<{ geometry: BufferGeometry | null }>({ geometry: null });
  const geo = useMemo(() => {
    const pts: number[] = [];
    for (let i = 0; i < N; i++) { const a = ring[i], b = ring[(i + 1) % N]; pts.push(a.x, a.h, a.z, b.x, b.h, b.z); }
    const gm = new BufferGeometry(); gm.setAttribute("position", new Float32BufferAttribute(pts, 3)); return gm;
  }, []);
  lines.current.geometry = geo;
  const { invalidate } = useThree();

  useFrame((state, dt) => {
    const p = progress.current;
    if (g.current) {
      // ring drifts into order as the visitor scrolls: scattered at the top, connected below
      g.current.rotation.y += ((state.pointer.x * 0.25 + p * 1.2) - g.current.rotation.y) * 0.05;
      g.current.position.y = -0.6 - p * 0.6;
    }
    meshes.current.forEach((m, i) => {
      if (!m) return;
      const mat = m.material as MeshStandardMaterial;
      const on = i === active;
      mat.emissiveIntensity += ((on ? 1.4 : 0.35 + p * 0.4) - mat.emissiveIntensity) * 0.1;
      const spread = 1 + (1 - Math.min(1, p * 2)) * 0.9;
      m.position.x += (ring[i].x * spread - m.position.x) * 0.06;
      m.position.z += (ring[i].z * spread - m.position.z) * 0.06;
      m.scale.y += ((on ? 1.25 : 1) - m.scale.y) * 0.1;
    });
    geo.setDrawRange(0, Math.max(0, Math.round(Math.min(1, Math.max(0, (p - 0.1) / 0.35)) * N)) * 2);
    state.camera.position.z += ((9.5 - p * 2.2) - state.camera.position.z) * 0.05;
    state.camera.position.y += ((1.6 - p * 0.6) - state.camera.position.y) * 0.05;
    state.camera.lookAt(0, 0.2, -2);
    if (dt < 0.2 && state.frameloop === "demand") invalidate();
  });

  return (
    <group ref={g}>
      {ring.map((r, i) => (
        <mesh key={i} ref={(el) => { meshes.current[i] = el; }} position={[r.x * 1.9, r.h / 2, r.z * 1.9]}>
          <boxGeometry args={[0.7, r.h, 0.7]} />
          <meshStandardMaterial color="#101E38" emissive={i === 6 ? "#36B9E9" : "#176BCE"} emissiveIntensity={0.35} roughness={0.35} metalness={0.5} />
        </mesh>
      ))}
      <lineSegments geometry={geo}><lineBasicMaterial color="#36B9E9" transparent opacity={0.8} /></lineSegments>
    </group>
  );
}

function Dust({ count }: { count: number }) {
  const ref = useRef<Points>(null);
  const geo = useMemo(() => {
    const a: number[] = [];
    for (let i = 0; i < count; i++) a.push((Math.random() - 0.5) * 22, Math.random() * 8 - 1, (Math.random() - 0.5) * 18 - 2);
    const g = new BufferGeometry(); g.setAttribute("position", new Float32BufferAttribute(a, 3)); return g;
  }, [count]);
  useFrame((_, dt) => { if (ref.current) ref.current.rotation.y += dt * 0.02; });
  return <points ref={ref} geometry={geo}><pointsMaterial color="#A9C8E8" size={0.04} sizeAttenuation transparent opacity={0.7} /></points>;
}

export default function StoryScene({ tier, active, progress }: { tier: Tier; active: number; progress: MutableRefObject<number> }) {
  return (
    <Canvas dpr={tier === "light" ? 1 : [1, 1.5]} frameloop={tier === "light" ? "demand" : "always"}
      camera={{ position: [0, 1.8, 9.5], fov: 50 }} gl={{ antialias: tier === "full", powerPreference: "low-power" }}>
      <ambientLight intensity={0.5} />
      <pointLight position={[4, 5, 3]} intensity={40} color="#A9C8E8" />
      <Structures active={active} progress={progress} />
      <Dust count={tier === "light" ? 70 : 260} />
    </Canvas>
  );
}
