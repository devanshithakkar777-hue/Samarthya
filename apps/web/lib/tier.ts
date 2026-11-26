export type Tier = "off" | "light" | "full";

/** 3D only when the device can afford it and the person has not asked for less motion or data. */
export function pickTier(): Tier {
  try {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return "off";
    const nav = navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string }; deviceMemory?: number };
    if (nav.connection?.saveData) return "off";
    if (["slow-2g", "2g", "3g"].includes(nav.connection?.effectiveType ?? "")) return "off";
    const c = document.createElement("canvas");
    if (!(c.getContext("webgl2") || c.getContext("webgl"))) return "off";
    const cores = navigator.hardwareConcurrency ?? 4;
    const mem = nav.deviceMemory ?? 4;
    if (cores < 4 || mem < 4) return "light";
    return window.innerWidth < 768 ? "light" : "full";
  } catch { return "off"; }
}
