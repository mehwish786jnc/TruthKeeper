/* Offline demo data — lets every view (Overview, Rot Report, Graph, Ask,
   Documents) work before the backend is deployed. Used ONLY when the API is
   unreachable. SAMPLE_AUDITS mirrors audit output; CORPUS mirrors the source docs. */

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

window.CORPUS = [
  { id: "deployment-guide", title: "How to Deploy the Northwind API", source: "wiki/engineering/deployment-guide", last_updated: "2022-03-14", body: "To deploy the Northwind API, run ./deploy.sh from the repo root. This script builds the app and pushes it directly to our Heroku dynos. Make sure you have the Heroku CLI installed and are logged in. Deployments typically take 3-4 minutes." },
  { id: "cicd-pipeline", title: "CI/CD Pipeline Standards", source: "wiki/engineering/cicd-pipeline", last_updated: "2026-08-30", body: "All deployments go through GitHub Actions. On merge to main, the workflow builds a container and deploys it to Cloud Run automatically. Manual deployment is forbidden: the legacy deploy.sh script was removed in 2025 and must never be used." },
  { id: "monitoring-setup", title: "Monitoring and Alerting Setup", source: "wiki/sre/monitoring-setup", last_updated: "2023-01-20", body: "We monitor all services using Stackdriver. Host-level checks run on the Nagios box at nagios.corp.internal. Alerts are routed to the #alerts channel." },
  { id: "vpn-access", title: "Connecting to the Corporate VPN", source: "wiki/it/vpn-access", last_updated: "2021-03-02", body: "To access internal systems from home, connect using Cisco AnyConnect to vpn.oldcorp.net. Use your LDAP credentials. The VPN is required for the internal Jenkins server and the staging database." },
  { id: "password-policy", title: "Password Policy", source: "wiki/security/password-policy", last_updated: "2022-06-11", body: "All employees must rotate their account passwords every 90 days. Passwords must be at least 10 characters and include a number and a symbol. Reusing any of your last 5 passwords is not allowed." },
  { id: "security-standards-2025", title: "Updated Security Standards (2025)", source: "wiki/security/security-standards-2025", last_updated: "2026-02-18", body: "Following updated NIST SP 800-63B guidance, Northwind no longer enforces periodic password rotation. Change a password only on evidence of compromise. Minimum 14 characters; passphrases and a hardware second factor are encouraged. Forced expiry is disabled." },
  { id: "onboarding-checklist", title: "New Engineer Onboarding Checklist", source: "wiki/people/onboarding-checklist", last_updated: "2026-07-05", body: "Week 1: get your laptop imaged, enable SSO and your second factor, request access to the engineering GitHub org. Week 2: pick up a good-first-issue and deploy a small change end to end." },
  { id: "expense-policy", title: "Travel and Expense Policy", source: "wiki/finance/expense-policy", last_updated: "2026-05-22", body: "Meals during business travel are reimbursable up to 60 USD per day. Flights should be booked in economy class. Submit receipts within 30 days through the expense portal." },
  { id: "oncall-runbook", title: "On-Call Runbook", source: "wiki/sre/oncall-runbook", last_updated: "2026-09-12", body: "The on-call engineer owns the pager for one week. Acknowledge pages within 5 minutes. For a production outage, open an incident channel and post status updates every 30 minutes." },
  { id: "api-auth-guide", title: "API Authentication Guide", source: "wiki/engineering/api-auth-guide", last_updated: "2026-06-01", body: "External clients authenticate using OAuth 2.0 client credentials. Access tokens expire after one hour; refresh using the token endpoint. All API traffic must use TLS 1.2 or higher." },
  { id: "data-retention", title: "Data Retention Policy", source: "wiki/legal/data-retention", last_updated: "2026-04-10", body: "Customer transaction records are retained for 7 years. Application logs are retained for 90 days. Personal data deletion requests are processed within 30 days." },
  { id: "code-review-guidelines", title: "Code Review Guidelines", source: "wiki/engineering/code-review-guidelines", last_updated: "2026-08-01", body: "Every pull request needs at least one approval before merge. Keep PRs under 400 lines where possible. CI must be green before merge; do not bypass required checks." },
  { id: "incident-severity", title: "Incident Severity Guide", source: "wiki/sre/incident-severity", last_updated: "2026-03-28", body: "SEV1: full outage or data loss affecting most customers; page immediately. SEV2: major feature broken. SEV3: minor issue with a workaround. SEV1 and SEV2 require a postmortem within five business days." },
  { id: "remote-work-policy", title: "Remote Work Policy", source: "wiki/people/remote-work-policy", last_updated: "2026-01-15", body: "Employees may work remotely up to three days per week. Core collaboration hours are 10:00 to 15:00 local time. Equipment stipends are available once per year." },
  { id: "database-backup", title: "Database Backup Procedure", source: "wiki/sre/database-backup", last_updated: "2021-11-09", body: "A nightly cron job runs mysqldump against the primary database and copies the archive to the on-prem NAS at nas.corp.internal. To restore, copy the dump from the NAS and pipe it into the mysql client." },
];

