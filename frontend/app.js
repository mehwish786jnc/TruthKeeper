"use strict";

/* ============================================================
   TruthKeeper — complete product experience (frontend / demo)
   UNDERSTAND → TRUST → DECIDE → ACT
   Demo-data driven (window.SAMPLE_AUDITS / CORPUS / DEMO).
   Backend calls happen ONLY if CLOUD_RUN_URL is set; empty = pure demo.
   ============================================================ */

function cfg(key, fallback) {
  const ov = localStorage.getItem("tk_" + key);
  if (ov !== null) return ov;
  return window.CONFIG?.[key] ?? fallback;
}
let API = cfg("CLOUD_RUN_URL", "").replace(/\/$/, "");
let TOKEN = cfg("AUDIT_TOKEN", "");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const STATUS = {
  contradictory: { label: "Contradictory", color: "var(--s-contradictory)", hex: "#fb7185" },
  deprecated:    { label: "Deprecated",    color: "var(--s-deprecated)",    hex: "#fb923c" },
  stale:         { label: "Stale",         color: "var(--s-stale)",         hex: "#fbbf24" },
  uncertain:     { label: "Uncertain",     color: "var(--s-uncertain)",     hex: "#60a5fa" },
  healthy:       { label: "Healthy",       color: "var(--s-healthy)",       hex: "#39ff14" },
};
const SEVERITY = ["contradictory", "deprecated", "stale", "uncertain", "healthy"];
const REL = { contradiction: "#fb7185", reference: "#60a5fa", dependency: "#a855f7" };
const REM_STEPS = ["Detected", "Suggested correction", "Preview changes", "Approved", "Completed"];

const VIEWS = {
  overview:  { title: "Knowledge Command Center", sub: "The health of everything your organization knows" },
  ask:       { title: "Ask", sub: "Get a trusted answer — or a cross-checked recommendation" },
  knowledge: { title: "Knowledge", sub: "Every document, its trust, and what it connects to" },
  graph:     { title: "Knowledge Graph", sub: "Relationships, contradictions and risk across knowledge" },
  manage:    { title: "Add & Manage Documents", sub: "Upload source material and keep your knowledge base current" },
  decisions: { title: "Decisions", sub: "The human approval log — who decided what, and when" },
  actions:   { title: "Actions", sub: "Fix knowledge problems and understand their impact" },
  settings:  { title: "Settings", sub: "Connect TruthKeeper to your backend" },
};

const STATE = {
  audits: [], corpus: [], demo: {}, decisions: {}, decisionLog: [],
  remediation: [], filter: "all", kTab: "documents", view: "overview",
  askMode: "quick",
  isDemo: true, health: null, graph: null,
};

