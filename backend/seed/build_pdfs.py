"""Build physical PDF documents from the seed corpus.

Build-time only: renders each document into a real multi-page PDF at
seed/pdfs/<id>.pdf. Long-form body content comes from seed/content.py
(lightweight markdown); if a doc has no long-form entry it falls back to
the short body in seed/corpus.json. Planted audit findings are preserved
verbatim. reportlab is NOT a runtime dependency of the app.

Run from the backend/ dir:  python -m seed.build_pdfs
"""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from seed.content import LONG_BODIES

SEED_DIR = Path(__file__).parent
CORPUS_PATH = SEED_DIR / "corpus.json"
PDF_DIR = SEED_DIR / "pdfs"

# Owner teams per doc (from the frontend DEMO.teams map).
OWNERS = {
    "deployment-guide": "Platform, SRE",
    "cicd-pipeline": "Platform",
    "monitoring-setup": "SRE",
    "vpn-access": "IT",
    "password-policy": "Security, IT",
    "security-standards-2025": "Security",
    "onboarding-checklist": "People, Platform",
    "expense-policy": "Finance",
    "oncall-runbook": "SRE",
    "api-auth-guide": "Platform",
    "data-retention": "Legal",
    "code-review-guidelines": "Platform",
    "incident-severity": "SRE",
    "remote-work-policy": "People",
    "database-backup": "SRE, Data",
}


def _esc(text: str) -> str:
    """Escape characters special to reportlab's mini-HTML paragraph markup."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=22, leading=26, spaceAfter=4, alignment=TA_LEFT,
        ),
        "meta": ParagraphStyle(
            "DocMeta", parent=base["Normal"], fontName="Helvetica",
            fontSize=9, leading=13, textColor="#6b7280", spaceAfter=16,
        ),
        "h2": ParagraphStyle(
            "DocH2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=15, leading=19, spaceBefore=24, spaceAfter=10, textColor="#111827",
        ),
        "h3": ParagraphStyle(
            "DocH3", parent=base["Heading3"], fontName="Helvetica-Bold",
            fontSize=12.5, leading=16, spaceBefore=14, spaceAfter=6, textColor="#374151",
        ),
        "body": ParagraphStyle(
            "DocBody", parent=base["Normal"], fontName="Helvetica",
            fontSize=12.5, leading=23, spaceAfter=16,
        ),
        "bullet": ParagraphStyle(
            "DocBullet", parent=base["Normal"], fontName="Helvetica",
            fontSize=12.5, leading=22, leftIndent=18, bulletIndent=5, spaceAfter=11,
        ),
    }


def _render_markdown(md: str, st) -> list:
    """Turn lightweight markdown into reportlab flowables.

    Consecutive non-blank text lines are joined into a single flowing
    paragraph (blank line or a heading/bullet ends the paragraph).
    """
    flow = []
    buf: list[str] = []

    def flush():
        if buf:
            flow.append(Paragraph(_esc(" ".join(buf)), st["body"]))
            buf.clear()

    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith("## "):
            flush()
            flow.append(Paragraph(_esc(line[3:]), st["h2"]))
        elif line.startswith("### "):
            flush()
            flow.append(Paragraph(_esc(line[4:]), st["h3"]))
        elif line.startswith("- "):
            flush()
            flow.append(Paragraph(_esc(line[2:]), st["bullet"], bulletText="•"))
        else:
            buf.append(line)
    flush()
    return flow


def build_pdf(doc: dict, st) -> Path:
    out = PDF_DIR / f"{doc['id']}.pdf"
    pdf = SimpleDocTemplate(
        str(out), pagesize=LETTER,
        topMargin=1.2 * inch, bottomMargin=1.2 * inch,
        leftMargin=1.25 * inch, rightMargin=1.25 * inch,
        title=doc["title"], author="Northwind Knowledge Base",
    )
    owner = OWNERS.get(doc["id"], "Unassigned")
    meta = (f"{_esc(doc.get('source', doc['id']))} &nbsp;&middot;&nbsp; "
            f"Updated {_esc(doc.get('last_updated', '—'))} &nbsp;&middot;&nbsp; "
            f"Owner: {_esc(owner)}")
    flow = [Paragraph(_esc(doc["title"]), st["title"]), Paragraph(meta, st["meta"]), Spacer(1, 2)]

    body_md = LONG_BODIES.get(doc["id"])
    if body_md:
        flow += _render_markdown(body_md, st)
    else:
        for para in doc["body"].split("\n"):
            if para.strip():
                flow.append(Paragraph(_esc(para.strip()), st["body"]))
    pdf.build(flow)
    return out


def main() -> int:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    st = _styles()
    written = [build_pdf(doc, st) for doc in corpus]
    missing = [d["id"] for d in corpus if d["id"] not in LONG_BODIES]
    print(f"Built {len(written)} PDFs in {PDF_DIR}")
    if missing:
        print(f"  (short-body fallback used for: {', '.join(missing)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
