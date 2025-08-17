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