/* Rich demo data powering the full product experience (frontend-only). */
window.DEMO = {
  health: {
    score: 62, grade: "C", trustedPct: 60, stale: 2, deprecated: 1, contradictions: 2, criticalRisks: 2, gaps: 3,
    trend: [
      { m: "May", score: 48 }, { m: "Jun", score: 51 }, { m: "Jul", score: 55 },
      { m: "Aug", score: 58 }, { m: "Sep", score: 60 }, { m: "Oct", score: 62 },
    ],
    recentlyChanged: [
      { id: "oncall-runbook", title: "On-Call Runbook", when: "2026-09-12", change: "updated" },
      { id: "cicd-pipeline", title: "CI/CD Pipeline Standards", when: "2026-08-30", change: "updated" },
      { id: "code-review-guidelines", title: "Code Review Guidelines", when: "2026-08-01", change: "updated" },
      { id: "security-standards-2025", title: "Updated Security Standards (2025)", when: "2026-02-18", change: "added" },
    ],
  },
  gaps: [
    { area: "Disaster Recovery", description: "No documented DR / failover procedure for the primary database.", severity: "high" },
    { area: "Cloud Run rollback", description: "The current pipeline has no documented rollback steps.", severity: "medium" },
    { area: "Incident comms", description: "No customer-facing incident communication template.", severity: "medium" },
  ],
  teams: {
    "deployment-guide": ["Platform", "SRE"], "cicd-pipeline": ["Platform"], "password-policy": ["Security", "IT"],
    "security-standards-2025": ["Security"], "monitoring-setup": ["SRE"], "vpn-access": ["IT"],
    "database-backup": ["SRE", "Data"], "api-auth-guide": ["Platform"], "oncall-runbook": ["SRE"],
    "incident-severity": ["SRE"], "onboarding-checklist": ["People", "Platform"], "data-retention": ["Legal"],
    "expense-policy": ["Finance"], "remote-work-policy": ["People"], "code-review-guidelines": ["Platform"],
  },
  processes: [
    { id: "release", name: "Release & Deployment", docs: ["deployment-guide", "cicd-pipeline"], status: "at-risk" },
    { id: "access", name: "Access & Authentication", docs: ["password-policy", "security-standards-2025", "vpn-access", "api-auth-guide"], status: "at-risk" },
    { id: "observability", name: "Monitoring & Incident Response", docs: ["monitoring-setup", "oncall-runbook", "incident-severity"], status: "review" },
    { id: "data", name: "Data & Backups", docs: ["database-backup", "data-retention"], status: "review" },
    { id: "onboarding", name: "Engineer Onboarding", docs: ["onboarding-checklist", "code-review-guidelines"], status: "healthy" },
  ],
  relationships: [
    { a: "deployment-guide", b: "cicd-pipeline", type: "contradiction" },
    { a: "password-policy", b: "security-standards-2025", type: "contradiction" },
    { a: "onboarding-checklist", b: "deployment-guide", type: "reference" },
    { a: "onboarding-checklist", b: "security-standards-2025", type: "dependency" },
    { a: "oncall-runbook", b: "incident-severity", type: "dependency" },
    { a: "monitoring-setup", b: "oncall-runbook", type: "reference" },
    { a: "cicd-pipeline", b: "api-auth-guide", type: "reference" },
    { a: "vpn-access", b: "database-backup", type: "dependency" },
  ],
  history: {
    "deployment-guide": [
      { v: "v3", date: "2022-03-14", note: "Heroku deploy via deploy.sh" },
      { v: "v2", date: "2021-07-02", note: "Added rollback notes" },
      { v: "v1", date: "2020-11-10", note: "Initial version" },
    ],
    "password-policy": [
      { v: "v2", date: "2022-06-11", note: "90-day rotation introduced" },
      { v: "v1", date: "2019-01-05", note: "Initial policy" },
    ],
    "monitoring-setup": [
      { v: "v2", date: "2023-01-20", note: "Stackdriver + Nagios" },
      { v: "v1", date: "2020-05-01", note: "Initial setup" },
    ],
    "cicd-pipeline": [
      { v: "v4", date: "2026-08-30", note: "Cloud Run via GitHub Actions; deploy.sh removed" },
      { v: "v3", date: "2025-03-11", note: "Containerized builds" },
    ],
  },
  research: [
    {
      id: "deploy", q: "What is our current deployment process?",
      match: ["deploy", "deployment", "release", "ship", "cloud run", "heroku"],
      sources: [
        { id: "cicd-pipeline", status: "healthy", conf: 0.9 },
        { id: "deployment-guide", status: "contradictory", conf: 0.14 },
        { id: "onboarding-checklist", status: "healthy", conf: 0.93 },
        { id: "oncall-runbook", status: "healthy", conf: 0.94 },
      ],
      evidence: [
        { doc: "cicd-pipeline", text: "On merge to main, the workflow builds a container and deploys it to Cloud Run automatically. The legacy deploy.sh script was removed in 2025." },
        { doc: "deployment-guide", text: "run ./deploy.sh from the repo root ... pushes it directly to our Heroku dynos." },
      ],
      contradictions: [{ between: ["deployment-guide", "cicd-pipeline"], explanation: "Manual deploy.sh/Heroku vs automated GitHub Actions → Cloud Run." }],
      gaps: ["No documented Cloud Run rollback procedure."],
      comparison: {
        title: "deploy.sh → Heroku (old) vs GitHub Actions → Cloud Run (current)",
        a: "deploy.sh → Heroku", b: "GitHub Actions → Cloud Run",
        rows: [
          { dim: "Trigger", a: "Manual, from a laptop", b: "Automated on merge to main" },
          { dim: "Target", a: "Heroku dynos", b: "Google Cloud Run" },
          { dim: "Status", a: "Removed in 2025", b: "Current standard" },
          { dim: "Risk", a: "High — misleads new engineers", b: "Low" },
        ],
      },
      recommendation: "Standardize on the GitHub Actions → Cloud Run pipeline (cicd-pipeline). Retire deployment-guide — its deploy.sh/Heroku steps were removed in 2025 and now actively mislead engineers. Document a Cloud Run rollback procedure to close the one remaining gap.",
      confidence: 0.86, decision: "Adopt cicd-pipeline; retire deployment-guide",
    },
    {
      id: "password", q: "Should we enforce 90-day password rotation?",
      match: ["password", "rotation", "rotate", "credential", "login"],
      sources: [
        { id: "security-standards-2025", status: "healthy", conf: 0.9 },
        { id: "password-policy", status: "contradictory", conf: 0.22 },
      ],
      evidence: [
        { doc: "security-standards-2025", text: "Following updated NIST SP 800-63B guidance, Northwind no longer enforces periodic password rotation." },
        { doc: "password-policy", text: "All employees must rotate their account passwords every 90 days." },
      ],
      contradictions: [{ between: ["password-policy", "security-standards-2025"], explanation: "90-day rotation vs no forced rotation (NIST 2025)." }],
      gaps: [],
      comparison: {
        title: "90-day rotation (old) vs no scheduled rotation (2025)",
        a: "Rotate every 90 days", b: "No scheduled rotation",
        rows: [
          { dim: "Trigger", a: "Calendar (every 90 days)", b: "Only on evidence of compromise" },
          { dim: "Min length", a: "10 characters", b: "14 characters + passphrases" },
          { dim: "Guidance", a: "Pre-2020 practice", b: "NIST SP 800-63B (current)" },
          { dim: "Status", a: "Superseded", b: "Current standard" },
        ],
      },
      recommendation: "Do NOT enforce 90-day rotation. The 2025 security standards supersede the old policy per NIST SP 800-63B: require 14+ character passphrases and a hardware second factor, and change passwords only on evidence of compromise. Retire the rotation rule in password-policy.",
      confidence: 0.88, decision: "Drop scheduled rotation; adopt 2025 standard",
    },
    {
      id: "monitoring", q: "Should we move off Stackdriver?",
      match: ["monitor", "stackdriver", "nagios", "observability", "alert", "metrics"],
      sources: [
        { id: "monitoring-setup", status: "deprecated", conf: 0.31 },
        { id: "oncall-runbook", status: "healthy", conf: 0.94 },
        { id: "incident-severity", status: "healthy", conf: 0.93 },
      ],
      evidence: [
        { doc: "monitoring-setup", text: "We monitor all services using Stackdriver ... the Nagios box at nagios.corp.internal." },
      ],
      contradictions: [],
      gaps: ["No current owner listed for the monitoring stack."],
      comparison: {
        title: "Stackdriver + Nagios (old) vs Cloud Monitoring (current)",
        a: "Stackdriver + Nagios", b: "Google Cloud Monitoring",
        rows: [
          { dim: "Product", a: "Stackdriver (renamed)", b: "Cloud Monitoring" },
          { dim: "Host checks", a: "Nagios box (on-prem)", b: "Cloud Monitoring agent" },
          { dim: "Status", a: "Deprecated / decommissioned", b: "Current" },
          { dim: "Risk", a: "Medium — dead references", b: "Low" },
        ],
      },
      recommendation: "Yes — migrate the documentation to Google Cloud Monitoring. Stackdriver was renamed and the Nagios box is decommissioned, so monitoring-setup points at infrastructure that no longer exists. Update references and assign an owner.",
      confidence: 0.79, decision: "Migrate docs to Cloud Monitoring",
    },
  ],
  impact: {
    "deployment-guide": {
      risk: "high",
      affectedDocs: [
        { id: "onboarding-checklist", reason: "Tells new engineers to deploy a change — they would follow the wrong (removed) steps." },
        { id: "cicd-pipeline", reason: "Documents the correct pipeline; must be cross-linked as the source of truth." },
      ],
      processes: [{ name: "Release & Deployment", status: "at-risk" }, { name: "Engineer Onboarding", status: "healthy" }],
      teams: ["Platform", "SRE", "People"], related: ["oncall-runbook"],
      actions: ["Retire deploy.sh / Heroku instructions", "Point onboarding to the Cloud Run pipeline", "Document a rollback procedure"],
    },
    "api-auth-guide": {
      risk: "high",
      affectedDocs: [
        { id: "cicd-pipeline", reason: "Build/deploy steps assume the current auth flow for service-to-service calls." },
        { id: "onboarding-checklist", reason: "New engineers are pointed here for API access setup." },
      ],
      processes: [{ name: "Access & Authentication", status: "at-risk" }],
      teams: ["Platform", "Security"], related: ["password-policy", "security-standards-2025"],
      actions: ["Publish a migration guide to the new API", "Add a deprecation banner + sunset date", "Notify all consuming teams"],
    },
    "monitoring-setup": {
      risk: "medium",
      affectedDocs: [
        { id: "oncall-runbook", reason: "References the monitoring dashboards and alert routing." },
        { id: "incident-severity", reason: "Severity classification assumes current monitoring signals." },
      ],
      processes: [{ name: "Monitoring & Incident Response", status: "review" }],
      teams: ["SRE"], related: [],
      actions: ["Update references to Cloud Monitoring", "Remove the decommissioned Nagios box", "Re-audit after the edit"],
    },
  },
  remediation: [
    {
      id: "rem1", doc_id: "deployment-guide", title: "Deployment guide uses removed deploy.sh / Heroku",
      severity: "high", status: "detected",
      problem: "References deploy.sh and Heroku, both removed in 2025. Directly contradicts cicd-pipeline.",
      before: "To deploy the Northwind API, run ./deploy.sh from the repo root. This script builds the app and pushes it directly to our Heroku dynos.",
      after: "To deploy the Northwind API, merge your change to main. GitHub Actions builds a container and deploys it to Cloud Run automatically. Manual deploys and deploy.sh are not permitted.",
    },
    {
      id: "rem2", doc_id: "password-policy", title: "Password policy mandates retired 90-day rotation",
      severity: "high", status: "detected",
      problem: "Requires 90-day rotation; superseded by security-standards-2025 (no forced rotation, NIST 2025).",
      before: "All employees must rotate their account passwords every 90 days. Passwords must be at least 10 characters.",
      after: "Passwords are not rotated on a schedule — change only on evidence of compromise. Minimum 14 characters; passphrases and a hardware second factor are strongly encouraged.",
    },
    {
      id: "rem3", doc_id: "monitoring-setup", title: "Monitoring references deprecated Stackdriver / Nagios",
      severity: "medium", status: "detected",
      problem: "Stackdriver was renamed to Cloud Monitoring; the Nagios box is decommissioned.",
      before: "We monitor all services using Stackdriver. Host-level checks run on the Nagios box at nagios.corp.internal.",
      after: "We monitor all services using Google Cloud Monitoring. Host-level checks run via the Cloud Monitoring agent. The Nagios box has been decommissioned.",
    },
  ],
  decisionLog: [
    { doc_id: "data-retention", action: "accept", title: "Confirmed 7-year retention is current", who: "A. Okafor", when: "2026-09-28" },
  ],
};

