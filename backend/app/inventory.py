"""Inventory, purchasing, recipes and stock-cost foundation for Emperator."""
from datetime import datetime, timezone
from fastapi import Depends, HTTPException

INVENTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS inventory_items(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, name TEXT NOT NULL,
 unit TEXT NOT NULL DEFAULT 'عدد', sku TEXT, min_stock REAL NOT NULL DEFAULT 0,
 cost_per_unit INTEGER NOT NULL DEFAULT 0, current_stock REAL NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
 UNIQUE(restaurant_id,name)
);
CREATE TABLE IF NOT EXISTS inventory_movements(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, item_id INTEGER NOT NULL,
 movement_type TEXT NOT NULL CHECK(movement_type IN ('purchase','sale_consumption','adjustment_in','adjustment_out','waste','return')),
 quantity REAL NOT NULL, unit_cost INTEGER NOT NULL DEFAULT 0, reference_type TEXT, reference_id INTEGER,
 note TEXT, created_by INTEGER NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(item_id) REFERENCES inventory_items(id)
);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_restaurant ON inventory_movements(restaurant_id,id DESC);
CREATE TABLE IF NOT EXISTS suppliers(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, name TEXT NOT NULL, phone TEXT, address TEXT, active INTEGER NOT NULL DEFAULT 1,
 UNIQUE(restaurant_id,name)
);
CREATE TABLE IF NOT EXISTS purchase_invoices(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, supplier_id INTEGER, total INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'posted', note TEXT, created_by INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS purchase_items(
 id INTEGER PRIMARY KEY AUTOINCREMENT, purchase_id INTEGER NOT NULL, item_id INTEGER NOT NULL, quantity REAL NOT NULL, unit_cost INTEGER NOT NULL,
 FOREIGN KEY(purchase_id) REFERENCES purchase_invoices(id) ON DELETE CASCADE, FOREIGN KEY(item_id) REFERENCES inventory_items(id)
);
CREATE TABLE IF NOT EXISTS recipes(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, product_id INTEGER NOT NULL, name TEXT NOT NULL, yield_quantity REAL NOT NULL DEFAULT 1, active INTEGER NOT NULL DEFAULT 1,
 UNIQUE(restaurant_id,product_id)
);
CREATE TABLE IF NOT EXISTS recipe_items(
 id INTEGER PRIMARY KEY AUTOINCREMENT, recipe_id INTEGER NOT NULL, item_id INTEGER NOT NULL, quantity REAL NOT NULL,
 FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE, FOREIGN KEY(item_id) REFERENCES inventory_items(id)
);
"""


def install_inventory_schema(c):
    c.executescript(INVENTORY_SCHEMA)


def now(): return datetime.now(timezone.utc).isoformat()


def movement(c, user, item_id, qty, typ, unit_cost=0, ref_type=None, ref_id=None, note=""):
    rid=user["restaurant_id"]
    item=c.execute("SELECT * FROM inventory_items WHERE id=? AND restaurant_id=? AND active=1",(item_id,rid)).fetchone()
    if not item: raise HTTPException(404,"ماده اولیه یافت نشد")
    new_stock=float(item["current_stock"])+float(qty)
    if new_stock < -1e-9: raise HTTPException(409,"موجودی کافی نیست")
    c.execute("UPDATE inventory_items SET current_stock=?,cost_per_unit=? WHERE id=?",(new_stock, unit_cost or item["cost_per_unit"],item_id))
    c.execute("INSERT INTO inventory_movements(restaurant_id,item_id,movement_type,quantity,unit_cost,reference_type,reference_id,note,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(rid,item_id,typ,qty,unit_cost or item["cost_per_unit"],ref_type,ref_id,note,user["id"],now()))


def mount_inventory_routes(app, conn_factory, current_user):
    @app.get("/api/inventory/items")
    def items(user=Depends(current_user)):
        c=conn_factory()
        try: return [dict(r) for r in c.execute("SELECT * FROM inventory_items WHERE restaurant_id=? AND active=1 ORDER BY name",(user["restaurant_id"],))]
        finally: c.close()

    @app.post("/api/inventory/items")
    def create_item(payload:dict,user=Depends(current_user)):
        name=str(payload.get("name","")).strip(); unit=str(payload.get("unit","عدد")).strip() or "عدد"
        if not name: raise HTTPException(400,"نام ماده اولیه الزامی است")
        c=conn_factory()
        try:
            cur=c.execute("INSERT INTO inventory_items(restaurant_id,name,unit,sku,min_stock,cost_per_unit) VALUES(?,?,?,?,?,?)",(user["restaurant_id"],name,unit,str(payload.get("sku","")).strip(),float(payload.get("min_stock",0)),int(payload.get("cost_per_unit",0))))
            c.commit(); return {"id":cur.lastrowid}
        except Exception as e:
            c.rollback(); raise HTTPException(409,"ماده اولیه تکراری یا نامعتبر است")
        finally: c.close()

    @app.post("/api/inventory/movements")
    def create_movement(payload:dict,user=Depends(current_user)):
        item_id=int(payload.get("item_id",0)); qty=float(payload.get("quantity",0)); typ=str(payload.get("movement_type","adjustment_in"))
        if item_id<=0 or qty<=0 or typ not in ("adjustment_in","adjustment_out","waste","return"): raise HTTPException(400,"اطلاعات حرکت موجودی نامعتبر است")
        signed=qty if typ in ("adjustment_in","return") else -qty
        c=conn_factory()
        try: movement(c,user,item_id,signed,typ,int(payload.get("unit_cost",0)),note=str(payload.get("note","")).strip()); c.commit(); return {"status":"posted"}
        finally: c.close()

    @app.get("/api/inventory/movements")
    def movements(limit:int=100,user=Depends(current_user)):
        c=conn_factory()
        try: return [dict(r) for r in c.execute("SELECT m.*,i.name item_name,i.unit FROM inventory_movements m JOIN inventory_items i ON i.id=m.item_id WHERE m.restaurant_id=? ORDER BY m.id DESC LIMIT ?",(user["restaurant_id"],max(1,min(limit,500))))]
        finally: c.close()

    @app.get("/api/inventory/low-stock")
    def low_stock(user=Depends(current_user)):
        c=conn_factory()
        try: return [dict(r) for r in c.execute("SELECT * FROM inventory_items WHERE restaurant_id=? AND active=1 AND current_stock<=min_stock ORDER BY current_stock",(user["restaurant_id"],))]
        finally: c.close()

    @app.post("/api/inventory/purchases")
    def purchase(payload:dict,user=Depends(current_user)):
        rows=payload.get("items") or []
        if not rows: raise HTTPException(400,"اقلام خرید الزامی است")
        c=conn_factory()
        try:
            rid=user["restaurant_id"]; total=sum(float(x.get("quantity",0))*int(x.get("unit_cost",0)) for x in rows)
            cur=c.execute("INSERT INTO purchase_invoices(restaurant_id,supplier_id,total,note,created_by,created_at) VALUES(?,?,?,?,?,?)",(rid,payload.get("supplier_id"),int(total),str(payload.get("note","")).strip(),user["id"],now())); pid=cur.lastrowid
            for x in rows:
                item_id=int(x.get("item_id",0)); q=float(x.get("quantity",0)); cost=int(x.get("unit_cost",0))
                if q<=0 or cost<0: raise HTTPException(400,"مقدار خرید نامعتبر است")
                c.execute("INSERT INTO purchase_items(purchase_id,item_id,quantity,unit_cost) VALUES(?,?,?,?)",(pid,item_id,q,cost)); movement(c,user,item_id,q,"purchase",cost,"purchase",pid)
            c.commit(); return {"id":pid,"total":int(total)}
        except HTTPException: c.rollback(); raise
        finally: c.close()

    @app.get("/api/inventory/recipes/{product_id}")
    def recipe(product_id:int,user=Depends(current_user)):
        c=conn_factory()
        try:
            r=c.execute("SELECT * FROM recipes WHERE restaurant_id=? AND product_id=? AND active=1",(user["restaurant_id"],product_id)).fetchone()
            if not r: return {"recipe":None,"items":[]}
            return {"recipe":dict(r),"items":[dict(x) for x in c.execute("SELECT ri.*,i.name item_name,i.unit,i.cost_per_unit FROM recipe_items ri JOIN inventory_items i ON i.id=ri.item_id WHERE ri.recipe_id=?",(r["id"],))]}
        finally: c.close()

    @app.post("/api/inventory/recipes")
    def save_recipe(payload:dict,user=Depends(current_user)):
        product_id=int(payload.get("product_id",0)); rows=payload.get("items") or []
        if product_id<=0 or not rows: raise HTTPException(400,"محصول و مواد دستور پخت الزامی است")
        c=conn_factory()
        try:
            rid=user["restaurant_id"]; old=c.execute("SELECT id FROM recipes WHERE restaurant_id=? AND product_id=?",(rid,product_id)).fetchone()
            if old:
                recipe_id=old[0]; c.execute("DELETE FROM recipe_items WHERE recipe_id=?",(recipe_id,)); c.execute("UPDATE recipes SET name=?,yield_quantity=?,active=1 WHERE id=?",(str(payload.get("name","دستور پخت")).strip(),float(payload.get("yield_quantity",1)),recipe_id))
            else:
                recipe_id=c.execute("INSERT INTO recipes(restaurant_id,product_id,name,yield_quantity) VALUES(?,?,?,?)",(rid,product_id,str(payload.get("name","دستور پخت")).strip(),float(payload.get("yield_quantity",1)))).lastrowid
            for x in rows: c.execute("INSERT INTO recipe_items(recipe_id,item_id,quantity) VALUES(?,?,?)",(recipe_id,int(x["item_id"]),float(x["quantity"])))
            c.commit(); return {"id":recipe_id}
        finally: c.close()
    return app
