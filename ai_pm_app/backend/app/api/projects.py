from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from ..db.database import get_session
from ..models.entities import Project, Outcome, Benefit, Deliverable, Task, BudgetLine, GovernanceEvent, ReportSpec, Risk
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
    return apply_suggestions(session, project_id, req)

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
