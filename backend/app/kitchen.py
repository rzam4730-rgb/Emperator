"""Kitchen Display System (KDS) core for Emperator."""
from datetime import datetime, timezone
from fastapi import Depends, HTTPException

KITCHEN_SCHEMA = """
CREATE TABLE IF NOT EXISTS kitchen_tickets(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, order_id INTEGER NOT NULL UNIQUE,
 station TEXT NOT NULL DEFAULT 'main', status TEXT NOT NULL DEFAULT 'new', priority INTEGER NOT NULL DEFAULT 0,
 started_at TEXT, ready_at TEXT, completed_at TEXT, note TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kitchen_ticket_items(
 id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id INTEGER NOT NULL, product_id INTEGER, product_name TEXT NOT NULL,
 quantity INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', note TEXT,
 FOREIGN KEY(ticket_id) REFERENCES kitchen_tickets(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_kitchen_queue ON kitchen_tickets(restaurant_id,status,priority DESC,id ASC);
"""
STATUSES = ("new", "preparing", "ready", "completed", "cancelled")

def install_kitchen_schema(c): c.executescript(KITCHEN_SCHEMA)
def now(): return datetime.now(timezone.utc).isoformat()

def mount_kitchen_routes(app, conn_factory, current_user):
    @app.get("/api/kitchen/queue")
    def queue(status:str="",user=Depends(current_user)):
        c=conn_factory()
        try:
            sql="SELECT k.*,o.total,o.customer_id FROM kitchen_tickets k JOIN orders o ON o.id=k.order_id WHERE k.restaurant_id=?"
            args=[user["restaurant_id"]]
            if status in STATUSES: sql+=" AND k.status=?"; args.append(status)
            rows=[]
            for t in c.execute(sql+" ORDER BY k.priority DESC,k.id ASC",args).fetchall():
                d=dict(t); d["items"]=[dict(x) for x in c.execute("SELECT * FROM kitchen_ticket_items WHERE ticket_id=? ORDER BY id",(t["id"],))]; rows.append(d)
            return rows
        finally: c.close()

    @app.post("/api/kitchen/tickets")
    def create_ticket(payload:dict,user=Depends(current_user)):
        oid=int(payload.get("order_id",0))
        if oid<=0: raise HTTPException(400,"شماره سفارش الزامی است")
        c=conn_factory()
        try:
            rid=user["restaurant_id"]
            order=c.execute("SELECT * FROM orders WHERE id=? AND restaurant_id=?",(oid,rid)).fetchone()
            if not order: raise HTTPException(404,"سفارش یافت نشد")
            existing=c.execute("SELECT id FROM kitchen_tickets WHERE order_id=?",(oid,)).fetchone()
            if existing: return {"id":existing[0],"status":"existing"}
            cur=c.execute("INSERT INTO kitchen_tickets(restaurant_id,order_id,station,priority,note,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(rid,oid,str(payload.get("station","main")),int(payload.get("priority",0)),str(payload.get("note","")),now(),now()))
            tid=cur.lastrowid
            items=c.execute("SELECT product_id,name,quantity FROM order_items WHERE order_id=?",(oid,)).fetchall()
            for x in items: c.execute("INSERT INTO kitchen_ticket_items(ticket_id,product_id,product_name,quantity) VALUES(?,?,?,?)",(tid,x["product_id"],x["name"],x["quantity"]))
            c.commit(); return {"id":tid,"order_id":oid,"status":"new"}
        except HTTPException: c.rollback(); raise
        finally: c.close()

    @app.patch("/api/kitchen/tickets/{ticket_id}")
    def update_ticket(ticket_id:int,payload:dict,user=Depends(current_user)):
        status=str(payload.get("status","")).lower();
        if status not in STATUSES: raise HTTPException(400,"وضعیت نامعتبر است")
        c=conn_factory()
        try:
            t=c.execute("SELECT * FROM kitchen_tickets WHERE id=? AND restaurant_id=?",(ticket_id,user["restaurant_id"])).fetchone()
            if not t: raise HTTPException(404,"تیکت آشپزخانه یافت نشد")
            ts=now(); fields=["status=?","updated_at=?"]; args=[status,ts]
            if status=="preparing": fields.append("started_at=?"); args.append(ts)
            if status=="ready": fields.append("ready_at=?"); args.append(ts)
            if status=="completed": fields.append("completed_at=?"); args.append(ts)
            args.append(ticket_id); c.execute("UPDATE kitchen_tickets SET "+",".join(fields)+" WHERE id=?",args)
            order_status={"new":"جدید","preparing":"در حال آماده‌سازی","ready":"آماده","completed":"تحویل شد","cancelled":"لغو شد"}[status]
            c.execute("UPDATE orders SET status=? WHERE id=? AND restaurant_id=?",(order_status,t["order_id"],user["restaurant_id"]))
            c.commit(); return dict(c.execute("SELECT * FROM kitchen_tickets WHERE id=?",(ticket_id,)).fetchone())
        finally: c.close()

    @app.post("/api/kitchen/tickets/{ticket_id}/items/{item_id}")
    def update_item(ticket_id:int,item_id:int,payload:dict,user=Depends(current_user)):
        status=str(payload.get("status","")).lower()
        if status not in ("pending","preparing","ready","cancelled"): raise HTTPException(400,"وضعیت قلم نامعتبر است")
        c=conn_factory()
        try:
            ok=c.execute("SELECT 1 FROM kitchen_tickets WHERE id=? AND restaurant_id=?",(ticket_id,user["restaurant_id"])).fetchone()
            if not ok: raise HTTPException(404,"تیکت یافت نشد")
            c.execute("UPDATE kitchen_ticket_items SET status=? WHERE id=? AND ticket_id=?",(status,item_id,ticket_id)); c.commit(); return {"status":"ok"}
        finally: c.close()
    return app
