"""POS/KDS order lifecycle for Emperator."""
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

    @app.patch('/api/orders/{order_id}/status')
    def update_status(order_id:int,payload:dict,user=Depends(current_user)):
        status=str(payload.get('status','')).strip()
        if status not in STATUSES: raise HTTPException(400,'وضعیت سفارش نامعتبر است')
        c=conn_factory(); rid=user['restaurant_id']
        try:
            row=c.execute('SELECT id,status FROM orders WHERE id=? AND restaurant_id=?',(order_id,rid)).fetchone()
            if not row: raise HTTPException(404,'سفارش یافت نشد')
            old=row['status']
            allowed={'جدید':{'در حال آماده‌سازی','لغوشده'},'در حال آماده‌سازی':{'آماده','لغوشده'},'آماده':{'تحویل‌شده'},'تحویل‌شده':set(),'لغوشده':set()}
            if status!=old and status not in allowed.get(old,set()): raise HTTPException(409,f'تغییر وضعیت از {old} به {status} مجاز نیست')
            c.execute('UPDATE orders SET status=? WHERE id=? AND restaurant_id=?',(status,order_id,rid))
            c.commit()
            return {'id':order_id,'old_status':old,'status':status}
        except HTTPException:
            c.rollback(); raise
        finally: c.close()

    @app.get('/api/orders/{order_id}/items')
    def order_items(order_id:int,user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            if not c.execute('SELECT 1 FROM orders WHERE id=? AND restaurant_id=?',(order_id,rid)).fetchone(): raise HTTPException(404,'سفارش یافت نشد')
            return [dict(x) for x in c.execute('SELECT * FROM order_items WHERE order_id=?',(order_id,)).fetchall()]
        finally: c.close()
