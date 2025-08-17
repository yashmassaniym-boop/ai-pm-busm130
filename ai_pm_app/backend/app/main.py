
from fastapi import FastAPI
from .db.database import create_db_and_tables
from .api.projects import router as projects_router
from .api.ui import router as ui_router

app = FastAPI(title="AI-Augmented PM System")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(projects_router)
app.include_router(ui_router)
