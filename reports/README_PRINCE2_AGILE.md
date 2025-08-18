# Evidence Pack — AI-Augmented PM System (PID=2)

This folder contains JSON snapshots pulled from the **live deployment** at
`https://ai-pm-busm130.onrender.com` for project_id **2**.

## Files
- `baseline_*.json` (if present): initial state captured before sprint work.
- `after_*.json`: state after sprint simulation (two tasks moved to *Done*).
- Endpoints mirror the dashboard: `/kpis`, `/budget/summary`, `/risk/summary`,
  `/backlog`, `/timeline`, `/burn`, `/velocity`.

## How this maps to PRINCE2 Agile
- **Backlog (To-Do/In-Progress/Done)** — work packages with status controls.
- **Burn-down & Velocity** — sprint tracking and throughput KPIs.
- **Timeline (Gantt-style)** — stage/iteration planning view.
- **Budget summary** — cost control reporting.
- **Activity Log** (server-side) — auditable log of applied changes.

The dashboard shows the same data products the JSON contains; screenshots of the live
dashboard (before/after) accompany these files in the dissertation appendix.
