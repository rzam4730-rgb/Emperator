"""Payment API helpers. Gateway logic remains replaceable."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from .payment import get_gateway

router = APIRouter(prefix="/api/payments", tags=["payments"])

PAYMENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS payments(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
 payment_type TEXT NOT NULL, reference_id TEXT, amount INTEGER NOT NULL,
 currency TEXT NOT NULL DEFAULT 'IRR', status TEXT NOT NULL DEFAULT 'pending', gateway TEXT NOT NULL,
 authority TEXT UNIQUE, gateway_transaction_id TEXT, metadata_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL, paid_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_payments_restaurant ON payments(restaurant_id, id DESC);
CREATE TABLE IF NOT EXISTS credit_ledger(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, user_id INTEGER,
 credit_type TEXT NOT NULL, amount INTEGER NOT NULL, balance_after INTEGER NOT NULL,
 source TEXT NOT NULL, reference_id TEXT, metadata_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_credit_ledger_restaurant ON credit_ledger(restaurant_id, credit_type, id DESC);
"""


def mount_payment_routes(app, conn_factory, current_user, subscription_view, ensure_subscription, plan_limits):
    @app.get("/api/payments")
    def list_payments(user=Depends(current_user)):
        c=conn_factory()
        try:
            return [dict(r) for r in c.execute("SELECT id,payment_type,reference_id,amount,currency,status,gateway,gateway_transaction_id,created_at,paid_at FROM payments WHERE restaurant_id=? ORDER BY id DESC LIMIT 100",(user["restaurant_id"],))]
        finally: c.close()

    @app.get("/api/credits")
    def credit_balances(user=Depends(current_user)):
        c=conn_factory()
        try:
            out={}
            for kind in ("sms","ai"):
                row=c.execute("SELECT COALESCE(SUM(amount),0) FROM credit_ledger WHERE restaurant_id=? AND credit_type=?",(user["restaurant_id"],kind)).fetchone()
                out[kind]=int(row[0] or 0)
            return out
        finally: c.close()

    @app.get("/api/credits/ledger")
    def credits_ledger(user=Depends(current_user)):
        c=conn_factory()
        try:
            return [dict(r) for r in c.execute("SELECT id,credit_type,amount,balance_after,source,reference_id,created_at FROM credit_ledger WHERE restaurant_id=? ORDER BY id DESC LIMIT 100",(user["restaurant_id"],))]
        finally: c.close()

    @app.post("/api/payments/create")
    def create_payment(payload: dict,user=Depends(current_user)):
        payment_type=str(payload.get("payment_type","")).strip(); reference_id=str(payload.get("reference_id","")).strip() or None; gateway_code=str(payload.get("gateway","mock")).strip().lower()
        try: amount=int(payload.get("amount",0))
        except (TypeError,ValueError): amount=0
        if payment_type not in {"subscription","sms_credits","ai_credits","module"}: raise HTTPException(400,"نوع پرداخت نامعتبر است")
        if amount<=0: raise HTTPException(400,"مبلغ پرداخت باید بیشتر از صفر باشد")
        metadata=payload.get("metadata") if isinstance(payload.get("metadata"),dict) else {}
        if payment_type in {"sms_credits","ai_credits"}:
            try: credits=int(metadata.get("credits",0))
            except (TypeError,ValueError): credits=0
            if credits<=0: raise HTTPException(400,"تعداد اعتبار نامعتبر است")
            metadata["credits"]=credits; metadata["credit_type"]="sms" if payment_type=="sms_credits" else "ai"
        c=conn_factory()
        try:
            start=get_gateway(gateway_code).create(amount,str(payload.get("description","پرداخت امپراتور")),str(payload.get("callback_url","/api/payments/callback/"+gateway_code)),metadata)
            now=datetime.now(timezone.utc).isoformat()
            cur=c.execute("INSERT INTO payments(restaurant_id,user_id,payment_type,reference_id,amount,currency,status,gateway,authority,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(user["restaurant_id"],user["id"],payment_type,reference_id,amount,"IRR","pending",gateway_code,start.authority,json.dumps(metadata,ensure_ascii=False),now)); c.commit()
            return {"payment_id":cur.lastrowid,"authority":start.authority,"payment_url":start.payment_url,"status":"pending"}
        finally: c.close()

    @app.get("/api/payments/{payment_id}")
    def payment_status(payment_id:int,user=Depends(current_user)):
        c=conn_factory(); row=c.execute("SELECT * FROM payments WHERE id=? AND restaurant_id=?",(payment_id,user["restaurant_id"])).fetchone(); c.close()
        if not row: raise HTTPException(404,"تراکنش پیدا نشد")
        result=dict(row); result.pop("metadata_json",None); return result

    @app.get("/api/payments/callback/{gateway_code}")
    def payment_callback(
        gateway_code:str,
        authority:str=Query(...,alias="Authority"),
        status:str=Query("OK",alias="Status")
    ):
        c=conn_factory(); row=c.execute("SELECT * FROM payments WHERE authority=? AND gateway=?",(authority,gateway_code)).fetchone()
        if not row: c.close(); raise HTTPException(404,"تراکنش پیدا نشد")
        if row["status"]=="paid": c.close(); return {"status":"paid","payment_id":row["id"]}
        if status.upper() not in {"OK","SUCCESS","1"}:
            c.execute("UPDATE payments SET status='failed' WHERE id=?",(row["id"],)); c.commit(); c.close(); return {"status":"failed","payment_id":row["id"]}
        result=get_gateway(gateway_code).verify(row["amount"],authority)
        if not result.success:
            c.execute("UPDATE payments SET status='failed' WHERE id=?",(row["id"],)); c.commit(); c.close(); return {"status":"failed","payment_id":row["id"],"message":result.message}
        now_dt=datetime.now(timezone.utc); now=now_dt.isoformat()
        c.execute("UPDATE payments SET status='paid',gateway_transaction_id=?,paid_at=? WHERE id=?",(result.transaction_id,now,row["id"]))
        try: meta=json.loads(row["metadata_json"] or "{}")
        except json.JSONDecodeError: meta={}
        if row["payment_type"]=="subscription":
            plan_code=meta.get("plan_code") or row["reference_id"]; plan=c.execute("SELECT * FROM plans WHERE code=? AND active=1",(plan_code,)).fetchone()
            if plan:
                old=ensure_subscription(c,row["restaurant_id"]); expires=(now_dt+timedelta(days=30)).isoformat()
                c.execute("UPDATE subscriptions SET plan_id=?,status='active',starts_at=?,expires_at=?,updated_at=? WHERE restaurant_id=?",(plan["id"],now,expires,now,row["restaurant_id"]))
                c.execute("INSERT INTO subscription_events(restaurant_id,event_type,plan_id,amount,metadata_json,created_at) VALUES(?,?,?,?,?,?)",(row["restaurant_id"],"payment",plan["id"],row["amount"],json.dumps({"payment_id":row["id"],"from":old["code"]},ensure_ascii=False),now))
        elif row["payment_type"] in {"sms_credits","ai_credits"}:
            kind="sms" if row["payment_type"]=="sms_credits" else "ai"
            try: credits=int(meta.get("credits",0))
            except (TypeError,ValueError): credits=0
            if credits>0:
                current=c.execute("SELECT COALESCE(SUM(amount),0) FROM credit_ledger WHERE restaurant_id=? AND credit_type=?",(row["restaurant_id"],kind)).fetchone()[0]
                balance=int(current or 0)+credits
                c.execute("INSERT INTO credit_ledger(restaurant_id,user_id,credit_type,amount,balance_after,source,reference_id,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(row["restaurant_id"],row["user_id"],kind,credits,balance,"purchase",str(row["id"]),json.dumps(meta,ensure_ascii=False),now))
        c.commit(); c.close(); return {"status":"paid","payment_id":row["id"],"transaction_id":result.transaction_id}
    return router
