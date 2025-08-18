from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from ..db.database import get_session
from ..models.entities import Project, Outcome, Benefit, Deliverable, Task, BudgetLine, GovernanceEvent, ReportSpec, Risk, ActivityLog, TaskState
from ..models.propagation_schemas import PropagationRequest, ApplyRequest
from ..services.generator import generate_and_persist
from ..services.propagation import preview_propagation, apply_suggestions

router = APIRouter(prefix="/projects", tags=["projects"])

class VisionReq(BaseModel):
    vision: str

@router.post("/generate")
def generate_project(req: VisionReq, session: Session = Depends(get_session)):
    new_id = generate_and_persist(session, req.vision)
    return {"project_id": new_id}

@router.post("/seed")
def seed_project(session: Session = Depends(get_session)):
    p = Project(name="AI Rollout", vision="Use AI to streamline support", description="Demo seed")
    session.add(p); session.commit(); session.refresh(p)

    o1 = Outcome(project_id=p.id, name="Faster response times")
    o2 = Outcome(project_id=p.id, name="Lower cost per ticket")
    session.add_all([o1, o2]); session.commit(); session.refresh(o1); session.refresh(o2)

    b11 = Benefit(outcome_id=o1.id, name="24/7 coverage")
    b12 = Benefit(outcome_id=o1.id, name="Reduced wait time")
    b21 = Benefit(outcome_id=o2.id, name="Automation savings")
    session.add_all([b11,b12,b21]); session.commit()

    d111 = Deliverable(benefit_id=b11.id, name="Chatbot MVP")
    d121 = Deliverable(benefit_id=b12.id, name="Queue optimizer")
    d211 = Deliverable(benefit_id=b21.id, name="Auto-routing")
    session.add_all([d111,d121,d211]); session.commit()

    t1 = Task(deliverable_id=d111.id, name="Design intents", est_days=3)
    t2 = Task(deliverable_id=d111.id, name="Implement flows", est_days=5)
    t3 = Task(deliverable_id=d121.id, name="Baseline metrics", est_days=2)
    t4 = Task(deliverable_id=d211.id, name="Integrate ticket system", est_days=4)
    session.add_all([t1,t2,t3,t4])

    session.add_all([
        BudgetLine(project_id=p.id, item="LLM API credits", amount=500.0, category="Opex"),
        GovernanceEvent(project_id=p.id, name="Steering Committee", cadence="biweekly", owner="Sponsor"),
        ReportSpec(project_id=p.id, name="Weekly status", frequency="weekly", audience="PMO"),
        Risk(project_id=p.id, title="Hallucinations in responses", probability=3, impact=4, mitigation="Schema + validation"),
    ])
    session.commit()
    return {"project_id": p.id}

@router.post("/{project_id}/propagate/preview")
def propagate_preview(project_id: int, req: PropagationRequest, session: Session = Depends(get_session)):
    return preview_propagation(session, project_id, req)

@router.post("/{project_id}/propagate/apply")
def propagate_apply(project_id: int, req: ApplyRequest, session: Session = Depends(get_session)):
    def fetch_old(op):
        model_map = {
            "project": Project, "outcome": Outcome, "benefit": Benefit,
            "deliverable": Deliverable, "task": Task, "budget": BudgetLine, "risk": Risk
        }
        mdl = model_map.get(op.entity)
        if not mdl:
            return None
        row = session.get(mdl, op.id)
        return getattr(row, op.field, None) if row else None

    # Snapshot old values
    oldmap = []
    for op in req.ops:
        try:
            oldmap.append((op, fetch_old(op)))
        except Exception:
            oldmap.append((op, None))

    # Apply via service
    applied = apply_suggestions(session, project_id, req)

    # Write audit logs
    for op, old in oldmap:
        try:
            session.add(ActivityLog(
                project_id=project_id,
                entity=op.entity,
                entity_id=op.id,
                field=op.field,
                old_value=None if old is None else str(old),
                new_value=None if op.new_value is None else str(op.new_value),
            ))
        except Exception:
            pass
    session.commit()
    return {"applied": applied}


