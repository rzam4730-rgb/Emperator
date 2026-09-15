from pathlib import Path

from fastapi.staticfiles import StaticFiles


def mount_frontend(app):
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    if frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
