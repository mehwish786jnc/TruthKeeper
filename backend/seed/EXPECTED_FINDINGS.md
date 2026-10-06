# Expected audit findings (for testing — do not feed to the model)

- CONTRADICTION A: `deployment-guide` (use deploy.sh → Heroku) vs
  `cicd-pipeline` (deploy.sh removed, deployments go to Cloud Run via GitHub Actions).
- CONTRADICTION B: `password-policy` (rotate every 90 days) vs
  `security-standards-2025` (no forced rotation per NIST). The 2025 doc supersedes.
- DEPRECATED: `monitoring-setup` references "Stackdriver" (renamed Cloud Monitoring)
  and a Nagios box (legacy/decommissioned).
- STALE: `vpn-access` (2021, Cisco AnyConnect / vpn.oldcorp.net) and
  `database-backup` (2021, mysqldump → on-prem NAS).
- The remaining ~8 docs are HEALTHY and should score high confidence.

Demo "aha": `deployment-guide` looks perfectly fine on its own — it's only
flagged because it CONTRADICTS `cicd-pipeline`. Keyword search never catches this.
