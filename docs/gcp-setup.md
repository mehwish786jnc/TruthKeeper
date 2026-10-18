# Google Cloud / Firebase setup — simple guide

You do the steps below (they need your login + a card). When you finish, tell the
assistant and it will do the rest (turning on services, database, deploy).

Cost: with the free $300 credit, a $5 budget alert, and scale-to-zero, this stays about $0.
A card is only for identity — Google does **not** auto-charge you after the trial; you'd have
to manually upgrade for that to happen.

---

## 1. Google account
You probably already have one (Gmail). If not, make one at https://accounts.google.com.

## 2. Google Cloud + free trial
1. Go to https://console.cloud.google.com
2. Accept the terms. Click **"Activate"** / **"Start free"** for the $300 free trial.
3. Enter your details and a card (for verification — not charged).
4. You now have a billing account with the free credit.

## 3. Create the project
1. Top bar → project dropdown → **New Project**.
2. Name it **truthkeeper** → Create.
3. Make sure that project is selected in the top bar.

## 4. Set a budget alert (safety)
1. Search bar → **Billing** → **Budgets & alerts** → **Create budget**.
2. Amount: **$5**. Save. (You'll get an email if spend ever approaches it.)

## 5. Firebase project (hosts the website)
1. Go to https://console.firebase.google.com
2. **Add project** → choose the **existing** `truthkeeper` project (don't make a new one).
3. Accept defaults. You can skip Google Analytics.

## 6. Install the command-line tools (on your Mac)
Open the Terminal and run:

- Google Cloud CLI:  `brew install --cask google-cloud-sdk`
  (or installer: https://cloud.google.com/sdk/docs/install)
- Firebase CLI:  `npm install -g firebase-tools`
  (or: `curl -sL https://firebase.tools | bash`)

## 7. Log in from the Terminal
Run these and complete the browser pop-ups:

- `gcloud auth login`
- `gcloud auth application-default login`
- `gcloud config set project truthkeeper`
- `firebase login`

## 8. (Optional) Free Gemini key — no card
Only if you want the free backup model path:
1. Go to https://aistudio.google.com/app/apikey
2. **Create API key**. Copy it. (Give it to the assistant to put in Secret Manager / `.env` —
   never commit it.)

---

## When you're done
Tell the assistant: **"accounts are ready"** plus your project id (e.g. `truthkeeper`).
It will then:
- turn on the needed services (Run, Vertex AI, Firestore, Document AI, Secret Manager),
- create the Firestore database and a Document AI processor,
- deploy the backend (Cloud Run) and the website (Firebase Hosting),
- load the 15 documents and pre-run the audit so the demo is instant.

## If you decide NOT to add a card
Tell the assistant. It will keep everything on the free AI Studio key + offline fallback
(no Cloud Run / Firestore deploy). Good for a demo video, but not a full live cloud deploy.
