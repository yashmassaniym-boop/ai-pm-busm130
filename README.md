# AI-Augmented PM System (BUSM130)

A schema-first, human-in-the-loop assistant that turns a Vision into a structured plan
(Vision → Outcomes → Benefits → Deliverables → Tasks + Budget/Governance/Reporting/Risks).
Includes preview→apply propagation and an API-generated dashboard.

## Quick start
```bash
pip install -r requirements.txt
python -m uvicorn ai_pm_app.backend.app.main:app --host 0.0.0.0 --port 8081
```
Open: http://127.0.0.1:8081/ui

## Key endpoints
- GET /health
- POST /projects/generate → { "project_id": n }
- GET /projects/{id} → nested plan
- POST /projects/{id}/propagate/preview
- POST /projects/{id}/propagate/apply
- GET /ui → API-generated dashboard

## Architecture
- Backend: FastAPI + SQLite + Pydantic (strict schema validation)
- Propagation: non-destructive preview → explicit apply
- Swap-ready: generator stub can be replaced by an LLM that returns the same JSON

## Next milestones
- KPI endpoints + Budget/Risk summaries
- Gantt fields + timeline endpoints
- Professional dashboard frontend (React)
- Deploy API & dashboard online

## License
MIT © Your Name

## Live Demo
- Dashboard: https://ai-pm-busm130.onrender.com/dashboard  
- API docs (OpenAPI): https://ai-pm-busm130.onrender.com/docs  
- Health: https://ai-pm-busm130.onrender.com/health

## Evidence (PRINCE2 Agile)
- Evidence pack (JSON snapshots + README) is versioned in `reports/` and attached to GitHub Releases.
- Includes **baseline** and **after** snapshots for: KPIs, Backlog, Budget, Risk, Timeline, Burn-down, Velocity.
- Aligns to PRINCE2 Agile controls: backlog status, sprint burn/velocity, stage/timeline planning, cost control, and change audit (Activity Log).

## How to Reproduce (Local)
    git clone https://github.com/yashmassaniym-boop/ai-pm-busm130
    cd ai-pm-busm130
    python -m pip install -r requirements.txt
    uvicorn ai_pm_app.backend.app.main:app --host 0.0.0.0 --port 8092
    # open http://127.0.0.1:8092/dashboard

## Architecture (brief)
- FastAPI backend, SQLModel demo DB, Pydantic schemas.
- Static HTML/JS dashboard served by FastAPI.
- LLM choice documented in thesis (Hugging Face / OpenAI): why and structure.

## PRINCE2 Agile Mapping
- Managing Product Delivery → Backlog statuses (To-Do / In-Progress / Done).
- Controlling a Stage → Burn-down, Velocity, Timeline.
- Managing a Stage Boundary → Baseline vs After evidence captured from LIVE.
- Progress Controls → Budget summary & Activity Log.

_Last updated: 2025-08-18_