@router.get("/{project_id}")
def get_project_tree(project_id: int, session: Session = Depends(get_session)):
    p = session.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    out = {
        "id": p.id, "name": p.name, "vision": p.vision, "description": p.description,
        "outcomes": [], "budget": [], "governance": [], "reporting": [], "risks": [],
    }

    outcomes = session.exec(select(Outcome).where(Outcome.project_id==p.id)).all()
    for o in outcomes:
        o_dict = {"id": o.id, "name": o.name, "description": o.description, "benefits": []}
        benefits = session.exec(select(Benefit).where(Benefit.outcome_id==o.id)).all()
        for b in benefits:
            b_dict = {"id": b.id, "name": b.name, "description": b.description, "deliverables": []}
            dels = session.exec(select(Deliverable).where(Deliverable.benefit_id==b.id)).all()
            for d in dels:
                d_dict = {"id": d.id, "name": d.name, "description": d.description, "tasks": []}
                tasks = session.exec(select(Task).where(Task.deliverable_id==d.id)).all()
                for t in tasks:
                    d_dict["tasks"].append({"id": t.id, "name": t.name, "est_days": t.est_days, "depends_on_id": t.depends_on_id})
                b_dict["deliverables"].append(d_dict)
            o_dict["benefits"].append(b_dict)
        out["outcomes"].append(o_dict)

    out["budget"] = [
        {"id": bl.id, "item": bl.item, "amount": bl.amount, "category": bl.category}
        for bl in session.exec(select(BudgetLine).where(BudgetLine.project_id==p.id)).all()
    ]
    out["governance"] = [
        {"id": g.id, "name": g.name, "cadence": g.cadence, "owner": g.owner}
        for g in session.exec(select(GovernanceEvent).where(GovernanceEvent.project_id==p.id)).all()
    ]
    out["reporting"] = [
        {"id": r.id, "name": r.name, "frequency": r.frequency, "audience": r.audience}
        for r in session.exec(select(ReportSpec).where(ReportSpec.project_id==p.id)).all()
    ]
    out["risks"] = [
        {"id": r.id, "title": r.title, "probability": r.probability, "impact": r.impact, "mitigation": r.mitigation}
        for r in session.exec(select(Risk).where(Risk.project_id==p.id)).all()
    ]
    return out

from datetime import datetime, timedelta, date

@router.get("/{project_id}/kpis")
def kpis(project_id: int, session: Session = Depends(get_session)):
    p = session.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    # Outcomes
    outcomes_list = session.exec(select(Outcome).where(Outcome.project_id == p.id)).all()
    outcome_count = len(outcomes_list)

    # Benefits, Deliverables, Tasks (count via .all() then len())
    benefit_count = 0
    deliverable_count = 0
    task_count = 0
    for o in outcomes_list:
        benefits = session.exec(select(Benefit).where(Benefit.outcome_id == o.id)).all()
        benefit_count += len(benefits)
        for b in benefits:
            dels = session.exec(select(Deliverable).where(Deliverable.benefit_id == b.id)).all()
            deliverable_count += len(dels)
            for d in dels:
                tasks = session.exec(select(Task).where(Task.deliverable_id == d.id)).all()
                task_count += len(tasks)

    logs = session.exec(select(ActivityLog).where(ActivityLog.project_id == p.id)).all()

    return {
        "project_id": p.id,
        "name": p.name,
        "vision": p.vision,
        "counts": {
            "outcomes": outcome_count,
            "benefits": benefit_count,
            "deliverables": deliverable_count,
            "tasks": task_count
        },
        "activity_applied": len(logs),
        "schema_pass_rate": 1.0  # stub generator => always valid
    }


@router.get("/{project_id}/budget/summary")
def budget_summary(project_id: int, session: Session = Depends(get_session)):
    p = session.get(Project, project_id)
    if not p: raise HTTPException(status_code=404, detail="Project not found")
    lines = session.exec(select(BudgetLine).where(BudgetLine.project_id==p.id)).all()
    total = sum((bl.amount or 0) for bl in lines)
    by_cat = {}
    for bl in lines:
        cat = bl.category or "Uncategorised"
        by_cat[cat] = by_cat.get(cat, 0.0) + float(bl.amount or 0.0)
    return {"project_id": p.id, "total": total, "by_category": by_cat, "count": len(lines)}

@router.get("/{project_id}/risk/summary")
def risk_summary(project_id: int, session: Session = Depends(get_session)):
    p = session.get(Project, project_id)
    if not p: raise HTTPException(status_code=404, detail="Project not found")
    risks = session.exec(select(Risk).where(Risk.project_id==p.id)).all()
    # 5x5 matrix (1..5)
    matrix = {i:{j:0 for j in range(1,6)} for i in range(1,6)}
    for r in risks:
        pr = int(getattr(r, "probability", 0) or 0); im = int(getattr(r, "impact", 0) or 0)
        pr = min(max(pr,1),5); im = min(max(im,1),5)
        matrix[pr][im] += 1
    return {"project_id": p.id, "count": len(risks), "matrix": matrix}