/* ---------- helpers ---------- */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
function el(tag, cls, html) { const n = document.createElement(tag); if (cls) n.className = cls; if (html !== undefined) n.innerHTML = html; return n; }
function esc(s) { return String(s ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;"); }
function toast(msg) { let t = $("#toast"); if (!t) { t = el("div", "toast"); t.id = "toast"; document.body.append(t); } t.textContent = msg; t.classList.add("show"); setTimeout(() => t.classList.remove("show"), 2400); }
function auditFor(id) { return STATE.audits.find((a) => a.doc_id === id); }
function docFor(id) { return STATE.corpus.find((d) => d.id === id); }
function titleOf(id) { return docFor(id)?.title || auditFor(id)?.title || id; }
function teamsOf(id) { return STATE.demo.teams?.[id] || []; }

/* ---------- user-added documents (persisted, offline) ---------- */
const USER_DOCS_KEY = "tk_user_docs";
const DEPRECATED_TERMS = ["stackdriver", "nagios", "heroku", "anyconnect", "mysqldump", "jenkins", "on-prem nas", "on-prem", "flash player", "python 2", "angularjs"];
function loadUserDocs() { try { return JSON.parse(localStorage.getItem(USER_DOCS_KEY) || "[]"); } catch { return []; } }
function saveUserDocs(docs) { localStorage.setItem(USER_DOCS_KEY, JSON.stringify(docs)); }
function slugify(s) { return String(s || "").toLowerCase().replace(/\.[a-z0-9]+$/, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "doc-" + Date.now(); }

// Lightweight client-side auditor so uploaded docs get a meaningful status offline.
function heuristicAudit(doc) {
  const body = (doc.body || "").toLowerCase();
  const found = DEPRECATED_TERMS.filter((t) => body.includes(t));
  const year = Number.parseInt(String(doc.last_updated || "").slice(0, 4), 10);
  const stale = year && year < new Date().getFullYear() - 1;
  let status = "healthy", confidence = 0.9, evidence = [], fix = "";
  if (found.length) {
    status = "deprecated"; confidence = 0.34;
    evidence = [`References deprecated tooling: ${found.join(", ")}.`];
    fix = `Replace deprecated references (${found.join(", ")}) with the currently supported tooling.`;
  } else if (!body || body.length < 40) {
    status = "uncertain"; confidence = 0.5;
    evidence = ["Document is very short — not enough content to verify confidently."];
  } else if (stale) {
    status = "stale"; confidence = 0.52;
    evidence = [`Last updated ${doc.last_updated} — content may no longer reflect current practice.`];
    fix = "Review and refresh; confirm the steps and references are still accurate.";
  }
  return { doc_id: doc.id, title: doc.title, confidence, status, contradictions: [], evidence, suggested_fix: fix, model_used: "heuristic", created_at: new Date().toISOString() };
}

function countUp(node, to, { suffix = "", dur = 900 } = {}) {
  if (reduceMotion) { node.textContent = to + suffix; return; }
  const start = performance.now();
  (function tick(now) {
    const p = Math.min(1, (now - start) / dur);
    node.textContent = Math.round(to * (1 - Math.pow(1 - p, 3))) + suffix;
    if (p < 1) requestAnimationFrame(tick);
  })(start);
}

/* ---------- data load (demo-first) ---------- */
async function loadData() {
  try {
    if (!API) throw new Error("demo");
    const res = await fetch(`${API}/report`, { cache: "no-store" });
    if (!res.ok) throw new Error("http");
    const data = await res.json();
    if (!data.audits?.length) throw new Error("empty");
    STATE.audits = data.audits; STATE.isDemo = false;
    setBadge("live · from cache", "var(--green)");
  } catch {
    STATE.audits = (window.SAMPLE_AUDITS || []).slice(); STATE.isDemo = true;
    setBadge("demo data", "var(--amber)");
  }
  STATE.corpus = (window.CORPUS || []).slice();
  STATE.demo = window.DEMO || {};
  STATE.demo.teams = { ...(STATE.demo.teams || {}) };
  loadUserDocs().forEach((d) => {
    if (!STATE.corpus.some((x) => x.id === d.id)) STATE.corpus.push({ id: d.id, title: d.title, source: d.source, body: d.body, last_updated: d.last_updated });
    if (d.owner?.length) STATE.demo.teams[d.id] = d.owner;
    if (!STATE.audits.some((a) => a.doc_id === d.id)) STATE.audits.push(heuristicAudit(d));
  });
  STATE.decisionLog = (STATE.demo.decisionLog || []).slice();
  STATE.remediation = (STATE.demo.remediation || []).map((r) => ({ ...r, step: 0 }));
  STATE.audits.sort((a, b) => (a.confidence ?? 1) - (b.confidence ?? 1));
  updateNavBadges();
  renderView(STATE.view);
}
function setBadge(text, color) { const b = $("#data-badge"); b.textContent = text; b.style.color = color; b.style.borderColor = `color-mix(in srgb, ${color} 45%, transparent)`; }
function updateNavBadges() {
  const flagged = STATE.audits.filter((a) => a.status !== "healthy").length;
  const nf = $("#nav-flagged"); if (nf) nf.textContent = flagged || "";
  const open = STATE.remediation.filter((r) => r.step < 4).length;
  const na = $("#nav-actions"); if (na) na.textContent = open || "";
}

/* ---------- health ---------- */
function healthScore() {
  const h = STATE.demo.health;
  const gradeColor = (s) => s >= 70 ? "var(--green)" : s >= 55 ? "var(--amber)" : s >= 40 ? "var(--s-deprecated)" : "var(--red)";
  if (h && typeof h.score === "number") return { score: h.score, grade: h.grade, color: gradeColor(h.score) };
  const a = STATE.audits;
  const avg = a.length ? a.reduce((s, x) => s + (x.confidence ?? 0), 0) / a.length : 0;
  const score = Math.round(avg * 100);
  const grade = score >= 85 ? "A" : score >= 70 ? "B" : score >= 55 ? "C" : score >= 40 ? "D" : "F";
  return { score, grade, color: gradeColor(score) };
}

/* ---------- reusable ring ---------- */
function ring(confidence, color, size = 60, stroke = 6) {
  const pct = Math.round((confidence ?? 0) * 100);
  const r = size / 2 - stroke, C = 2 * Math.PI * r;
  const wrap = el("div", "ring"); wrap.style.width = wrap.style.height = size + "px"; wrap.style.setProperty("--c", color);
  wrap.innerHTML = `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <circle class="track" cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke-width="${stroke}"/>
    <circle class="meter" cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke-width="${stroke}" stroke-dasharray="${C}" stroke-dashoffset="${C}"/>
  </svg><span class="pct">0%</span>`;
  requestAnimationFrame(() => { wrap.querySelector(".meter").style.strokeDashoffset = C * (1 - pct / 100); });
  setTimeout(() => countUp(wrap.querySelector(".pct"), pct, { suffix: "%", dur: 1000 }), 250);
  return wrap;
}
function miniBadge(status) {
  const m = STATUS[status] || STATUS.uncertain;
  return `<span class="d-mini-badge" style="color:${m.color};background:color-mix(in srgb, ${m.color} 15%, transparent)">${m.label}</span>`;
}

/* ============================================================
   OVERVIEW — command center
   ============================================================ */
function renderOverview() {
  const host = $("#view-overview");
  const { score, grade, color } = healthScore();
  const a = STATE.audits;
  const h = STATE.demo.health || {};
  const trustedPct = h.trustedPct ?? Math.round(a.filter((x) => x.status === "healthy").length / Math.max(1, a.length) * 100);
  const metrics = [
    { num: trustedPct, suffix: "%", label: "trusted knowledge", color: "var(--green)" },
    { num: h.contradictions ?? a.filter((x) => x.status === "contradictory").length, label: "contradictions", color: "var(--s-contradictory)" },
    { num: (h.stale ?? a.filter((x) => x.status === "stale").length) + (h.deprecated ?? a.filter((x) => x.status === "deprecated").length), label: "stale / deprecated", color: "var(--s-deprecated)" },
    { num: h.gaps ?? 0, label: "knowledge gaps", color: "var(--s-uncertain)" },
  ];

  host.innerHTML = `
    <div class="welcome reveal">
      <h2>The AI that audits your knowledge <span class="grad">before it misleads you.</span></h2>
      <p>TruthKeeper continuously verifies your wikis, runbooks and policies — surfacing contradictions, rot and risk, then helping your team decide and act. This is the live health of your organization's knowledge.</p>
    </div>
    <div class="ov-grid">
      <div class="score-card reveal">
        <div class="score-ring" id="score-ring"></div>
        <div class="score-label">Organizational Knowledge Health</div>
        <div class="score-trend" id="score-trend"></div>
      </div>
      <div>
        <div class="kpi-grid" id="ov-kpis"></div>
        <div class="panel reveal">
          <div class="panel-head"><h3>Critical risks</h3><button class="link-btn" data-goto="knowledge">View all →</button></div>
          <div id="ov-risks"></div>
        </div>
      </div>
    </div>
    <div class="ov-grid-2">
      <div class="panel reveal">
        <div class="panel-head"><h3>Recently changed knowledge</h3></div>
        <div id="ov-recent"></div>
      </div>
      <div class="panel reveal">
        <div class="panel-head"><h3>Knowledge gaps</h3><span class="muted-sm">missing coverage</span></div>
        <div id="ov-gaps"></div>
      </div>
    </div>`;

  // score ring
  const sr = $("#score-ring"), size = 170, rr = size / 2 - 11, C = 2 * Math.PI * rr;
  sr.innerHTML = `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <circle class="track" cx="${size / 2}" cy="${size / 2}" r="${rr}" fill="none" stroke-width="12"/>
    <circle class="meter" cx="${size / 2}" cy="${size / 2}" r="${rr}" fill="none" stroke-width="12" stroke-dasharray="${C}" stroke-dashoffset="${C}" style="stroke:${color}"/>
  </svg><div class="score-center"><span class="score-num" style="color:${color}">0</span><span class="score-grade" style="color:${color}">GRADE ${grade}</span></div>`;
  requestAnimationFrame(() => { sr.querySelector(".meter").style.strokeDashoffset = C * (1 - score / 100); });
  setTimeout(() => countUp(sr.querySelector(".score-num"), score, { dur: 1300 }), 250);
  if (h.trend) $("#score-trend").append(trendChart(h.trend));

  // kpis
  const kg = $("#ov-kpis");
  metrics.forEach((t, i) => {
    const tile = el("div", "stat"); tile.style.animationDelay = `${i * 0.08}s`;
    const num = el("div", "stat-num", "0"); num.style.color = t.color;
    tile.append(num, el("span", "stat-label", t.label)); kg.append(tile);
    setTimeout(() => countUp(num, t.num, { suffix: t.suffix || "" }), 150 + i * 80);
  });

  // risks
  const risks = $("#ov-risks");
  a.filter((x) => x.status !== "healthy").slice(0, 5).forEach((x) => {
    const m = STATUS[x.status];
    const row = el("div", "toprisk", `
      <span class="tr-dot" style="background:${m.color}"></span>
      <div><div class="tr-title">${esc(x.title || x.doc_id)}</div><div class="tr-sub">${m.label} · ${teamsOf(x.doc_id).join(", ") || "unassigned"}</div></div>
      <span class="tr-score" style="color:${m.color}">${Math.round((x.confidence ?? 0) * 100)}%</span>`);
    row.onclick = () => openDoc(x.doc_id);
    risks.append(row);
  });

  // recent
  const recent = $("#ov-recent");
  (h.recentlyChanged || []).forEach((r) => {
    const au = auditFor(r.id); const m = STATUS[au?.status] || STATUS.uncertain;
    const row = el("div", "toprisk", `
      <span class="tr-dot" style="background:${m.color}"></span>
      <div><div class="tr-title">${esc(r.title)}</div><div class="tr-sub">${r.change} · ${esc(r.when)}</div></div>
      ${miniBadge(au?.status || "uncertain")}`);
    row.onclick = () => openDoc(r.id);
    recent.append(row);
  });

  // gaps
  const gaps = $("#ov-gaps");
  (h.gaps !== undefined ? STATE.demo.gaps : []).forEach((g) => {
    const col = g.severity === "high" ? "var(--red)" : "var(--amber)";
    gaps.append(el("div", "gap-item", `<span class="gap-sev" style="background:${col}"></span><div><div class="tr-title">${esc(g.area)}</div><div class="tr-sub">${esc(g.description)}</div></div>`));
  });

  $$("[data-goto]", host).forEach((b) => (b.onclick = () => go(b.dataset.goto)));
}

function trendChart(series) {
  const w = 240, hgt = 60, pad = 6;
  const max = Math.max(...series.map((s) => s.score)), min = Math.min(...series.map((s) => s.score));
  const span = Math.max(1, max - min);
  const pts = series.map((s, i) => {
    const x = pad + i * ((w - 2 * pad) / (series.length - 1));
    const y = hgt - pad - ((s.score - min) / span) * (hgt - 2 * pad);
    return [x, y];
  });
  const line = pts.map((p) => p.join(",")).join(" ");
  const area = `${pad},${hgt - pad} ${line} ${w - pad},${hgt - pad}`;
  const wrap = el("div", "trend");
  wrap.innerHTML = `<svg width="100%" viewBox="0 0 ${w} ${hgt}" preserveAspectRatio="none">
    <defs><linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="var(--cyan)" stop-opacity="0.35"/><stop offset="100%" stop-color="var(--cyan)" stop-opacity="0"/></linearGradient></defs>
    <polygon points="${area}" fill="url(#tg)"/>
    <polyline points="${line}" fill="none" stroke="var(--cyan)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </svg><div class="trend-label">6-month trend · now ${series[series.length - 1].score}</div>`;
  return wrap;
}

/* ============================================================
   ASK AI — trustworthy assistant
   ============================================================ */
function renderAsk() {
  const host = $("#view-ask");
  const mode = STATE.askMode || (STATE.askMode = "quick");
  const deep = mode === "deep";
  host.innerHTML = `
    <div class="ask-wrap">
      <div class="ask-modes" role="tablist">
        <button class="ask-mode ${deep ? "" : "active"}" data-mode="quick" role="tab" aria-selected="${!deep}">
          <span class="am-t">Quick answer</span>
          <span class="am-s">One trusted source · instant · withheld if the source can't be trusted</span>
        </button>
        <button class="ask-mode ${deep ? "active" : ""}" data-mode="deep" role="tab" aria-selected="${deep}">
          <span class="am-t">Deep research</span>
          <span class="am-s">Cross-checks many sources → recommendation you can record</span>
        </button>
      </div>
      <div class="ask-box">
        <input class="ask-input" id="ask-input" placeholder="${deep ? "Ask a decision question — e.g. Should we migrate from API A to API B?" : "Ask anything — e.g. How do I deploy the API?"}" />
        <button class="btn btn-primary" id="ask-go"><span class="btn-glow"></span><span class="btn-label">${deep ? "Research" : "Ask"}</span></button>
      </div>
      <div class="ask-suggests" id="ask-suggests"></div>
      <div id="ask-answer"></div>
    </div>`;
  renderAskSuggests();
  $("#ask-go").onclick = askSubmit;
  $("#ask-input").addEventListener("keydown", (e) => { if (e.key === "Enter") askSubmit(); });
  $$(".ask-mode", host).forEach((b) => (b.onclick = () => {
    if (STATE.askMode === b.dataset.mode) return;
    const prev = $("#ask-input")?.value || "";
    STATE.askMode = b.dataset.mode;
    renderAsk();
    if (prev) $("#ask-input").value = prev;
  }));
}

function renderAskSuggests() {
  const sw = $("#ask-suggests"); if (!sw) return;
  sw.innerHTML = "";
  if (STATE.askMode === "deep") {
    (STATE.demo.research || []).forEach((r) => { const s = el("button", "suggest", esc(r.q)); s.onclick = () => { $("#ask-input").value = r.q; research(); }; sw.append(s); });
  } else {
    const quick = ["How do I deploy the API?", "What is the password rotation policy?", "How is monitoring set up?", "How are database backups taken?"];
    quick.forEach((q) => { const s = el("button", "suggest", esc(q)); s.onclick = () => { $("#ask-input").value = q; ask(); }; sw.append(s); });
  }
}

function askSubmit() { if (STATE.askMode === "deep") research(); else ask(); }

function retrieve(query) {
  const q = query.toLowerCase().split(/\W+/).filter((w) => w.length > 2);
  let best = null, bestScore = 0, second = null;
  const scored = STATE.corpus.map((d) => {
    const text = (d.title + " " + d.body).toLowerCase();
    return { d, s: q.filter((w) => text.includes(w)).length };
  }).filter((x) => x.s > 0).sort((a, b) => b.s - a.s);
  if (scored[0]) { best = scored[0].d; bestScore = scored[0].s; }
  if (scored[1]) second = scored[1].d;
  return { best, second, bestScore };
}

function ask() {
  const query = $("#ask-input").value.trim(); if (!query) return;
  const out = $("#ask-answer");
  out.innerHTML = `<div class="answer"><div class="answer-body"><p class="ans-text"><span class="spinner"></span> checking knowledge trust…</p></div></div>`;
  setTimeout(() => renderAnswer(out, query), reduceMotion ? 0 : 650);
}

function renderAnswer(out, query) {
  const { best: doc, second } = retrieve(query);
  if (!doc) { out.innerHTML = `<div class="answer"><div class="answer-body"><p class="ans-text">No document in the knowledge base matches that question.</p></div></div>`; return; }
  const a = auditFor(doc.id);
  const trusted = a && a.status === "healthy" && (a.confidence ?? 0) >= 0.7;
  const snippet = doc.body.split(/(?<=[.!?])\s/).slice(0, 2).join(" ");
  const m = STATUS[a?.status] || STATUS.uncertain;
  const con = a?.contradictions?.[0];

  // "why" explanations
  const why = trusted
    ? `This document is audited <b>healthy</b> at ${Math.round((a.confidence) * 100)}% confidence, was reviewed recently, and no other document contradicts it.`
    : `This source is flagged <b>${esc(m.label)}</b> at ${Math.round((a?.confidence ?? 0) * 100)}% confidence${con ? `, and it conflicts with <code>${esc(con.other_doc)}</code>` : ""}. TruthKeeper withholds a confident answer until it's resolved.`;

  const conflictBlock = con ? `
    <h4>Conflicting source</h4>
    <div class="contradiction"><div class="vs"><code>${esc(doc.id)}</code> ⟷ <code>${esc(con.other_doc)}</code></div><p>${esc(con.explanation)}</p>${con.evidence ? `<blockquote>${esc(con.evidence)}</blockquote>` : ""}</div>` : "";

  const relatedIds = (STATE.demo.relationships || []).filter((r) => r.a === doc.id || r.b === doc.id).map((r) => r.a === doc.id ? r.b : r.a);
  const related = [...new Set(relatedIds)].slice(0, 4).map((id) => `<button class="chip-link" data-doc="${esc(id)}">${esc(titleOf(id))}</button>`).join("");

  out.innerHTML = `
    <div class="answer">
      <div class="trust-banner ${trusted ? "ok" : "warn"}">
        <span class="tb-ico" style="background:color-mix(in srgb, ${trusted ? "var(--green)" : "var(--red)"} 25%, transparent)">${trusted ? "✓" : "!"}</span>
        ${trusted ? "Verified answer — safe to trust" : "Answer withheld — source cannot be trusted"}
      </div>
      <div class="answer-body">
        <p class="ans-text">${trusted ? esc(snippet) : "TruthKeeper did not surface a confident answer because the best-matching source is not trustworthy."}</p>
        <div class="why ${trusted ? "ok" : "warn"}"><b>${trusted ? "Why do I trust this?" : "Why was this withheld?"}</b> ${why}</div>
        <h4>Source</h4>
        <div class="answer-src">${miniBadge(a?.status || "uncertain")} <code>${esc(doc.id)}</code> · updated ${esc(doc.last_updated || "—")} · ${teamsOf(doc.id).join(", ") || "unassigned"} <button class="chip-link" data-doc="${esc(doc.id)}">open</button></div>
        <h4>Evidence</h4><blockquote>${esc(snippet)}</blockquote>
        ${conflictBlock}
        ${related ? `<h4>Related knowledge</h4><div class="chip-row">${related}</div>` : ""}
      </div>
    </div>`;
  $$("[data-doc]", out).forEach((b) => (b.onclick = () => openDoc(b.dataset.doc)));
}

/* ============================================================
   RESEARCH & DECISION — "Deep research" mode of the Ask view
   ============================================================ */
function matchResearch(q) {
  const ql = q.toLowerCase();
  return (STATE.demo.research || []).find((r) => r.match.some((k) => ql.includes(k))) || null;
}

function research() {
  const q = $("#ask-input").value.trim(); if (!q) return;
  const out = $("#ask-answer");
  const scenario = matchResearch(q);
  const steps = ["Parsing the question", "Selecting relevant knowledge", "Reading sources", "Cross-checking claims", "Detecting conflicts & gaps", "Composing recommendation"];
  out.innerHTML = `<div class="research-progress" id="rs-prog"></div>`;
  const prog = $("#rs-prog");
  let i = 0;
  const tick = () => {
    if (i < steps.length) {
      const node = el("div", "rp-step", `<span class="rp-dot"></span> ${esc(steps[i])}`);
      prog.append(node);
      requestAnimationFrame(() => node.classList.add("done"));
      i++;
      setTimeout(tick, reduceMotion ? 0 : 420);
    } else {
      renderResearchResult(out, scenario || genericResearch(q), q);
    }
  };
  tick();
}

function genericResearch(q) {
  const { best, second } = retrieve(q);
  const docs = [best, second].filter(Boolean);
  if (!docs.length) return { recommendation: "No relevant knowledge found for this question.", sources: [], evidence: [], contradictions: [], gaps: ["No matching documents."], confidence: 0 };
  const sources = docs.map((d) => ({ id: d.id, status: auditFor(d.id)?.status || "uncertain", conf: auditFor(d.id)?.confidence ?? 0.5 }));
  const trusted = docs.find((d) => auditFor(d.id)?.status === "healthy") || docs[0];
  return {
    sources,
    evidence: docs.map((d) => ({ doc: d.id, text: d.body.split(/(?<=[.!?])\s/)[0] })),
    contradictions: [], gaps: trusted === docs[0] ? [] : ["No fully-trusted source matched — provisional."],
    recommendation: trusted.body.split(/(?<=[.!?])\s/).slice(0, 2).join(" "),
    confidence: Math.round((sources.reduce((s, x) => s + x.conf, 0) / sources.length) * 100) / 100,
  };
}

function renderResearchResult(out, d, q) {
  const sources = (d.sources || []).map((s) => `<div class="src-pill">${miniBadge(s.status)} <code>${esc(s.id)}</code> <b>${Math.round((s.conf || 0) * 100)}%</b></div>`).join("");
  const evidence = (d.evidence || []).map((e) => `<div class="ev-row"><code>${esc(e.doc)}</code><blockquote>${esc(e.text)}</blockquote></div>`).join("");
  const cons = (d.contradictions || []).length
    ? `<h4>Contradictions</h4>` + d.contradictions.map((c) => `<div class="contradiction"><div class="vs"><code>${esc(c.between[0])}</code> ⟷ <code>${esc(c.between[1])}</code></div><p>${esc(c.explanation)}</p></div>`).join("")
    : "";
  const gaps = (d.gaps || []).length ? `<h4>Knowledge gaps</h4><div class="evidence"><ul>${d.gaps.map((g) => `<li>${esc(g)}</li>`).join("")}</ul></div>` : "";
  const cmp = d.comparison ? `
    <h4>Comparison — ${esc(d.comparison.title)}</h4>
    <table class="cmp"><thead><tr><th></th><th>${esc(d.comparison.a)}</th><th>${esc(d.comparison.b)}</th></tr></thead>
    <tbody>${d.comparison.rows.map((r) => `<tr><td class="cmp-dim">${esc(r.dim)}</td><td>${esc(r.a)}</td><td class="cmp-win">${esc(r.b)}</td></tr>`).join("")}</tbody></table>` : "";
  const pct = Math.round((d.confidence || 0) * 100);
  const col = pct >= 75 ? "var(--green)" : pct >= 50 ? "var(--amber)" : "var(--red)";

  out.innerHTML = `
    <div class="research-result">
      <div class="rr-head">
        <div><div class="rr-q">${esc(q)}</div><div class="muted-sm">${(d.sources || []).length} sources examined · ${(d.contradictions || []).length} conflicts · ${(d.gaps || []).length} gaps</div></div>
        <div class="rr-conf"><div class="rr-conf-num" style="color:${col}">${pct}%</div><div class="muted-sm">confidence</div></div>
      </div>
      <div class="recommend"><div class="rec-badge">Recommendation</div><p>${esc(d.recommendation)}</p>${d.decision ? `<div class="rec-decide">Decision: <b>${esc(d.decision)}</b> <button class="btn btn-sm btn-primary" id="rs-adopt">Record decision</button></div>` : ""}</div>
      ${cmp}
      ${sources ? `<h4>Sources examined</h4><div class="src-row">${sources}</div>` : ""}
      ${evidence ? `<h4>Evidence</h4>${evidence}` : ""}
      ${cons}${gaps}
    </div>`;
  const adopt = $("#rs-adopt", out);
  if (adopt) adopt.onclick = () => { STATE.decisionLog.unshift({ doc_id: d.based_on || (d.sources?.[0]?.id ?? "—"), action: "accept", title: d.decision, who: "You", when: new Date().toISOString().slice(0, 10) }); toast("Decision recorded"); go("decisions"); };
}

/* ============================================================
   KNOWLEDGE — documents + findings + per-doc drawer
   ============================================================ */
function renderKnowledge() {
  const host = $("#view-knowledge");
  host.innerHTML = `
    <div class="tabs">
      <button class="tab ${STATE.kTab === "documents" ? "active" : ""}" data-tab="documents">Documents <span class="cnt">${STATE.corpus.length}</span></button>
      <button class="tab ${STATE.kTab === "findings" ? "active" : ""}" data-tab="findings">Findings <span class="cnt">${STATE.audits.filter((a) => a.status !== "healthy").length}</span></button>
    </div>
    <div id="k-body"></div>`;
  $$(".tab", host).forEach((t) => (t.onclick = () => { STATE.kTab = t.dataset.tab; renderKnowledge(); }));
  if (STATE.kTab === "documents") renderDocTable($("#k-body")); else renderFindings($("#k-body"));
}

function renderDocTable(host) {
  host.innerHTML = `<div class="doc-table" id="doc-table">
    <div class="doc-row head"><span>Document</span><span class="d-updated">Updated</span><span>Owner</span><span>Status</span><span style="text-align:right">Trust</span></div></div>`;
  const table = $("#doc-table");
  STATE.corpus.forEach((d) => {
    const a = auditFor(d.id); const m = STATUS[a?.status] || STATUS.uncertain;
    const row = el("div", "doc-row", `
      <div><div class="d-title">${esc(d.title)}</div><div class="d-src">${esc(d.source || d.id)}</div></div>
      <span class="d-updated d-src">${esc(d.last_updated || "—")}</span>
      <span class="d-src">${teamsOf(d.id).join(", ") || "—"}</span>
      ${miniBadge(a?.status || "uncertain")}
      <span class="d-conf" style="color:${m.color}">${a ? Math.round((a.confidence ?? 0) * 100) + "%" : "—"}</span>`);
    row.onclick = () => openDoc(d.id);
    table.append(row);
  });
}

function renderFindings(host) {
  const counts = {}; for (const a of STATE.audits) counts[a.status] = (counts[a.status] || 0) + 1;
  host.innerHTML = `<div class="filters" id="filters"></div><div class="grid" id="report-grid"></div>`;
  const filters = $("#filters");
  const mk = (key, label, color) => {
    const chip = el("button", "chip" + (STATE.filter === key ? " active" : ""));
    if (color) { const sw = el("span", "swatch"); sw.style.background = color; chip.append(sw); }
    chip.append(document.createTextNode(label));
    chip.append(el("span", "cnt", String(key === "all" ? STATE.audits.length : counts[key] || 0)));
    chip.onclick = () => { STATE.filter = key; renderFindings(host); };
    return chip;
  };
  filters.append(mk("all", "All", null));
  SEVERITY.forEach((s) => { if (counts[s]) filters.append(mk(s, STATUS[s].label, STATUS[s].color)); });
  const grid = $("#report-grid");
  const items = STATE.audits.filter((a) => STATE.filter === "all" || a.status === STATE.filter);
  if (!items.length) { grid.append(el("div", "empty", "Nothing in this category.")); return; }
  const io = new IntersectionObserver((es, obs) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); obs.unobserve(e.target); } }), { threshold: 0.1 });
  items.forEach((a, i) => { const n = card(a); n.style.animationDelay = `${Math.min(i * 0.06, 0.5)}s`; grid.append(n); reduceMotion ? n.classList.add("in") : io.observe(n); });
}

