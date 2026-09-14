"""Accounting core: cash, income, expense, receivables/payables and reconciliation."""
from datetime import datetime, timezone
from fastapi import Depends, HTTPException

ACCOUNTING_SCHEMA = """
CREATE TABLE IF NOT EXISTS accounting_categories(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, name TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('income','expense','asset','liability','equity')), active INTEGER NOT NULL DEFAULT 1,
 UNIQUE(restaurant_id,name,kind)
);
CREATE TABLE IF NOT EXISTS accounting_accounts(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, name TEXT NOT NULL,
 account_type TEXT NOT NULL CHECK(account_type IN ('cash','bank','receivable','payable','other')), balance INTEGER NOT NULL DEFAULT 0,
 active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS accounting_transactions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, account_id INTEGER NOT NULL,
 category_id INTEGER, direction TEXT NOT NULL CHECK(direction IN ('in','out')),
 amount INTEGER NOT NULL CHECK(amount>0), description TEXT, counterparty TEXT, reference TEXT,
 status TEXT NOT NULL DEFAULT 'posted' CHECK(status IN ('posted','voided')),
 created_by INTEGER NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(account_id) REFERENCES accounting_accounts(id), FOREIGN KEY(category_id) REFERENCES accounting_categories(id)
);
CREATE INDEX IF NOT EXISTS idx_accounting_tx_restaurant ON accounting_transactions(restaurant_id,id DESC);
CREATE TABLE IF NOT EXISTS accounting_reconciliations(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, account_id INTEGER NOT NULL,
 statement_balance INTEGER NOT NULL, reconciled_at TEXT NOT NULL, reconciled_by INTEGER NOT NULL, note TEXT
);
"""
DEFAULT_CATEGORIES=[("فروش","income"),("سایر درآمد","income"),("خرید مواد اولیه","expense"),("حقوق و دستمزد","expense"),("اجاره","expense"),("قبوض و خدمات","expense"),("بازاریابی","expense"),("سایر هزینه","expense")]
DEFAULT_ACCOUNTS=[("صندوق","cash"),("حساب بانکی","bank"),("دریافتنی مشتریان","receivable"),("پرداختنی تأمین‌کنندگان","payable")]

def install_accounting_schema(c): c.executescript(ACCOUNTING_SCHEMA)

def seed_accounting(c,rid):
    for name,kind in DEFAULT_CATEGORIES: c.execute("INSERT OR IGNORE INTO accounting_categories(restaurant_id,name,kind) VALUES(?,?,?)",(rid,name,kind))
    for name,typ in DEFAULT_ACCOUNTS:
        c.execute("INSERT INTO accounting_accounts(restaurant_id,name,account_type) SELECT ?,?,? WHERE NOT EXISTS(SELECT 1 FROM accounting_accounts WHERE restaurant_id=? AND name=?)",(rid,name,typ,rid,name))

