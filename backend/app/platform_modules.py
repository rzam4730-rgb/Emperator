"""Central registration point for cross-cutting platform modules."""

def install_platform_modules(c):
    from .accounting import install_accounting_schema, seed_accounting
    from .payment_routes import PAYMENT_SCHEMA
    from .billing_core import install_billing_schema
    from .order_lifecycle import install_lifecycle_schema
    install_accounting_schema(c)
    c.executescript(PAYMENT_SCHEMA)
    install_billing_schema(c)
    install_lifecycle_schema(c)
    for r in c.execute("SELECT id FROM restaurants").fetchall():
        seed_accounting(c, r[0])

def mount_platform_modules(app, conn, current_user, subscription_view, ensure_subscription, plan_limits):
    from .accounting import mount_accounting_routes
    from .payment_routes import mount_payment_routes
    mount_accounting_routes(app, conn, current_user)
    mount_payment_routes(app, conn, current_user, subscription_view, ensure_subscription, plan_limits)
