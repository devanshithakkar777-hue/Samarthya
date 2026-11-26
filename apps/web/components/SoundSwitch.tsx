"use client";

import { useEffect, useState } from "react";
import { cueFor, play, setSoundEnabled, soundEnabled } from "@/lib/sound";

/** Plays a short sound when something is pressed, and offers the switch to turn sound off. */
export default function SoundSwitch() {
  const [on, setOn] = useState(true);
  useEffect(() => {
    setOn(soundEnabled());
    const h = (e: MouseEvent) => {
      if (!(e.target instanceof Element) || !e.isTrusted) return;
      const cue = cueFor(e.target);
      if (cue) play(cue);
    };
    document.addEventListener("click", h, true);
    return () => document.removeEventListener("click", h, true);
  }, []);
  return (
    <button type="button" data-sound="off" aria-pressed={on} aria-label={on ? "Interface sounds are on. Press to turn them off" : "Interface sounds are off. Press to turn them on"}
      onClick={() => { const n = !on; setOn(n); setSoundEnabled(n); if (n) play("toggle"); }}
      className="rounded-md border border-cool-silver/40 px-3 py-2 text-left text-sm text-cool-silver hover:text-cyan">
      <span aria-hidden="true">{on ? "♪" : "♪̸"}</span> Sound {on ? "on" : "off"}
    </button>
  );
}
