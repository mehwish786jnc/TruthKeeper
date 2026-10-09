"""Long-form body content for the 15 Northwind knowledge-base documents.

Each value is lightweight markdown rendered by seed/build_pdfs.py:
  "## "  -> section heading
  "### " -> subheading
  "- "   -> bullet item
  blank line separates blocks; everything else is a paragraph.

Target length: ~6 pages per rendered PDF.

Planted audit findings are embedded verbatim (do not alter these phrases):
  deployment-guide: "./deploy.sh", "Heroku dynos", "Heroku CLI"
  cicd-pipeline:    "deploy.sh ... removed in 2025", "GitHub Actions", "Cloud Run", "Manual deployment is forbidden"
  monitoring-setup: "Stackdriver", "Nagios box at nagios.corp.internal"
  vpn-access:       "Cisco AnyConnect to vpn.oldcorp.net", "Jenkins"
  password-policy:  "rotate ... every 90 days"
  security-standards-2025: "no longer enforces periodic password rotation", "NIST SP 800-63B", "Forced expiry has been disabled"
  database-backup:  "mysqldump", "on-prem NAS at nas.corp.internal"
"""

LONG_BODIES = {
    # ================================================================== #
    "deployment-guide": """
## Overview
This guide describes how to deploy the Northwind API to production. It is intended for
engineers on the Platform and SRE teams who are responsible for shipping changes to the
customer-facing service. Read it end to end before your first deploy, and keep it open the
first few times you run a release.

The Northwind API is the backbone of our order-management platform. A failed or partial
deploy can take down checkout for every customer, so the process below is deliberately
conservative: it favours predictability over speed. When in doubt, slow down.

## Audience and scope
This document covers deploying the Northwind API service only. It does not cover database
schema migrations, infrastructure changes, or front-end releases, each of which has its own
runbook. If your change touches more than the API service, coordinate with the owning teams
before you begin.

## Prerequisites
Before you can deploy, make sure your workstation is set up correctly.

- Install the Heroku CLI and log in with your corporate account. Deploys will not work
  without a valid Heroku session.
- Request "deployer" access to the Northwind pipeline from your team lead. Access is granted
  per person and reviewed quarterly.
- Clone the repository and confirm you can build it locally with the standard build task.
- Make sure you are on the main branch with a clean working tree. Never deploy from a
  feature branch.
- Confirm you have access to the production dashboards so you can watch the rollout.

### Access and permissions
Deployer access is tied to your corporate identity and your team membership. If you change
teams, your access is re-evaluated. Do not share credentials or run a deploy on behalf of
someone who lacks access; the audit trail must reflect who actually shipped the change.

## Pre-deploy checklist
Run through this list before every release. Skipping steps here is the most common cause of
failed deploys.

- The change has merged to main and the pull request is approved.
- All automated checks are green on the merge commit.
- You have read the change and understand its blast radius.
- There is no change freeze in effect for the current window.
- You have told the team you are about to deploy.

## Deploying a release
To deploy the Northwind API, run ./deploy.sh from the repo root. This script builds the app
and pushes it directly to our Heroku dynos. Make sure you have the Heroku CLI installed and
are logged in. Deployments typically take 3-4 minutes. If a deploy fails, re-run the script;
it is idempotent.

The script performs the following steps in order:

- Verifies that you are authenticated and that the working tree is clean.
- Builds a production bundle and runs the smoke test suite.
- Tags the release with the current timestamp and short commit hash.
- Pushes the build to the Heroku dynos and waits for the health check to pass.
- Prints the release URL and the rollback command for the previous release.

### Watching the rollout
Once the push completes, watch the dyno logs for at least five minutes. Look for a clean
boot, a successful database migration, and steady request latency. If error rates climb or
the health check flaps, roll back immediately rather than trying to debug in production.

### Deploy windows
Prefer to deploy during business hours when the team is around to help if something goes
wrong. Avoid deploying late in the day on a Friday or immediately before a holiday. High-risk
changes should be scheduled and announced in advance.

## Worked example
A typical release looks like this. You merge an approved pull request to main in the morning.
You announce in the team channel that you are deploying. You run the deploy script from a
clean checkout of main. The build runs the smoke tests, tags the release, and pushes to the
dynos. You watch the logs for five minutes, confirm the version endpoint reports your commit,
check the dashboards, and post a short note with the release tag. The whole process takes
under fifteen minutes including the watch window.

## Rollback
Every deploy prints the command needed to roll back to the previous release. Keep that
command handy during the rollout window. Rolling back restores the previous dyno slug and is
usually faster than rolling forward with a fix. After a rollback, open an incident so the
root cause is tracked and the bad release is not accidentally re-shipped.

### When to roll back
Roll back if error rates rise, latency degrades, the health check will not stay green, or a
migration fails. Do not try to debug a bad release live in production. Restore the previous
release first, then investigate with the pressure off.

## Post-deploy checklist
- Confirm the version endpoint reports the commit you just shipped.
- Check the dashboards for error rate, latency, and saturation.
- Post a short note in the team channel with the release tag and anything to watch.
- Close the deploy ticket and link the release notes.
- Update any status page entry if the change affects customers.

## Troubleshooting
If the build step fails, the problem is almost always a dirty working tree or a failing smoke
test; fix those locally and re-run. If the push to the dynos times out, check the platform
status page before retrying. If the health check never passes, roll back and investigate with
a fresh pair of eyes. When in doubt, prefer rolling back over leaving a degraded release in
production.

### Common mistakes
- Deploying from a feature branch instead of main.
- Skipping the watch window and walking away immediately.
- Ignoring a flapping health check and hoping it settles.
- Forgetting to announce the deploy, so nobody can help if it goes wrong.

## Frequently asked questions
How long should a deploy take? Three to four minutes for the push, plus a five-minute watch
window. If it is taking much longer, something is wrong.

Can I deploy two changes at once? Prefer one change per deploy so that if something breaks you
know exactly what caused it.

What if I am not sure the change is safe? Ask for a second opinion before you deploy. It is
always cheaper to delay than to recover from a bad release.

## Roles and responsibilities
The engineer running the deploy owns the rollout and the decision to roll back. The Platform
team owns the deploy tooling and the pipeline. The SRE team owns the production environment
and is the escalation point if a deploy causes an incident.

## Related documents
See the CI/CD Pipeline Standards for how changes are built and promoted, the On-Call Runbook
for what to do if a deploy causes an incident, and the Incident Severity Guide for how to
classify customer impact.
""",

    # ================================================================== #
    "cicd-pipeline": """
## Purpose
This document defines the standard continuous integration and continuous delivery (CI/CD)
process for all Northwind services. It is the single source of truth for how code moves from
a pull request to production. Every engineering team is expected to follow it.

The goals of the pipeline are safety, repeatability, and auditability. No change should reach
customers without passing automated checks, and every production change must be traceable to
a merged pull request and a green pipeline run.

## Principles
- Every change is reviewed and tested before it ships.
- The pipeline, not a person, performs deploys.
- What runs in production always matches a reviewed commit.
- Rollbacks are fast, boring, and always available.
- Secrets never live in the repository or in build logs.

## Pipeline stages
All deployments go through GitHub Actions. On merge to main, the workflow builds a container
and deploys it to Cloud Run automatically. The pipeline runs the following stages in order,
and a failure in any stage stops the release:

- Lint and static analysis on every pull request.
- Unit and integration tests, with coverage reported back to the pull request.
- Container build, tagged with the commit SHA and pushed to Artifact Registry.
- Automated deploy to the staging Cloud Run service.
- Smoke tests against staging.
- Promotion to the production Cloud Run service on merge to main.

### Pull request checks
Every pull request triggers the lint and test stages. The results are reported directly on
the pull request so reviewers can see them. A pull request cannot merge until all required
checks pass.

### Build and artifact storage
On merge, the pipeline builds a container image tagged with the commit SHA and pushes it to
Artifact Registry. Images are immutable and retained, which is what makes fast rollbacks
possible.

### Branch protection
The main branch is protected. Pull requests require at least one approval and a fully green
pipeline before they can merge. Required status checks cannot be bypassed, and force-pushes
to main are disabled.

## No manual deploys
Manual deployment is forbidden: the legacy deploy.sh script was removed in 2025 and must
never be used. Any service still referencing it must be migrated to the pipeline before its
next release. If you find documentation or runbooks that tell you to deploy by hand, treat
them as out of date and raise a correction.

The only supported way to ship a change is to merge an approved pull request to main and let
the pipeline promote the build. This guarantees that what runs in production exactly matches
a reviewed, tested commit.

### Why manual deploys were removed
Manual deploys bypassed review and testing, produced releases that did not match any reviewed
commit, and left no reliable audit trail. Removing them eliminated an entire category of
production incidents caused by someone shipping an unreviewed or stale build.

## Environments
There are two deploy environments: staging and production, each a separate Cloud Run service.
Changes are always promoted to staging first and smoke-tested there before production. Never
test an unverified change directly in production.

## Rollbacks
Rollbacks are handled by redeploying a previous Cloud Run revision from the console. Because
every revision is immutable and retained, rolling back is a single action and does not require
a rebuild. Pin traffic to the last known-good revision, confirm the service recovers, then
open an incident to track the root cause.

### Gradual rollout
For higher-risk changes, use Cloud Run traffic splitting to send a small percentage of
requests to the new revision first. Watch the metrics, then shift traffic to 100 percent once
the new revision proves healthy. If the new revision misbehaves, shift traffic back to the
previous revision instantly.

## Secrets and configuration
Pipeline secrets live in Secret Manager and are injected at deploy time. Never commit secrets
to the repository or print them in build logs. Configuration that differs between staging and
production is managed through environment variables set on each Cloud Run service, not baked
into the container image.

### Managing configuration changes
Treat configuration changes with the same care as code changes. A bad environment variable can
be just as damaging as a bad commit. Review configuration changes and roll them out through the
same promotion path where possible.

## Worked example
An engineer opens a pull request. The pipeline lints and tests it and reports green on the
pull request. A reviewer approves. On merge to main, the pipeline builds a container, pushes it
to Artifact Registry, deploys to staging, runs smoke tests, and promotes the build to
production on Cloud Run. If the production revision shows errors, the engineer pins traffic
back to the previous revision from the console and opens an incident.

## Frequently asked questions
Can I bypass a failing check in an emergency? No. Required checks exist precisely for
emergencies. If a check is wrong, fix the check.

How do I roll back? Redeploy the previous Cloud Run revision from the console and pin traffic
to it. No rebuild is needed.

What happened to deploy.sh? It was removed in 2025. Manual deploys are forbidden; use the
pipeline.

## Common mistakes
- Trying to deploy by hand with an old script instead of using the pipeline.
- Committing a secret and then rewriting history to hide it instead of rotating it.
- Baking environment-specific config into the container image.
- Merging with a red pipeline by disabling a required check.

## Ownership
The Platform team owns the pipeline definition and the shared workflow templates. Service teams
own their own tests and deploy configuration. Requests to change the shared workflow go through
the Platform team's review.

## Related documents
See the Deployment Guide for the service-level view, the On-Call Runbook for incident response,
and the API Authentication Guide for how services handle secrets.
""",

    # ================================================================== #
    "monitoring-setup": """
## Overview
This page explains how observability is set up for Northwind services and how to get access to
dashboards and alerts. It covers metrics, logs, host checks, and alert routing. It is
maintained by the SRE team.

Good monitoring is what turns an outage from a customer-reported surprise into something we
catch and fix first. Every production service is expected to emit the standard metrics
described below.

## The four golden signals
Our monitoring is built around four signals. Every service dashboard shows all four, and most
alerts are derived from them.

- Latency: how long requests take, measured at several percentiles.
- Traffic: how much demand the service is handling.
- Errors: the rate of failed requests.
- Saturation: how full the service's resources are.

## Metrics and dashboards
We monitor all services using Stackdriver. Dashboards live in the Stackdriver console. Each
service has a standard dashboard showing request rate, error rate, latency percentiles, and
saturation. Teams may add service-specific panels, but the four standard signals must always
be present.

- Request rate: requests per second, split by endpoint and status class.
- Error rate: the percentage of 5xx responses over a rolling window.
- Latency: p50, p95, and p99 response times.
- Saturation: CPU, memory, and connection-pool usage.

### Custom metrics
For custom metrics, export to Stackdriver Monitoring via the agent. Keep metric cardinality
under control: avoid high-cardinality labels such as raw user IDs, which make dashboards slow
and expensive. Prefer a small, fixed set of label values.

### Dashboard conventions
Keep dashboards readable. Put the four golden signals at the top, group related panels, and
label axes with units. A dashboard that nobody can interpret during an incident is worse than
no dashboard at all.

## Logs
Structured logs complement metrics. Emit logs as structured records with a consistent set of
fields so they can be searched and correlated.

- Include a request identifier so logs can be traced across services.
- Log at an appropriate level; do not log sensitive data.
- Keep log volume reasonable to control cost and noise.

Application logs are retained according to the data retention policy. Do not rely on logs for
long-term storage of anything you need to keep.

## Host checks
Host-level checks run on the Nagios box at nagios.corp.internal; ping the SRE team if you need
an account. These checks cover disk usage, process liveness, and certificate expiry on the
legacy hosts that are not yet fully migrated. New services on managed platforms do not need
Nagios checks and should rely on platform health checks instead.

### Legacy hosts
A handful of legacy hosts are still monitored this way while they are being migrated. Once a
service moves to a managed platform, its Nagios checks are removed and platform health checks
take over.

## Alerting
Alerts are routed to the #alerts channel. Every alert must be actionable and must link to a
runbook. Alerts that fire repeatedly without a clear action are noise and should be tuned or
removed.

- Page-level alerts notify the on-call engineer directly and are reserved for customer impact.
- Ticket-level alerts create a tracked item for the owning team to handle during business
  hours.
- Informational alerts post to the channel only and never page.

### Alert hygiene
Review alert volume monthly. If an alert has not led to a useful action in the last quarter, it
is a candidate for removal. The goal is that every page means something is actually wrong. Alert
fatigue is dangerous: when every page is noise, the one real page gets ignored.

### Writing a good alert
A good alert fires on customer-visible symptoms, not on internal causes. Alert on high error
rate or latency, not on a single server being busy. Always link the alert to a runbook that
tells the responder what to do.

## Worked example
A service's error rate crosses its threshold. A page-level alert fires to the on-call engineer
and posts to the #alerts channel with a link to the service runbook. The engineer opens the
Stackdriver dashboard, sees error rate and latency both climbing after a recent deploy, rolls
the deploy back, watches the signals recover, and closes the alert. The runbook link made the
first thirty seconds obvious.

## Getting access
To get dashboard and alerting access, open a request with the SRE team and include the services
you work on. Access is granted by team and reviewed periodically. If you are on-call, make sure
you can log in and silence alerts before your rotation begins.

## Frequently asked questions
Why is my dashboard slow? Usually high-cardinality labels. Reduce the number of distinct label
values.

How do I silence a noisy alert during an incident? Silence it from the alerting console for a
bounded time, and follow up to tune or remove it.

Do new services need Nagios checks? No. Rely on platform health checks; Nagios is for legacy
hosts only.

## Common mistakes
- Alerting on causes instead of customer-visible symptoms.
- Creating alerts with no linked runbook.
- Logging sensitive data or logging so much that signal is lost.
- Leaving stale alerts firing until everyone ignores the channel.

## Responsibilities
Service teams own the thresholds and runbooks for their own alerts. The SRE team owns the shared
monitoring platform, the standard dashboard template, and the alert routing configuration.

## Related documents
See the On-Call Runbook for how pages are handled, the Incident Severity Guide for classifying
impact, and the Data Retention Policy for how long logs are kept.
""",

    # ================================================================== #
    "vpn-access": """
## Overview
This document explains how to connect to the corporate VPN so you can reach internal systems
from outside the office. It is maintained by the IT team. If you are a new hire, set this up
during your first week.

The VPN provides an encrypted tunnel into the corporate network. Many internal tools are only
reachable through it, so getting connected is a prerequisite for most engineering work done
remotely.

## Who needs the VPN
You need the VPN if you work remotely and must reach internal-only systems: admin consoles,
internal wikis, legacy hosts, and certain build and database servers. If everything you need is
available over the public internet, you may not need the VPN day to day, but most engineers do.

## Connecting
To access internal systems from home, connect using Cisco AnyConnect to vpn.oldcorp.net. Use
your LDAP credentials. The first connection may prompt you to download and install the
AnyConnect client; accept the defaults.

- Open the Cisco AnyConnect client.
- Enter the gateway address vpn.oldcorp.net.
- Sign in with your LDAP username and password.
- Approve the second-factor prompt on your device.

### First-time setup
On your first connection the client may download and install components and ask for permission
to configure a network interface. Accept the defaults. If your device management tool has
already pushed the client, you can skip the download and go straight to signing in.

### What the VPN gives you access to
The VPN is required for accessing the internal Jenkins server and the staging database. It also
provides access to internal wikis, admin consoles, and the legacy hosts that are not exposed to
the public internet.

## Troubleshooting
If you cannot connect, clear the AnyConnect cache and retry. Most connection problems are
resolved by signing out completely, clearing the cache, and signing back in.

- Confirm you are not already connected to another VPN profile.
- Check that your LDAP password has not expired.
- If the client reports a certificate error, restart it and try once more.
- If you still cannot connect, open a ticket with IT and include the exact error message.

### Slow or dropping connections
If the VPN connects but is slow or keeps dropping, check your local network first. A weak
wireless signal is the most common cause. Try a wired connection, move closer to the access
point, or switch networks. If the problem persists across networks, open a ticket with IT and
include the times it dropped.

### Error messages
Record the exact text of any error message before you retry. "Login failed" usually means an
expired password; a certificate error usually clears after a client restart; a gateway timeout
usually points to a local network problem.

## Security expectations
Treat the VPN as a sensitive gateway into the corporate network.

- Never share your VPN credentials or approve a second-factor prompt you did not initiate.
- Disconnect from the VPN when you are finished to free capacity for others.
- Do not use the VPN from a shared or public computer.
- Keep the client updated when prompted.

### If you suspect compromise
If you believe your credentials or device have been compromised, disconnect, change your
password, and notify IT and Security immediately. Do not keep working on the suspect session.

## Worked example
A remote engineer needs to reach the staging database. They open AnyConnect, enter
vpn.oldcorp.net, sign in with LDAP, and approve the prompt on their phone. The tunnel comes up
and the staging host and internal Jenkins server become reachable. When they finish for the
day, they disconnect to free capacity.

## Frequently asked questions
I get "login failed" every time. Your LDAP password has probably expired. Reset it and try
again.

Why can I reach some internal sites but not others? Some systems require additional access
beyond the VPN. Open a ticket to request access to the specific system.

Do I need the VPN in the office? Usually not; the office network already has access.

## Common mistakes
- Using an old gateway address instead of vpn.oldcorp.net.
- Leaving the VPN connected all day and consuming capacity you are not using.
- Approving a second-factor prompt you did not trigger.
- Working around a connection problem on a personal or public computer.

## Getting help
For access requests, password resets, or persistent connection failures, contact the IT help
desk. Include your username, the device you are using, and a screenshot of any error. Response
times are faster during core business hours.

## Related documents
See the Password Policy for credential requirements, the Remote Work Policy for expectations
while working remotely, and the Onboarding Checklist for first-week setup.
""",

    # ================================================================== #
    "password-policy": """
## Scope
This policy defines password requirements for all employee accounts at Northwind. It applies to
every system that authenticates against the corporate identity provider. It is maintained by the
Security and IT teams.

Strong account hygiene is one of the cheapest and most effective defences we have against
account takeover. Everyone is expected to follow this policy.

## Why passwords matter
Most breaches start with a compromised credential. A single reused or guessable password can
give an attacker a foothold that spreads across systems. The requirements below exist to make
that first step as hard as possible.

## Rotation
All employees must rotate their account passwords every 90 days. The identity provider enforces
this automatically and will prompt you as the deadline approaches.

- You will receive reminders starting ten days before expiry.
- Failure to rotate within the window will lock your account until IT resets it.
- A locked account requires a verified identity check before it is restored.

### Planning around rotation
Do not wait until the last day to rotate. If you are travelling or on leave when your password
expires, your account will lock and you will need IT to reset it. Rotate before you go.

## Composition requirements
Passwords must meet the following minimum requirements:

- At least 10 characters in length.
- Include at least one number and one symbol.
- Not reuse any of your last 5 passwords.
- Not contain your username, your name, or common dictionary words.

### Choosing a strong password
Longer is stronger. A memorable passphrase made of several unrelated words is both easier to
remember and harder to crack than a short string of substitutions. Avoid predictable patterns
such as appending the current year or season, and never base a password on information that is
public about you.

### Password managers
We encourage using an approved password manager. It lets you use a long, unique password for
every system without having to remember them, which is far safer than reusing one password
everywhere.

## Multi-factor authentication
Passwords alone are not sufficient. All accounts must have a second factor enabled.

- Prefer an authenticator app or hardware key over SMS where available.
- Register a backup factor in case your primary device is lost.
- Never approve a prompt you did not initiate; report unexpected prompts to Security.

### Losing your second factor
If you lose your second-factor device, contact IT for a verified reset and register a new
factor immediately. This is why a backup factor matters: without one, losing your device locks
you out.

## Account lockout and recovery
After several failed sign-in attempts your account is temporarily locked to slow down guessing
attacks. If you are locked out, wait for the cool-down period or contact IT for a verified
reset. Recovery always requires confirming your identity.

## Handling compromise
If you believe your password has been exposed, change it immediately and notify the Security
team. Do not wait for the next rotation deadline. Report any phishing attempts that targeted
your credentials so the team can block the source.

### Recognising phishing
Be suspicious of any message that creates urgency and asks you to sign in through a link. Check
the address before entering credentials, and when in doubt, navigate to the system directly
rather than following a link.

## Worked example
An employee receives a reminder that their password expires in a week. They open their password
manager, generate a new long passphrase that meets the composition rules and has not been used
before, update it in the identity provider, and confirm their second factor still works. The
whole thing takes two minutes and their account never locks.

## Frequently asked questions
How often must I change my password? Every 90 days under this policy.

Can I reuse an old password? No, not any of your last five.

What happens if I miss the deadline? Your account locks until IT performs a verified reset.

## Common mistakes
- Waiting until the expiry day and locking out while travelling.
- Incrementing a number on the end of the same base password every cycle.
- Reusing a work password on a personal site.
- Approving an unexpected second-factor prompt out of habit.

## Enforcement
Compliance is monitored centrally. Repeated policy violations are escalated to your manager.
Exceptions require documented approval from the Security team.

## Related documents
See the Updated Security Standards for the current direction of our authentication guidance,
the VPN Access guide for remote credentials, and the Onboarding Checklist for first-week setup.
""",

    # ================================================================== #
    "security-standards-2025": """
## Purpose
This document sets out Northwind's updated security standards, effective 2025. It supersedes
earlier guidance where the two conflict. It is maintained by the Security team and reflects
current industry best practice.

Security standards evolve as research improves. The changes below bring Northwind in line with
modern guidance and, in several cases, reduce friction for employees while improving real-world
safety.

## Guiding principles
- Prefer controls that work with human behaviour, not against it.
- Length and uniqueness beat complexity rules.
- Phishing-resistant factors beat shared secrets.
- Least privilege, reviewed regularly, limits the blast radius of any compromise.

## Passwords
Following the updated NIST SP 800-63B guidance, Northwind no longer enforces periodic password
rotation. Users are required to change a password only when there is evidence of compromise.
Forced expiry has been disabled in the identity provider.

- Minimum length is now at least 14 characters.
- Passphrases are strongly encouraged over complex but short passwords.
- We screen new passwords against known-breached password lists.
- Composition rules such as forced symbols are relaxed in favour of length.

### Why rotation was removed
Mandatory periodic rotation pushed users toward predictable, incremented passwords and did not
meaningfully reduce compromise. Modern guidance favours long, unique secrets that are only
changed when there is a reason to. Removing forced expiry reduces password reuse and support
load without weakening security.

### Transition from the old policy
Where this document conflicts with the older password policy, this document wins. The identity
provider has been reconfigured accordingly. Teams should update any local documentation that
still references forced 90-day rotation.

## Multi-factor authentication
A second factor is mandatory for all accounts, and a hardware second factor is strongly
encouraged for privileged access.

- Phishing-resistant factors such as hardware security keys are preferred.
- SMS codes are permitted only as a last-resort backup.
- Privileged and administrative accounts must use a hardware key.

### Privileged access
Administrative and production access carries extra requirements: a hardware key, access that is
time-bound where possible, and quarterly review. Privileged sessions are logged.

## Data protection
- Sensitive data must be encrypted in transit and at rest.
- Access to production data follows least privilege and is reviewed quarterly.
- Secrets are stored in Secret Manager, never in code or configuration files.
- Data is classified so that controls match sensitivity.

### Data classification
Classify data as public, internal, confidential, or restricted, and apply controls to match.
The higher the classification, the tighter the access and the more thorough the logging.

## Device security
Company devices must have disk encryption enabled, automatic screen lock, and current
operating-system updates. Lost or stolen devices must be reported to IT and Security
immediately so access can be revoked.

### Patching
Keep operating systems and key applications current. Many compromises exploit known
vulnerabilities that a pending update would have closed. Do not defer security updates
indefinitely.

## Incident reporting
Report suspected security incidents to the Security team without delay. Early reporting is
always better than waiting for certainty. There is no penalty for a good-faith report that turns
out to be a false alarm.

## Worked example
A team is building a new service that stores customer records. They classify the data as
confidential, encrypt it in transit and at rest, store the database credentials in Secret
Manager, grant production access only to the two engineers who need it, and schedule that access
for quarterly review. They require a hardware key for the admin console. The service passes its
security review on the first pass.

## Frequently asked questions
Do I still have to change my password every quarter? No. Forced expiry has been disabled; change
it only on evidence of compromise.

What is the minimum password length now? At least 14 characters, with passphrases encouraged.

Is SMS acceptable as a second factor? Only as a last-resort backup; prefer an authenticator app
or a hardware key.

## Common mistakes
- Treating the old 90-day rotation rule as still in force.
- Using a short, complex password instead of a long passphrase.
- Storing secrets in configuration files instead of Secret Manager.
- Granting broad production access and never reviewing it.

## Exceptions
Any exception to these standards requires written approval from the Security team, a documented
compensating control, and a review date.

## Related documents
This document supersedes the older Password Policy where they conflict. See the API
Authentication Guide for secret handling and the Data Retention Policy for how long data is kept.
""",

    # ================================================================== #
    "onboarding-checklist": """
## Welcome
This checklist walks a new engineer through their first two weeks at Northwind. It is maintained
by the People and Platform teams. Your onboarding buddy will help you work through it; ask
questions early and often in the #eng-help channel.

The aim of onboarding is simple: by the end of week two you should have shipped a small change to
production and understand how we build, review, and release software.

## Before day one
Your manager and IT arrange your accounts and equipment before you start. If something is not
ready on day one, that is normal; open a ticket and your buddy will help you chase it. Do not
worry about being productive immediately. The first week is about setup and context.

## Week 1: setup and access
- Get your laptop imaged by IT and enable disk encryption.
- Enable single sign-on and register your second factor.
- Request access to the engineering GitHub organisation.
- Read the architecture overview and the engineering handbook.
- Set up your local development environment and build a service end to end.
- Join the core team channels and introduce yourself.
- Set up the VPN so you can reach internal systems.

### Meet your team
Spend time in week one meeting the people you will work with. Schedule short introductions with
your manager, your onboarding buddy, and the leads of the teams your service depends on. Ask them
what they wish they had known in their first month.

### Learn the landscape
Read the top-level architecture overview and skim the runbooks for the services your team owns.
You are not expected to remember it all; the goal is to know where to look.

## Week 2: your first change
- Pick up a starter task labelled good-first-issue.
- Pair with your onboarding buddy on the change.
- Open a pull request and go through code review.
- Deploy a small change end to end following the CI/CD pipeline.
- Write a short note about anything in the docs that was confusing or wrong.

### Learning the release process
Shadow a teammate through a real release so you understand how changes reach production. Read the
CI/CD standards and the on-call runbook so you know what happens after you merge. Your first
deploy should be a small, low-risk change with your buddy watching.

### Your first code review
Expect feedback on your first pull request; that is the point. Review is a conversation, not a
judgement. Respond to comments, ask questions when something is unclear, and treat it as the
fastest way to learn how we work.

## Tools and accounts
By the end of onboarding you should have working access to source control, the CI/CD pipeline,
observability dashboards, the internal wiki, and the communication channels your team uses. If
anything is missing, open a ticket with IT.

## Culture and expectations
- Ask questions; nobody expects you to know everything in week one.
- Prefer small, reviewable changes over large ones.
- Write things down so the next new hire has an easier time.
- Flag anything unclear so we can keep the documentation healthy.
- Default to sharing context in the open so others can follow along.

## Worked example
A new engineer spends week one getting their laptop set up, enabling single sign-on, joining
channels, and reading the architecture overview. In week two they pick up a good-first-issue,
pair with their buddy, open a pull request, respond to review feedback, and deploy the change
through the pipeline with their buddy watching. They finish by noting two confusing steps in the
setup docs so the next hire has it easier.

## Frequently asked questions
I do not have access to something I need. Open a ticket with IT and ask your buddy to help you
follow up.

How quickly should I be productive? The first two weeks are about setup and context. A small
shipped change by the end of week two is a great outcome.

Who do I ask for help? Your onboarding buddy first, then your team, then #eng-help.

## Common mistakes
- Trying to take on a large task before understanding the release process.
- Staying stuck in silence instead of asking in #eng-help.
- Skipping the architecture reading and getting lost later.
- Not writing down the rough edges you hit, so the next hire hits them too.

## Getting help
If you are blocked, ask in #eng-help before spending more than thirty minutes stuck. Your buddy
and your manager are there to unblock you, and asking early is a sign of good judgement, not
weakness.

## Related documents
See the Deployment Guide and CI/CD Pipeline Standards for how changes ship, the VPN Access guide
for remote access, and the Remote Work Policy for working arrangements.
""",

    # ================================================================== #
    "expense-policy": """
## Purpose
This policy explains what business expenses Northwind reimburses and how to submit them. It
applies to all employees and contractors who incur costs on behalf of the company. It is
maintained by the Finance team.

The policy balances two goals: making it easy for employees to do their jobs without being out of
pocket, and keeping spending reasonable and auditable.

## General principles
- Spend company money as if it were your own.
- Keep a receipt for everything and submit promptly.
- When unsure, ask before you spend.
- Choose the reasonable option, not the cheapest or the most expensive.

## Travel
- Flights should be booked in economy class. Premium cabins require director approval.
- Book travel as far in advance as practical to control cost.
- Ground transport should use standard options; use ride-share or transit over premium services
  where reasonable.
- Hotels should be booked at a standard business rate.

### Booking travel
Use the approved booking tool where possible so travel is tracked and negotiated rates apply. If
you must book outside it, keep the receipts and note why. Combine trips where it makes sense to
reduce cost and time away.

### Meals during travel
Meals during business travel are reimbursable up to 60 USD per day. This covers all meals
combined, not per meal. Alcohol is not reimbursable except at an approved client event.

## Client entertainment
Client dinners require manager approval above 150 USD per head. Always record the names and
companies of attendees and the business purpose. Reasonable, occasional client entertainment is
expected; lavish or frequent entertainment is not.

### Documentation for entertainment
For any client entertainment, record who attended, which companies they represented, and the
business reason. This is required both for reimbursement and for compliance.

## Submitting expenses
- Submit receipts within 30 days through the expense portal.
- Itemise each expense and attach a legible receipt.
- Select the correct cost centre and project code.
- Add a short business justification for anything unusual.

### Approval flow
Expenses route to your manager for approval and then to Finance for payment. Approved expenses are
typically reimbursed in the next payroll cycle. Incomplete submissions are returned, which delays
payment.

### Receipts
A valid receipt shows the vendor, date, amount, and what was purchased. A card statement line is
not a receipt. If you lose a receipt, note it and provide what detail you can; repeated missing
receipts will be questioned.

## What is not reimbursable
- Personal expenses are never reimbursable.
- Fines, penalties, and traffic tickets.
- Personal entertainment and non-business subscriptions.
- Upgrades and add-ons that are not pre-approved.

## Worked example
An employee travels for two days to meet a client. They book an economy flight through the
approved tool, stay at a standard business-rate hotel, and spend within the 60 USD daily meal
limit. They host a client dinner at 120 USD per head, which is under the approval threshold, and
record the attendees and purpose. They submit itemised receipts within a week and are reimbursed
in the next cycle.

## Frequently asked questions
What is the daily meal limit while travelling? 60 USD per day, covering all meals combined.

Do I need approval for a client dinner? Yes, if it is above 150 USD per head.

How long do I have to submit? 30 days through the expense portal.

## Common mistakes
- Submitting a card statement line instead of an itemised receipt.
- Missing the 30-day window and delaying your own reimbursement.
- Booking premium travel without director approval.
- Mixing personal purchases into a business expense claim.

## Questions
If you are unsure whether something is reimbursable, ask Finance before you spend. It is much
easier to confirm in advance than to resolve a rejected claim afterwards.

## Related documents
See the Remote Work Policy for equipment stipends and the Data Retention Policy for how financial
records are retained.
""",

    # ================================================================== #
    "oncall-runbook": """
## Overview
This runbook describes how on-call works for Northwind services and what to do when you are
paged. It is maintained by the SRE team. Read it before your first rotation and keep it within
reach while you are on call.

On-call exists to protect customers. The person on call is empowered to take whatever reasonable
action is needed to restore service, including rolling back releases and escalating to anyone in
the company.

## Before your rotation
Prepare before your week starts so you are not scrambling when the first page arrives.

- Confirm you can log in to the dashboards and the alerting console.
- Confirm you can silence and acknowledge alerts.
- Install and test the paging app on your phone.
- Read the recent incident history and any known risks.

## The rotation
The on-call engineer owns the pager for one week. Hand-off happens at a fixed time with a short
sync covering open incidents, risky changes, and anything to watch.

- Acknowledge pages within 5 minutes.
- Escalate to the secondary on-call if a page is unacknowledged after 15 minutes.
- Keep your phone charged and your laptop reachable during your rotation.

### Hand-off
At the start and end of each rotation, run a short hand-off. The outgoing engineer summarises
open incidents, recent deploys, and anything fragile. The incoming engineer confirms access and
asks questions.

## Responding to a page
When you are paged, first decide whether customers are affected.

- Confirm the alert is real and not a monitoring glitch.
- Classify the severity using the incident severity guide.
- For a production outage, open an incident channel and assign an incident commander.
- Post status updates every 30 minutes until the incident is resolved.

### During an incident
Keep communication clear and frequent. The incident commander coordinates; everyone else focuses
on their task. Prefer fast, reversible actions such as rolling back a recent release over risky
forward fixes. Capture a rough timeline as you go so the postmortem is easier later.

### Mitigate first, diagnose later
The first priority is restoring service, not understanding why it broke. If a recent deploy is
the likely cause, roll it back before investigating. Diagnosis can happen once customers are no
longer affected.

## Common actions
- Roll back the most recent release if the incident started right after a deploy.
- Pin Cloud Run traffic to the last known-good revision.
- Scale up if the service is saturated.
- Fail over to a healthy region if one region is degraded.

### Communication
For a customer-facing outage, keep stakeholders informed with regular updates even if there is no
news. Silence makes people assume the worst. A short "still investigating, next update in 30
minutes" is enough.

## After the incident
Once service is restored, close the incident channel and schedule a postmortem for SEV1 and SEV2
incidents. Postmortems are blameless and focus on systems and process, not individuals.

### The postmortem
A good postmortem captures the timeline, the contributing factors, what went well, and concrete
actions to reduce the chance of recurrence. Assign owners and due dates to the actions, and track
them to completion.

## Worked example
At 2 a.m. the on-call engineer is paged for a rising error rate. They acknowledge within two
minutes, confirm the alert is real, and classify it as a SEV2. The dashboards show the errors
began right after a deploy, so they pin Cloud Run traffic to the previous revision. Errors
recover. They post an update, open an incident, and schedule a postmortem for the next morning.

## Frequently asked questions
What if I cannot fix it? Escalate. Pull in the service owner, the secondary on-call, or your
manager. Escalating early is good judgement.

Do I diagnose or mitigate first? Mitigate first. Restore service, then investigate.

How often do I update stakeholders? Every 30 minutes for a SEV1, and regularly for a SEV2, even
if there is no change.

## Common mistakes
- Trying to debug a bad release in production instead of rolling back.
- Going quiet during an incident so stakeholders assume the worst.
- Not writing down the timeline, making the postmortem guesswork.
- Hesitating to escalate because it feels like admitting failure.

## Escalation
If you are unsure or overwhelmed, escalate early. Pull in the service owner, the secondary
on-call, or your manager. Escalating is never a failure; a prolonged customer-impacting outage is.

## Related documents
See the Incident Severity Guide for classification, the Monitoring and Alerting Setup for
dashboards and alerts, and the CI/CD Pipeline Standards for how to roll back a release.
""",

    # ================================================================== #
    "api-auth-guide": """
## Overview
This guide explains how external clients authenticate with the Northwind API. It is maintained by
the Platform team and is the reference for partners and internal teams building integrations.

Authentication is the front door to customer data, so the API uses a standard, well understood
scheme and enforces transport security everywhere.

## Concepts
A few terms are used throughout this guide. A client is an application that calls the API. A
client identity is the credential that identifies that application. An access token is a
short-lived credential the client presents on each request. A scope is a permission that limits
what a token can do.

## Authentication model
External clients authenticate using OAuth 2.0 client credentials. Each integration is issued its
own client identity so access can be granted and revoked independently.

- Request a client ID and secret from the developer portal.
- Exchange the client credentials for an access token at the token endpoint.
- Send the access token as a bearer token on every API request.

### Getting credentials
Register your integration in the developer portal to receive a client ID and secret. Use a
separate client identity for each environment and each distinct integration so you can revoke one
without affecting the others.

### Token lifetime
Access tokens expire after one hour; refresh using the token endpoint. Build your client to
refresh tokens automatically shortly before they expire rather than waiting for a request to
fail. Cache the token and reuse it until it is close to expiry; do not request a new token on
every call.

## Handling secrets
Client secrets are sensitive and must be protected.

- Never embed secrets in frontend code or mobile apps.
- Store secrets in a secret manager or secure server-side configuration.
- Rotate secrets periodically and immediately if you suspect exposure.
- Use a separate client identity per environment.

### Rotating a secret
To rotate without downtime, create a second secret for the same client, deploy it, confirm the
new secret works, then retire the old one. Never rotate by deleting the only working secret
first.

## Transport security
All API traffic must use TLS 1.2 or higher. Requests over plain HTTP are rejected. Verify server
certificates and do not disable certificate validation, even in test environments.

## Scopes and least privilege
Each client is granted only the scopes it needs. Request the minimum set of scopes for your
integration, and request additional scopes only when a new feature requires them. Over-broad
access is a common source of security findings.

### Reviewing scopes
Review the scopes your integration holds periodically and give up any you no longer use. The
fewer permissions a leaked token carries, the less damage it can do.

## Error handling and rate limits
- A 401 response means the token is missing, expired, or invalid; refresh and retry once.
- A 403 response means the token is valid but lacks the required scope.
- A 429 response means you are being rate limited; back off and retry with jitter.

### Retries
Use exponential backoff with jitter for transient errors. Do not retry non-idempotent requests
blindly, and never retry a 4xx that indicates a client mistake without fixing the request first.

## Worked example
A partner builds a server-side integration. They register a client in the developer portal for
the staging environment, store the secret in their secret manager, and request only the read
scopes they need. Their client fetches an access token, caches it, and refreshes it a few minutes
before the one-hour expiry. On a 429 they back off with jitter and retry. When they go live they
register a separate production client.

## Frequently asked questions
How long do tokens last? One hour. Refresh at the token endpoint before expiry.

Where do I put my secret? In a server-side secret manager, never in frontend or mobile code.

What does a 403 mean? Your token is valid but lacks the required scope.

## Common mistakes
- Embedding a client secret in a mobile app or single-page frontend.
- Requesting a new token on every API call instead of caching it.
- Requesting far more scopes than the integration needs.
- Disabling certificate validation to "make it work" in testing.

## Support
For client credentials, scope changes, or integration help, contact the Platform team through the
developer portal. Include your client ID but never your secret.

## Related documents
See the Updated Security Standards for secret handling, and the CI/CD Pipeline Standards for how
services manage configuration and secrets at deploy time.
""",

    # ================================================================== #
    "data-retention": """
## Purpose
This policy defines how long Northwind retains different categories of data and how data is
disposed of at the end of its life. It is maintained by the Legal team and applies to all systems
that store company or customer data.

Retention is a balance between regulatory obligations, business needs, and the principle of not
keeping data longer than necessary.

## Principles
- Keep data only as long as there is a legal or business reason.
- Classify data so that retention and controls match its sensitivity.
- Automate disposal so expired data does not accumulate.
- Honour deletion requests promptly and verifiably.

## Retention periods
- Customer transaction records are retained for 7 years to meet regulatory requirements.
- Application logs are retained for 90 days.
- Backups are retained according to their own schedule and purged when expired.
- Analytics data is retained in aggregated form only after its raw window closes.

### Why these periods
Transaction records are kept for seven years because financial and tax regulations require it.
Operational logs are kept only as long as they are useful for debugging and security
investigations, which is why their window is short. Keeping logs forever would raise cost and
privacy risk with little benefit.

## Personal data
Personal data deletion requests are processed within 30 days. When a verified request is received,
personal data is removed or anonymised across primary systems and scheduled for removal from
backups as they roll off.

- Requests are verified before any data is deleted.
- Deletion covers primary stores and propagates to downstream systems.
- Some records may be retained where law requires, with a documented basis.

### Handling a deletion request
When a deletion request arrives, verify the requester's identity, locate the personal data across
systems, delete or anonymise it in primary stores, and record that the request was completed.
Data in backups is removed as those backups expire on their normal schedule.

## Disposal
Backups older than their retention window are purged automatically each month. Automated jobs
enforce retention so that expired data does not linger. Manual deletion of production data
requires approval and is logged.

### Secure disposal
Disposal must be irreversible. Deleting a pointer while the underlying data remains recoverable is
not disposal. For physical media, follow the secure destruction process.

## Access and auditing
Access to retained data follows least privilege and is reviewed periodically. Access to sensitive
historical records is logged, and the logs themselves are retained for audit.

## Worked example
A customer requests deletion of their personal data. The team verifies the request, removes the
personal fields from the primary database and the downstream analytics store within the 30-day
window, and records completion. The customer's transaction records, which must be kept for seven
years for tax reasons, are retained with a documented legal basis but stripped of unnecessary
personal detail.

## Frequently asked questions
How long are transaction records kept? Seven years, to meet regulatory requirements.

How long are application logs kept? 90 days.

How fast are deletion requests handled? Within 30 days of a verified request.

## Common mistakes
- Keeping logs indefinitely "just in case," raising cost and privacy risk.
- Deleting a reference while the underlying data remains recoverable.
- Processing a deletion request without verifying the requester.
- Forgetting that some records must be retained even after a deletion request.

## Responsibilities
Service teams implement retention controls in their systems. Legal defines the required periods and
reviews them when regulations change. Security reviews the controls as part of regular audits.

## Exceptions and legal holds
When data is subject to a legal hold, normal retention and deletion are suspended for the affected
records until the hold is lifted. Legal manages holds and notifies the relevant teams.

## Related documents
See the Updated Security Standards for data classification and protection, and the Database Backup
Procedure for how backups are retained and purged.
""",

    # ================================================================== #
    "code-review-guidelines": """
## Purpose
These guidelines describe how code review works at Northwind. They are maintained by the Platform
team and apply to every repository. Good review keeps our code correct, maintainable, and shared
across the team.

Review is not a gate to pass; it is a conversation that improves the change and spreads knowledge.
Both authors and reviewers share responsibility for making it effective.

## Why we review
Review catches defects early, spreads knowledge across the team so no one person is a single point
of failure, and keeps the codebase consistent. It is one of the highest-leverage habits an
engineering team can have.

## Requirements
- Every pull request needs at least one approval before merge.
- CI must be green before merge; do not bypass required checks.
- Keep pull requests under 400 lines where possible.
- Reviewers should respond within one business day.

### Why small pull requests
Small changes are reviewed faster, more thoroughly, and with fewer mistakes. If a change is large,
split it into a series of reviewable steps rather than asking for one enormous review. A reviewer's
attention does not scale with the size of the diff.

## What reviewers look for
Focus review on correctness, tests, and readability.

- Correctness: does the change do what it claims, including edge cases?
- Tests: are there tests that would fail without the change?
- Readability: will someone understand this in six months?
- Security: are inputs validated and secrets kept out of the code?

### What not to block on
Avoid blocking a change on personal style preferences that the formatter does not enforce. Prefer
suggestions over demands for subjective matters, and let automated tooling handle formatting.
Reserve blocking comments for genuine problems.

## For authors
- Write a clear description explaining what changed and why.
- Keep each pull request focused on a single concern.
- Respond to feedback promptly and assume good intent.
- Do not merge your own change without the required approval.
- Make the diff easy to review: separate refactors from behaviour changes.

### Writing a good description
A good description tells the reviewer what the change does, why it is needed, and anything they
should pay special attention to. It saves the reviewer from reverse-engineering your intent from
the diff.

## For reviewers
- Be timely; a stalled review blocks your teammate.
- Be specific and kind; explain the reasoning behind a request.
- Distinguish between must-fix issues and optional suggestions.
- Approve once the must-fix items are addressed.
- Praise good work, not just problems.

### Giving good feedback
Explain the why behind a comment so the author learns, not just complies. Mark optional
suggestions clearly so the author knows what actually blocks the merge. Assume the author made
reasonable choices and ask before asserting.

## Worked example
An author opens a focused 180-line pull request with a clear description and tests. A reviewer
responds the same day, flags one correctness issue as must-fix and two readability points as
optional suggestions, and explains the reasoning for each. The author fixes the must-fix issue,
adopts one suggestion, replies to the other, and the reviewer approves. CI is green, so the author
merges.

## Frequently asked questions
Can I merge my own change? Only with the required approval from someone else.

What if a required check is wrong? Fix the check; do not bypass it.

How big is too big? Aim for under 400 lines. Split larger changes into reviewable steps.

## Common mistakes
- Opening a huge pull request that mixes a refactor with a behaviour change.
- Blocking a merge over subjective style the formatter does not enforce.
- Letting a review sit for days and blocking a teammate.
- Bypassing a required check under deadline pressure.

## Merging
Once a change has the required approval and a green pipeline, the author merges it. Required checks
exist to protect everyone and must never be bypassed, even under deadline pressure.

## Related documents
See the CI/CD Pipeline Standards for the checks that run on every pull request and the Deployment
Guide for what happens after a change merges.
""",

    # ================================================================== #
    "incident-severity": """
## Purpose
This guide defines how Northwind classifies incident severity so that response matches impact. It
is maintained by the SRE team and is referenced by the on-call runbook. Classify every incident at
the start, and adjust the classification as you learn more.

A shared severity language lets everyone understand how serious an incident is without a long
explanation, which speeds up the response.

## How to classify
Classify by customer impact, not by internal cause. A failing internal component that customers do
not notice is lower severity than a small but customer-visible failure. When in doubt, start higher
and downgrade.

## Severity levels
- SEV1: full outage or data loss affecting most customers; page immediately.
- SEV2: major feature broken or significant degradation.
- SEV3: minor issue with a workaround.

### SEV1
A SEV1 is an all-hands situation. Open an incident channel immediately, assign an incident
commander, and page the service owner. Communicate frequently with clear status updates. The
priority is restoring service, not finding the root cause. Data loss is always at least a SEV1.

### SEV2
A SEV2 is serious but not a full outage. A major feature may be broken or performance badly
degraded for many users. Respond promptly during the day and page out of hours if customer impact
is ongoing. Many SEV2s become SEV1s if left unaddressed, so do not sit on them.

### SEV3
A SEV3 is a minor issue with a reasonable workaround. Track it and fix it during normal working
hours; it does not require paging. If a SEV3 starts affecting more customers, raise it.

## Classifying and adjusting
Classify at the start of an incident and adjust as you learn more. It is better to start high and
downgrade than to under-call a serious incident. If customer impact grows, raise the severity and
expand the response.

## Communication expectations
- SEV1: status updates every 30 minutes to stakeholders.
- SEV2: regular updates until the issue is resolved.
- SEV3: a tracked ticket with normal updates.

### Who communicates
The incident commander owns communication for SEV1 and SEV2 incidents, or delegates it to a
dedicated communications lead for large incidents. Responders should not be interrupted for status;
the commander aggregates and shares it.

## Postmortems
SEV1 and SEV2 require a written postmortem within five business days. Postmortems are blameless and
focus on contributing factors and actions that reduce the chance of recurrence. Share them widely so
the whole organisation learns.

### Blameless culture
A blameless postmortem assumes everyone acted reasonably given what they knew. The goal is to fix
the system, not to assign fault. People report problems honestly only when they are not punished for
them.

## Worked example
A payment feature starts failing for a subset of customers. The on-call engineer classifies it as a
SEV2, opens an incident, and assigns a commander. As more customers are affected, they raise it to
SEV1 and page the service owner. After mitigation, they hold a blameless postmortem within five
business days and track the follow-up actions to completion.

## Frequently asked questions
Is data loss always a SEV1? Yes, at minimum.

Should I classify by cause or impact? By customer impact.

What if I am not sure of the severity? Start higher and downgrade as you learn more.

## Common mistakes
- Under-calling a serious incident to avoid waking people up.
- Classifying by internal cause instead of customer impact.
- Treating a postmortem as a search for someone to blame.
- Leaving a SEV2 unattended until it becomes a SEV1.

## Roles
The incident commander coordinates the response and owns communication. Responders focus on
diagnosis and mitigation. A scribe captures the timeline for the postmortem.

## Related documents
See the On-Call Runbook for how incidents are handled and the Monitoring and Alerting Setup for the
alerts that surface them.
""",

    # ================================================================== #
    "remote-work-policy": """
## Purpose
This policy sets expectations for remote and hybrid work at Northwind. It is maintained by the
People team and applies to all employees whose roles can be performed remotely.

Northwind supports flexible work while recognising that some collaboration is best done together.
The guidelines below aim to get the benefits of both.

## Philosophy
We trust people to do their best work in the arrangement that suits them, within some shared
structure that keeps teams connected. Flexibility is a benefit, not a loophole; it works because
everyone holds up their side.

## Working arrangements
- Employees may work remotely up to three days per week.
- Coordinate your in-office days with your team to maximise overlap.
- Teams may agree on fixed in-office days to make planning easier.

### Core hours
Core collaboration hours are 10:00 to 15:00 local time. During core hours you should be reachable
for meetings and quick questions. Outside core hours you have more flexibility to structure your
day, as long as your work and commitments are covered.

### Time zones
For distributed teams, agree on an overlap window that respects everyone's core hours. Rotate the
burden of inconvenient meeting times rather than always imposing it on the same people.

## Expectations while remote
- Ensure a reliable internet connection for meetings.
- Keep your calendar accurate so colleagues know your availability.
- Be present and engaged in meetings, with your camera on where practical.
- Respond to messages within a reasonable time during working hours.

### Communication
Default to clear, written communication so that people in different locations and time zones can
follow along. Document decisions where others will need them, and prefer asynchronous updates over
meetings when a meeting is not necessary.

## Equipment and workspace
Equipment stipends are available once per year to help you set up a safe and productive workspace.
Use company-approved devices for company work, and keep your workspace free from anyone who should
not see confidential information.

### Security while remote
Follow the same security standards at home as in the office. Lock your screen when you step away,
connect through the VPN when required, and never use public computers for company work. Treat your
home network as you would any untrusted network.

## Meetings and focus time
Protect focus time by keeping meetings purposeful and short. Default to no meeting when an
asynchronous update will do. When you do meet, have an agenda and end with clear next steps.

## Worked example
An engineer on a distributed team works remotely three days a week. They keep their calendar
accurate, join the team's agreed overlap window during core hours, and use written updates for
everything that does not need a meeting. They connect through the VPN for internal systems and lock
their screen when they step away. On office days they coordinate with their team for maximum
overlap.

## Frequently asked questions
How many days can I work remotely? Up to three per week.

What are core hours? 10:00 to 15:00 local time, when you should be reachable.

Can I work from anywhere? Within your approved arrangement; fully remote or out-of-region work
needs People team approval.

## Common mistakes
- Treating flexibility as being unreachable during core hours.
- Letting your calendar drift out of date so nobody knows your availability.
- Relaxing security habits at home that you would keep in the office.
- Defaulting to meetings when a written update would be clearer and faster.

## Wellbeing
Remote work can blur the line between work and personal time. Set boundaries, take breaks, and use
your time off. Managers should model healthy habits and respect core hours.

## Exceptions
Arrangements that differ from this policy, such as fully remote roles or different in-office
expectations, require manager and People team approval.

## Related documents
See the VPN Access guide for connecting remotely, the Updated Security Standards for device
security, and the Expense Policy for equipment stipends.
""",

    # ================================================================== #
    "database-backup": """
## Overview
This procedure describes how the Northwind primary database is backed up and how to restore from a
backup. It is maintained by the SRE and Data teams. Backups are our last line of defence against
data loss, so the process must be reliable and regularly verified.

A backup that has never been tested is not a backup. In addition to taking backups, we periodically
practise restoring them.

## Backup strategy
We take full nightly backups and retain enough history to recover from a problem that is not
noticed immediately. The strategy balances recovery needs against storage cost and keeps the
process simple enough to run reliably every night.

## How backups run
A nightly cron job runs mysqldump against the primary database and copies the archive to the
on-prem NAS at nas.corp.internal. The job runs during the low-traffic window to limit impact on
production.

- The dump captures a consistent snapshot of the database.
- The archive is compressed and timestamped.
- The archive is copied to the on-prem NAS for retention.

### Scheduling
The job is scheduled for the quietest part of the night to minimise impact on production. If the
window shifts because of traffic patterns, update the schedule rather than letting backups run
during peak load.

### Verification
Verify the backup size each morning. A sudden drop in size usually means the dump failed or was
truncated. If the size looks wrong, investigate before the next nightly run so you do not stack up
multiple bad backups.

## Retention
Backups are retained according to the data retention policy and older archives are purged when they
expire. Keep enough history to recover from a problem that is not noticed immediately.

### Storage and purging
Expired archives are purged automatically so storage does not grow without bound. Confirm the purge
job is running; a full NAS causes the nightly backup to fail silently.

## Restoring
To restore, copy the dump from the NAS and pipe it into the mysql client on the standby host.
Always restore to the standby first and validate before promoting it, rather than restoring directly
over production.

- Copy the chosen archive from the NAS to the standby host.
- Decompress the archive.
- Pipe the dump into the mysql client on the standby.
- Validate row counts and spot-check critical tables.
- Promote the standby only after validation passes.

### Validating a restore
A restore is not complete until it is validated. Compare row counts against expectations, spot-check
a few critical tables, and confirm the application can connect and read. Only then consider
promoting the standby.

## Testing restores
Schedule a restore drill on a regular cadence. A drill proves the backups are usable and keeps the
team practised, so that a real recovery is routine rather than improvised. Record each drill,
including how long the restore took, so recovery-time expectations are realistic.

## Worked example
During a drill, an engineer copies the most recent dump from the on-prem NAS to the standby host,
decompresses it, and pipes it into the mysql client on the standby. They validate row counts against
the previous day's figures, spot-check the orders and customers tables, and confirm a test
application can read from the standby. The drill takes forty minutes, which they record as the
realistic recovery time.

## Frequently asked questions
How often do backups run? Nightly, during the low-traffic window.

Where are backups stored? On the on-prem NAS at nas.corp.internal.

Where do I restore to? The standby host first; validate before promoting, never restore straight
over production.

## Common mistakes
- Restoring directly over production instead of to the standby first.
- Never testing a restore and discovering at recovery time that the backups are unusable.
- Ignoring a sudden drop in backup size.
- Letting the NAS fill up so nightly backups fail silently.

## Responsibilities
The SRE team owns the backup jobs and the restore procedure. The Data team owns validation of
restored data. Failures of the nightly job page the on-call engineer.

## Related documents
See the Data Retention Policy for how long backups are kept, the On-Call Runbook for what happens
when a backup job fails, and the Monitoring and Alerting Setup for how failures are detected.
""",
}


