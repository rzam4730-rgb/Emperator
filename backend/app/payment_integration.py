"""Payment integration helpers for the Emperator API.

This module intentionally contains no FastAPI app mutation at import time. The
main application should call install_payment_integration(app, conn, ...)
after authentication and subscription dependencies have been defined.
"""

from .payment_routes import PAYMENT_SCHEMA, mount_payment_routes


def install_payment_integration(app, conn_factory, current_user, subscription_view, ensure_subscription, plan_limits):
    """Install payment database schema and HTTP routes into the main app."""
    c = conn_factory()
    try:
        c.executescript(PAYMENT_SCHEMA)
        c.commit()
    finally:
        c.close()
    return mount_payment_routes(
        app,
        conn_factory,
        current_user,
        subscription_view,
        ensure_subscription,
        plan_limits,
    )