@router.get("/{project_id}/timeline")
def timeline(project_id: int, start: str | None = None, session: Session = Depends(get_session)):
    """
    Returns a simple, computed Gantt-friendly timeline using Task.est_days.
    Optional query param ?start=YYYY-MM-DD sets the project start; default = today (UTC).
    Tasks are sequenced per Deliverable in the order they exist.
    """
    p = session.get(Project, project_id)
    if not p: raise HTTPException(status_code=404, detail="Project not found")
    try:
        t0 = date.fromisoformat(start) if start else datetime.utcnow().date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ?start date")

    plan = []
    oc = session.exec(select(Outcome).where(Outcome.project_id==p.id)).all()
    for o in oc:
        bs = session.exec(select(Benefit).where(Benefit.outcome_id==o.id)).all()
        for b in bs:
            ds = session.exec(select(Deliverable).where(Deliverable.benefit_id==b.id)).all()
            for d in ds:
                cursor = t0
                ts = session.exec(select(Task).where(Task.deliverable_id==d.id)).all()
                for t in ts:
                    days = int(getattr(t, "est_days", 1) or 1)
                    start_d = cursor
                    end_d = cursor + timedelta(days=max(days,1))
                    plan.append({
                        "deliverable_id": d.id, "deliverable": d.name,
                        "task_id": t.id, "task": t.name,
                        "start": start_d.isoformat(), "end": end_d.isoformat(),
                        "duration_days": days
                    })
                    cursor = end_d  # chain tasks within a deliverable
    return {"project_id": p.id, "start": t0.isoformat(), "items": plan}


from datetime import datetime, timedelta, date

class TaskPatch(BaseModel):
    est_days: int | None = None
    status: str | None = None   # todo|inprogress|done
    done: bool | None = None

