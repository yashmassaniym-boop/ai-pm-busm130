
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class GenTask(BaseModel):
    name: str
    est_days: int = Field(ge=1, description="Estimated duration in days")
    depends_on_index: Optional[int] = Field(default=None, description="Index of another task in the SAME deliverable")

class GenDeliverable(BaseModel):
    name: str
    description: Optional[str] = None
    tasks: List[GenTask]

class GenBenefit(BaseModel):
    name: str
    description: Optional[str] = None
    deliverables: List[GenDeliverable]

class GenOutcome(BaseModel):
    name: str
    description: Optional[str] = None
    benefits: List[GenBenefit]

class GenBudgetLine(BaseModel):
    item: str
    amount: float = Field(ge=0)
    category: str = "General"

class GenGovernanceEvent(BaseModel):
    name: str
    cadence: str
    owner: Optional[str] = None

class GenReportSpec(BaseModel):
    name: str
    frequency: str
    audience: Optional[str] = None

class GenRisk(BaseModel):
    title: str
    probability: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    mitigation: Optional[str] = None

class GenProject(BaseModel):
    # This is the STRICT return we expect from any generator/LLM
    name: str
    vision: str
    description: Optional[str] = None
    outcomes: List[GenOutcome]
    budget: List[GenBudgetLine] = []
    governance: List[GenGovernanceEvent] = []
    reporting: List[GenReportSpec] = []
    risks: List[GenRisk] = []

    @validator("outcomes")
    def must_have_at_least_one_outcome(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one outcome is required")
        return v
