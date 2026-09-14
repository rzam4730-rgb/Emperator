"""Credits, add-on modules and billing helpers for Emperator."""
import os
import json
from datetime import datetime, timezone
from fastapi import Depends, HTTPException

MODULES = {
    "inventory": {"name": "انبار و خرید", "price": 290000},
    "crm": {"name": "باشگاه مشتریان", "price": 390000},
    "ai": {"name": "مشاور هوشمند AI", "price": 590000},
    "multi_branch": {"name": "چند شعبه", "price": 790000},
    "advanced_reports": {"name": "گزارش‌های پیشرفته", "price": 350000},
}
CREDIT_PACKS = {
    "sms_500": {"type": "sms", "name": "۵۰۰ پیامک", "credits": 500, "price": 150000},
    "sms_2000": {"type": "sms", "name": "۲۰۰۰ پیامک", "credits": 2000, "price": 490000},
    "ai_100": {"type": "ai", "name": "۱۰۰ اعتبار AI", "credits": 100, "price": 190000},
    "ai_500": {"type": "ai", "name": "۵۰۰ اعتبار AI", "credits": 500, "price": 790000},
}
SCHEMA = """
CREATE TABLE IF NOT EXISTS credit_accounts(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 restaurant_id INTEGER NOT NULL,
 credit_type TEXT NOT NULL,
 balance INTEGER NOT NULL DEFAULT 0,
 updated_at TEXT NOT NULL,
 UNIQUE(restaurant_id, credit_type)
);
CREATE TABLE IF NOT EXISTS credit_ledger(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 restaurant_id INTEGER NOT NULL,
 credit_type TEXT NOT NULL,
 delta INTEGER NOT NULL,
 balance_after INTEGER NOT NULL,
 reason TEXT NOT NULL,
 reference_id TEXT,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS restaurant_modules(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 restaurant_id INTEGER NOT NULL,
 module_code TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'active',
 activated_at TEXT NOT NULL,
 expires_at TEXT,
 UNIQUE(restaurant_id,module_code)
);
CREATE INDEX IF NOT EXISTS idx_credit_ledger_restaurant ON credit_ledger(restaurant_id,id DESC);
CREATE INDEX IF NOT EXISTS idx_modules_restaurant ON restaurant_modules(restaurant_id);
"""
def now(): return datetime.now(timezone.utc).isoformat()
def ensure_account(c, restaurant_id, credit_type):
    c.execute("INSERT OR IGNORE INTO credit_accounts(restaurant_id,credit_type,balance,updated_at) VALUES(?,?,0,?)", (restaurant_id,credit_type,now()))
def credit(c, restaurant_id, credit_type, delta, reason, reference_id=None):
    ensure_account(c, restaurant_id, credit_type)
    row=c.execute("SELECT balance FROM credit_accounts WHERE restaurant_id=? AND credit_type=?",(restaurant_id,credit_type)).fetchone()
    balance=int(row[0])+int(delta)
    if balance < 0: raise ValueError("اعتبار کافی نیست")
    ts=now(); c.execute("UPDATE credit_accounts SET balance=?,updated_at=? WHERE restaurant_id=? AND credit_type=?",(balance,ts,restaurant_id,credit_type))
    c.execute("INSERT INTO credit_ledger(restaurant_id,credit_type,delta,balance_after,reason,reference_id,created_at) VALUES(?,?,?,?,?,?,?)",(restaurant_id,credit_type,delta,balance,reason,reference_id,ts))
    return balance
def balances(c, restaurant_id):
    rows=c.execute("SELECT credit_type,balance FROM credit_accounts WHERE restaurant_id=?",(restaurant_id,)).fetchall()
    return {r[0]:int(r[1]) for r in rows}
def install_billing_schema(conn):
    conn.executescript(SCHEMA)
def mount_billing_routes(app, conn_factory, current_user):
    @app.get('/api/billing/catalog')
    def catalog(user=Depends(current_user)):
        return {'modules':[dict(code=k,**v) for k,v in MODULES.items()], 'credit_packs':[dict(code=k,**v) for k,v in CREDIT_PACKS.items()]}
    @app.get('/api/billing/credits')
    def get_credits(user=Depends(current_user)):
        c=conn_factory();
        try: return balances(c,user['restaurant_id'])
        finally: c.close()
    @app.get('/api/billing/ledger')
    def ledger(user=Depends(current_user)):
        c=conn_factory();
        try: return [dict(r) for r in c.execute("SELECT credit_type,delta,balance_after,reason,reference_id,created_at FROM credit_ledger WHERE restaurant_id=? ORDER BY id DESC LIMIT 200",(user['restaurant_id'],))]
        finally: c.close()
    @app.get('/api/billing/modules')
    def modules(user=Depends(current_user)):
        c=conn_factory();
        try: return [dict(r) for r in c.execute("SELECT module_code,status,activated_at,expires_at FROM restaurant_modules WHERE restaurant_id=?",(user['restaurant_id'],))]
        finally: c.close()
    return True
