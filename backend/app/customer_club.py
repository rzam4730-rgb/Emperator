"""Customer club: automatic loyalty rewards, segments and SMS campaigns."""
from datetime import datetime, timezone
from fastapi import Depends, HTTPException

SCHEMA = """
CREATE TABLE IF NOT EXISTS loyalty_transactions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, customer_id INTEGER NOT NULL,
 order_id INTEGER, points INTEGER NOT NULL, transaction_type TEXT NOT NULL, note TEXT, created_at TEXT NOT NULL, created_by INTEGER
);
CREATE INDEX IF NOT EXISTS idx_loyalty_customer ON loyalty_transactions(restaurant_id,customer_id,created_at);
CREATE TABLE IF NOT EXISTS sms_campaigns(
 id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, name TEXT NOT NULL, message TEXT NOT NULL,
 segment TEXT NOT NULL DEFAULT 'all', status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL, sent_at TEXT,
 sent_count INTEGER NOT NULL DEFAULT 0, failed_count INTEGER NOT NULL DEFAULT 0, created_by INTEGER
);
CREATE TABLE IF NOT EXISTS sms_campaign_recipients(
 id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id INTEGER NOT NULL, customer_id INTEGER NOT NULL, phone TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending', provider_message_id TEXT, error TEXT, sent_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_campaign_recipients ON sms_campaign_recipients(campaign_id,status);
"""

POINTS_PER_1000 = 1

def _now(): return datetime.now(timezone.utc).isoformat()

def install_customer_club_schema(c): c.executescript(SCHEMA)

