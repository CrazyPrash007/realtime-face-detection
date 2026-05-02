# Real-Time Face Detection Video Streaming System

This is a containerized backend API and frontend application that accepts a video feed, processes it to detect a face using MediaPipe and PIL (strictly avoiding OpenCV), stores ROI data in PostgreSQL, and streams the processed feed to viewers.

## Requirements
- Docker & Docker Compose

## Quickstart
1. Rename `.env.example` to `.env` and fill in any required variables.
2. Run `docker-compose up --build`
3. Navigate to `http://localhost:5173` (Frontend)

## Security
- **Secrets**: Managed via `.env` and validated with `pydantic_settings`.
- **CORS**: Strict allowed origins configured via environment.
- **WebSocket Frame Size**: Capped to prevent memory exhaustion DoS attacks.
- **Database**: Runs on an isolated internal network with a least-privilege user (`faceuser`).
- **Connection Limits**: IP-based limits enforced on the WebSocket endpoints.