# Additional sections appended to the shorter documents to bring every PDF to
# roughly six pages. Planted phrases live in LONG_BODIES above and are unaffected.
APPENDIX = {
    "data-retention": """
## Compliance and audit
Retention is not only good hygiene; for several data categories it is a legal obligation. The
periods in this policy are set so that Northwind can demonstrate compliance to auditors and
regulators on request. Keep the mapping between data category and retention period documented and
current.

- Maintain a register of data categories, their retention periods, and the legal basis.
- Record when automated purges run and whether they succeeded.
- Keep evidence that deletion requests were completed within the required window.
- Review the register whenever a regulation or business process changes.

Auditors typically ask two questions: can you show what you keep and why, and can you show that you
delete what you should. A current register and reliable purge logs answer both.

## Data minimisation
The cheapest data to protect is the data you never collected. Before adding a new field or log, ask
whether it is actually needed and for how long.

- Collect only the data a feature genuinely requires.
- Prefer aggregated or anonymised data where the raw detail is not needed.
- Set a retention period for every new data store at the time it is created.
- Delete prototype and test data sets that are no longer in use.

Minimisation reduces both cost and risk: there is less to store, less to secure, and less to expose
if something goes wrong.
""",

    "database-backup": """
## Recovery objectives
Two numbers define what our backups must achieve. The recovery point objective is how much data we
can afford to lose, measured in time. With nightly backups, our worst-case recovery point is close
to twenty-four hours, so anything that needs a tighter window requires additional protection such as
replication. The recovery time objective is how long a restore is allowed to take, and restore
drills are what keep it honest.

- Know the recovery point and recovery time expected for the database before relying on this process.
- If a tighter recovery point is required, combine backups with replication; backups alone are not enough.
- Record restore-drill durations so the recovery time reflects reality, not hope.

## Offsite and resilience
A backup that sits next to the thing it protects is vulnerable to the same failure. Treat offsite
resilience as part of the backup strategy, not an afterthought.

- Ensure at least one copy is isolated from a single-site failure.
- Protect backups from accidental or malicious deletion.
- Encrypt archives so that a stolen copy is not a data breach.
- Monitor the backup job and page the on-call engineer on failure.

## Restore drill log
Every restore drill should be recorded so the team can see that backups are regularly proven and how
long recovery actually takes. The log is also useful evidence during audits and incident reviews.

- Record the date of each drill and who performed it.
- Note which backup was restored and to which host.
- Record how long the restore and validation took end to end.
- Capture any problems encountered and the follow-up actions.

Review the log periodically. A drill that has not happened in a long time, or that keeps hitting the
same problem, is a signal to invest in the recovery process before a real incident forces the issue.
""",

    "expense-policy": """
## Corporate cards
Where a corporate card is issued, it is for business expenses only. The card does not change what is
reimbursable; it changes how the expense is paid. Reconcile card charges in the expense portal just
as you would a personal out-of-pocket expense.

- Use the corporate card only for approved business expenses.
- Reconcile every charge with an itemised receipt in the portal.
- Report a lost or stolen card to Finance and the issuer immediately.
- Never use the corporate card for personal purchases, even intending to repay.

## Approvals and limits
Approval requirements scale with amount and category. Most routine expenses need only your manager's
approval; larger or unusual spending needs additional sign-off.

- Routine travel and meals within the limits need manager approval only.
- Client entertainment above the per-head threshold needs manager approval in advance.
- Premium travel needs director approval.
- Anything unusual should be cleared with Finance before you commit the spend.

When an expense is likely to be questioned, attach a short justification up front. A clear note at
submission time is far faster than a back-and-forth after the fact.
""",

    "incident-severity": """
## Examples by severity
Concrete examples make the levels easier to apply under pressure. Use these as a guide, and when a
situation sits between two levels, choose the higher one.

- SEV1: checkout is down for all customers; the primary database is unreachable; customer data has
  been exposed or lost.
- SEV2: payments fail for a region; a core page is badly degraded; a key integration is down with no
  workaround.
- SEV3: a non-critical report is delayed; a cosmetic defect; an issue affecting a handful of users
  with a workaround.

## Severity and response times
Severity drives how quickly and how widely we respond. These expectations exist so that effort
matches impact and nobody has to negotiate the response in the middle of an incident.

- SEV1: immediate response, day or night, with an incident commander and updates every 30 minutes.
- SEV2: prompt response during the day, paged out of hours if customer impact continues.
- SEV3: handled during normal working hours as tracked work.

Downgrade only when customer impact has genuinely reduced, and record the change so the timeline is
accurate.
""",

    "remote-work-policy": """
## Home office setup
A good remote setup protects both your productivity and your health. The annual equipment stipend is
there to help you build one. Prioritise the things you use for hours every day.

- A reliable internet connection suitable for video meetings.
- A comfortable chair and a desk at the right height.
- An external monitor, keyboard, and mouse where helpful.
- Adequate lighting and a quiet space for calls.

Take regular breaks and set up your workspace to avoid strain; the company would rather you invest in
a healthy setup than work through discomfort.

## Hybrid collaboration
Hybrid teams work best when remote and in-office members have an equal experience. Small habits make
a large difference to the people who are not in the room.

- In mixed meetings, have everyone join the video call individually so remote members are equal
  participants.
- Share agendas and notes in writing so decisions are visible to everyone.
- Rotate meeting times fairly across time zones rather than always favouring one.
- Record decisions where distributed colleagues will need them later.
""",

    "api-auth-guide": """
## Testing your integration
Test against the staging environment with a dedicated staging client before going live. This lets you
exercise the full flow without touching production data or limits.

- Register a separate client identity for staging and never reuse production secrets there.
- Verify that your client fetches a token, caches it, and refreshes it before the one-hour expiry.
- Confirm that your error handling behaves correctly for 401, 403, and 429 responses.
- Check that your client only requests the scopes it actually needs.

Once staging looks correct, register a production client, move the secret into your production secret
store, and repeat a brief smoke test before cutting over real traffic.
""",

    "code-review-guidelines": """
## Review checklist
Use this quick checklist as a reviewer. It is not exhaustive, but it covers the issues that most often
matter and are easiest to miss when skimming a diff.

- Does the change do what the description says, including the edge cases?
- Are there tests that would fail without the change, and do they pass with it?
- Will this be understandable to someone reading it in six months?
- Are inputs validated and are secrets kept out of the code and logs?
- Is the change appropriately small and focused on a single concern?
- Does it update any documentation or runbooks that the change makes stale?

If every box is ticked and CI is green, approve. If something is unclear, ask rather than assume.

## Handling disagreements
Most review comments are resolved quickly, but occasionally an author and reviewer disagree. Keep the
discussion focused on the change and the reasoning, not on who is right.

- Explain the trade-off you see and ask for the other person's reasoning.
- If you cannot converge, bring in a third engineer or the code owner for a quick decision.
- Prefer the simpler option that is easier to change later when the evidence is balanced.
- Record the decision in the pull request so the reasoning is not lost.

Disagreements handled well are a strength: they surface assumptions and usually produce a better change
than either person would have made alone.
""",

    "monitoring-setup": """
## Service level objectives
A service level objective expresses, as a target, how reliable a service should be from the customer's
point of view, for example a percentage of requests served successfully and quickly over a window.
Objectives turn vague reliability goals into something measurable that teams can act on.

- Define objectives around customer-visible behaviour, not internal implementation details.
- Track the error budget: the amount of unreliability the objective allows before action is required.
- When the error budget is nearly spent, prioritise reliability work over new features.
- Review objectives periodically so they still reflect what customers actually need.

Alerts derived from these objectives tend to be far better than ad-hoc thresholds, because they fire
on real customer impact rather than on internal noise.
""",

    "onboarding-checklist": """
## Your first 90 days
Onboarding does not end after two weeks. The first ninety days are about going from your first small
change to being a confident, independent contributor to your team.

- By day 30: you are shipping small changes regularly and know who owns what.
- By day 60: you are picking up normal team work and reviewing others' changes.
- By day 90: you are contributing to design discussions and can take an incident shift with support.

Check in with your manager at each milestone. If anything is blocking your progress, surface it early;
onboarding is a shared responsibility, and feedback about rough edges helps the next hire too.

## Working with your buddy
Your onboarding buddy is your first point of contact for the small questions that are faster to ask
than to search for. Use them, and do not worry about asking too much in the early weeks.

- Set up a regular short check-in for your first few weeks.
- Keep a running list of questions so you can batch the small ones.
- Ask your buddy to walk you through a real change and a real incident response.
- Pass on what you learn by improving the docs for the next person.

A good buddy relationship shortens the time to your first confident contribution and makes the whole
team more welcoming.
""",

    "oncall-runbook": """
## Handover notes
A good handover is the difference between a smooth week and a chaotic one. At the end of your rotation,
write a short note for the next engineer covering anything they should watch.

- Open incidents and their current status.
- Recent or upcoming deploys that carry risk.
- Any alert that has been firing and why.
- Temporary silences you set and when they expire.

Keep the note in the agreed place so it is easy to find, and walk through it live at hand-off so the
incoming engineer can ask questions.
""",

    "password-policy": """
## Password managers and shared accounts
An approved password manager is the single most effective way to meet this policy comfortably. It
generates and stores a long, unique password for every system so you never reuse one or have to
remember it.

- Use the approved password manager for all work accounts.
- Protect the manager itself with a strong passphrase and a second factor.
- Avoid shared accounts; where one is unavoidable, manage its credential through the approved tool and
  rotate it when a member leaves.

Shared logins undermine accountability because you cannot tell who did what. Prefer individual accounts
with appropriate access wherever the system supports them.
""",

    "security-standards-2025": """
## Third-party and vendor security
Our security is only as strong as the vendors we rely on. Before integrating a third-party service that
will handle company or customer data, assess its security posture and limit what it can access.

- Review the vendor's security documentation and certifications before integrating.
- Grant the vendor the least access necessary and review it periodically.
- Prefer vendors that support modern authentication and encryption.
- Have a plan to revoke access and export or delete data if the relationship ends.

Record each vendor that handles sensitive data, what it can access, and who owns the relationship, so
the list can be reviewed as part of regular security audits.
""",

    "vpn-access": """
## Performance and connectivity
If the VPN is connected but slow, the bottleneck is usually your local network rather than the VPN
itself. A few checks resolve most performance complaints before they need a ticket.

- Prefer a wired connection or a strong wireless signal for video calls.
- Close bandwidth-heavy applications you are not using.
- If a specific internal site is slow for everyone, report it rather than assuming it is your
  connection.
- Reconnect if the tunnel has been up for a very long time and feels sluggish.

If performance is poor across multiple networks and times of day, open a ticket with IT and include
the specifics so they can investigate the gateway rather than your local setup.
""",
}

for _doc_id, _extra in APPENDIX.items():
    LONG_BODIES[_doc_id] = LONG_BODIES[_doc_id] + _extra