def mount_accounting_routes(app,conn_factory,current_user):
    @app.get("/api/accounting/summary")
    def summary(user=Depends(current_user)):
        c=conn_factory(); rid=user["restaurant_id"]
        try:
            seed_accounting(c,rid); c.commit()
            income=c.execute("SELECT COALESCE(SUM(amount),0) FROM accounting_transactions WHERE restaurant_id=? AND direction='in' AND status='posted'",(rid,)).fetchone()[0]
            expense=c.execute("SELECT COALESCE(SUM(amount),0) FROM accounting_transactions WHERE restaurant_id=? AND direction='out' AND status='posted'",(rid,)).fetchone()[0]
            def bal(t): return c.execute("SELECT COALESCE(SUM(CASE WHEN direction='in' THEN amount ELSE -amount END),0) FROM accounting_transactions t JOIN accounting_accounts a ON a.id=t.account_id WHERE t.restaurant_id=? AND a.account_type=? AND t.status='posted'",(rid,t)).fetchone()[0]
            return {"income":income,"expense":expense,"profit":income-expense,"cash":bal("cash"),"bank":bal("bank")}
        finally: c.close()
    @app.get("/api/accounting/categories")
    def categories(user=Depends(current_user)):
        c=conn_factory();
        try: seed_accounting(c,user["restaurant_id"]); c.commit(); return [dict(r) for r in c.execute("SELECT id,name,kind,active FROM accounting_categories WHERE restaurant_id=? ORDER BY kind,name",(user["restaurant_id"],))]
        finally: c.close()
    @app.get("/api/accounting/accounts")
    def accounts(user=Depends(current_user)):
        c=conn_factory();
        try: seed_accounting(c,user["restaurant_id"]); c.commit(); return [dict(r) for r in c.execute("SELECT id,name,account_type,balance,active FROM accounting_accounts WHERE restaurant_id=? ORDER BY id",(user["restaurant_id"],))]
        finally: c.close()
    @app.get("/api/accounting/transactions")
    def transactions(limit:int=100,user=Depends(current_user)):
        c=conn_factory(); limit=max(1,min(limit,500))
        try: return [dict(r) for r in c.execute("SELECT t.*,a.name account_name,c.name category_name,u.name created_by_name FROM accounting_transactions t JOIN accounting_accounts a ON a.id=t.account_id LEFT JOIN accounting_categories c ON c.id=t.category_id LEFT JOIN users u ON u.id=t.created_by WHERE t.restaurant_id=? ORDER BY t.id DESC LIMIT ?",(user["restaurant_id"],limit))]
        finally: c.close()
    @app.post("/api/accounting/transactions")
    def create_transaction(payload:dict,user=Depends(current_user)):
        direction=str(payload.get("direction","")).strip(); amount=int(payload.get("amount",0)); account_id=int(payload.get("account_id",0)); category_id=payload.get("category_id")
        if direction not in ("in","out") or amount<=0 or account_id<=0: raise HTTPException(400,"نوع، مبلغ و حساب معتبر الزامی است")
        c=conn_factory(); rid=user["restaurant_id"]
        try:
            if not c.execute("SELECT id FROM accounting_accounts WHERE id=? AND restaurant_id=? AND active=1",(account_id,rid)).fetchone(): raise HTTPException(404,"حساب یافت نشد")
            if category_id is not None and not c.execute("SELECT id FROM accounting_categories WHERE id=? AND restaurant_id=? AND active=1",(int(category_id),rid)).fetchone(): raise HTTPException(404,"دسته‌بندی یافت نشد")
            now=datetime.now(timezone.utc).isoformat(); tx=c.execute("INSERT INTO accounting_transactions(restaurant_id,account_id,category_id,direction,amount,description,counterparty,reference,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(rid,account_id,category_id,direction,amount,str(payload.get("description","")).strip(),str(payload.get("counterparty","")).strip(),str(payload.get("reference","")).strip(),user["id"],now)).lastrowid
            c.execute("UPDATE accounting_accounts SET balance=balance+? WHERE id=?",(amount if direction=="in" else -amount,account_id)); c.commit(); return {"id":tx,"status":"posted"}
        finally: c.close()
    @app.post("/api/accounting/transactions/{tx_id}/void")
    def void_transaction(tx_id:int,user=Depends(current_user)):
        c=conn_factory();
        try:
            tx=c.execute("SELECT * FROM accounting_transactions WHERE id=? AND restaurant_id=? AND status='posted'",(tx_id,user["restaurant_id"])).fetchone()
            if not tx: raise HTTPException(404,"تراکنش یافت نشد")
            c.execute("UPDATE accounting_transactions SET status='voided' WHERE id=?",(tx_id,)); c.execute("UPDATE accounting_accounts SET balance=balance+? WHERE id=?",(-tx["amount"] if tx["direction"]=="in" else tx["amount"],tx["account_id"])); c.commit(); return {"status":"voided"}
        finally: c.close()
    @app.post("/api/accounting/reconcile")
    def reconcile(payload:dict,user=Depends(current_user)):
        account_id=int(payload.get("account_id",0)); statement_balance=int(payload.get("statement_balance",0)); c=conn_factory(); rid=user["restaurant_id"]
        try:
            if not c.execute("SELECT 1 FROM accounting_accounts WHERE id=? AND restaurant_id=?",(account_id,rid)).fetchone(): raise HTTPException(404,"حساب یافت نشد")
            now=datetime.now(timezone.utc).isoformat(); c.execute("INSERT INTO accounting_reconciliations(restaurant_id,account_id,statement_balance,reconciled_at,reconciled_by,note) VALUES(?,?,?,?,?,?)",(rid,account_id,statement_balance,now,user["id"],str(payload.get("note","")).strip())); c.commit(); current=c.execute("SELECT balance FROM accounting_accounts WHERE id=?",(account_id,)).fetchone()[0]; return {"status":"reconciled","book_balance":current,"statement_balance":statement_balance,"difference":statement_balance-current}
        finally: c.close()
    return app
