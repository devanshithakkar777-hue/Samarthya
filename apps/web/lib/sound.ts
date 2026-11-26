/** Tiny interface sounds made with the browser's own audio engine: no files to download, no licences.
 *  They play only in answer to a press, never on their own, and one switch turns them all off. */
export type Cue = "tap" | "nav" | "primary" | "toggle";
const KEY = "samarthya.sound";
let ctx: AudioContext | null = null;
let last = 0;

export function soundEnabled(): boolean {
  try { return window.localStorage.getItem(KEY) !== "off"; } catch { return true; }
}
export function setSoundEnabled(on: boolean) {
  try { window.localStorage.setItem(KEY, on ? "on" : "off"); } catch { /* storage can be blocked */ }
}

const CUES: Record<Cue, { f: number[]; ms: number; vol: number; type: OscillatorType }> = {
  tap: { f: [740], ms: 70, vol: 0.05, type: "sine" },
  nav: { f: [520, 780], ms: 55, vol: 0.05, type: "sine" },
  primary: { f: [523, 659, 784], ms: 60, vol: 0.06, type: "triangle" },
  toggle: { f: [440, 330], ms: 50, vol: 0.05, type: "sine" },
};

export function play(cue: Cue) {
  if (typeof window === "undefined" || !soundEnabled()) return;
  const now = performance.now();
  if (now - last < 45) return;
  last = now;
  try {
    const AC = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AC) return;
    ctx = ctx ?? new AC();
    if (ctx.state === "suspended") void ctx.resume();
    const c = CUES[cue];
    const t0 = ctx.currentTime;
    c.f.forEach((hz, i) => {
      const o = ctx!.createOscillator(), g = ctx!.createGain();
      const start = t0 + (i * c.ms) / 1000, end = start + c.ms / 1000 + 0.05;
      o.type = c.type; o.frequency.value = hz;
      g.gain.setValueAtTime(0.0001, start);
      g.gain.exponentialRampToValueAtTime(c.vol, start + 0.008);
      g.gain.exponentialRampToValueAtTime(0.0001, end);
      o.connect(g).connect(ctx!.destination);
      o.start(start); o.stop(end + 0.02);
    });
  } catch { /* sound is a nicety; never break the page for it */ }
}

/** Pick a cue from what was pressed. */
export function cueFor(el: Element): Cue | null {
  const t = el.closest<HTMLElement>('a[href],button,[role="button"],[role="tab"],[role="menuitem"],summary,input[type="checkbox"],input[type="radio"],select,[data-sound]');
  if (!t || t.hasAttribute("disabled") || t.getAttribute("aria-disabled") === "true" || t.dataset.sound === "off") return null;
  if (t.dataset.sound) return t.dataset.sound as Cue;
  if (t.tagName === "A") return "nav";
  if (t.matches('input[type="checkbox"],input[type="radio"],summary') || t.hasAttribute("aria-pressed") || t.hasAttribute("aria-expanded")) return "toggle";
  if (t.matches('button[type="submit"]') ) return "primary";
  return "tap";
}
