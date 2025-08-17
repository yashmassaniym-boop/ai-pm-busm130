
from typing import Dict, Any, List
from sqlmodel import Session
from ..models.schemas import GenProject, GenOutcome, GenBenefit, GenDeliverable, GenTask, GenBudgetLine, GenGovernanceEvent, GenReportSpec, GenRisk
from ..models.entities import Project, Outcome, Benefit, Deliverable, Task, BudgetLine, GovernanceEvent, ReportSpec, Risk

def build_prompt(vision: str) -> str:
    # For now this is just a placeholder. Later, you’ll add seeds/constraints here.
    return f"Generate a project plan for: {vision}"

def llm_generate_fixture(vision: str) -> Dict[str, Any]:
    # A small, valid example matching GenProject strictly.
    return {
        "name": f"{vision[:32]} Plan",
        "vision": vision,
        "description": "Auto-generated demo plan (fixture).",
        "outcomes": [
            {
                "name": "Outcome A: Faster response",
                "description": "Improve support response time.",
                "benefits": [
                    {
                        "name": "24/7 coverage",
                        "description": "Round-the-clock help",
                        "deliverables": [
                            {
                                "name": "Chatbot MVP",
                                "description": "Basic flows and FAQs",
                                "tasks": [
                                    {"name": "Design intents", "est_days": 3, "depends_on_index": None},
                                    {"name": "Implement flows", "est_days": 5, "depends_on_index": 0},
                                ],
                            }
                        ],
                    }
                ],
            },
            {
                "name": "Outcome B: Lower cost per ticket",
                "description": "Automate triage and routing.",
                "benefits": [
                    {
                        "name": "Automation savings",
                        "description": "Reduce manual handling",
                        "deliverables": [
                            {
                                "name": "Auto-routing",
                                "description": "Integrate with ticketing",
                                "tasks": [
                                    {"name": "Baseline metrics", "est_days": 2, "depends_on_index": None},
                                    {"name": "Integrate ticket system", "est_days": 4, "depends_on_index": 0},
                                ],
                            }
                        ],
                    }
                ],
            },
        ],
        "budget": [
            {"item": "LLM API credits", "amount": 500.0, "category": "Opex"}
        ],
        "governance": [
            {"name": "Steering Committee", "cadence": "biweekly", "owner": "Sponsor"}
        ],
        "reporting": [
            {"name": "Weekly status", "frequency": "weekly", "audience": "PMO"}
        ],
        "risks": [
            {"title": "Inaccurate outputs", "probability": 3, "impact": 3, "mitigation": "Strict schema + validation"}
        ],
    }

def validate_generated(raw: Dict[str, Any]) -> GenProject:
    # Pydantic enforces structure and types
    return GenProject(**raw)

def persist_generated(session: Session, gen: GenProject) -> int:
    # Insert Project
    p = Project(name=gen.name, vision=gen.vision, description=gen.description)
    session.add(p)
    session.commit()
    session.refresh(p)

    # Walk tree inserting rows
    for o in gen.outcomes:
        o_row = Outcome(project_id=p.id, name=o.name, description=o.description)
        session.add(o_row); session.commit()
        for b in o.benefits:
            b_row = Benefit(outcome_id=o_row.id, name=b.name, description=b.description)
            session.add(b_row); session.commit()
            for d in b.deliverables:
                d_row = Deliverable(benefit_id=b_row.id, name=d.name, description=d.description)
                session.add(d_row); session.commit()
                # build tasks and resolve depends_on_index -> task ids
                task_ids: List[int] = []
                for idx, t in enumerate(d.tasks):
                    t_row = Task(deliverable_id=d_row.id, name=t.name, est_days=t.est_days, depends_on_id=None)
                    session.add(t_row); session.commit(); session.refresh(t_row)
                    task_ids.append(t_row.id)
                # now set depends_on_id if any
                for idx, t in enumerate(d.tasks):
                    if t.depends_on_index is not None:
                        depends_idx = t.depends_on_index
                        if depends_idx < 0 or depends_idx >= len(task_ids):
                            # invalid reference; skip instead of failing hard
                            continue
                        target_id = task_ids[depends_idx]
                        tr = session.get(Task, task_ids[idx])
                        tr.depends_on_id = target_id
                        session.add(tr)
                session.commit()

    for bl in gen.budget:
        session.add(BudgetLine(project_id=p.id, item=bl.item, amount=bl.amount, category=bl.category))
    for g in gen.governance:
        session.add(GovernanceEvent(project_id=p.id, name=g.name, cadence=g.cadence, owner=g.owner))
    for r in gen.reporting:
        session.add(ReportSpec(project_id=p.id, name=r.name, frequency=r.frequency, audience=r.audience))
    for rk in gen.risks:
        session.add(Risk(project_id=p.id, title=rk.title, probability=rk.probability, impact=rk.impact, mitigation=rk.mitigation))

    session.commit()
    return p.id

def generate_and_persist(session: Session, vision: str) -> int:
    # 1) build prompt (stubbed)
    _prompt = build_prompt(vision)

    # 2) (Stub) call fixture instead of a real LLM
    raw = llm_generate_fixture(vision)

    # 3) validate against strict schema
    gen = validate_generated(raw)

    # 4) persist to DB and return new id
    return persist_generated(session, gen)
