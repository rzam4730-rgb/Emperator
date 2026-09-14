"""AI credit metering and business-advisor foundation for Emperator."""
import json
from datetime import datetime, timezone
from fastapi import Depends, HTTPException

AI_SCHEMA = """
CREATE TABLE IF NOT EXISTS ai_usage(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
 action TEXT NOT NULL, credits INTEGER NOT NULL, prompt TEXT, result_json TEXT,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ai_usage_restaurant ON ai_usage(restaurant_id,id DESC);
"""

AI_ACTION_COSTS = {
    "dashboard_analysis": 1,
    "sales_analysis": 2,
    "forecast": 3,
    "menu_engineering": 3,
    "marketing_plan": 3,
    "business_advisor": 2,
}


def install_ai_schema(c):
    c.executescript(AI_SCHEMA)


def ai_balance(c, restaurant_id):
    row = c.execute(
        "SELECT COALESCE(SUM(amount),0) FROM credit_ledger WHERE restaurant_id=? AND credit_type='ai'",
        (restaurant_id,),
    ).fetchone()
    return int(row[0] or 0)


def consume_ai(c, user, action, prompt=None, result=None):
    cost = AI_ACTION_COSTS.get(action)
    if not cost:
        raise HTTPException(400, "عملیات AI نامعتبر است")
    balance = ai_balance(c, user["restaurant_id"])
    if balance < cost:
        raise HTTPException(402, f"اعتبار AI کافی نیست. اعتبار موردنیاز: {cost}")
    new_balance = balance - cost
    now = datetime.now(timezone.utc).isoformat()
    c.execute(
        "INSERT INTO credit_ledger(restaurant_id,user_id,credit_type,amount,balance_after,source,reference_id,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (user["restaurant_id"], user["id"], "ai", -cost, new_balance, "ai_usage", action,
         json.dumps({"action": action}, ensure_ascii=False), now),
    )
    c.execute(
        "INSERT INTO ai_usage(restaurant_id,user_id,action,credits,prompt,result_json,created_at) VALUES(?,?,?,?,?,?,?)",
        (user["restaurant_id"], user["id"], action, cost, prompt or "",
         json.dumps(result or {}, ensure_ascii=False), now),
    )
    return new_balance, cost


def mount_ai_routes(app, conn_factory, current_user):
    @app.get("/api/ai/balance")
    def ai_balance_api(user=Depends(current_user)):
        c = conn_factory()
        try:
            return {"balance": ai_balance(c, user["restaurant_id"]), "costs": AI_ACTION_COSTS}
        finally:
            c.close()

    @app.get("/api/ai/usage")
    def ai_usage_api(user=Depends(current_user)):
        c = conn_factory()
        try:
            return [dict(r) for r in c.execute(
                "SELECT id,action,credits,prompt,created_at FROM ai_usage WHERE restaurant_id=? ORDER BY id DESC LIMIT 100",
                (user["restaurant_id"],),
            )]
        finally:
            c.close()

    @app.post("/api/ai/analyze")
    def ai_analyze(payload: dict, user=Depends(current_user)):
        action = str(payload.get("action", "business_advisor")).strip()
        prompt = str(payload.get("prompt", "")).strip()
        c = conn_factory()
        try:
            # This is the metering contract; an external LLM can be attached later without changing billing.
            result = {
                "action": action,
                "message": "تحلیل AI آماده اتصال به موتور هوش مصنوعی است.",
                "prompt": prompt,
            }
            balance, cost = consume_ai(c, user, action, prompt, result)
            c.commit()
            return {"success": True, "credits_used": cost, "balance": balance, "result": result}
        finally:
            c.close()

    return app
