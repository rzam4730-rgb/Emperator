"""Emperator subscription, entitlements and usage helpers.

This module is intentionally framework-light so the existing API can import it
without coupling billing rules to individual business modules.
"""
from datetime import datetime, timezone, timedelta
import json

PLANS = {
    "starter": {
        "name": "اقتصادی",
        "price_monthly": 490000,
        "invoice_daily_limit": 80,
        "customer_limit": 1000,
        "sms_credits": 100,
        "ai_credits": 20,
        "modules": ["orders", "customers", "products", "reports"],
    },
    "professional": {
        "name": "حرفه‌ای",
        "price_monthly": 890000,
        "invoice_daily_limit": 300,
        "customer_limit": 5000,
        "sms_credits": 500,
        "ai_credits": 100,
        "modules": ["orders", "customers", "products", "inventory", "finance", "reports", "crm"],
    },
    "business": {
        "name": "سازمانی",
        "price_monthly": 1490000,
        "invoice_daily_limit": 1000,
        "customer_limit": 20000,
        "sms_credits": 2000,
        "ai_credits": 300,
        "modules": ["orders", "customers", "products", "inventory", "finance", "reports", "crm", "ai", "multi_branch"],
    },
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    price_monthly INTEGER NOT NULL DEFAULT 0,
    limits_json TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL UNIQUE,
    plan_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    starts_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    auto_renew INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    FOREIGN KEY(plan_id) REFERENCES plans(id)
);
CREATE TABLE IF NOT EXISTS subscription_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    plan_id INTEGER,
    amount INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS usage_counters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    metric TEXT NOT NULL,
    period_key TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    UNIQUE(restaurant_id, metric, period_key)
);
"""


def utcnow():
    return datetime.now(timezone.utc)


def plan_limits(plan):
    return json.loads(plan["limits_json"]) if isinstance(plan["limits_json"], str) else plan["limits_json"]


def seed_plans(c):
    now = utcnow().isoformat()
    for code, p in PLANS.items():
        c.execute(
            "INSERT OR IGNORE INTO plans(code,name,price_monthly,limits_json,created_at) VALUES(?,?,?,?,?)",
            (code, p["name"], p["price_monthly"], json.dumps(p, ensure_ascii=False), now),
        )


def ensure_subscription(c, restaurant_id, default_plan="starter"):
    row = c.execute(
        "SELECT s.*,p.code,p.name,p.price_monthly,p.limits_json FROM subscriptions s JOIN plans p ON p.id=s.plan_id WHERE s.restaurant_id=?",
        (restaurant_id,),
    ).fetchone()
    if row:
        return row
    plan = c.execute("SELECT * FROM plans WHERE code=? AND active=1", (default_plan,)).fetchone()
    if not plan:
        raise RuntimeError("Default subscription plan is missing")
    now = utcnow()
    expires = now + timedelta(days=30)
    c.execute(
        "INSERT INTO subscriptions(restaurant_id,plan_id,status,starts_at,expires_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
        (restaurant_id, plan["id"], "active", now.isoformat(), expires.isoformat(), now.isoformat(), now.isoformat()),
    )
    return c.execute(
        "SELECT s.*,p.code,p.name,p.price_monthly,p.limits_json FROM subscriptions s JOIN plans p ON p.id=s.plan_id WHERE s.restaurant_id=?",
        (restaurant_id,),
    ).fetchone()


def usage_period(metric, now=None):
    now = now or utcnow()
    if metric == "invoices_daily":
        return now.strftime("%Y-%m-%d")
    return now.strftime("%Y-%m")


def get_usage(c, restaurant_id, metric, now=None):
    period = usage_period(metric, now)
    row = c.execute(
        "SELECT used FROM usage_counters WHERE restaurant_id=? AND metric=? AND period_key=?",
        (restaurant_id, metric, period),
    ).fetchone()
    return int(row[0]) if row else 0


def increment_usage(c, restaurant_id, metric, amount=1, now=None):
    now = now or utcnow()
    period = usage_period(metric, now)
    c.execute(
        "INSERT INTO usage_counters(restaurant_id,metric,period_key,used,updated_at) VALUES(?,?,?,?,?) "
        "ON CONFLICT(restaurant_id,metric,period_key) DO UPDATE SET used=used+excluded.used,updated_at=excluded.updated_at",
        (restaurant_id, metric, period, amount, now.isoformat()),
    )
    return get_usage(c, restaurant_id, metric, now)
