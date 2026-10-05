// Public backend endpoint (Cloud Run). Set this after `gcloud run deploy`.
// For local dev, point at the local uvicorn server.
window.CONFIG = {
  // e.g. "https://truthkeeper-api-xxxxx-uc.a.run.app"
  CLOUD_RUN_URL: "http://localhost:8080",
};
