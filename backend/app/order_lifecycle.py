"""Unified order lifecycle for Emperator."""
import sqlite3
from datetime import datetime, timezone
from fastapi import Depends, HTTPException


def _now(): return datetime.now(timezone.utc).isoformat()


def install_lifecycle_schema(c):
    c.executescript('''
    CREATE TABLE IF NOT EXISTS order_status_history(
      id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL, restaurant_id INTEGER NOT NULL,
      from_status TEXT, to_status TEXT NOT NULL, changed_by INTEGER, created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_order_status_history_order ON order_status_history(order_id, created_at);
    CREATE TABLE IF NOT EXISTS order_receipts(
      id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL UNIQUE, restaurant_id INTEGER NOT NULL,
      receipt_type TEXT NOT NULL DEFAULT 'thermal', printed_at TEXT, created_at TEXT NOT NULL
    );
    ''')


def mount_order_lifecycle_routes(app, conn_factory, current_user):
    @app.get('/api/orders/{order_id}/lifecycle')
    def lifecycle(order_id:int,user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            o=c.execute('SELECT * FROM orders WHERE id=? AND restaurant_id=?',(order_id,rid)).fetchone()
            if not o: raise HTTPException(404,'سفارش یافت نشد')
            history=[dict(x) for x in c.execute('SELECT * FROM order_status_history WHERE order_id=? AND restaurant_id=? ORDER BY id',(order_id,rid)).fetchall()]
            return {'order':dict(o),'history':history}
        finally: c.close()

    @app.post('/api/orders/{order_id}/finalize')
    def finalize(order_id:int,user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            o=c.execute('SELECT * FROM orders WHERE id=? AND restaurant_id=?',(order_id,rid)).fetchone()
            if not o: raise HTTPException(404,'سفارش یافت نشد')
            if o['status']=='تحویل‌شده': return {'status':'already_finalized','order_id':order_id}
            old=o['status']; c.execute('UPDATE orders SET status=? WHERE id=? AND restaurant_id=?',('تحویل‌شده',order_id,rid))
            c.execute('INSERT INTO order_status_history(order_id,restaurant_id,from_status,to_status,changed_by,created_at) VALUES(?,?,?,?,?,?)',(order_id,rid,old,'تحویل‌شده',user['id'],_now()))
            c.commit()
            result={'order_id':order_id,'status':'تحویل‌شده','inventory':None,'loyalty':None,'sms':None}
            try:
                from .order_inventory import consume_order_inventory
                result['inventory']=consume_order_inventory(c,rid,order_id,user['id'])
            except Exception as e:
                # Lifecycle remains usable even when a recipe is not configured.
                result['inventory']={'skipped':True,'reason':str(e)}
            try:
                from .customer_club import award_order_points
                result['loyalty']=award_order_points(c,rid,order_id,user['id'])
            except Exception as e: result['loyalty']={'skipped':True,'reason':str(e)}
            c.commit()
            return result
        except HTTPException: c.rollback(); raise
        finally: c.close()

    @app.post('/api/orders/{order_id}/receipt')
    def receipt(order_id:int,user=Depends(current_user)):
        c=conn_factory(); rid=user['restaurant_id']
        try:
            o=c.execute('SELECT o.*,COALESCE(c.name,\'مشتری حضوری\') customer_name FROM orders o LEFT JOIN customers c ON c.id=o.customer_id WHERE o.id=? AND o.restaurant_id=?',(order_id,rid)).fetchone()
            if not o: raise HTTPException(404,'سفارش یافت نشد')
            items=[dict(x) for x in c.execute('SELECT name,price,quantity FROM order_items WHERE order_id=?',(order_id,)).fetchall()]
            c.execute('INSERT INTO order_receipts(order_id,restaurant_id,receipt_type,printed_at,created_at) VALUES(?,?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET printed_at=excluded.printed_at',(order_id,rid,'thermal',_now(),_now()))
            c.commit()
            return {'order':dict(o),'items':items,'printer_widths_mm':[58,80],'receipt_ready':True}
        finally: c.close()
