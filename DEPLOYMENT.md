# Deployment guide

## Local development

On Windows, run `./run.ps1` from PowerShell (use `-Reload` while developing). On Linux/macOS, install `requirements.txt`, run `python team3-ml-simulation/train_models.py` once, then start `uvicorn main:app --app-dir team2-backend --host 0.0.0.0 --port 8000`.

Open `http://localhost:8000/`; dashboard pages and assets are served by the FastAPI process. Check `GET /health` before putting the service behind a load balancer. A `healthy` state includes loaded ML artifacts; `degraded` means the heuristic fallback is active.

## Containers

Copy `.env.example` to `.env`, adjust `HOST_PORT` and any model path values, then run `docker compose up --build`. The image trains deterministic synthetic-data models during its build and ships those artifacts. Production should normally build/version that image in CI, not train at runtime.

## Production placeholders

Set `MODEL_REGISTRY_URL` and replace the image-bundled model copy with your approved registry download or mounted read-only volume. Configure the reverse proxy, domain, TLS certificates, firewall rules, secrets manager, telemetry persistence, monitoring, and alert escalation in your infrastructure layer. Do not expose this simulation system as an industrial safety control without an independent safety review and real-sensor validation.
