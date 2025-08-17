
from typing import List, Tuple, Dict, Any
from sqlmodel import Session, select
from ..models.propagation_schemas import ChangeItem, SuggestedOp, PropagationRequest, PropagationPreview, ApplyRequest, ApplyResult
from ..models.entities import Project, Outcome, Benefit, Deliverable, Task, BudgetLine

MODEL_MAP = {
    "project": Project,
    "outcome": Outcome,
    "benefit": Benefit,
    "deliverable": Deliverable,
    "task": Task,
    "budget": BudgetLine,
}

def _get_row(session: Session, entity: str, _id: int):
    Model = MODEL_MAP[entity]
    return session.get(Model, _id)

def preview_propagation(session: Session, project_id: int, req: PropagationRequest) -> PropagationPreview:
    suggestions: List[SuggestedOp] = []

    for ch in req.changes:
        # include the original edit itself as the first suggestion
        row = _get_row(session, ch.entity, ch.id)
        if not row:
            # skip unknown rows
            continue
        old = getattr(row, ch.field, None)
        suggestions.append(SuggestedOp(
            entity=ch.entity, id=ch.id, field=ch.field,
            old_value=old, new_value=ch.new_value,
            reason="Original requested change.", original=True
        ))

        # ripple rules
        if ch.entity == "outcome" and ch.field == "name":
            # outcome -> benefits
            benefits = session.exec(select(Benefit).where(Benefit.project_id == project_id))  # we don't store outcome_id on benefits? we do; use it.
            benefits = session.exec(select(Benefit).where(Benefit.outcome_id == ch.id)).all()
            for b in benefits:
                tag = f"[Aligned with Outcome: {ch.new_value}]"
                new_desc = (b.description or "")
                if tag not in new_desc:
                    new_desc = (new_desc + " " + tag).strip()
                    suggestions.append(SuggestedOp(
                        entity="benefit", id=b.id, field="description",
                        old_value=b.description, new_value=new_desc,
                        reason="Outcome renamed; keep benefits aligned."
                    ))

        if ch.entity == "benefit" and ch.field == "name":
            # benefit -> deliverables
            deliverables = session.exec(select(Deliverable).where(Deliverable.benefit_id == ch.id)).all()
            for d in deliverables:
                tag = f"[Aligned with Benefit: {ch.new_value}]"
                new_desc = (d.description or "")
                if tag not in new_desc:
                    new_desc = (new_desc + " " + tag).strip()
                    suggestions.append(SuggestedOp(
                        entity="deliverable", id=d.id, field="description",
                        old_value=d.description, new_value=new_desc,
                        reason="Benefit renamed; keep deliverables aligned."
                    ))

        if ch.entity == "task" and ch.field == "est_days":
            # task -> parent deliverable description
            t = row  # already fetched
            d = session.get(Deliverable, t.deliverable_id)
            if d:
                tag = "[Timeline updated due to task change]"
                new_desc = (d.description or "")
                if tag not in new_desc:
                    new_desc = (new_desc + " " + tag).strip()
                    suggestions.append(SuggestedOp(
                        entity="deliverable", id=d.id, field="description",
                        old_value=d.description, new_value=new_desc,
                        reason="Task duration changed; reflect in deliverable description."
                    ))

    return PropagationPreview(suggestions=suggestions)

def apply_suggestions(session: Session, project_id: int, req: ApplyRequest) -> ApplyResult:
    applied = 0
    for op in req.ops:
        row = _get_row(session, op.entity, op.id)
        if not row:
            continue
        if not hasattr(row, op.field):
            continue
        setattr(row, op.field, op.new_value)
        session.add(row)
        applied += 1
    session.commit()
    return ApplyResult(applied=applied)
