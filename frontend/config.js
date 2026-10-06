// Public backend endpoint (Cloud Run). Set this after `gcloud run deploy`.
// For local dev, point at the local uvicorn server.
// Leave CLOUD_RUN_URL empty ("") to force offline demo mode (sample data).
window.CONFIG = {
  // e.g. "https://truthkeeper-api-xxxxx-uc.a.run.app"
  CLOUD_RUN_URL: "",

  // Only needed if the backend enforces AUDIT_TOKEN on POST /audit.
  AUDIT_TOKEN: "",
};