function card(a) {
  const m = STATUS[a.status] || STATUS.uncertain;
  const c = el("article", `card sev-${a.status}`); c.id = "card-" + a.doc_id;
  c.append(el("div", "glare"));
  const head = el("div", "card-head");
  head.append(el("div", "card-title", `<h3>${esc(a.title || a.doc_id)}</h3><span class="doc-id">${esc(a.doc_id)}</span>`), ring(a.confidence, m.color));
  c.append(head);
  c.append(el("div", "badge", `<span class="bdot"></span>${m.label}`));
  if (a.contradictions?.length) {
    c.append(el("h4", null, "Contradictions"));
    a.contradictions.forEach((x) => {
      const quote = x.evidence ? `<blockquote>${esc(x.evidence)}</blockquote>` : "";
      c.append(el("div", "contradiction", `<div class="vs"><span class="tag">conflicts with</span> <code>${esc(x.other_doc)}</code></div><p>${esc(x.explanation)}</p>${quote}`));
    });
  }
  if (a.evidence?.length) {
    c.append(el("h4", null, "Evidence"));
    const box = el("div", "evidence"), ul = el("ul");
    a.evidence.forEach((e) => ul.append(el("li", null, esc(e)))); box.append(ul); c.append(box);
  }
  if (a.suggested_fix) c.append(el("div", "fix", `<h4>Suggested fix</h4><p>${esc(a.suggested_fix)}</p>`));
  if (a.status !== "healthy") {
    const acts = el("div", "card-acts");
    const bOpen = el("button", "btn btn-sm btn-ghost", "Inspect");
    const bRemy = el("button", "btn btn-sm btn-primary", "Remediate");
    bOpen.onclick = () => openDoc(a.doc_id);
    bRemy.onclick = () => { ensureRemediation(a.doc_id); go("actions"); };
    acts.append(bOpen, bRemy); c.append(acts);
  }
  c.append(el("div", "card-foot", `<span>${new Date(a.created_at || Date.now()).toLocaleDateString()}</span><span class="chipmodel">${esc(a.model_used || "—")}</span>`));
  attachTilt(c);
  return c;
}

