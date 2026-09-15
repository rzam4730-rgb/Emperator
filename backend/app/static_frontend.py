from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_frontend(app):
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    index_file = frontend_dir / "index.html"

    if not frontend_dir.is_dir() or not index_file.is_file():
        return

    # Serve the application shell explicitly. This is more reliable on the
    # older FastAPI/Starlette stack used by the Windows 7-compatible build.
    @app.get("/", include_in_schema=False)
    def frontend_index():
        return FileResponse(str(index_file), media_type="text/html")

    @app.get("/index.html", include_in_schema=False)
    def frontend_index_file():
        return FileResponse(str(index_file), media_type="text/html")

    # Static assets (JS/CSS/images) remain available from /.
    app.mount("/assets", StaticFiles(directory=str(frontend_dir)), name="frontend-assets")

    @app.get("/{asset_path:path}", include_in_schema=False)
    def frontend_asset(asset_path: str):
        candidate = (frontend_dir / asset_path).resolve()
        try:
            candidate.relative_to(frontend_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=404, detail="Not Found")
        if candidate.is_file():
            return FileResponse(str(candidate))
        raise HTTPException(status_code=404, detail="Not Found")
