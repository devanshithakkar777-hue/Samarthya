"use client";

import { createContext, useContext, useEffect, useMemo, useRef, useState, type MutableRefObject, type ReactNode } from "react";
import dynamic from "next/dynamic";
import { pickTier, type Tier } from "@/lib/tier";

const StoryScene = dynamic(() => import("./StoryScene"), { ssr: false });

type Ctx = { tier: Tier; active: number; setActive: (i: number) => void; progress: MutableRefObject<number> };
const C = createContext<Ctx>({ tier: "off", active: -1, setActive: () => {}, progress: { current: 0 } });
export const useStory = () => useContext(C);

/** One fixed 3D backdrop for the dark scenes. Content never depends on it: every scene is plain, readable HTML. */
export default function StoryProvider({ children }: { children: ReactNode }) {
  const [tier, setTier] = useState<Tier>("off");
  const [active, setActive] = useState(-1);
  const progress = useRef(0);
  const wrap = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const run = () => setTier(pickTier());
    const w = window as Window & { requestIdleCallback?: (cb: () => void) => number };
    if (w.requestIdleCallback) w.requestIdleCallback(run); else setTimeout(run, 400);
  }, []);

  // scroll-linked camera progress, loaded only when 3D is on so low-end devices never download it
  useEffect(() => {
    if (tier === "off" || !wrap.current) return;
    let kill = () => {};
    let alive = true;
    (async () => {
      const [{ gsap }, { ScrollTrigger }] = await Promise.all([import("gsap"), import("gsap/ScrollTrigger")]);
      if (!alive || !wrap.current) return;
      gsap.registerPlugin(ScrollTrigger);
      const st = ScrollTrigger.create({
        trigger: wrap.current, start: "top top", end: "bottom bottom", scrub: 0.6,
        onUpdate: (self) => { progress.current = self.progress; },
      });
      kill = () => st.kill();
    })();
    return () => { alive = false; kill(); };
  }, [tier]);

  const value = useMemo(() => ({ tier, active, setActive, progress }), [tier, active]);
  return (
    <C.Provider value={value}>
      <div ref={wrap} className="relative">
        {tier !== "off" && (
          <div className="pointer-events-none sticky top-0 z-0 -mb-[100vh] h-screen opacity-80" aria-hidden="true">
            <StoryScene tier={tier} active={active} progress={progress} />
          </div>
        )}
        <div className="relative z-10">{children}</div>
      </div>
    </C.Provider>
  );
}