/* ---------- document drawer ---------- */
function openDrawer(html) { const d = $("#drawer"); $("#drawer-body").innerHTML = html; d.classList.add("open"); $("#scrim").classList.add("show"); d.setAttribute("aria-hidden", "false"); }
function closeDrawer() { $("#drawer").classList.remove("open"); $("#scrim").classList.remove("show"); $("#drawer").setAttribute("aria-hidden", "true"); }

function openDoc(id, tab = "overview") {
  const d = docFor(id); const a = auditFor(id);
  if (!d && !a) return;
  const m = STATUS[a?.status] || STATUS.uncertain;
  const rels = (STATE.demo.relationships || []).filter((r) => r.a === id || r.b === id);
  const hist = STATE.demo.history?.[id] || [{ v: "v1", date: d?.last_updated || "—", note: "Current version" }];

  const tabBtn = (key, label) => `<button class="dtab ${tab === key ? "active" : ""}" data-dtab="${key}">${label}</button>`;
  let body = "";
  if (tab === "overview") {
    body = `
      <p class="drawer-text">${esc(d?.body || "")}</p>
      <div class="kv"><span>Status</span>${miniBadge(a?.status || "uncertain")}</div>
      <div class="kv"><span>Confidence</span><b style="color:${m.color}">${Math.round((a?.confidence ?? 0) * 100)}%</b></div>
      <div class="kv"><span>Owner teams</span><span>${teamsOf(id).join(", ") || "unassigned"}</span></div>
      <div class="kv"><span>Last updated</span><span>${esc(d?.last_updated || "—")}</span></div>
      ${a?.suggested_fix ? `<div class="fix"><h4>Suggested fix</h4><p>${esc(a.suggested_fix)}</p></div>` : ""}`;
  } else if (tab === "evidence") {
    body = (a?.evidence?.length || a?.contradictions?.length)
      ? `${(a.contradictions || []).map((c) => `<div class="contradiction"><div class="vs"><span class="tag">conflicts with</span> <code>${esc(c.other_doc)}</code></div><p>${esc(c.explanation)}</p>${c.evidence ? `<blockquote>${esc(c.evidence)}</blockquote>` : ""}</div>`).join("")}${a.evidence?.length ? `<div class="evidence"><ul>${a.evidence.map((e) => `<li>${esc(e)}</li>`).join("")}</ul></div>` : ""}`
      : `<p class="muted-sm">No issues found — this document is healthy.</p>`;
  } else if (tab === "relationships") {
    body = rels.length
      ? rels.map((r) => { const other = r.a === id ? r.b : r.a; return `<div class="rel-row"><span class="rel-type" style="--c:${REL[r.type]}">${r.type}</span><button class="chip-link" data-doc="${esc(other)}">${esc(titleOf(other))}</button></div>`; }).join("")
      : `<p class="muted-sm">No relationships recorded.</p>`;
  } else if (tab === "history") {
    body = `<div class="timeline">${hist.map((h) => `<div class="tl-item"><span class="tl-dot"></span><div><div class="tr-title">${esc(h.v)} · ${esc(h.date)}</div><div class="tr-sub">${esc(h.note)}</div></div></div>`).join("")}</div>`;
  }

  openDrawer(`
    <div class="drawer-head">
      <div><div class="muted-sm">${esc(d?.source || id)}</div><h2>${esc(d?.title || id)}</h2></div>
      <button class="icon-btn" id="drawer-close" aria-label="Close">✕</button>
    </div>
    <div class="drawer-actions">
      <button class="btn btn-sm btn-ghost" data-act="verify">Verify</button>
      <button class="btn btn-sm btn-ghost" data-act="audit">Re-audit</button>
      <button class="btn btn-sm btn-ghost" data-act="compare">Compare</button>
      ${a && a.status !== "healthy" ? `<button class="btn btn-sm btn-primary" data-act="fix">Generate fix</button>` : ""}
    </div>
    <div id="verify-slot"></div>
    <div class="dtabs">${tabBtn("overview", "Overview")}${tabBtn("evidence", "Evidence")}${tabBtn("relationships", "Relationships")}${tabBtn("history", "History")}</div>
    <div class="dtab-body">${body}</div>`);

  $("#drawer-close").onclick = closeDrawer;
  $$(".dtab", $("#drawer")).forEach((b) => (b.onclick = () => openDoc(id, b.dataset.dtab)));
  $$("[data-doc]", $("#drawer")).forEach((b) => (b.onclick = () => openDoc(b.dataset.doc)));
  $$("[data-act]", $("#drawer")).forEach((b) => (b.onclick = () => docAction(b.dataset.act, id)));
}

