"""Customer club: loyalty points, tiers and customer segmentation."""
from fastapi import Depends, HTTPException

SCHEMA = """
CREATE TABLE IF NOT EXISTS loyalty_transactions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    points INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    reference_id INTEGER,
    note TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_loyalty_customer ON loyalty_transactions(restaurant_id, customer_id, id DESC);
"""


def install_customer_club_schema(c):
    c.executescript(SCHEMA)


def mount_customer_club_routes(app, conn_factory, current_user):
    @app.get('/api/customer-club/summary')
    def summary(user=Depends(current_user)):
        c=conn_factory()
        try:
            rid=user['restaurant_id']
            total=c.execute('SELECT COUNT(*) FROM customers WHERE restaurant_id=?',(rid,)).fetchone()[0]
            members=c.execute('SELECT COUNT(*) FROM customers WHERE restaurant_id=? AND points>0',(rid,)).fetchone()[0]
            points=c.execute('SELECT COALESCE(SUM(points),0) FROM loyalty_transactions WHERE restaurant_id=?',(rid,)).fetchone()[0]
            return {'customers':total,'members':members,'points_issued':points}
        finally: c.close()

    @app.get('/api/customer-club/customers')
    def club_customers(user=Depends(current_user)):
        c=conn_factory()
        try:
            rid=user['restaurant_id']
            rows=c.execute('''SELECT c.id,c.name,c.phone,c.points,
                COUNT(o.id) orders,COALESCE(SUM(o.total),0) total_spend
                FROM customers c LEFT JOIN orders o ON o.customer_id=c.id AND o.restaurant_id=c.restaurant_id
                WHERE c.restaurant_id=? GROUP BY c.id ORDER BY c.points DESC,c.id DESC''',(rid,)).fetchall()
            return [dict(x) for x in rows]
        finally: c.close()

    @app.post('/api/customer-club/points')
    def add_points(payload:dict,user=Depends(current_user)):
        customer_id=int(payload.get('customer_id',0)); points=int(payload.get('points',0)); note=str(payload.get('note','')).strip()
        if not customer_id or points==0: raise HTTPException(400,'مشتری و مقدار امتیاز الزامی است')
        c=conn_factory()
        try:
            rid=user['restaurant_id']
            if not c.execute('SELECT 1 FROM customers WHERE id=? AND restaurant_id=?',(customer_id,rid)).fetchone(): raise HTTPException(404,'مشتری یافت نشد')
            c.execute('BEGIN')
            c.execute('UPDATE customers SET points=MAX(0,points+?) WHERE id=? AND restaurant_id=?',(points,customer_id,rid))
            c.execute("INSERT INTO loyalty_transactions(restaurant_id,customer_id,points,transaction_type,note,created_at) VALUES(?,?,?,?,?,datetime('now'))",(rid,customer_id,points,'manual',note))
            c.commit()
            return dict(c.execute('SELECT id,name,phone,points FROM customers WHERE id=?',(customer_id,)).fetchone())
        except HTTPException:
            c.rollback(); raise
        finally: c.close()

    @app.get('/api/customer-club/segments')
    def segments(user=Depends(current_user)):
        c=conn_factory()
        try:
            rid=user['restaurant_id']
            rows=c.execute('''SELECT c.id,c.name,c.phone,c.points,
              COUNT(o.id) orders,COALESCE(SUM(o.total),0) spend,
              MAX(o.created_at) last_order
              FROM customers c LEFT JOIN orders o ON o.customer_id=c.id AND o.restaurant_id=c.restaurant_id
              WHERE c.restaurant_id=? GROUP BY c.id''',(rid,)).fetchall()
            out=[]
            for x in rows:
                d=dict(x)
                if not d['orders']: d['segment']='بدون خرید'
                elif d['spend']>=5000000: d['segment']='VIP'
                elif d['orders']>=5: d['segment']='وفادار'
                elif d['last_order']: d['segment']='فعال'
                else: d['segment']='سایر'
                out.append(d)
            return out
        finally: c.close()
