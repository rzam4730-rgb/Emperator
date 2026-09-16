from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles


def _index_response(index_file: Path):
    html = index_file.read_text(encoding="utf-8")
    marker = "</head>"
    head_injection = '<link rel="stylesheet" href="/assets/final-polish.css?v=1">'
    html = html.replace(marker, head_injection + marker)
    marker = "</body>"
    injection = (
        '<script src="/assets/app-core.js?v=6"></script>'
        '<script src="/assets/auth-fix.js?v=5"></script>'
        '<script src="/assets/navigation-fix.js?v=5"></script>'
        '<script src="/assets/kds.js?v=4"></script>'
        '<script src="/assets/inventory-ui.js?v=3"></script>'
        '<script src="/assets/theme.js?v=4"></script>'
        '<script src="/assets/runtime-fix.js?v=1"></script>'
        '<script src="/assets/ui-polish.js?v=1"></script>'
        '<script src="/assets/final-polish.js?v=1"></script>'
        '<script src="/assets/functional-fix.js?v=1"></script>'
        '<script src="/assets/personnel-ui.js?v=2"></script>'
        '<script src="/assets/personnel-nav-fix.js?v=1"></script>'
        '<script src="/assets/confirmation-gate.js?v=1"></script>'
        '<script src="/assets/emergency-nav.js?v=1"></script>'
    )
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
            raise HTTPException(status_code=404, detail="صفحه یا فایل موردنظر پیدا نشد.")
        if candidate.is_file():
            return FileResponse(str(candidate))
        raise HTTPException(status_code=404, detail="صفحه یا فایل موردنظر پیدا نشد.")