function docAction(act, id) {
  const a = auditFor(id);
  if (act === "verify") {
    const trusted = a && a.status === "healthy" && (a.confidence ?? 0) >= 0.7;
    $("#verify-slot").innerHTML = `<div class="verify-chip ${trusted ? "ok" : "warn"}">${trusted ? "✓ Verified — safe to trust" : `✕ Not trusted — ${STATUS[a?.status]?.label || "unknown"} (${Math.round((a?.confidence ?? 0) * 100)}%)`}</div>`;
  } else if (act === "audit") {
    $("#verify-slot").innerHTML = `<div class="verify-chip"><span class="spinner"></span> re-auditing with Gemini…</div>`;
    setTimeout(() => docAction("verify", id), reduceMotion ? 0 : 1100);
  } else if (act === "compare") {
    const con = a?.contradictions?.[0]?.other_doc;
    openCompare(id, con || STATE.corpus.find((d) => d.id !== id)?.id);
  } else if (act === "fix") {
    ensureRemediation(id); closeDrawer(); go("actions");
  }
}

function openCompare(aId, bId) {
  const A = docFor(aId), B = docFor(bId);
  const conflict = auditFor(aId)?.contradictions?.find((c) => c.other_doc === bId) || auditFor(bId)?.contradictions?.find((c) => c.other_doc === aId);
  openDrawer(`
    <div class="drawer-head"><h2>Compare documents</h2><button class="icon-btn" id="drawer-close">✕</button></div>
    ${conflict ? `<div class="verify-chip warn">⚠ These documents contradict each other</div><p class="muted-sm">${esc(conflict.explanation)}</p>` : `<div class="verify-chip ok">No direct contradiction detected</div>`}
    <div class="compare">
      <div class="cmp-col"><div class="cmp-head">${miniBadge(auditFor(aId)?.status || "uncertain")} <code>${esc(aId)}</code></div><p>${esc(A?.body || "")}</p></div>
      <div class="cmp-col"><div class="cmp-head">${miniBadge(auditFor(bId)?.status || "uncertain")} <code>${esc(bId)}</code></div><p>${esc(B?.body || "")}</p></div>
    </div>`);
  $("#drawer-close").onclick = closeDrawer;
}

/* ============================================================
   KNOWLEDGE GRAPH — with inspector
   ============================================================ */
let graphRAF = null;
function renderGraph() {
  const host = $("#view-graph");
  host.innerHTML = `
    <div class="graph-layout">
      <div class="graph-wrap">
        <canvas id="graph-canvas"></canvas>
        <div class="graph-legend">
          <div class="lg"><i style="background:${REL.contradiction}"></i>Contradiction</div>
          <div class="lg"><i style="background:${REL.reference}"></i>Reference</div>
          <div class="lg"><i style="background:${REL.dependency}"></i>Dependency</div>
        </div>
        <div class="graph-hint">drag nodes · click to inspect</div>
      </div>
      <aside class="graph-inspector" id="graph-inspector">
        <div class="gi-empty">Select a node to inspect its contradictions, dependencies and risk.</div>
      </aside>
    </div>`;
  startGraph();
}

function graphModel() {
  const nodes = STATE.corpus.map((d) => ({ id: d.id, status: auditFor(d.id)?.status || "uncertain", conf: auditFor(d.id)?.confidence ?? 0.5 }));
  const ids = new Set(nodes.map((n) => n.id));
  const edges = [];
  (STATE.demo.relationships || []).forEach((r) => { if (ids.has(r.a) && ids.has(r.b)) edges.push({ a: r.a, b: r.b, type: r.type }); });
  // ensure audit contradictions are present
  STATE.audits.forEach((au) => (au.contradictions || []).forEach((c) => {
    if (ids.has(au.doc_id) && ids.has(c.other_doc) && !edges.some((e) => (e.a === au.doc_id && e.b === c.other_doc) || (e.a === c.other_doc && e.b === au.doc_id))) edges.push({ a: au.doc_id, b: c.other_doc, type: "contradiction" });
  }));
  return { nodes, edges };
}

function startGraph() {
  const canvas = $("#graph-canvas"); if (!canvas) return;
  const ctx = canvas.getContext("2d"); const wrap = canvas.parentElement;
  let W, H;
  const size = () => { W = canvas.width = wrap.clientWidth; H = canvas.height = wrap.clientHeight; };
  size(); window.addEventListener("resize", size);
  const model = graphModel();
  const nodes = model.nodes.map((n, i) => ({ ...n, x: W / 2 + Math.cos(i) * 150 + (Math.random() - 0.5) * 50, y: H / 2 + Math.sin(i) * 150 + (Math.random() - 0.5) * 50, vx: 0, vy: 0, r: 8 + (1 - n.conf) * 10 }));
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const edges = model.edges.map((e) => ({ ...e, A: byId[e.a], B: byId[e.b] })).filter((e) => e.A && e.B);

  let drag = null, hover = null, selected = null;
  const pos = (e) => { const r = canvas.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; };
  canvas.onpointerdown = (e) => { const p = pos(e); drag = nodes.find((n) => Math.hypot(n.x - p.x, n.y - p.y) < n.r + 6) || null; if (drag) canvas.setPointerCapture(e.pointerId); };
  canvas.onpointermove = (e) => { const p = pos(e); if (drag) { drag.x = p.x; drag.y = p.y; drag.vx = drag.vy = 0; } else { hover = nodes.find((n) => Math.hypot(n.x - p.x, n.y - p.y) < n.r + 6) || null; canvas.style.cursor = hover ? "pointer" : "grab"; } };
  canvas.onpointerup = (e) => { const p = pos(e); const hit = nodes.find((n) => Math.hypot(n.x - p.x, n.y - p.y) < n.r + 6); if (hit && drag === hit) { selected = hit; inspectNode(hit.id); } drag = null; };

  function step() {
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      for (let j = i + 1; j < nodes.length; j++) {
        const mm = nodes[j]; let dx = n.x - mm.x, dy = n.y - mm.y, dd = Math.hypot(dx, dy) || 1;
        const f = 1500 / (dd * dd), ux = dx / dd, uy = dy / dd;
        n.vx += ux * f; n.vy += uy * f; mm.vx -= ux * f; mm.vy -= uy * f;
      }
      n.vx += (W / 2 - n.x) * 0.0016; n.vy += (H / 2 - n.y) * 0.0016;
    }
    edges.forEach((e) => { let dx = e.B.x - e.A.x, dy = e.B.y - e.A.y, dd = Math.hypot(dx, dy) || 1, f = (dd - 140) * 0.01, ux = dx / dd, uy = dy / dd; e.A.vx += ux * f; e.A.vy += uy * f; e.B.vx -= ux * f; e.B.vy -= uy * f; });
    nodes.forEach((n) => { if (n === drag) return; n.vx *= 0.82; n.vy *= 0.82; n.x += n.vx; n.y += n.vy; n.x = Math.max(n.r, Math.min(W - n.r, n.x)); n.y = Math.max(n.r, Math.min(H - n.r, n.y)); });
  }
  function draw() {
    ctx.clearRect(0, 0, W, H);
    edges.forEach((e) => { ctx.strokeStyle = REL[e.type] || "#889"; ctx.globalAlpha = 0.55; ctx.lineWidth = e.type === "contradiction" ? 2.2 : 1.3; ctx.shadowColor = REL[e.type]; ctx.shadowBlur = e.type === "contradiction" ? 8 : 0; ctx.beginPath(); ctx.moveTo(e.A.x, e.A.y); ctx.lineTo(e.B.x, e.B.y); ctx.stroke(); ctx.shadowBlur = 0; ctx.globalAlpha = 1; });
    nodes.forEach((n) => {
      const hex = STATUS[n.status].hex;
      ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2); ctx.fillStyle = hex;
      ctx.shadowColor = hex; ctx.shadowBlur = (n === hover || n === selected) ? 22 : 10; ctx.fill(); ctx.shadowBlur = 0;
      if (n === selected) { ctx.strokeStyle = "#fff"; ctx.lineWidth = 2; ctx.stroke(); }
      if (n === hover || n === selected || n.r > 14) { ctx.fillStyle = "rgba(234,240,255,0.9)"; ctx.font = "600 11px Inter, sans-serif"; ctx.textAlign = "center"; ctx.fillText(n.id, n.x, n.y + n.r + 13); }
    });
  }
  function loop() { if (!reduceMotion) step(); draw(); graphRAF = requestAnimationFrame(loop); }
  cancelAnimationFrame(graphRAF); loop();
}
function stopGraph() { if (graphRAF) cancelAnimationFrame(graphRAF); graphRAF = null; }

