# AI Collaboration Attestation

As required by the assignment brief, this document describes how AI assistance was used during the design, planning, and implementation of this project.

---

## How AI Was Used

### 1. Architecture Design & Planning

I used an AI assistant (Google DeepMind's Antigravity) as a senior engineering reviewer to design the overall system architecture. Specifically:

- **System component breakdown**: The AI helped identify the three-service architecture (React frontend, FastAPI backend, PostgreSQL) and the two-network Docker topology (internal for DB isolation, external for frontend-backend communication).
- **Security review**: After proposing an initial design, I ran it through an AI-assisted audit that surfaced seven critical gaps — including the session ID ownership flaw (clients shouldn't generate their own session IDs), the missing nginx WebSocket headers, and the memory leaks in the frontend.
- **Implementation plan**: The AI produced a phased implementation plan with a 15-commit atomic git strategy, which I used as a checklist throughout development.

### 2. Code Quality Review

The AI acted as a code reviewer, surfacing:
- The need to run MediaPipe in `loop.run_in_executor()` so the async event loop isn't blocked by CPU-intensive detection.
- The `pytest-asyncio` configuration requirement (`asyncio_mode = auto` in `pytest.ini`) without which async tests silently pass without actually running.
- The need to revoke Blob URLs (`URL.revokeObjectURL`) on each frame to prevent browser memory leaks during a live stream.

### 3. What I Did Independently

- Final code implementation, debugging, and integration of all components.
- All design decisions regarding the specific MediaPipe model selection, JPEG quality trade-offs, and frame-rate choice (10fps).
- Testing the end-to-end flow and verifying stream isolation between sessions.
- Git commit authorship and message writing.

---

## AI Tools Used

| Tool | Purpose |
|---|---|
| Google DeepMind Antigravity | Architecture planning, security audit, code review, documentation |

---

## Reflection

The AI collaboration was most valuable during the **planning and audit phase** — it's easy to miss security edge cases (like client-controlled session IDs enabling stream hijacking) when building a system end-to-end solo. Using the AI as a reviewer before writing code, rather than after, meant the architecture was solid from the start rather than patched retrospectively.

The actual implementation — understanding the MediaPipe API, wiring FastAPI's async lifecycle, and debugging Docker networking — required hands-on work that the AI couldn't substitute for.
