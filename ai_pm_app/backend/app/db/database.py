import pathlib
from sqlmodel import SQLModel, create_engine, Session

DB_FILE = pathlib.Path.cwd() / "ai_pm_app" / "ai_pm.db"
DB_FILE.parent.mkdir(parents=True, exist_ok=True)
SQLITE_URL = f"sqlite:///{DB_FILE.as_posix()}"

engine = create_engine(SQLITE_URL, echo=False)

def create_db_and_tables():
    # Import models so SQLModel sees them before create_all
    from ..models.entities import Project, Outcome, Benefit, Deliverable, Task, BudgetLine, GovernanceEvent, ReportSpec, Risk  # noqa: F401
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
