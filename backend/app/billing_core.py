"""Add-on modules and billing catalog for Emperator."""
from fastapi import Depends
MODULES={'inventory':{'name':'انبار و خرید','price':290000},'crm':{'name':'باشگاه مشتریان','price':390000},'ai':{'name':'مشاور هوشمند AI','price':590000},'multi_branch':{'name':'چند شعبه','price':790000},'advanced_reports':{'name':'گزارش‌های پیشرفته','price':350000}}
CREDIT_PACKS={'sms_500':{'type':'sms','name':'۵۰۰ پیامک','credits':500,'price':150000},'sms_2000':{'type':'sms','name':'۲۰۰۰ پیامک','credits':2000,'price':490000},'ai_100':{'type':'ai','name':'۱۰۰ اعتبار AI','credits':100,'price':190000},'ai_500':{'type':'ai','name':'۵۰۰ اعتبار AI','credits':500,'price':790000}}
SCHEMA="""
CREATE TABLE IF NOT EXISTS restaurant_modules(id INTEGER PRIMARY KEY AUTOINCREMENT,restaurant_id INTEGER NOT NULL,module_code TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',activated_at TEXT NOT NULL,expires_at TEXT,UNIQUE(restaurant_id,module_code));
CREATE INDEX IF NOT EXISTS idx_modules_restaurant ON restaurant_modules(restaurant_id);
"""
def install_billing_schema(conn): conn.executescript(SCHEMA)
def mount_billing_routes(app,conn_factory,current_user):
 @app.get('/api/billing/catalog')
 def catalog(user=Depends(current_user)): return {'modules':[dict(code=k,**v) for k,v in MODULES.items()],'credit_packs':[dict(code=k,**v) for k,v in CREDIT_PACKS.items()]}
 @app.get('/api/billing/modules')
 def modules(user=Depends(current_user)):
  c=conn_factory()
  try:return [dict(r) for r in c.execute('SELECT module_code,status,activated_at,expires_at FROM restaurant_modules WHERE restaurant_id=?',(user['restaurant_id'],))]
  finally:c.close()
 return True
