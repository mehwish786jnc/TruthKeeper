"use strict";

/* ============================================================
   TruthKeeper opening page — scroll engine (no dependencies)
   - scroll progress bar
   - parallax layers (data-par)
   - reveal-on-scroll
   - count-up stats
   - pinned "scrollytelling" journey
   - horizontal feature scroll driven by vertical scroll
   ============================================================ */
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

/* ---------- reveal + count-up ---------- */
const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (!e.isIntersecting) return;
    e.target.classList.add("in");
    if (e.target.classList.contains("stats")) startCounts();
    io.unobserve(e.target);
  });
}, { threshold: 0.18 });
$$(".reveal").forEach((n) => io.observe(n));

let counted = false;
function startCounts() {
  if (counted) return; counted = true;
  $$(".stat .num").forEach((node) => {
    const to = parseInt(node.dataset.to || "0", 10);
    const suffix = node.dataset.suffix || "";
    if (node.dataset.suffix) { node.textContent = suffix + to; return; }
    if (reduceMotion) { node.textContent = to; return; }
    const start = performance.now();
    (function tick(now) {
      const p = Math.min(1, (now - start) / 1100);
      node.textContent = Math.round(to * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
    })(start);
  });
}

/* ---------- scroll-driven effects (one rAF loop) ---------- */
const progress = $("#progress");
const nav = $("#nav");
const parallax = $$("[data-par]");
const journey = $("#journey");
const jSteps = $$("#jsteps li");
const jCards = $$("#jvisual .jv-card");
const hscroll = $("#hscroll");
const htrack = $("#htrack");
const tint = $("#scrollTint");

/* smooth palette interpolation across scroll progress */
const TINT_STOPS = [[188, 19, 254], [0, 242, 255], [57, 255, 20], [124, 58, 237], [188, 19, 254]];
function tintAt(p) {
  const seg = Math.max(0, Math.min(1, p)) * (TINT_STOPS.length - 1);
  const i = Math.min(TINT_STOPS.length - 2, Math.floor(seg));
  const f = seg - i, a = TINT_STOPS[i], b = TINT_STOPS[i + 1];
  return `${Math.round(a[0] + (b[0] - a[0]) * f)},${Math.round(a[1] + (b[1] - a[1]) * f)},${Math.round(a[2] + (b[2] - a[2]) * f)}`;
}

let ticking = false;
function onScroll() {
  if (ticking) return;
  ticking = true;
  requestAnimationFrame(() => {
    const y = window.scrollY;
    const docH = document.documentElement.scrollHeight - innerHeight;

    // progress bar
    if (progress) progress.style.width = (docH > 0 ? (y / docH) * 100 : 0) + "%";

    // smooth scroll-driven color wash
    if (tint) {
      const p = docH > 0 ? y / docH : 0;
      const rgb = tintAt(p);
      tint.style.background = `radial-gradient(1200px 820px at 50% ${16 + p * 54}%, rgba(${rgb},0.17), transparent 68%)`;
    }

    // nav solid after a bit
    if (nav) nav.classList.toggle("solid", y > 40);

    // parallax
    if (!reduceMotion) {
      for (const el of parallax) {
        const speed = parseFloat(el.dataset.par) || 0;
        el.style.transform = `translate3d(0, ${y * speed}px, 0)`;
      }
    }

    // pinned journey: which step is active
    if (journey && jSteps.length) {
      const rect = journey.getBoundingClientRect();
      const total = journey.offsetHeight - innerHeight;
      const p = Math.min(1, Math.max(0, -rect.top / total));
      const active = Math.min(jSteps.length - 1, Math.floor(p * jSteps.length));
      jSteps.forEach((li, i) => li.classList.toggle("active", i === active));
      jCards.forEach((c, i) => c.classList.toggle("show", i === active));
    }

    // horizontal feature scroll
    if (hscroll && htrack) {
      const rect = hscroll.getBoundingClientRect();
      const total = hscroll.offsetHeight - innerHeight;
      const p = Math.min(1, Math.max(0, -rect.top / total));
      const maxX = Math.max(0, htrack.scrollWidth - innerWidth + 80);
      htrack.style.transform = `translate3d(${-p * maxX}px,0,0)`;
    }

    ticking = false;
  });
}
window.addEventListener("scroll", onScroll, { passive: true });
window.addEventListener("resize", onScroll);
onScroll();

/* first journey step/card visible on load */
if (jSteps[0]) jSteps[0].classList.add("active");
if (jCards[0]) jCards[0].classList.add("show");
