
from __future__ import annotations
from typing import List, Literal, Any, Optional
from pydantic import BaseModel, Field

EntityType = Literal["project","outcome","benefit","deliverable","task","budget"]

class ChangeItem(BaseModel):
    entity: EntityType
    id: int
    field: str
    new_value: Any

class SuggestedOp(BaseModel):
    entity: EntityType
    id: int
    field: str
    old_value: Optional[Any] = None
    new_value: Any
    reason: str
    original: bool = False  # True when this is the user's original change

class PropagationRequest(BaseModel):
    changes: List[ChangeItem] = Field(default_factory=list)

class PropagationPreview(BaseModel):
    suggestions: List[SuggestedOp] = Field(default_factory=list)

class ApplyRequest(BaseModel):
    ops: List[SuggestedOp] = Field(default_factory=list)

class ApplyResult(BaseModel):
    applied: int
