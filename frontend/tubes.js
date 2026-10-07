/* ============================================================
   TruthKeeper — light-bleeding neon tubes cursor (hero background)
   Adapted from `threejs-components` tubes-cursor, recolored to the
   cyber palette. Loads three + the bundle from a CDN via dynamic
   import; if offline, the static hero aura is kept. Click to recolor.
   ============================================================ */
const CYBER = ["#00f2ff", "#bc13fe", "#39ff14", "#60aed5", "#7c3aed", "#2de2ff"];

function pick(n) {
  const pool = CYBER.slice(), out = [];
  for (let i = 0; i < n; i++) out.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0] || CYBER[i % CYBER.length]);
  return out;
}

async function bootTubes() {
  const canvas = document.getElementById("tubes");
  if (!canvas) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const fit = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(canvas.clientWidth * dpr);
    canvas.height = Math.floor(canvas.clientHeight * dpr);
  };
  fit();

  try {
    const mod = await import("https://cdn.jsdelivr.net/npm/threejs-components@0.0.19/build/cursors/tubes1.min.js");
    const TubesCursor = mod.default;
    const app = TubesCursor(canvas, {
      tubes: {
        colors: ["#00f2ff", "#bc13fe", "#39ff14"],
        lights: { intensity: 240, colors: ["#00f2ff", "#bc13fe", "#39ff14", "#60aed5"] },
      },
    });
    canvas.classList.add("on");
    window.addEventListener("resize", () => { fit(); app?.resize?.(); });
    const recolor = () => { try { app.tubes.setColors(pick(3)); app.tubes.setLightsColors(pick(4)); } catch { /* ignore */ } };
    document.querySelector(".hero")?.addEventListener("click", recolor);
  } catch (e) {
    console.warn("[Tubes] library unavailable — keeping static hero aura.", e);
  }
}

if (document.readyState !== "loading") bootTubes();
else document.addEventListener("DOMContentLoaded", bootTubes);
