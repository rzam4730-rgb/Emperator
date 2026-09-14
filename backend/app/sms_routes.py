"""SMS API and credit metering for Emperator."""
from datetime import datetime, timezone
from fastapi import Depends, HTTPException
from .sms import get_sms_provider

SMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS sms_messages(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 restaurant_id INTEGER NOT NULL,
 user_id INTEGER,
 receptor TEXT NOT NULL,
 message TEXT NOT NULL,
 provider TEXT NOT NULL,
 provider_message_id TEXT,
 status TEXT NOT NULL,
 credit_cost INTEGER NOT NULL DEFAULT 1,
 error_message TEXT,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sms_messages_restaurant ON sms_messages(restaurant_id, id DESC);
"""


def mount_sms_routes(app, conn_factory, current_user):
    @app.get("/api/sms/history")
    def sms_history(user=Depends(current_user)):
        c = conn_factory()
        try:
            return [dict(r) for r in c.execute(
                "SELECT id,receptor,message,provider,provider_message_id,status,credit_cost,error_message,created_at "
                "FROM sms_messages WHERE restaurant_id=? ORDER BY id DESC LIMIT 100",
                (user["restaurant_id"],)
            )]
        finally:
            c.close()

    @app.post("/api/sms/send")
    def send_sms(payload: dict, user=Depends(current_user)):
        receptor = str(payload.get("receptor", "")).strip()
        message = str(payload.get("message", "")).strip()
        provider_code = str(payload.get("provider", "")).strip().lower() or None
        if not receptor or not message:
            raise HTTPException(400, "شماره گیرنده و متن پیام الزامی است")
        if len(message) > 1000:
            raise HTTPException(400, "متن پیام بیش از حد طولانی است")
        c = conn_factory()
        try:
            balance = int(c.execute(
                "SELECT COALESCE(SUM(amount),0) FROM credit_ledger WHERE restaurant_id=? AND credit_type='sms'",
                (user["restaurant_id"],)
            ).fetchone()[0] or 0)
            if balance < 1:
                raise HTTPException(402, "اعتبار پیامک کافی نیست")
            provider = get_sms_provider(provider_code)
            result = provider.send(receptor, message, payload.get("sender"))
            now = datetime.now(timezone.utc).isoformat()
            status = "sent" if result.success else "failed"
            if result.success:
                new_balance = balance - 1
                c.execute(
                    "INSERT INTO credit_ledger(restaurant_id,user_id,credit_type,amount,balance_after,source,reference_id,metadata_json,created_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?)",
                    (user["restaurant_id"], user["id"], "sms", -1, new_balance, "send", None, "{}", now)
                )
            else:
                new_balance = balance
            cur = c.execute(
                "INSERT INTO sms_messages(restaurant_id,user_id,receptor,message,provider,provider_message_id,status,credit_cost,error_message,created_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (user["restaurant_id"], user["id"], receptor, message, provider.code,
                 result.message_id, status, 1 if result.success else 0,
                 None if result.success else result.message, now)
            )
            c.commit()
            if not result.success:
                raise HTTPException(502, result.message or "ارسال پیامک ناموفق بود")
            return {"id": cur.lastrowid, "status": "sent", "message_id": result.message_id, "balance": new_balance}
        finally:
            c.close()
