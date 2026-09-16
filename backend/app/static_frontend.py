from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


def _index_response(index_file: Path):
    html = index_file.read_text(encoding="utf-8")
    marker = "</body>"
    injection = '<script src="/assets/navigation-fix.js"></script>'
    if injection not in html:
        html = html.replace(marker, injection + marker)
    return HTMLResponse(html, media_type="text/html")


def mount_frontend(app):
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    index_file = frontend_dir / "index.html"

    if not frontend_dir.is_dir() or not index_file.is_file():
        return

    @app.get("/", include_in_schema=False)
    def frontend_index():
        return _index_response(index_file)

    @app.get("/index.html", include_in_schema=False)
    def frontend_index_file():
        return _index_response(index_file)

    app.mount("/assets", StaticFiles(directory=str(frontend_dir)), name="frontend-assets")

    @app.get("/{asset_path:path}", include_in_schema=False)
    def frontend_asset(asset_path: str):
        candidate = (frontend_dir / asset_path).resolve()
        try:
            candidate.relative_to(frontend_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=404, detail="Not Found")
        if candidate.is_file():
            return HTMLResponse(candidate.read_text(encoding="utf-8"), media_type="text/html") if candidate.suffix.lower() in {".html"} else __import__("fastapi").responses.FileResponse(str(candidate))
        raise HTTPException(status_code=404, detail="Not Found")