def award_order_points(c, restaurant_id, order_id, user_id=None):
    order=c.execute("SELECT customer_id,total FROM orders WHERE id=? AND restaurant_id=?",(order_id,restaurant_id)).fetchone()
    if not order or not order['customer_id']: return 0
    if c.execute("SELECT 1 FROM loyalty_transactions WHERE restaurant_id=? AND order_id=? AND transaction_type='order_reward' LIMIT 1",(restaurant_id,order_id)).fetchone(): return 0
    points=max(0,int(order['total'])//1000*POINTS_PER_1000)
    if not points: return 0
    c.execute("UPDATE customers SET points=COALESCE(points,0)+? WHERE id=? AND restaurant_id=?",(points,order['customer_id'],restaurant_id))
    c.execute("INSERT INTO loyalty_transactions(restaurant_id,customer_id,order_id,points,transaction_type,note,created_at,created_by) VALUES(?,?,?,?,?,?,?,?)",(restaurant_id,order['customer_id'],order_id,points,'order_reward','امتیاز خرید',_now(),user_id))
    return points

def _segment_sql(segment):
    return {
      'vip': "COALESCE(c.points,0)>=500",
      'loyal': "COALESCE(c.points,0)>=100 AND COALESCE(c.points,0)<500",
      'active': "EXISTS (SELECT 1 FROM orders o WHERE o.customer_id=c.id AND o.restaurant_id=c.restaurant_id AND datetime(o.created_at)>=datetime('now','-30 day'))",
      'inactive': "NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id=c.id AND o.restaurant_id=c.restaurant_id AND datetime(o.created_at)>=datetime('now','-30 day'))"
    }.get(segment,'1=1')

def mount_customer_club_routes(app, conn_factory, current_user, sms_provider_getter=None):
    @app.get('/api/customer-club/summary')
    def summary(user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            return {'customers':c.execute('SELECT COUNT(*) FROM customers WHERE restaurant_id=?',(rid,)).fetchone()[0],
                    'members':c.execute('SELECT COUNT(*) FROM customers WHERE restaurant_id=? AND points>0',(rid,)).fetchone()[0],
                    'points_issued':c.execute("SELECT COALESCE(SUM(points),0) FROM loyalty_transactions WHERE restaurant_id=? AND points>0",(rid,)).fetchone()[0],
                    'vip':c.execute('SELECT COUNT(*) FROM customers WHERE restaurant_id=? AND COALESCE(points,0)>=500',(rid,)).fetchone()[0]}
        finally: c.close()

    @app.get('/api/customer-club/customers')
    def club_customers(segment:str='all',user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            rows=c.execute(f'''SELECT c.id,c.name,c.phone,COALESCE(c.points,0) points,
                COUNT(o.id) orders,COALESCE(SUM(o.total),0) total_spend,MAX(o.created_at) last_order
                FROM customers c LEFT JOIN orders o ON o.customer_id=c.id AND o.restaurant_id=c.restaurant_id
                WHERE c.restaurant_id=? AND {_segment_sql(segment)} GROUP BY c.id ORDER BY c.points DESC,c.id DESC''',(rid,)).fetchall()
            return [dict(x) for x in rows]
        finally: c.close()

    @app.get('/api/customer-club/segments')
    def segments(user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            rows=c.execute('''SELECT c.id,c.name,c.phone,COALESCE(c.points,0) points,COUNT(o.id) orders,
              COALESCE(SUM(o.total),0) spend,MAX(o.created_at) last_order FROM customers c
              LEFT JOIN orders o ON o.customer_id=c.id AND o.restaurant_id=c.restaurant_id WHERE c.restaurant_id=? GROUP BY c.id''',(rid,)).fetchall()
            out=[]
            for x in rows:
                d=dict(x); d['segment']='بدون خرید' if not d['orders'] else ('VIP' if d['spend']>=5000000 else ('وفادار' if d['orders']>=5 else 'فعال'))
                out.append(d)
            return out
        finally: c.close()

    @app.get('/api/customer-club/customers/{customer_id}/ledger')
    def ledger(customer_id:int,user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            if not c.execute('SELECT 1 FROM customers WHERE id=? AND restaurant_id=?',(customer_id,rid)).fetchone(): raise HTTPException(404,'مشتری یافت نشد')
            return [dict(x) for x in c.execute('SELECT * FROM loyalty_transactions WHERE customer_id=? AND restaurant_id=? ORDER BY id DESC',(customer_id,rid)).fetchall()]
        finally: c.close()

    @app.post('/api/customer-club/points')
    def add_points(payload:dict,user=Depends(current_user)):
        customer_id=int(payload.get('customer_id',0)); points=int(payload.get('points',0)); note=str(payload.get('note','اصلاح دستی امتیاز')).strip()
        if not customer_id or not points: raise HTTPException(400,'مشتری و مقدار امتیاز الزامی است')
        c=conn_factory(); rid=user['restaurant_id']
        try:
            if not c.execute('SELECT 1 FROM customers WHERE id=? AND restaurant_id=?',(customer_id,rid)).fetchone(): raise HTTPException(404,'مشتری یافت نشد')
            c.execute('UPDATE customers SET points=MAX(0,COALESCE(points,0)+?) WHERE id=? AND restaurant_id=?',(points,customer_id,rid))
            c.execute("INSERT INTO loyalty_transactions(restaurant_id,customer_id,points,transaction_type,note,created_at,created_by) VALUES(?,?,?,?,?,?,?)",(rid,customer_id,points,'manual',note,_now(),user['id']))
            c.commit(); return dict(c.execute('SELECT id,name,phone,points FROM customers WHERE id=?',(customer_id,)).fetchone())
        finally: c.close()

    @app.post('/api/customer-club/award-order/{order_id}')
    def award(order_id:int,user=Depends(current_user)):
        c=conn_factory()
        try:
            points=award_order_points(c,user['restaurant_id'],order_id,user['id']); c.commit(); return {'order_id':order_id,'points_awarded':points}
        finally: c.close()

    @app.get('/api/customer-club/campaigns')
    def campaigns(user=Depends(current_user)):
        c=conn_factory()
        try: return [dict(x) for x in c.execute('SELECT * FROM sms_campaigns WHERE restaurant_id=? ORDER BY id DESC',(user['restaurant_id'],)).fetchall()]
        finally: c.close()

    @app.post('/api/customer-club/campaigns')
    def create_campaign(payload:dict,user=Depends(current_user)):
        name=str(payload.get('name','')).strip(); message=str(payload.get('message','')).strip(); segment=str(payload.get('segment','all')).lower()
        if not name or not message: raise HTTPException(400,'نام کمپین و متن پیامک الزامی است')
        if segment not in ('all','vip','loyal','active','inactive'): raise HTTPException(400,'بخش‌بندی نامعتبر است')
        c=conn_factory()
        try:
            cur=c.execute('INSERT INTO sms_campaigns(restaurant_id,name,message,segment,created_at,created_by) VALUES(?,?,?,?,?,?)',(user['restaurant_id'],name,message,segment,_now(),user['id']))
            c.commit(); return dict(c.execute('SELECT * FROM sms_campaigns WHERE id=?',(cur.lastrowid,)).fetchone())
        finally: c.close()

    @app.post('/api/customer-club/campaigns/{campaign_id}/prepare')
    def prepare(campaign_id:int,user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            camp=c.execute('SELECT * FROM sms_campaigns WHERE id=? AND restaurant_id=?',(campaign_id,rid)).fetchone()
            if not camp: raise HTTPException(404,'کمپین یافت نشد')
            c.execute('DELETE FROM sms_campaign_recipients WHERE campaign_id=?',(campaign_id,))
            rows=c.execute(f"SELECT c.id,c.phone FROM customers c WHERE c.restaurant_id=? AND c.phone IS NOT NULL AND TRIM(c.phone)<>'' AND {_segment_sql(camp['segment'])}",(rid,)).fetchall()
            c.executemany('INSERT INTO sms_campaign_recipients(campaign_id,customer_id,phone) VALUES(?,?,?)',[(campaign_id,x['id'],x['phone']) for x in rows])
            c.execute("UPDATE sms_campaigns SET status='prepared' WHERE id=?",(campaign_id,)); c.commit(); return {'campaign_id':campaign_id,'recipients':len(rows),'status':'prepared'}
        finally: c.close()

    @app.post('/api/customer-club/campaigns/{campaign_id}/send')
    def send(campaign_id:int,user=Depends(current_user)):
        if sms_provider_getter is None: raise HTTPException(503,'سرویس پیامک متصل نیست')
        c=conn_factory(); rid=user['restaurant_id']
        try:
            camp=c.execute('SELECT * FROM sms_campaigns WHERE id=? AND restaurant_id=?',(campaign_id,rid)).fetchone()
            if not camp: raise HTTPException(404,'کمپین یافت نشد')
            recipients=c.execute("SELECT * FROM sms_campaign_recipients WHERE campaign_id=? AND status='pending'",(campaign_id,)).fetchall()
            if not recipients: raise HTTPException(400,'ابتدا کمپین را آماده کنید یا گیرنده‌ای باقی نمانده است')
            provider=sms_provider_getter(); sent=failed=0
            for r in recipients:
                try:
                    result=provider.send(r['phone'],camp['message'])
                    ok=getattr(result,'success',False)
                    c.execute("UPDATE sms_campaign_recipients SET status=?,provider_message_id=?,error=?,sent_at=? WHERE id=?",('sent' if ok else 'failed',getattr(result,'message_id',None),None if ok else getattr(result,'message','ارسال ناموفق'),_now() if ok else None,r['id']))
                    sent+=int(ok); failed+=int(not ok)
                except Exception as exc:
                    c.execute("UPDATE sms_campaign_recipients SET status='failed',error=? WHERE id=?",(str(exc)[:500],r['id'])); failed+=1
            c.execute("UPDATE sms_campaigns SET status='sent',sent_at=?,sent_count=?,failed_count=? WHERE id=?",(_now(),sent,failed,campaign_id)); c.commit()
            return {'campaign_id':campaign_id,'sent':sent,'failed':failed,'status':'sent'}
        finally: c.close()