function inspectNode(id) {
  const ins = $("#graph-inspector"); if (!ins) return;
  const a = auditFor(id); const d = docFor(id); const m = STATUS[a?.status] || STATUS.uncertain;
  const rels = (STATE.demo.relationships || []).filter((r) => r.a === id || r.b === id);
  const group = (type) => rels.filter((r) => r.type === type).map((r) => { const o = r.a === id ? r.b : r.a; return `<button class="chip-link" data-doc="${esc(o)}">${esc(titleOf(o))}</button>`; }).join("") || `<span class="muted-sm">none</span>`;
  const risk = a?.status === "contradictory" ? "High" : a?.status === "deprecated" ? "Medium" : a?.status === "stale" ? "Medium" : "Low";
  const riskCol = risk === "High" ? "var(--red)" : risk === "Medium" ? "var(--amber)" : "var(--green)";
  ins.innerHTML = `
    <div class="gi-head"><div><div class="muted-sm">${esc(d?.source || id)}</div><h3>${esc(d?.title || id)}</h3></div></div>
    <div class="kv"><span>Status</span>${miniBadge(a?.status || "uncertain")}</div>
    <div class="kv"><span>Risk</span><b style="color:${riskCol}">${risk}</b></div>
    <div class="kv"><span>Owner</span><span>${teamsOf(id).join(", ") || "—"}</span></div>
    <h4>Contradictions</h4><div class="chip-row">${group("contradiction")}</div>
    <h4>Dependencies</h4><div class="chip-row">${group("dependency")}</div>
    <h4>References</h4><div class="chip-row">${group("reference")}</div>
    <div class="gi-actions"><button class="btn btn-sm btn-ghost" data-open="${esc(id)}">Open document</button>${a && a.status !== "healthy" ? `<button class="btn btn-sm btn-primary" data-impact="${esc(id)}">Impact</button>` : ""}</div>`;
  $$("[data-doc]", ins).forEach((b) => (b.onclick = () => openDoc(b.dataset.doc)));
  $$("[data-open]", ins).forEach((b) => (b.onclick = () => openDoc(b.dataset.open)));
  $$("[data-impact]", ins).forEach((b) => (b.onclick = () => { STATE.impactTarget = b.dataset.impact; go("actions"); }));
}

/* ============================================================
   DECISIONS — approval log
   ============================================================ */
function renderDecisions() {
  const host = $("#view-decisions");
  const pending = STATE.remediation.filter((r) => r.step >= 2 && r.step < 3);
  host.innerHTML = `
    <div class="section-head"><h2>Decision log</h2><p>Every human decision TruthKeeper recorded — accepted fixes, dismissals and research calls.</p></div>
    ${pending.length ? `<div class="panel"><div class="panel-head"><h3>Pending approvals</h3><span class="ni-badge">${pending.length}</span></div><div id="dec-pending"></div></div>` : ""}
    <div class="panel"><div class="panel-head"><h3>History</h3></div><div id="dec-log"></div></div>`;
  if (pending.length) {
    const p = $("#dec-pending");
    pending.forEach((r) => {
      const row = el("div", "toprisk", `<span class="tr-dot" style="background:var(--amber)"></span><div><div class="tr-title">${esc(r.title)}</div><div class="tr-sub">awaiting approval · ${esc(r.doc_id)}</div></div>`);
      const btn = el("button", "btn btn-sm btn-primary", "Review"); btn.onclick = () => { STATE.openRem = r.id; go("actions"); };
      row.append(btn); p.append(row);
    });
  }
  const log = $("#dec-log");
  if (!STATE.decisionLog.length) { log.append(el("div", "empty", "No decisions yet. Accept a fix or record a research decision.")); return; }
  STATE.decisionLog.forEach((dcn) => {
    const icon = dcn.action === "accept" ? "✓" : "✕";
    const col = dcn.action === "accept" ? "var(--green)" : "var(--muted)";
    log.append(el("div", "dec-row", `
      <span class="dec-ic" style="color:${col};border-color:${col}">${icon}</span>
      <div><div class="tr-title">${esc(dcn.title || dcn.doc_id)}</div><div class="tr-sub">${esc(dcn.doc_id)} · ${dcn.action === "accept" ? "approved" : "dismissed"}</div></div>
      <div class="dec-meta"><div>${esc(dcn.who || "—")}</div><div class="muted-sm">${esc(dcn.when || "")}</div></div>`));
  });
}

/* ============================================================
   ACTIONS — remediation workflow + impact analysis
   ============================================================ */
function ensureRemediation(docId) {
  if (STATE.remediation.some((r) => r.doc_id === docId)) return;
  const a = auditFor(docId); const d = docFor(docId);
  STATE.remediation.unshift({
    id: "rem-" + docId, doc_id: docId, title: a?.suggested_fix ? `${d?.title}: ${a.suggested_fix.slice(0, 48)}…` : `Review ${d?.title}`,
    severity: a?.status === "contradictory" ? "high" : "medium", step: 0,
    problem: a?.contradictions?.[0]?.explanation || a?.suggested_fix || "Flagged by audit.",
    before: (d?.body || "").slice(0, 160) + "…", after: a?.suggested_fix || "Reviewed and corrected.",
  });
  updateNavBadges();
}

function renderActions() {
  const host = $("#view-actions");
  host.innerHTML = `
    <div class="tabs">
      <button class="tab active" data-atab="remediation">Remediation <span class="cnt">${STATE.remediation.filter((r) => r.step < 4).length}</span></button>
      <button class="tab" data-atab="impact">Impact Analysis</button>
    </div>
    <div id="a-body"></div>`;
  $$(".tab", host).forEach((t) => (t.onclick = () => { $$(".tab", host).forEach((x) => x.classList.remove("active")); t.classList.add("active"); t.dataset.atab === "impact" ? renderImpactTool($("#a-body")) : renderRemediation($("#a-body")); }));
  if (STATE.impactTarget) { $$(".tab", host)[1].click(); } else renderRemediation($("#a-body"));
}

function renderRemediation(host) {
  host.innerHTML = `<div class="section-head"><h2>Remediation workflow</h2><p>Fix a knowledge problem end-to-end — with a human approving before anything is published.</p></div><div class="rem-list" id="rem-list"></div>`;
  const list = $("#rem-list");
  if (!STATE.remediation.length) { list.append(el("div", "empty", "No remediation items. Flag a finding to start one.")); return; }
  STATE.remediation.forEach((r) => list.append(remediationCard(r)));
  if (STATE.openRem) { const c = $("#rem-" + CSS.escape(STATE.openRem)); if (c) c.scrollIntoView({ behavior: "smooth", block: "center" }); STATE.openRem = null; }
}

