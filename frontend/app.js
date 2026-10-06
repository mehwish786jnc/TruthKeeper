"use strict";

/* ============================================================
   TruthKeeper frontend logic
   - Keeps the API contract: GET /report, POST /audit
   - Falls back to window.SAMPLE_AUDITS when the backend is
     unreachable so every animation is demoable offline.
   ============================================================ */

const API = (window.CONFIG?.CLOUD_RUN_URL || "").replace(/\/$/, "");
const TOKEN = window.CONFIG?.AUDIT_TOKEN || "";
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const STATUS = {
  contradictory: { label: "Contradictory", color: "var(--s-contradictory)" },
  deprecated:    { label: "Deprecated",    color: "var(--s-deprecated)" },
  stale:         { label: "Stale",         color: "var(--s-stale)" },
  uncertain:     { label: "Uncertain",     color: "var(--s-uncertain)" },
  healthy:       { label: "Healthy",       color: "var(--s-healthy)" },
};
const SEVERITY = ["contradictory", "deprecated", "stale", "uncertain", "healthy"];

let STATE = { audits: [], filter: "all", isDemo: false };

/* ---------- tiny helpers ---------- */
const $ = (sel) => document.querySelector(sel);
function el(tag, cls, html) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html !== undefined) n.innerHTML = html;
  return n;
}
function esc(s) {
  return String(s ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

/* count-up animation for numbers */
function countUp(node, to, { suffix = "", dur = 900 } = {}) {
  if (reduceMotion) { node.textContent = to + suffix; return; }
  const start = performance.now();
  const from = 0;
  function tick(now) {
    const p = Math.min(1, (now - start) / dur);
    const eased = 1 - Math.pow(1 - p, 3);
    node.textContent = Math.round(from + (to - from) * eased) + suffix;
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ---------- data loading ---------- */
async function loadReport() {
  try {
    if (!API) throw new Error("no API configured");
    const res = await fetch(`${API}/report`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const audits = data.audits || [];
    if (!audits.length) throw new Error("empty");
    STATE.audits = audits;
    STATE.isDemo = false;
    setDataBadge("live · from cache", false);
  } catch {
    // backend unreachable or empty → graceful offline demo mode
    STATE.audits = (window.SAMPLE_AUDITS || []).slice();
    STATE.isDemo = true;
    setDataBadge("demo data · backend offline", true);
  }
  STATE.audits.sort((a, b) => (a.confidence ?? 1) - (b.confidence ?? 1));
  render();
}

function setDataBadge(text, demo) {
  const b = $("#data-badge");
  b.hidden = false;
  b.textContent = text;
  b.style.color = demo ? "var(--amber)" : "var(--green)";
  b.style.borderColor = demo ? "color-mix(in srgb, var(--amber) 45%, transparent)" : "color-mix(in srgb, var(--green) 45%, transparent)";
}

/* ---------- rendering ---------- */
function render() {
  renderStats();
  renderFilters();
  renderCards();
}

function renderStats() {
  const a = STATE.audits;
  const flagged = a.filter((x) => x.status !== "healthy").length;
  const avg = a.length ? Math.round((a.reduce((s, x) => s + (x.confidence ?? 0), 0) / a.length) * 100) : 0;
  const tiles = [
    { num: a.length, label: "docs audited", color: "var(--cyan)" },
    { num: flagged, label: "need attention", color: "var(--amber)", flag: true },
    { num: a.filter((x) => x.status === "contradictory").length, label: "contradictions", color: "var(--s-contradictory)" },
    { num: avg, label: "avg confidence", color: "var(--green)", suffix: "%" },
  ];
  const wrap = $("#summary");
  wrap.innerHTML = "";
  tiles.forEach((t, i) => {
    const tile = el("div", "stat" + (t.flag ? " accent-flag" : ""));
    tile.style.animationDelay = `${i * 0.09}s`;
    const num = el("div", "stat-num", "0");
    num.style.color = t.color;
    tile.append(num, el("span", "stat-label", t.label));
    const bar = el("div", "bar"); const fill = el("i");
    fill.style.background = t.color;
    bar.append(fill); tile.append(bar);
    wrap.append(tile);
    const pct = t.suffix === "%" ? t.num : Math.min(100, Math.round((t.num / Math.max(1, a.length)) * 100));
    setTimeout(() => { countUp(num, t.num, { suffix: t.suffix || "" }); fill.style.width = pct + "%"; }, 120 + i * 90);
  });
}

function renderFilters() {
  const counts = {};
  for (const a of STATE.audits) counts[a.status] = (counts[a.status] || 0) + 1;
  const wrap = $("#filters");
  wrap.innerHTML = "";
  const make = (key, label, color) => {
    const chip = el("button", "chip" + (STATE.filter === key ? " active" : ""));
    if (color) chip.append(Object.assign(el("span", "swatch"), { style: `background:${color}` }));
    chip.append(document.createTextNode(label));
    const n = key === "all" ? STATE.audits.length : (counts[key] || 0);
    chip.append(el("span", "cnt", String(n)));
    chip.onclick = () => { STATE.filter = key; renderFilters(); renderCards(); };
    return chip;
  };
  wrap.append(make("all", "All", null));
  SEVERITY.forEach((s) => { if (counts[s]) wrap.append(make(s, STATUS[s].label, STATUS[s].color)); });
}

function ring(confidence, color) {
  const pct = Math.round((confidence ?? 0) * 100);
  const R = 26, C = 2 * Math.PI * R;
  const wrap = el("div", "ring");
  wrap.style.setProperty("--c", color);
  wrap.innerHTML = `
    <svg width="62" height="62" viewBox="0 0 62 62">
      <circle class="track" cx="31" cy="31" r="${R}" fill="none" stroke-width="6"/>
      <circle class="meter" cx="31" cy="31" r="${R}" fill="none" stroke-width="6"
        stroke-dasharray="${C}" stroke-dashoffset="${C}"/>
    </svg>
    <span class="pct">0%</span>`;
  // animate the ring stroke on the next frame
  const meter = wrap.querySelector(".meter");
  const label = wrap.querySelector(".pct");
  requestAnimationFrame(() => {
    meter.style.strokeDashoffset = C * (1 - pct / 100);
  });
  setTimeout(() => countUp(label, pct, { suffix: "%", dur: 1000 }), 260);
  return wrap;
}

function card(a) {
  const meta = STATUS[a.status] || STATUS.uncertain;
  const c = el("article", `card sev-${a.status}`);
  c.dataset.status = a.status;
  c.append(el("div", "glare"));

  const head = el("div", "card-head");
  const title = el("div", "card-title",
    `<h3>${esc(a.title || a.doc_id)}</h3><span class="doc-id">${esc(a.doc_id)}</span>`);
  head.append(title, ring(a.confidence, meta.color));
  c.append(head);

  const badge = el("div", "badge", `<span class="bdot"></span>${meta.label}`);
  c.append(badge);

  if (a.contradictions?.length) {
    c.append(el("h4", null, "Contradictions"));
    a.contradictions.forEach((x) => {
      const quote = x.evidence ? `<blockquote>${esc(x.evidence)}</blockquote>` : "";
      c.append(el("div", "contradiction", `
        <div class="vs"><span class="tag">conflicts with</span> <code>${esc(x.other_doc)}</code></div>
        <p>${esc(x.explanation)}</p>
        ${quote}`));
    });
  }

  if (a.evidence?.length) {
    c.append(el("h4", null, "Evidence"));
    const box = el("div", "evidence");
    const ul = el("ul");
    a.evidence.forEach((e) => ul.append(el("li", null, esc(e))));
    box.append(ul);
    c.append(box);
  }

  if (a.suggested_fix) {
    c.append(el("div", "fix", `<h4>Suggested fix</h4><p>${esc(a.suggested_fix)}</p>`));
  }

  c.append(el("div", "card-foot",
    `<span>${new Date(a.created_at || Date.now()).toLocaleDateString()}</span>
     <span class="chipmodel">${esc(a.model_used || "—")}</span>`));

  attachTilt(c);
  return c;
}

function renderCards() {
  const report = $("#report");
  report.innerHTML = "";
  const items = STATE.audits.filter((a) => STATE.filter === "all" || a.status === STATE.filter);
  if (!items.length) {
    report.append(el("div", "empty", "Nothing in this category. 🎉"));
    return;
  }
  const io = new IntersectionObserver((entries, obs) => {
    entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); obs.unobserve(e.target); } });
  }, { threshold: 0.12 });

  items.forEach((a, i) => {
    const node = card(a);
    node.style.animationDelay = `${Math.min(i * 0.07, 0.6)}s`;
    report.append(node);
    if (reduceMotion) node.classList.add("in");
    else io.observe(node);
  });
}

/* ---------- 3D pointer tilt + glare ---------- */
function attachTilt(node) {
  if (reduceMotion) return;
  const MAX = 6;
  node.addEventListener("pointermove", (e) => {
    const r = node.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width;
    const py = (e.clientY - r.top) / r.height;
    node.style.transform = `perspective(900px) rotateY(${(px - 0.5) * MAX}deg) rotateX(${(0.5 - py) * MAX}deg) translateY(-4px)`;
    node.style.setProperty("--mx", px * 100 + "%");
    node.style.setProperty("--my", py * 100 + "%");
  });
  node.addEventListener("pointerleave", () => { node.style.transform = ""; });
}

/* ---------- Run Audit ---------- */
const SCAN_STEPS = [
  "booting auditor…",
  "loading knowledge base (15 docs)…",
  "cross-referencing claims with Gemini…",
  "scoring confidence per document…",
  "detecting contradictions…",
  "ranking the Rot Report…",
];
let scanTimer = null;

async function runAudit() {
  const overlay = $("#scan-overlay");
  const sub = $("#scan-sub");
  overlay.classList.add("on");
  let i = 0;
  sub.textContent = SCAN_STEPS[0];
  scanTimer = setInterval(() => { i = (i + 1) % SCAN_STEPS.length; sub.textContent = SCAN_STEPS[i]; }, 700);

  const buttons = document.querySelectorAll("#run-audit, #hero-audit");
  buttons.forEach((b) => (b.disabled = true));

  try {
    if (API) {
      const res = await fetch(`${API}/audit`, {
        method: "POST",
        headers: TOKEN ? { "X-Audit-Token": TOKEN } : {},
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await new Promise((r) => setTimeout(r, 1400)); // let the radar breathe
      await loadReport();
    } else {
      // offline demo: just replay the scan then show sample data
      await new Promise((r) => setTimeout(r, 2600));
      await loadReport();
    }
    $("#dashboard").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth" });
  } catch {
    sub.textContent = "audit failed — showing cached report";
    await new Promise((r) => setTimeout(r, 900));
    await loadReport();
  } finally {
    clearInterval(scanTimer);
    overlay.classList.remove("on");
    buttons.forEach((b) => (b.disabled = false));
  }
}

/* ---------- constellation canvas ---------- */
function constellation() {
  if (reduceMotion) return;
  const canvas = $("#constellation");
  const ctx = canvas.getContext("2d");
  let w, h, pts;
  const N = Math.min(70, Math.floor(window.innerWidth / 22));
  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
    pts = Array.from({ length: N }, () => ({
      x: Math.random() * w, y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
    }));
  }
  resize();
  window.addEventListener("resize", resize);
  function frame() {
    ctx.clearRect(0, 0, w, h);
    for (const p of pts) {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > w) p.vx *= -1;
      if (p.y < 0 || p.y > h) p.vy *= -1;
    }
    for (let i = 0; i < pts.length; i++) {
      ctx.fillStyle = "rgba(130,170,255,0.55)";
      ctx.beginPath(); ctx.arc(pts[i].x, pts[i].y, 1.4, 0, Math.PI * 2); ctx.fill();
      for (let j = i + 1; j < pts.length; j++) {
        const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
        const d = Math.hypot(dx, dy);
        if (d < 130) {
          ctx.strokeStyle = `rgba(120,160,255,${(1 - d / 130) * 0.18})`;
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y); ctx.stroke();
        }
      }
    }
    requestAnimationFrame(frame);
  }
  frame();
}

/* ---------- scroll reveal for static .reveal elements ---------- */
function revealObserver() {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add("in"); });
  }, { threshold: 0.15 });
  document.querySelectorAll(".reveal").forEach((n) => io.observe(n));
}

/* ---------- magnetic buttons ---------- */
function magnetic() {
  if (reduceMotion) return;
  document.querySelectorAll(".magnetic").forEach((btn) => {
    btn.addEventListener("pointermove", (e) => {
      const r = btn.getBoundingClientRect();
      btn.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * 0.18}px, ${(e.clientY - r.top - r.height / 2) * 0.28}px) translateY(-2px)`;
    });
    btn.addEventListener("pointerleave", () => (btn.style.transform = ""));
  });
}

/* ---------- init ---------- */
document.addEventListener("DOMContentLoaded", () => {
  $("#run-audit").addEventListener("click", runAudit);
  $("#hero-audit").addEventListener("click", runAudit);
  constellation();
  revealObserver();
  magnetic();
  void loadReport();
});
