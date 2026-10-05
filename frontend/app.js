"use strict";

const API = window.CONFIG.CLOUD_RUN_URL.replace(/\/$/, "");

const STATUS_META = {
  contradictory: { label: "Contradictory", cls: "s-contradictory" },
  deprecated:    { label: "Deprecated",    cls: "s-deprecated" },
  stale:         { label: "Stale",         cls: "s-stale" },
  uncertain:     { label: "Uncertain",     cls: "s-uncertain" },
  healthy:       { label: "Healthy",       cls: "s-healthy" },
};

function confidenceClass(c) {
  if (c < 0.4) return "conf-low";
  if (c < 0.7) return "conf-mid";
  return "conf-high";
}

function el(tag, cls, html) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (html !== undefined) node.innerHTML = html;
  return node;
}

function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function renderSummary(audits) {
  const counts = audits.reduce((acc, a) => {
    acc[a.status] = (acc[a.status] || 0) + 1;
    return acc;
  }, {});
  const flagged = audits.filter((a) => a.status !== "healthy").length;

  const summary = document.getElementById("summary");
  summary.innerHTML = "";
  summary.append(
    el("div", "stat", `<span class="stat-num">${audits.length}</span><span class="stat-label">docs audited</span>`),
    el("div", "stat stat-flag", `<span class="stat-num">${flagged}</span><span class="stat-label">flagged</span>`)
  );
  for (const [status, meta] of Object.entries(STATUS_META)) {
    if (status === "healthy") continue;
    const n = counts[status] || 0;
    if (n) summary.append(el("div", "stat", `<span class="stat-num">${n}</span><span class="stat-label">${meta.label.toLowerCase()}</span>`));
  }
}

function renderCard(a) {
  const meta = STATUS_META[a.status] || STATUS_META.uncertain;
  const card = el("article", `card ${meta.cls}`);

  const pct = Math.round((a.confidence ?? 0) * 100);
  card.append(el("div", "card-head", `
    <div class="card-title">
      <h3>${escapeHtml(a.title || a.doc_id)}</h3>
      <code class="doc-id">${escapeHtml(a.doc_id)}</code>
    </div>
    <div class="card-meta">
      <span class="badge ${meta.cls}">${meta.label}</span>
      <span class="confidence ${confidenceClass(a.confidence ?? 0)}" title="confidence">${pct}%</span>
    </div>
  `));

  if (Array.isArray(a.contradictions) && a.contradictions.length) {
    const box = el("div", "contradictions");
    box.append(el("h4", null, "Contradictions"));
    for (const c of a.contradictions) {
      box.append(el("div", "contradiction", `
        <div class="vs">vs <code>${escapeHtml(c.other_doc)}</code></div>
        <p>${escapeHtml(c.explanation)}</p>
        ${c.evidence ? `<blockquote>${escapeHtml(c.evidence)}</blockquote>` : ""}
      `));
    }
    card.append(box);
  }

  if (Array.isArray(a.evidence) && a.evidence.length) {
    const box = el("div", "evidence");
    box.append(el("h4", null, "Evidence"));
    const ul = el("ul");
    for (const e of a.evidence) ul.append(el("li", null, escapeHtml(e)));
    box.append(ul);
    card.append(box);
  }

  if (a.suggested_fix) {
    card.append(el("div", "fix", `<h4>Suggested fix</h4><p>${escapeHtml(a.suggested_fix)}</p>`));
  }

  card.append(el("div", "card-foot", `model: ${escapeHtml(a.model_used || "—")}`));
  return card;
}

function renderReport(audits) {
  const report = document.getElementById("report");
  report.innerHTML = "";
  if (!audits.length) {
    report.append(el("div", "loading", "No audits cached yet. Click “Run Audit”."));
    return;
  }
  // Already sorted worst-first by the API; sort defensively anyway.
  audits.sort((a, b) => (a.confidence ?? 1) - (b.confidence ?? 1));
  for (const a of audits) report.append(renderCard(a));
}

async function loadReport() {
  const loading = document.getElementById("loading");
  if (loading) loading.textContent = "Loading Rot Report…";
  try {
    const res = await fetch(`${API}/report`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    document.getElementById("cache-badge").hidden = false; // read from cache
    renderSummary(data.audits || []);
    renderReport(data.audits || []);
  } catch (err) {
    const report = document.getElementById("report");
    report.innerHTML = "";
    report.append(el("div", "error", `Could not load report: ${escapeHtml(err.message)}.<br>Is the backend URL set in config.js?`));
  }
}

async function runAudit() {
  const btn = document.getElementById("run-audit");
  btn.disabled = true;
  btn.textContent = "Auditing…";
  try {
    const res = await fetch(`${API}/audit`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await loadReport();
  } catch (err) {
    alert(`Audit failed: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = "Run Audit";
  }
}

document.getElementById("run-audit").addEventListener("click", runAudit);
loadReport();
