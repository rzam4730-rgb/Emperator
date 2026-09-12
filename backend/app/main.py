import sqlite3
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

BASE=Path(__file__).resolve().parents[2]
DB=BASE/"emperator.db"

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    c=conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,category TEXT,price INTEGER NOT NULL,icon TEXT DEFAULT '🍽️',active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT UNIQUE,address TEXT,points INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER,status TEXT DEFAULT 'جدید',total INTEGER DEFAULT 0,payment_method TEXT DEFAULT 'نقدی',created_at TEXT);
    CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER,product_id INTEGER,name TEXT,price INTEGER,quantity INTEGER);
    """)
    if not c.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
        c.executemany("INSERT INTO products(name,category,price,icon) VALUES(?,?,?,?)",[("چلوکباب مخصوص","غذا",285000,"🥩"),("زرشک‌پلو با مرغ","غذا",190000,"🍗"),("قورمه‌سبزی","غذا",175000,"🍲"),("جوجه کباب","غذا",210000,"🍢"),("نوشابه","نوشیدنی",25000,"🥤"),("دوغ محلی","نوشیدنی",35000,"🥛")])
    c.commit(); c.close()
init_db()

app=FastAPI(title="Emperator API")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.get("/api/health")
def health(): return {"status":"ok","database":str(DB)}

@app.get("/api/products")
def products():
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM products WHERE active=1 ORDER BY id")]; c.close(); return rows

@app.post("/api/products")
def add_product(p:dict):
    if not p.get("name") or not p.get("price"): raise HTTPException(400,"نام و قیمت الزامی است")
    c=conn(); cur=c.execute("INSERT INTO products(name,category,price,icon) VALUES(?,?,?,?)",(p["name"],p.get("category","سایر"),int(p["price"]),p.get("icon","🍽️"))); c.commit(); x=dict(c.execute("SELECT * FROM products WHERE id=?",(cur.lastrowid,)).fetchone()); c.close(); return x

@app.get("/api/customers")
def customers():
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM customers ORDER BY id DESC")]; c.close(); return rows

@app.post("/api/customers")
def add_customer(x:dict):
    if not x.get("name") or not x.get("phone"): raise HTTPException(400,"نام و شماره تلفن الزامی است")
    c=conn()
    try:
        cur=c.execute("INSERT INTO customers(name,phone,address) VALUES(?,?,?)",(x["name"],x["phone"],x.get("address",""))); c.commit()
    except sqlite3.IntegrityError:
        c.close(); raise HTTPException(400,"این شماره قبلاً ثبت شده است")
    row=dict(c.execute("SELECT * FROM customers WHERE id=?",(cur.lastrowid,)).fetchone()); c.close(); return row

@app.get("/api/orders")
def orders():
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM orders ORDER BY id DESC")]; c.close(); return rows

@app.post("/api/orders")
def create_order(payload:dict):
    items=payload.get("items",[])
    if not items: raise HTTPException(400,"سبد سفارش خالی است")
    c=conn(); lines=[]; total=0
    for item in items:
        p=c.execute("SELECT * FROM products WHERE id=?",(item.get("product_id"),)).fetchone()
        if not p: continue
        q=max(1,int(item.get("quantity",1))); total+=p["price"]*q; lines.append((p,q))
    if not lines: c.close(); raise HTTPException(400,"محصول معتبر وجود ندارد")
    cur=c.execute("INSERT INTO orders(customer_id,status,total,payment_method,created_at) VALUES(?,?,?,?,?)",(payload.get("customer_id"),"جدید",total,payload.get("payment_method","نقدی"),datetime.now().isoformat()))
    oid=cur.lastrowid
    for p,q in lines:c.execute("INSERT INTO order_items(order_id,product_id,name,price,quantity) VALUES(?,?,?,?,?)",(oid,p["id"],p["name"],p["price"],q))
    c.commit(); row=dict(c.execute("SELECT * FROM orders WHERE id=?",(oid,)).fetchone()); c.close(); return row

@app.get("/api/dashboard")
def dashboard():
    c=conn(); sales=c.execute("SELECT COALESCE(SUM(total),0) FROM orders").fetchone()[0]; orders=c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]; customers=c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]; c.close(); return {"orders":orders,"sales":sales,"customers":customers}