function remediationCard(r) {
  const sevCol = r.severity === "high" ? "var(--red)" : "var(--amber)";
  const c = el("article", "rem-card"); c.id = "rem-" + r.id;
  const stepper = REM_STEPS.map((s, i) => `<div class="rstep ${i <= r.step ? "on" : ""} ${i === r.step ? "cur" : ""}"><span class="rstep-dot">${i < r.step ? "✓" : i + 1}</span><span class="rstep-label">${s}</span></div>`).join("<div class='rstep-line'></div>");
  let panel = "";
  if (r.step === 0) panel = `<p class="rem-problem">${esc(r.problem)}</p><button class="btn btn-sm btn-primary" data-adv="${r.id}">Suggest correction →</button>`;
  else if (r.step === 1) panel = `<div class="fix"><h4>Suggested correction (Gemini)</h4><p>${esc(r.after)}</p></div><button class="btn btn-sm btn-primary" data-adv="${r.id}">Preview changes →</button>`;
  else if (r.step === 2) panel = `<div class="diff"><div class="diff-col before"><div class="diff-h">− current</div><p>${esc(r.before)}</p></div><div class="diff-col after"><div class="diff-h">+ proposed</div><p>${esc(r.after)}</p></div></div><div class="fix-actions"><button class="btn btn-sm btn-primary" data-approve="${r.id}">Approve &amp; apply</button><button class="btn btn-sm btn-ghost" data-reject="${r.id}">Dismiss</button></div>`;
  else if (r.step === 3) panel = `<div class="verify-chip ok">✓ Approved — applying…</div>`;
  else panel = `<div class="verify-chip ok">✓ Completed — document corrected &amp; re-verified</div>`;
  c.innerHTML = `
    <div class="rem-head"><span class="rem-sev" style="background:${sevCol}"></span><div><div class="tr-title">${esc(r.title)}</div><div class="tr-sub">${esc(r.doc_id)} · ${r.severity} severity</div></div></div>
    <div class="stepper">${stepper}</div>
    <div class="rem-panel">${panel}</div>`;
  c.querySelectorAll("[data-adv]").forEach((b) => (b.onclick = () => { r.step = Math.min(4, r.step + 1); renderActions(); }));
  c.querySelectorAll("[data-approve]").forEach((b) => (b.onclick = () => approveRemediation(r)));
  c.querySelectorAll("[data-reject]").forEach((b) => (b.onclick = () => { STATE.decisionLog.unshift({ doc_id: r.doc_id, action: "dismiss", title: r.title, who: "You", when: new Date().toISOString().slice(0, 10) }); STATE.remediation = STATE.remediation.filter((x) => x.id !== r.id); updateNavBadges(); toast("Dismissed"); renderActions(); }));
  return c;
}

function approveRemediation(r) {
  r.step = 3; renderActions();
  STATE.decisionLog.unshift({ doc_id: r.doc_id, action: "accept", title: r.title, who: "You", when: new Date().toISOString().slice(0, 10) });
  const au = auditFor(r.doc_id);
  setTimeout(() => {
    r.step = 4;
    if (au) { au.status = "healthy"; au.confidence = 0.92; au.contradictions = []; au.model_used = "remediated"; }
    STATE.audits.sort((a, b) => (a.confidence ?? 1) - (b.confidence ?? 1));
    updateNavBadges(); toast("Fix applied — document re-verified"); renderActions();
  }, reduceMotion ? 0 : 1400);
}

function renderImpactTool(host) {
  const flagged = STATE.audits.filter((a) => a.status !== "healthy");
  const target = STATE.impactTarget || flagged[0]?.doc_id;
  STATE.impactTarget = null;
  host.innerHTML = `
    <div class="section-head"><h2>Impact Analysis</h2><p>See what breaks if a document changes or a tool is deprecated — before you touch it.</p></div>
    <div class="impact-pick"><label>Analyze impact of a change to:</label><select id="impact-sel" class="ask-input">${STATE.corpus.map((d) => `<option value="${esc(d.id)}" ${d.id === target ? "selected" : ""}>${esc(d.title)}</option>`).join("")}</select><button class="btn btn-primary btn-sm" id="impact-run">Analyze</button></div>
    <div id="impact-out"></div>`;
  const run = () => showImpact($("#impact-sel").value, $("#impact-out"));
  $("#impact-run").onclick = run;
  if (target) run();
}

function computeImpact(id) {
  if (STATE.demo.impact?.[id]) return STATE.demo.impact[id];
  const affectedDocs = [];
  (auditFor(id)?.contradictions || []).forEach((c) => affectedDocs.push({ id: c.other_doc, reason: c.explanation }));
  (STATE.demo.relationships || []).filter((r) => r.a === id || r.b === id).forEach((r) => { const o = r.a === id ? r.b : r.a; if (!affectedDocs.some((x) => x.id === o)) affectedDocs.push({ id: o, reason: `Linked via ${r.type}.` }); });
  const procs = (STATE.demo.processes || []).filter((p) => p.docs.includes(id)).map((p) => ({ name: p.name, status: p.status }));
  const teams = [...new Set([id, ...affectedDocs.map((x) => x.id)].flatMap((x) => teamsOf(x)))];
  const st = auditFor(id)?.status;
  return { risk: st === "contradictory" ? "high" : st === "healthy" ? "low" : "medium", affectedDocs, processes: procs, teams, related: [], actions: ["Review affected documents", "Notify owner teams", "Re-audit after the change"] };
}

function showImpact(id, out) {
  out.innerHTML = `<div class="verify-chip"><span class="spinner"></span> tracing impact across knowledge…</div>`;
  setTimeout(() => {
    const d = computeImpact(id);
    const riskCol = d.risk === "high" ? "var(--red)" : d.risk === "medium" ? "var(--amber)" : "var(--green)";
    const docs = (d.affectedDocs || []).map((x) => `<div class="act-item"><span class="act-rel" style="--c:var(--red)">affected</span><div><div class="act-title">${esc(titleOf(x.id))} <span class="doc-id">${esc(x.id)}</span></div><div class="act-reason">${esc(x.reason)}</div></div></div>`).join("");
    const procs = (d.processes || []).map((p) => `<span class="pill-tag" style="--c:${p.status === "at-risk" ? "var(--red)" : "var(--amber)"}">${esc(p.name)}</span>`).join("");
    const teams = (d.teams || []).map((t) => `<span class="pill-tag" style="--c:var(--cyan)">${esc(t)}</span>`).join("");
    const actions = (d.actions || []).map((x) => `<li>${esc(x)}</li>`).join("");
    out.innerHTML = `
      <div class="impact-grid">
        <div class="impact-risk" style="--c:${riskCol}"><div class="muted-sm">Risk level</div><div class="risk-big" style="color:${riskCol}">${d.risk.toUpperCase()}</div></div>
        <div class="panel"><div class="panel-head"><h3>Affected processes</h3></div><div class="chip-row">${procs || "<span class='muted-sm'>none</span>"}</div><div class="panel-head" style="margin-top:14px"><h3>Affected teams</h3></div><div class="chip-row">${teams || "<span class='muted-sm'>none</span>"}</div></div>
      </div>
      <div class="panel"><div class="panel-head"><h3>Affected documents</h3></div>${docs || "<span class='muted-sm'>No other documents affected.</span>"}</div>
      <div class="panel"><div class="panel-head"><h3>Recommended actions</h3></div><ol class="act-steps">${actions}</ol><button class="btn btn-sm btn-primary" id="impact-fix">Start remediation</button></div>`;
    const fix = $("#impact-fix", out); if (fix) fix.onclick = () => { ensureRemediation(id); go("actions"); };
  }, reduceMotion ? 0 : 700);
}

/* ============================================================
   SETTINGS
   ============================================================ */
function renderSettings() {
  const host = $("#view-settings");
  host.innerHTML = `
    <div class="section-head"><h2>Settings</h2><p>Point the dashboard at your deployed backend. Blank = offline demo mode (current).</p></div>
    <div class="settings-wrap">
      <div class="field"><label>Cloud Run backend URL</label><input id="set-url" placeholder="https://truthkeeper-api-xxxx-uc.a.run.app" value="${esc(API)}" /><div class="hint">The dashboard calls <code>GET /report</code> here. Blank = offline demo data.</div></div>
      <div class="field"><label>Audit token (optional)</label><input id="set-token" placeholder="only if backend enforces AUDIT_TOKEN" value="${esc(TOKEN)}" /></div>
      <div style="display:flex;gap:10px"><button class="btn btn-primary" id="set-save"><span class="btn-glow"></span><span class="btn-label">Save &amp; reconnect</span></button><button class="btn btn-ghost" id="set-test">Test connection</button></div>
      <div class="conn-row" id="conn-row"></div>
    </div>`;
  $("#set-save").onclick = () => { API = $("#set-url").value.trim().replace(/\/$/, ""); TOKEN = $("#set-token").value.trim(); localStorage.setItem("tk_CLOUD_RUN_URL", API); localStorage.setItem("tk_AUDIT_TOKEN", TOKEN); toast("Saved — reconnecting"); loadData(); };
  $("#set-test").onclick = async () => {
    const row = $("#conn-row"), url = $("#set-url").value.trim().replace(/\/$/, "");
    if (!url) { row.innerHTML = `<span class="conn-dot" style="background:var(--amber)"></span> No URL — using offline demo data`; return; }
    row.innerHTML = `<span class="spinner"></span> testing…`;
    try { const r = await fetch(`${url}/healthz`); row.innerHTML = `<span class="conn-dot" style="background:${r.ok ? "var(--green)" : "var(--red)"}"></span> ${r.ok ? "Connected — backend healthy" : "Reachable but unhealthy"}`; }
    catch { row.innerHTML = `<span class="conn-dot" style="background:var(--red)"></span> Could not reach backend`; }
  };
}

/* ============================================================
   ADD & MANAGE DOCUMENTS — upload / create / delete
   ============================================================ */
