"""Connect order lifecycle to recipes, inventory consumption and cost of goods."""
from fastapi import Depends, HTTPException

SCHEMA = """
CREATE TABLE IF NOT EXISTS order_costs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    order_id INTEGER NOT NULL UNIQUE,
    material_cost INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_order_costs_restaurant ON order_costs(restaurant_id, order_id);
"""


def install_order_inventory_schema(c):
    c.executescript(SCHEMA)


def consume_order_inventory(c, order_id, user):
    """Consume recipe ingredients for an order inside the caller's transaction."""
    rid = user["restaurant_id"]
    order = c.execute(
        "SELECT id,status,total FROM orders WHERE id=? AND restaurant_id=?",
        (order_id, rid),
    ).fetchone()
    if not order:
        raise HTTPException(404, "سفارش یافت نشد")

    existing = c.execute(
        "SELECT material_cost FROM order_costs WHERE restaurant_id=? AND order_id=?",
        (rid, order_id),
    ).fetchone()
    if existing:
        return int(existing["material_cost"]), "already_consumed"

    rows = c.execute(
        "SELECT oi.product_id, oi.quantity FROM order_items oi WHERE oi.order_id=?",
        (order_id,),
    ).fetchall()
    total_cost = 0
    movements = []

    for row in rows:
        recipe = c.execute(
            "SELECT id,yield_quantity FROM recipes WHERE restaurant_id=? AND product_id=? AND active=1",
            (rid, row["product_id"]),
        ).fetchone()
        if not recipe:
            continue
        factor = float(row["quantity"]) / max(float(recipe["yield_quantity"]), 1e-9)
        ingredients = c.execute(
            "SELECT ri.item_id,ri.quantity,i.current_stock,i.cost_per_unit "
            "FROM recipe_items ri JOIN inventory_items i ON i.id=ri.item_id WHERE ri.recipe_id=?",
            (recipe["id"],),
        ).fetchall()
        for ing in ingredients:
            needed = float(ing["quantity"]) * factor
            if float(ing["current_stock"]) < needed - 1e-9:
                raise HTTPException(409, f"موجودی ماده اولیه {ing['item_id']} کافی نیست")
            movements.append((ing, needed))

    for ing, needed in movements:
        new_stock = float(ing["current_stock"]) - needed
        c.execute("UPDATE inventory_items SET current_stock=? WHERE id=?", (new_stock, ing["item_id"]))
        unit_cost = int(ing["cost_per_unit"] or 0)
        c.execute(
            "INSERT INTO inventory_movements(restaurant_id,item_id,movement_type,quantity,unit_cost,reference_type,reference_id,note,created_by,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,datetime('now'))",
            (rid, ing["item_id"], "sale_consumption", -needed, unit_cost, "order", order_id, "مصرف خودکار تکمیل سفارش", user["id"]),
        )
        total_cost += needed * unit_cost

    c.execute(
        "INSERT INTO order_costs(restaurant_id,order_id,material_cost,created_at) VALUES(?,?,?,datetime('now'))",
        (rid, order_id, int(total_cost)),
    )
    return int(total_cost), "consumed"


def mount_order_inventory_routes(app, conn_factory, current_user):
    @app.post('/api/orders/{order_id}/consume-inventory')
    def consume(order_id: int, user=Depends(current_user)):
        c = conn_factory()
        try:
            c.execute("BEGIN")
            cost, status = consume_order_inventory(c, order_id, user)
            c.commit()
            return {"status": status, "cost": cost}
        except HTTPException:
            c.rollback()
            raise
        finally:
            c.close()

    @app.patch('/api/orders/{order_id}/status')
    def update_status(order_id: int, payload: dict, user=Depends(current_user)):
        status = str(payload.get("status", "")).strip()
        allowed = {"جدید", "درحال آماده‌سازی", "آماده", "تحویل‌شده", "لغوشده"}
        if status not in allowed:
            raise HTTPException(400, "وضعیت سفارش نامعتبر است")
        c = conn_factory()
        try:
            c.execute("BEGIN")
            order = c.execute(
                "SELECT id,status FROM orders WHERE id=? AND restaurant_id=?",
                (order_id, user["restaurant_id"]),
            ).fetchone()
            if not order:
                raise HTTPException(404, "سفارش یافت نشد")
            if order["status"] == "لغوشده":
                raise HTTPException(409, "سفارش لغوشده قابل تغییر نیست")
            cost = 0
            if status in {"درحال آماده‌سازی", "آماده", "تحویل‌شده"}:
                cost, _ = consume_order_inventory(c, order_id, user)
            c.execute("UPDATE orders SET status=? WHERE id=? AND restaurant_id=?", (status, order_id, user["restaurant_id"]))
            c.commit()
            return {"status": status, "material_cost": cost}
        except HTTPException:
            c.rollback()
            raise
        finally:
            c.close()

    @app.get('/api/orders/{order_id}/profit')
    def profit(order_id: int, user=Depends(current_user)):
        c = conn_factory()
        try:
            row = c.execute(
                "SELECT o.id,o.total,COALESCE(oc.material_cost,0) material_cost,"
                "o.total-COALESCE(oc.material_cost,0) gross_profit "
                "FROM orders o LEFT JOIN order_costs oc ON oc.order_id=o.id AND oc.restaurant_id=o.restaurant_id "
                "WHERE o.id=? AND o.restaurant_id=?",
                (order_id, user["restaurant_id"]),
            ).fetchone()
            if not row:
                raise HTTPException(404, 'سفارش یافت نشد')
            return dict(row)
        finally:
            c.close()

    @app.get('/api/reports/profit')
    def profit_report(user=Depends(current_user)):
        c = conn_factory()
        try:
            r = c.execute(
                "SELECT COALESCE(SUM(o.total),0) sales,"
                "COALESCE(SUM(oc.material_cost),0) material_cost,"
                "COALESCE(SUM(o.total-COALESCE(oc.material_cost,0)),0) gross_profit,"
                "COUNT(o.id) orders "
                "FROM orders o LEFT JOIN order_costs oc ON oc.order_id=o.id AND oc.restaurant_id=o.restaurant_id "
                "WHERE o.restaurant_id=?",
                (user["restaurant_id"],),
            ).fetchone()
            return dict(r)
        finally:
            c.close()
