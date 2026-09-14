"""Kitchen Display System (KDS) for Emperator.
Status mutation is intentionally owned by order_inventory so inventory consumption
and status changes stay atomic. This module only exposes KDS reads."""
from fastapi import Depends, HTTPException

STATUSES = ["جدید", "در حال آماده‌سازی", "آماده", "تحویل‌شده", "لغوشده"]


def mount_kds_routes(app, conn_factory, current_user):
    @app.get('/api/kds/orders')
    def kds_orders(user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            rows=c.execute("SELECT o.*,COALESCE(c.name,'مشتری حضوری') customer_name FROM orders o LEFT JOIN customers c ON c.id=o.customer_id AND c.restaurant_id=o.restaurant_id WHERE o.restaurant_id=? AND o.status IN ('جدید','در حال آماده‌سازی','آماده') ORDER BY CASE o.status WHEN 'جدید' THEN 1 WHEN 'در حال آماده‌سازی' THEN 2 ELSE 3 END,o.id",(rid,)).fetchall()
            out=[]
            for r in rows:
                d=dict(r); d['items']=[dict(x) for x in c.execute('SELECT product_id,name,price,quantity FROM order_items WHERE order_id=?',(r['id'],)).fetchall()]; out.append(d)
            return out
        finally: c.close()

    @app.get('/api/orders/{order_id}/items')
    def order_items(order_id:int,user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            if not c.execute('SELECT 1 FROM orders WHERE id=? AND restaurant_id=?',(order_id,rid)).fetchone(): raise HTTPException(404,'سفارش یافت نشد')
            return [dict(x) for x in c.execute('SELECT * FROM order_items WHERE order_id=?',(order_id,)).fetchall()]
        finally: c.close()
