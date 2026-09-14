import uvicorn

from app.main import (
    app, conn, current_user, require_permission, hash_password, verify_password,
    create_access_token, issue_refresh_token, hash_refresh_token,
)
from app.compat_routes import seed_core, mount_core_routes
from app.subscription import ensure_subscription, plan_limits, get_usage, utcnow


def activate():
    c = conn()
    try:
        seed_core(c)
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


if __name__ == '__main__':
    activate()
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='warning')
