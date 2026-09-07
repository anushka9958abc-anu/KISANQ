# KISANQ

Agriculture procurement status platform: smart slots, live queues, crowd prediction, GIS centres, and officer analytics.

## Run locally (Docker)

```bash
docker compose up --build
```

- App: http://localhost:5173
- API: http://localhost:8000/docs

Demo farmer: `9876543210` / `farmer123`  
Demo admin: `9990001111` / `admin123`

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | React + Tailwind |
| API | Python FastAPI |
| Notifications | Node.js (SMPP SMS + WhatsApp worker) |
| Offline | SMPP gateway + Asterisk IVR (`ivr/kisanq_ivr.py`) |
| Data | PostgreSQL + PostGIS, Redis |
| Hardware | ESP32 gate sketch + handheld QR (`iot/esp32_gate_scanner.ino`) |
| Deploy | Docker Compose, Kubernetes (`infra/k8s`), AWS / MeghRaj |

Without Docker: start PostGIS and Redis, then `pip install -r backend/requirements.txt`, `python -m app.seed` from `backend`, `uvicorn app.main:app --reload`, and `npm install && npm run dev` in `frontend`.
