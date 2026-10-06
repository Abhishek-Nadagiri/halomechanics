# HoloMechanix Deployment Guide

## 1. Local Desktop Execution
The fastest, lowest-latency mode for testing and development.
```bash
# Web Mode (FastAPI + WebSocket + Three.js Browser Client)
python app/main.py --mode web

# Desktop Mode (OpenCV Native Window)
python app/main.py --mode desktop
```

## 2. Docker Deployment (Phase 51)
Run the backend in a containerized environment:
```bash
docker compose up --build
```
Access the application at `http://localhost:8000`.

*Note:* Standard headless cloud Docker instances cannot directly access local client webcams; when deployed to the cloud, the browser frontend uses client-side `navigator.mediaDevices.getUserMedia()`, while the backend processes telemetry via WebSockets.

## 3. Web & Cloud Hosting (Phase 50)
- **Frontend / Static UI**: Can be served via FastAPI or hosted on Vercel/Netlify.
- **Backend API & WebSocket Server**: Suitable for Render, Railway, AWS ECS, or GCP Cloud Run.