@router.patch("/tasks/{task_id}")
def patch_task(task_id: int, body: TaskPatch, session: Session = Depends(get_session)):
    t = session.get(Task, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update est_days
    if body.est_days is not None:
        old = t.est_days
        t.est_days = int(max(1, body.est_days))
        try:
            session.add(ActivityLog(project_id=getattr(t, "project_id", 0),
                                    entity="task", entity_id=task_id, field="est_days",
                                    old_value=str(old), new_value=str(t.est_days)))
        except Exception:
            pass

    # Upsert TaskState for status/done
    ts = session.exec(select(TaskState).where(TaskState.task_id == task_id)).first()
    if not ts:
        ts = TaskState(task_id=task_id)
        session.add(ts)
        session.flush()

    changed = False
    if body.status is not None:
        old = ts.status
        ts.status = body.status.lower()
        ts.done = (ts.status == "done") if body.done is None else bool(body.done)
        ts.updated_at = datetime.utcnow()
        changed = True
        try:
            session.add(ActivityLog(project_id=0, entity="task", entity_id=task_id,
                                    field="status", old_value=old, new_value=ts.status))
        except Exception:
            pass

    if body.done is not None:
        old = ts.done
        ts.done = bool(body.done)
        ts.status = "done" if ts.done else (ts.status if ts.status != "done" else "inprogress")
        ts.updated_at = datetime.utcnow()
        changed = True
        try:
            session.add(ActivityLog(project_id=0, entity="task", entity_id=task_id,
                                    field="done", old_value=str(old), new_value=str(ts.done)))
        except Exception:
            pass

    if changed or body.est_days is not None:
        session.add(ts)
        session.add(t)
        session.commit()
    return {"ok": True}

@router.get("/{project_id}/backlog")
def backlog(project_id: int, session: Session = Depends(get_session)):
    p = session.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    rows = []
    oc = session.exec(select(Outcome).where(Outcome.project_id == p.id)).all()
    for o in oc:
        bs = session.exec(select(Benefit).where(Benefit.outcome_id == o.id)).all()
        for b in bs:
            ds = session.exec(select(Deliverable).where(Deliverable.benefit_id == b.id)).all()
            for d in ds:
                tsks = session.exec(select(Task).where(Task.deliverable_id == d.id)).all()
                for t in tsks:
                    st = session.exec(select(TaskState).where(TaskState.task_id == t.id)).first()
                    status = (st.status if st else "todo")
                    done = bool(st.done) if st else False
                    rows.append({
                        "task_id": t.id, "task": t.name, "deliverable": d.name,
                        "est_days": int(getattr(t, "est_days", 1) or 1),
                        "status": status, "done": done
                    })
    cols = {"todo": [], "inprogress": [], "done": []}
    for r in rows:
        (cols[r["status"]] if r["status"] in cols else cols["todo"]).append(r)
    return {"project_id": p.id, "columns": cols, "count": len(rows)}

@router.get("/{project_id}/burn")
def burn(project_id: int, start: str | None = None, sprint_days: int = 14, session: Session = Depends(get_session)):
    p = session.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        t0 = date.fromisoformat(start) if start else datetime.utcnow().date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ?start date")

    tasks = []
    oc = session.exec(select(Outcome).where(Outcome.project_id == p.id)).all()
    for o in oc:
        bs = session.exec(select(Benefit).where(Benefit.outcome_id == o.id)).all()
        for b in bs:
            ds = session.exec(select(Deliverable).where(Deliverable.benefit_id == b.id)).all()
            for d in ds:
                tsks = session.exec(select(Task).where(Task.deliverable_id == d.id)).all()
                for t in tsks:
                    points = int(getattr(t, "est_days", 1) or 1)
                    st = session.exec(select(TaskState).where(TaskState.task_id == t.id)).first()
                    done_date = st.updated_at.date() if (st and st.done and st.updated_at) else None
                    tasks.append({"points": points, "done_date": done_date})

    total = sum(x["points"] for x in tasks) or 0
    days = max(1, int(sprint_days))
    labels = [(t0 + timedelta(days=i)) for i in range(days+1)]

    ideal = [round(total * (1 - i/days), 2) for i in range(days+1)]
    actual = []
    for dte in labels:
        done_sum = sum(x["points"] for x in tasks if x["done_date"] and x["done_date"] <= dte)
        actual.append(max(0, total - done_sum))

    return {
        "project_id": p.id,
        "start": t0.isoformat(),
        "sprint_days": days,
        "labels": [d.isoformat() for d in labels],
        "ideal": ideal,
        "actual": actual,
        "total_points": total
    }

@router.get("/{project_id}/velocity")
def velocity(project_id: int, start: str | None = None, sprint_days: int = 14, periods: int = 4, session: Session = Depends(get_session)):
    p = session.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        t0 = date.fromisoformat(start) if start else datetime.utcnow().date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ?start date")
    days = max(1, int(sprint_days))

    done = []
    oc = session.exec(select(Outcome).where(Outcome.project_id == p.id)).all()
    for o in oc:
        bs = session.exec(select(Benefit).where(Benefit.outcome_id == o.id)).all()
        for b in bs:
            ds = session.exec(select(Deliverable).where(Deliverable.benefit_id == b.id)).all()
            for d in ds:
                tsks = session.exec(select(Task).where(Task.deliverable_id == d.id)).all()
                for t in tsks:
                    st = session.exec(select(TaskState).where(TaskState.task_id == t.id)).first()
                    if st and st.done and st.updated_at:
                        pts = int(getattr(t, "est_days", 1) or 1)
                        done.append((st.updated_at.date(), pts))

    vel = []
    labels = []
    for i in range(int(periods)):
        s = t0 + timedelta(days=i*days)
        e = s + timedelta(days=days)
        labels.append(f"S{i+1} {s.isoformat()}→{e.isoformat()}")
        vel.append(sum(pts for (dd, pts) in done if s <= dd < e))
    return {"project_id": p.id, "sprint_days": days, "labels": labels, "velocity": vel}

@router.get("/{project_id}/cadence")
def cadence(project_id: int, start: str | None = None, sprint_days: int = 14):
    try:
        t0 = date.fromisoformat(start) if start else datetime.utcnow().date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ?start date")
    days = max(1, int(sprint_days))
    today = datetime.utcnow().date()
    sprint_idx = ((today - t0).days // days) + 1
    cur_start = t0 + timedelta(days=(sprint_idx-1)*days)
    cur_end = cur_start + timedelta(days=days)
    next_review = cur_end
    return {
        "start": t0.isoformat(),
        "sprint_days": days,
        "current_sprint": sprint_idx,
        "current_window": {"start": cur_start.isoformat(), "end": cur_end.isoformat()},
        "ceremonies": {"review": next_review.isoformat(), "retro": next_review.isoformat()}
    }
