/* Offline demo data — mirrors the Northwind seed corpus audit results so the
   UI shows every animation even before the backend is deployed. The app uses
   this ONLY when GET /report is unreachable or empty. */
window.SAMPLE_AUDITS = [
  {
    doc_id: "deployment-guide",
    title: "How to Deploy the Northwind API",
    confidence: 0.14,
    status: "contradictory",
    contradictions: [
      {
        other_doc: "cicd-pipeline",
        explanation:
          "This guide says to deploy manually with ./deploy.sh to Heroku, but the CI/CD standards doc states deploy.sh was removed in 2025 and all deploys now go to Cloud Run via GitHub Actions. Manual deploys are explicitly forbidden.",
        evidence: "run ./deploy.sh from the repo root … pushes it directly to our Heroku dynos",
      },
    ],
    evidence: ["run ./deploy.sh from the repo root", "pushes it directly to our Heroku dynos"],
    suggested_fix:
      "Rewrite to point at the GitHub Actions → Cloud Run pipeline and remove all deploy.sh / Heroku instructions.",
    model_used: "gemini-pro",
    created_at: "2026-10-05T12:00:00+00:00",
  },
  {
    doc_id: "password-policy",
    title: "Password Policy",
    confidence: 0.22,
    status: "contradictory",
    contradictions: [
      {
        other_doc: "security-standards-2025",
        explanation:
          "Mandates 90-day password rotation, directly contradicting the 2025 security standards which disable forced expiry per updated NIST SP 800-63B guidance.",
        evidence: "must rotate their account passwords every 90 days",
      },
    ],
    evidence: ["rotate their account passwords every 90 days"],
    suggested_fix: "Supersede with security-standards-2025: remove the 90-day rotation rule.",
    model_used: "gemini-flash",
    created_at: "2026-10-05T12:00:00+00:00",
  },
  {
    doc_id: "monitoring-setup",
    title: "Monitoring and Alerting Setup",
    confidence: 0.31,
    status: "deprecated",
    contradictions: [],
    evidence: ["We monitor all services using Stackdriver", "the Nagios box at nagios.corp.internal"],
    suggested_fix: "Stackdriver is now Cloud Monitoring; the Nagios box is decommissioned. Update references.",
    model_used: "gemini-flash",
    created_at: "2026-10-05T12:00:00+00:00",
  },
  {
    doc_id: "vpn-access",
    title: "Connecting to the Corporate VPN",
    confidence: 0.36,
    status: "stale",
    contradictions: [],
    evidence: ["last_updated 2021-03-02", "Cisco AnyConnect to vpn.oldcorp.net"],
    suggested_fix: "Last updated 2021 and references a retired VPN host. Verify against current remote-access tooling.",
    model_used: "heuristic",
    created_at: "2026-10-05T12:00:00+00:00",
  },
  {
    doc_id: "database-backup",
    title: "Database Backup Procedure",
    confidence: 0.4,
    status: "stale",
    contradictions: [],
    evidence: ["last_updated 2021-11-09", "mysqldump … copies the archive to the on-prem NAS"],
    suggested_fix: "2021 procedure using on-prem NAS; confirm it matches current managed-backup practice.",
    model_used: "heuristic",
    created_at: "2026-10-05T12:00:00+00:00",
  },
  {
    doc_id: "cicd-pipeline",
    title: "CI/CD Pipeline Standards",
    confidence: 0.52,
    status: "contradictory",
    contradictions: [
      {
        other_doc: "deployment-guide",
        explanation: "Contradicted by the deployment guide, which still documents the removed deploy.sh/Heroku flow.",
        evidence: "the legacy deploy.sh script was removed in 2025 and must never be used",
      },
    ],
    evidence: ["deployments go through GitHub Actions", "deploys it to Cloud Run automatically"],
    suggested_fix: "Accurate — but add a banner linking the outdated deployment-guide for cleanup.",
    model_used: "gemini-flash",
    created_at: "2026-10-05T12:00:00+00:00",
  },
  { doc_id: "onboarding-checklist", title: "New Engineer Onboarding Checklist", confidence: 0.93, status: "healthy", contradictions: [], evidence: [], suggested_fix: "", model_used: "gemini-flash", created_at: "2026-10-05T12:00:00+00:00" },
  { doc_id: "expense-policy", title: "Travel and Expense Policy", confidence: 0.95, status: "healthy", contradictions: [], evidence: [], suggested_fix: "", model_used: "gemini-flash", created_at: "2026-10-05T12:00:00+00:00" },
  { doc_id: "oncall-runbook", title: "On-Call Runbook", confidence: 0.94, status: "healthy", contradictions: [], evidence: [], suggested_fix: "", model_used: "gemini-flash", created_at: "2026-10-05T12:00:00+00:00" },
  { doc_id: "api-auth-guide", title: "API Authentication Guide", confidence: 0.96, status: "healthy", contradictions: [], evidence: [], suggested_fix: "", model_used: "gemini-flash", created_at: "2026-10-05T12:00:00+00:00" },
  { doc_id: "data-retention", title: "Data Retention Policy", confidence: 0.92, status: "healthy", contradictions: [], evidence: [], suggested_fix: "", model_used: "gemini-flash", created_at: "2026-10-05T12:00:00+00:00" },
  { doc_id: "code-review-guidelines", title: "Code Review Guidelines", confidence: 0.95, status: "healthy", contradictions: [], evidence: [], suggested_fix: "", model_used: "gemini-flash", created_at: "2026-10-05T12:00:00+00:00" },
  { doc_id: "incident-severity", title: "Incident Severity Guide", confidence: 0.93, status: "healthy", contradictions: [], evidence: [], suggested_fix: "", model_used: "gemini-flash", created_at: "2026-10-05T12:00:00+00:00" },
  { doc_id: "remote-work-policy", title: "Remote Work Policy", confidence: 0.91, status: "healthy", contradictions: [], evidence: [], suggested_fix: "", model_used: "gemini-flash", created_at: "2026-10-05T12:00:00+00:00" },
  { doc_id: "security-standards-2025", title: "Updated Security Standards (2025)", confidence: 0.9, status: "healthy", contradictions: [], evidence: [], suggested_fix: "", model_used: "gemini-flash", created_at: "2026-10-05T12:00:00+00:00" },
];
