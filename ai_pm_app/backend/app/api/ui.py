from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/ui", response_class=HTMLResponse)
def ui_page():
    # __file__ = .../backend/app/api/ui.py
    # parents[1] = .../backend/app  → app/ui/index.html
    base = Path(__file__).resolve().parents[1] / "ui" / "index.html"
    return base.read_text(encoding="utf-8")
