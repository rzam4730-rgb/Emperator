"""Connect orders to recipes, inventory consumption and cost of goods."""
from fastapi import Depends, HTTPException

def mount_order_inventory_routes(app, conn_factory, current_user):
    @app.post('/api/orders/{order_id}/consume-inventory')
    def consume(order_id:int,user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            order=c.execute('SELECT id,status FROM orders WHERE id=? AND restaurant_id=?',(order_id,rid)).fetchone()
            if not order: raise HTTPException(404,'سفارش یافت نشد')
            done=c.execute("SELECT 1 FROM inventory_movements WHERE restaurant_id=? AND reference_type='order' AND reference_id=? AND movement_type='sale_consumption' LIMIT 1",(rid,order_id)).fetchone()
            if done: return {'status':'already_consumed','cost':sum(x['quantity']*x['unit_cost'] for x in c.execute("SELECT quantity,unit_cost FROM inventory_movements WHERE restaurant_id=? AND reference_type='order' AND reference_id=? AND movement_type='sale_consumption'",(rid,order_id)))}
            rows=c.execute('SELECT oi.product_id,oi.quantity FROM order_items oi WHERE oi.order_id=?',(order_id,)).fetchall(); total_cost=0
            for row in rows:
                recipe=c.execute('SELECT id,yield_quantity FROM recipes WHERE restaurant_id=? AND product_id=? AND active=1',(rid,row['product_id'])).fetchone()
                if not recipe: continue
                factor=float(row['quantity'])/max(float(recipe['yield_quantity']),1e-9)
                ingredients=c.execute('SELECT ri.item_id,ri.quantity,i.current_stock,i.cost_per_unit FROM recipe_items ri JOIN inventory_items i ON i.id=ri.item_id WHERE ri.recipe_id=?',(recipe['id'],)).fetchall()
                for ing in ingredients:
                    needed=float(ing['quantity'])*factor
                    if float(ing['current_stock']) < needed-1e-9: raise HTTPException(409,f"موجودی {ing['item_id']} کافی نیست")
                    new=float(ing['current_stock'])-needed
                    c.execute('UPDATE inventory_items SET current_stock=? WHERE id=?',(new,ing['item_id']))
                    c.execute("INSERT INTO inventory_movements(restaurant_id,item_id,movement_type,quantity,unit_cost,reference_type,reference_id,note,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?,datetime('now'))",(rid,ing['item_id'],'sale_consumption',-needed,int(ing['cost_per_unit']),'order',order_id,'مصرف خودکار سفارش',user['id']))
                    total_cost += needed*int(ing['cost_per_unit'])
            c.execute('CREATE TABLE IF NOT EXISTS order_costs(id INTEGER PRIMARY KEY AUTOINCREMENT,restaurant_id INTEGER NOT NULL,order_id INTEGER NOT NULL UNIQUE,material_cost INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL)')
            c.execute("INSERT INTO order_costs(restaurant_id,order_id,material_cost,created_at) VALUES(?,?,?,datetime('now'))",(rid,order_id,int(total_cost)))
            c.commit(); return {'status':'consumed','cost':int(total_cost)}
        except HTTPException: c.rollback(); raise
        finally: c.close()

    @app.get('/api/orders/{order_id}/profit')
    def profit(order_id:int,user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            row=c.execute("SELECT o.id,o.total,COALESCE(oc.material_cost,0) material_cost,o.total-COALESCE(oc.material_cost,0) gross_profit FROM orders o LEFT JOIN order_costs oc ON oc.order_id=o.id AND oc.restaurant_id=o.restaurant_id WHERE o.id=? AND o.restaurant_id=?",(order_id,rid)).fetchone()
            if not row: raise HTTPException(404,'سفارش یافت نشد')
            return dict(row)
        finally: c.close()

    @app.get('/api/reports/profit')
    def profit_report(user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            r=c.execute("SELECT COALESCE(SUM(o.total),0) sales,COALESCE(SUM(oc.material_cost),0) material_cost,COALESCE(SUM(o.total-COALESCE(oc.material_cost,0)),0) gross_profit,COUNT(o.id) orders FROM orders o LEFT JOIN order_costs oc ON oc.order_id=o.id AND oc.restaurant_id=o.restaurant_id WHERE o.restaurant_id=?",(rid,)).fetchone()
            return dict(r)
        finally: c.close()
