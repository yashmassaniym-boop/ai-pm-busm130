
from __future__ import annotations
from typing import Optional
from sqlmodel import SQLModel, Field

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    vision: str
    description: Optional[str] = None

class Outcome(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    name: str
    description: Optional[str] = None

class Benefit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    outcome_id: int = Field(foreign_key="outcome.id")
    name: str
    description: Optional[str] = None

class Deliverable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    benefit_id: int = Field(foreign_key="benefit.id")
    name: str
    description: Optional[str] = None

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    deliverable_id: int = Field(foreign_key="deliverable.id")
    name: str
    est_days: int = 1
    depends_on_id: Optional[int] = Field(default=None, foreign_key="task.id")

class BudgetLine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    item: str
    amount: float
    category: str = "General"

class GovernanceEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    name: str
    cadence: str
    owner: Optional[str] = None

class ReportSpec(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    name: str
    frequency: str
    audience: Optional[str] = None

class Risk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    title: str
    probability: int = 2
    impact: int = 2
    mitigation: Optional[str] = None

from datetime import datetime
from typing import Optional

class ActivityLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    entity: str
    entity_id: int
    field: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

from datetime import datetime
from typing import Optional

class TaskState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(index=True)
    status: str = Field(default="todo")  # todo | inprogress | done
    done: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

