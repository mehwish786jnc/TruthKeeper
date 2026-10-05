# Expected Findings (Ground Truth)

> **Do NOT feed this file to the model.** It exists only to verify that
> TruthKeeper independently rediscovers these planted issues, and to drive the
> demo narration.

The seed corpus (`corpus.json`) contains **15 docs** with **5 planted findings**.
The rest are healthy filler.

## 1. Contradiction — Deployment (the "aha")
- **Docs:** `deployment-guide` ⟷ `cicd-pipeline`
- **Conflict:** `deployment-guide` says deploys are **manual via `deploy.sh` to Heroku**;
  `cicd-pipeline` says deploys are **fully automated via GitHub Actions to Cloud Run**
  and explicitly states "there is no Heroku in our stack."
- **Why it matters:** `deployment-guide` *looks* fine on its own — keyword search would
  never flag it. It's wrong only *because another doc contradicts it*. This is the demo
  centerpiece.
- **Expected status:** both `contradictory`; `deployment-guide` is the lower-confidence/
  more-stale of the pair.

## 2. Contradiction — Password rotation
- **Docs:** `password-policy` ⟷ `security-handbook`
- **Conflict:** `password-policy` mandates **90-day rotation**; `security-handbook` says
  rotation is **no longer required** (NIST-aligned) and is "explicitly discouraged."
- **Expected status:** both `contradictory`.

## 3. Deprecated references
- **Doc:** `monitoring-setup`
- **Issue:** relies on **Stackdriver** (renamed to Google Cloud Operations) and **Nagios**.
- **Expected status:** `deprecated`.

## 4. Stale — VPN access
- **Doc:** `vpn-access`
- **Issue:** last updated **2021**; "validated for the 2021 office network layout."
- **Expected status:** `stale`.

## 5. Stale — DB backup
- **Doc:** `db-backup`
- **Issue:** last updated **2021**; references **PostgreSQL 11** + on-prem NAS.
- **Expected status:** `stale`.

## Healthy filler (should NOT be flagged as contradictory/deprecated)
`onboarding`, `api-style-guide`, `incident-response`, `data-retention`,
`code-review`, `oncall-rotation`, `expense-policy`, `release-notes-process`

## Smoke-test assertion
`smoke_test.py` passes iff `deployment-guide` has `status == "contradictory"` and lists
`cicd-pipeline` in its contradictions.