function renderManage() {
  const host = $("#view-manage");
  host.innerHTML = `
    <div class="manage-grid">
      <div class="panel reveal">
        <div class="panel-head"><h3>Add a document</h3></div>
        <div class="dropzone" id="dropzone" role="button" tabindex="0">
          <svg viewBox="0 0 24 24" class="dz-ic"><path d="M12 15V4"/><path d="m8 8 4-4 4 4"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/></svg>
          <div class="dz-main">Drop a .txt or .md file here</div>
          <div class="dz-sub">or click to browse — it fills the form below</div>
          <input type="file" id="dz-file" accept=".txt,.md,.markdown,text/plain,text/markdown" hidden />
        </div>
        <div class="field"><label>Title</label><input id="m-title" placeholder="e.g. How to Deploy the Northwind API" /></div>
        <div class="field"><label>Path / source</label><input id="m-source" placeholder="e.g. wiki/engineering/deployment-guide" /></div>
        <div class="field"><label>Owner team(s)</label><input id="m-owner" placeholder="comma-separated — e.g. Platform, SRE" /></div>
        <div class="field"><label>Last updated</label><input id="m-updated" type="date" /></div>
        <div class="field"><label>Content</label><textarea id="m-body" rows="7" placeholder="Paste or write the document content…"></textarea></div>
        <div class="form-actions"><button class="btn btn-primary" id="m-add"><span class="btn-glow"></span><span class="btn-label">Add &amp; audit</span></button><button class="btn btn-ghost" id="m-clear">Clear</button></div>
      </div>
      <div class="panel reveal">
        <div class="panel-head"><h3>Manage documents</h3><span class="muted-sm" id="m-count"></span></div>
        <div id="m-list"></div>
      </div>
    </div>`;

  const dz = $("#dropzone"), file = $("#dz-file");
  dz.onclick = () => file.click();
  dz.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); file.click(); } };
  file.onchange = () => { if (file.files[0]) readDocFile(file.files[0]); };
  ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("drag"); }));
  ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("drag"); }));
  dz.addEventListener("drop", (e) => { const f = e.dataTransfer?.files?.[0]; if (f) readDocFile(f); });

  $("#m-add").onclick = submitDoc;
  $("#m-clear").onclick = () => ["m-title", "m-source", "m-owner", "m-updated", "m-body"].forEach((id) => ($("#" + id).value = ""));
  renderManageList();
}

function readDocFile(f) {
  const r = new FileReader();
  r.onload = () => {
    $("#m-body").value = String(r.result || "");
    if (!$("#m-title").value) $("#m-title").value = f.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    if (!$("#m-source").value) $("#m-source").value = "upload/" + f.name;
    toast("File loaded — review and add");
  };
  r.readAsText(f);
}

function submitDoc() {
  const title = $("#m-title").value.trim();
  const body = $("#m-body").value.trim();
  if (!title || !body) { toast("Title and content are required"); return; }
  const id = slugify($("#m-source").value.trim() || title);
  if (STATE.corpus.some((d) => d.id === id)) { toast("A document with that path already exists"); return; }
  const owner = $("#m-owner").value.split(",").map((s) => s.trim()).filter(Boolean);
  const doc = {
    id, title,
    source: $("#m-source").value.trim() || id,
    body,
    last_updated: $("#m-updated").value || new Date().toISOString().slice(0, 10),
    owner,
  };
  addUserDoc(doc);
}

function addUserDoc(doc) {
  const docs = loadUserDocs(); docs.push(doc); saveUserDocs(docs);
  STATE.corpus.push({ id: doc.id, title: doc.title, source: doc.source, body: doc.body, last_updated: doc.last_updated });
  if (doc.owner?.length) STATE.demo.teams[doc.id] = doc.owner;
  const audit = heuristicAudit(doc);
  STATE.audits.push(audit);
  STATE.audits.sort((a, b) => (a.confidence ?? 1) - (b.confidence ?? 1));
  updateNavBadges();

  const overlay = $("#scan-overlay"), sub = $("#scan-sub");
  overlay.classList.add("on"); sub.textContent = "auditing new document…";
  setTimeout(() => {
    overlay.classList.remove("on");
    toast(`Added — audited ${STATUS[audit.status].label}`);
    renderManage();
    openDoc(doc.id);
  }, reduceMotion ? 0 : 1300);
}

function deleteUserDoc(id) {
  saveUserDocs(loadUserDocs().filter((d) => d.id !== id));
  STATE.corpus = STATE.corpus.filter((d) => d.id !== id);
  STATE.audits = STATE.audits.filter((a) => a.doc_id !== id);
  if (STATE.demo.teams) delete STATE.demo.teams[id];
  updateNavBadges();
  toast("Document deleted");
  renderManage();
}

function renderManageList() {
  const list = $("#m-list"); if (!list) return;
  const mine = new Set(loadUserDocs().map((d) => d.id));
  $("#m-count").textContent = `${STATE.corpus.length} total · ${mine.size} added by you`;
  list.innerHTML = "";
  STATE.corpus.forEach((d) => {
    const a = auditFor(d.id);
    const row = el("div", "manage-row", `
      <div class="mr-main"><div class="d-title">${esc(d.title)}${mine.has(d.id) ? `<span class="mr-tag">added</span>` : ""}</div><div class="d-src">${esc(d.source || d.id)}</div></div>
      ${miniBadge(a?.status || "uncertain")}
      <div class="mr-actions"><button class="btn btn-sm btn-ghost mr-open">Open</button>${mine.has(d.id) ? `<button class="btn btn-sm btn-ghost mr-del">Delete</button>` : ""}</div>`);
    row.querySelector(".mr-open").onclick = () => openDoc(d.id);
    const del = row.querySelector(".mr-del");
    if (del) del.onclick = () => deleteUserDoc(d.id);
    list.append(row);
  });
}

/* ============================================================
   Router
   ============================================================ */
const RENDER = { overview: renderOverview, ask: renderAsk, knowledge: renderKnowledge, graph: renderGraph, manage: renderManage, decisions: renderDecisions, actions: renderActions, settings: renderSettings };
function renderView(name) {
  if (name !== "graph") stopGraph();
  $$(".view").forEach((v) => v.classList.remove("active"));
  $("#view-" + name)?.classList.add("active");
  $$(".nav-item").forEach((n) => n.classList.toggle("active", n.dataset.view === name));
  const meta = VIEWS[name] || VIEWS.overview;
  $("#view-title").textContent = meta.title; $("#view-sub").textContent = meta.sub;
  (RENDER[name] || renderOverview)();
  requestAnimationFrame(() => $$("#view-" + name + " .reveal").forEach((r, i) => setTimeout(() => r.classList.add("in"), i * 60)));
  closeSidebar();
}
function go(name) { STATE.view = name; location.hash = "#/" + name; }
function route() {
  let name = (location.hash.replace(/^#\//, "") || "overview");
  if (name === "research") { STATE.askMode = "deep"; name = "ask"; }  // legacy link → Deep research
  STATE.view = RENDER[name] ? name : "overview";
  renderView(STATE.view);
}

/* ---------- tilt ---------- */
function attachTilt(node) {
  if (reduceMotion) return;
  node.addEventListener("pointermove", (e) => { const r = node.getBoundingClientRect(), px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height; node.style.transform = `perspective(900px) rotateY(${(px - 0.5) * 5}deg) rotateX(${(0.5 - py) * 5}deg) translateY(-3px)`; node.style.setProperty("--mx", px * 100 + "%"); node.style.setProperty("--my", py * 100 + "%"); });
  node.addEventListener("pointerleave", () => (node.style.transform = ""));
}

/* ---------- Run Audit ---------- */
const SCAN_STEPS = ["booting auditor…", "loading knowledge base…", "cross-referencing claims with Gemini…", "scoring confidence per document…", "detecting contradictions…", "ranking the Rot Report…"];
let scanTimer = null;
async function runAudit() {
  const overlay = $("#scan-overlay"), sub = $("#scan-sub"); overlay.classList.add("on"); let i = 0; sub.textContent = SCAN_STEPS[0];
  scanTimer = setInterval(() => { i = (i + 1) % SCAN_STEPS.length; sub.textContent = SCAN_STEPS[i]; }, 650);
  const btn = $("#run-audit"); btn.disabled = true;
  try {
    if (API && !STATE.isDemo) { const r = await fetch(`${API}/audit`, { method: "POST", headers: TOKEN ? { "X-Audit-Token": TOKEN } : {} }); if (!r.ok) throw new Error("audit"); await new Promise((res) => setTimeout(res, 1100)); await loadData(); }
    else { await new Promise((res) => setTimeout(res, 2300)); renderView(STATE.view); }
    toast("Audit complete");
  } catch { toast("Showing cached report"); }
  finally { clearInterval(scanTimer); overlay.classList.remove("on"); btn.disabled = false; }
}

/* ---------- background is CSS-only now (clean, no canvas animation) ---------- */

/* ---------- sidebar (mobile) ---------- */
function openSidebar() { $("#sidebar").classList.add("open"); $("#scrim").classList.add("show"); }
function closeSidebar() { $("#sidebar").classList.remove("open"); if (!$("#drawer").classList.contains("open")) $("#scrim").classList.remove("show"); }

/* ---------- init ---------- */
document.addEventListener("DOMContentLoaded", () => {
  $("#run-audit").addEventListener("click", runAudit);
  $("#menu-toggle").addEventListener("click", openSidebar);
  $("#scrim").addEventListener("click", () => { closeDrawer(); closeSidebar(); });
  window.addEventListener("hashchange", route);
  window.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDrawer(); });
  if (!location.hash) location.hash = "#/overview";
  loadData().then(route);
});
