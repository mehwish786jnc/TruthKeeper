# TASK.md — TruthKeeper

Simple status board. What's done, what you need to set up, and what's next.

**Last updated: 2026-10-09**

---

## In one line
TruthKeeper reads your documents and flags the ones that are wrong, out of date, or
contradict each other. The app and 15 sample documents already work offline for free.
To put it on the internet, we need to set up some Google Cloud accounts.

---

## Done ✅
- The backend (the "brain" that audits documents) is written.
- The website is built: dashboard, Ask AI, Knowledge, Graph, Add Documents, Decisions, Actions, Settings, and a landing page.
- 15 sample documents are made as real PDF files (about 6 pages each).
- Everything runs offline on demo data — no login, no cost.
- Code is on GitHub.

---

## Accounts YOU need to create (my part can't be done without these)
These need your login and a payment method, so only you can do them.
Nothing here costs money for our use — but a card/credit must be on file.

1. **Google Cloud account + a project** (turn on billing — use the $300 free credit).
   This is the main one. Gemini and Document AI need billing switched on, even though
   our real cost stays about $0.
2. **Firebase project** — link it to the same Google Cloud project. This hosts the website.
3. **Log in to the tools on your computer:**
   - `gcloud auth login`
   - `gcloud auth application-default login`
   - `firebase login`
4. **(Optional) AI Studio key** from aistudio.google.com — only for the free backup model.
   Skip if you don't want it.

GitHub is already set up.

> Don't want to add a card at all? We can stay on the free AI Studio key + the built-in
> fallback instead of Google Cloud. It won't be a full cloud deploy, but it stays free.

---

## What's next (in order)

### 1. Save the current work
- [ ] Commit and push the 15 PDFs and the updated files.

### 2. Make the app dynamic (backend work)
Right now the documents are typed into the code (hard-coded) and uploads only save in the
browser. "Dynamic" means the documents live in the database, and adding, auditing, or
deleting one actually updates everywhere. This is the main backend job.

**Database**
- [ ] Add a "documents" area in Firestore (save a document, get one, list all, delete one).
- [ ] Load the 15 PDFs into it: read each PDF's text (with Document AI, and a free offline
      reader as backup), then save it.
- [ ] Keep a copy of the documents on disk so the app still works offline for free.

**Backend endpoints (what the website can ask the backend to do)**
- [ ] Upload a document (send a PDF → read its text → save it → audit it → return the result).
- [ ] List all documents (from the database).
- [ ] Delete a document (and its audit result).
- [ ] Make the backend load documents from the database first, and fall back to the disk copy
      if the database isn't available.

**Website (make it use the backend instead of the fake data)**
- [ ] When connected to the backend, load the real documents and audit results from it.
- [ ] Let "Add Documents" upload a real PDF that gets saved and audited for real.
- [ ] Make delete and re-audit actually change the database.
- [ ] If there's no backend, keep showing the offline demo data (so it never breaks).

**Built to grow (later)**
- [ ] Leave simple hooks so other sources (company wiki, runbooks) can be plugged in later
      without rebuilding this.

**Done when:** you upload a PDF in the website, it gets saved and audited, and it shows up in
the Knowledge list and the Graph with a real status — and offline mode still works.


### 3. Set up Google Cloud *(needs your accounts above)*
- [ ] Create the project, turn on billing, set a $5 budget alert.
- [ ] Turn on the needed services and create the database.

### 4. Put it online
- [ ] Deploy the backend (Cloud Run).
- [ ] Deploy the website (Firebase Hosting).
- [ ] Point the website at the backend.

### 5. Make it demo-proof
- [ ] Run the audit once so results are saved and the demo is instant.
- [ ] Check it works logged-out, offline, and never shows a broken screen.

### 6. Submission
- [ ] Record a short demo video (under 4 minutes).
- [ ] Write the description and fill the pitch deck.

---

## Rules to remember
- Use Google models only (Gemini / Gemma).
- Audit each document once, save the result, and just read it after that (keeps it fast and free).
- Keep cost near $0.
- It must always work even when logged out or offline.
- Never put passwords or keys in the code.

## Done when
The website is live on a public link, shows the flagged documents with evidence, uses
Google Cloud behind it, and the 15 documents live in the database — all for about $0.
