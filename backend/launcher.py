import os
from pathlib import Path


def load_local_env():
    """Load a local .env file without adding a runtime dependency.

    Environment variables already supplied by the OS always win. This keeps
    Kavenegar credentials out of source code while allowing the Windows build
    to run with a local backend/.env file.
    """
    candidates = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            for raw in path.read_text(encoding="utf-8-sig").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except OSError as exc:
            print("Local .env load warning:", exc)
        break


load_local_env()

import uvicorn

from app.main import (
    app, conn, init_db, current_user, require_permission, hash_password, verify_password,
    create_access_token, issue_refresh_token, hash_refresh_token,
)
from app.compat_routes import seed_core, mount_core_routes
from app.bootstrap import ensure_initial_owner
from app.subscription import ensure_subscription, plan_limits, get_usage, utcnow
from app.static_frontend import mount_frontend


def activate():
    # Database schema must exist before compatibility route seeding. FastAPI's
    # startup event runs only after uvicorn starts, while activate() runs first.
    init_db()
    c = conn()
    try:
        seed_core(c)
        ensure_initial_owner(c, hash_password)
        c.commit()
    finally:
        c.close()
    mount_core_routes(
        app, conn, current_user, require_permission, hash_password, verify_password,
        create_access_token, issue_refresh_token, hash_refresh_token,
        ensure_subscription, plan_limits, get_usage, utcnow,
        lambda c, user, action, target_type=None, target_id=None, details=None: c.execute(
            "INSERT INTO audit_logs(user_id,restaurant_id,action,target_type,target_id,details,created_at) VALUES(?,?,?,?,?,?,?)",
            (user["id"], user["restaurant_id"], action, target_type, target_id, details, utcnow().isoformat()),
        ),
    )
    mount_frontend(app)


if __name__ == '__main__':
    activate()
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='warning')
