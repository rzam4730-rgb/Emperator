import os
import secrets
import hashlib
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from .subscription import SCHEMA as SUBSCRIPTION_SCHEMA, seed_plans, ensure_subscription, plan_limits, get_usage, increment_usage, utcnow

BASE = Path(__file__).resolve().parents[2]
DB = BASE / "emperator.db"
JWT_SECRET = os.getenv("EMPERATOR_JWT_SECRET", "dev-only-change-this-secret")
JWT_ALGORITHM = "HS256"
ACCESS_MINUTES = int(os.getenv("EMPERATOR_ACCESS_MINUTES", "15"))
REFRESH_DAYS = int(os.getenv("EMPERATOR_REFRESH_DAYS", "30"))


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: int, restaurant_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user_id), "rid": restaurant_id, "role": role, "type": "access", "iat": now, "exp": now + timedelta(minutes=ACCESS_MINUTES), "jti": secrets.token_hex(16)}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def issue_refresh_token(c, user_id: int, restaurant_id: int) -> str:
    token = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS)
    c.execute("INSERT INTO refresh_tokens(user_id,restaurant_id,token_hash,expires_at,created_at) VALUES(?,?,?,?,?)", (user_id, restaurant_id, hash_refresh_token(token), expires.isoformat(), datetime.now(timezone.utc).isoformat()))
    return token


def add_column_if_missing(c, table: str, column: str, definition: str):
    cols = {r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,category TEXT,price INTEGER NOT NULL,icon TEXT DEFAULT '🍽️',active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT UNIQUE,address TEXT,points INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER,status TEXT DEFAULT 'جدید',total INTEGER DEFAULT 0,payment_method TEXT DEFAULT 'نقدی',created_at TEXT);
    CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER,product_id INTEGER,name TEXT,price INTEGER,quantity INTEGER);
    CREATE TABLE IF NOT EXISTS restaurants(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS roles(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE);
    CREATE TABLE IF NOT EXISTS permissions(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE);
    CREATE TABLE IF NOT EXISTS role_permissions(role_id INTEGER NOT NULL,permission_id INTEGER NOT NULL,PRIMARY KEY(role_id,permission_id),FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE,FOREIGN KEY(permission_id) REFERENCES permissions(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS user_restaurants(user_id INTEGER NOT NULL,restaurant_id INTEGER NOT NULL,role_id INTEGER NOT NULL,PRIMARY KEY(user_id,restaurant_id),FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,FOREIGN KEY(restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,FOREIGN KEY(role_id) REFERENCES roles(id));
    CREATE TABLE IF NOT EXISTS refresh_tokens(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,restaurant_id INTEGER NOT NULL,token_hash TEXT NOT NULL UNIQUE,expires_at TEXT NOT NULL,created_at TEXT NOT NULL,revoked_at TEXT,FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,FOREIGN KEY(restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,restaurant_id INTEGER,action TEXT NOT NULL,target_type TEXT,target_id INTEGER,details TEXT,created_at TEXT NOT NULL);
    """)
    add_column_if_missing(c, "products", "restaurant_id", "INTEGER")
    add_column_if_missing(c, "customers", "restaurant_id", "INTEGER")
    add_column_if_missing(c, "orders", "restaurant_id", "INTEGER")
    c.executescript(SUBSCRIPTION_SCHEMA)
    seed_plans(c)
    c.commit(); c.close()


app = FastAPI(title="Emperator API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "احراز هویت لازم است")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access": raise HTTPException(401, "توکن نامعتبر است")
        uid = int(payload.get("sub")); rid = int(payload.get("rid"))
    except Exception:
        raise HTTPException(401, "توکن نامعتبر یا منقضی شده است")
    c = conn()
    row = c.execute("SELECT u.id,u.name,u.phone,u.status,ur.restaurant_id,r.name role,rest.name restaurant_name FROM users u JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id JOIN restaurants rest ON rest.id=ur.restaurant_id WHERE u.id=? AND ur.restaurant_id=?", (uid, rid)).fetchone()
    c.close()
    if not row or row["status"] != "active": raise HTTPException(401, "کاربر غیرفعال است")
    return dict(row)


def require_permission(permission: str):
    def checker(user=Depends(current_user)):
        c = conn(); ok = c.execute("SELECT 1 FROM role_permissions rp JOIN permissions p ON p.id=rp.permission_id JOIN roles r ON r.id=rp.role_id WHERE r.name=? AND p.name=?", (user["role"], permission)).fetchone(); c.close()
        if not ok: raise HTTPException(403, "دسترسی کافی نیست")
        return user
    return checker


def require_active_subscription(c, restaurant_id):
    s = ensure_subscription(c, restaurant_id)
    if s["status"] != "active" or datetime.fromisoformat(s["expires_at"]) <= utcnow():
        raise HTTPException(402, "اشتراک شما منقضی شده است. لطفاً تمدید کنید.")
    return s


def audit(c, user, action, target_type=None, target_id=None, details=None):
    c.execute("INSERT INTO audit_logs(user_id,restaurant_id,action,target_type,target_id,details,created_at) VALUES(?,?,?,?,?,?,?)", (user["id"], user["restaurant_id"], action, target_type, target_id, details, datetime.now(timezone.utc).isoformat()))


@app.on_event("startup")
def startup():
    init_db()
    try:
        from .sms_routes import SMS_SCHEMA, mount_sms_routes
        c = conn(); c.executescript(SMS_SCHEMA); c.commit(); c.close()
        mount_sms_routes(app, conn, current_user)
    except Exception as exc:
        print("SMS module initialization warning:", exc)
    try:
        from .kds import mount_kds_routes
        mount_kds_routes(app, conn, current_user)
    except Exception as exc:
        print("KDS module initialization warning:", exc)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "emperator-api", "sms_provider": os.getenv("EMPERATOR_SMS_PROVIDER", "mock")}


@app.post("/api/auth/register")
def register(payload: dict):
    name = str(payload.get("name", "")).strip(); phone = str(payload.get("phone", "")).strip(); password = str(payload.get("password", "")); restaurant_name = str(payload.get("restaurant_name", "")).strip()
    if len(name) < 2 or len(phone) < 7 or len(password) < 8 or len(restaurant_name) < 2: raise HTTPException(400, "نام، موبایل، رمز و نام مجموعه الزامی است")
    c = conn()
    try:
        now = datetime.now(timezone.utc).isoformat()
        owner_role = c.execute("SELECT id FROM roles WHERE name='owner'").fetchone()
        if not owner_role: raise HTTPException(500, "نقش‌های پایه ایجاد نشده‌اند")
        rid = c.execute("INSERT INTO restaurants(name,status,created_at) VALUES(?,?,?)", (restaurant_name, "active", now)).lastrowid
        uid = c.execute("INSERT INTO users(name,phone,password_hash,created_at) VALUES(?,?,?,?)", (name, phone, hash_password(password), now)).lastrowid
        c.execute("INSERT INTO user_restaurants(user_id,restaurant_id,role_id) VALUES(?,?,?)", (uid, rid, owner_role["id"]))
        ensure_subscription(c, rid)
        c.commit()
        access = create_access_token(uid, rid, "owner"); refresh = issue_refresh_token(c, uid, rid); c.commit()
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
    except sqlite3.IntegrityError:
        c.rollback(); raise HTTPException(409, "این شماره موبایل قبلاً ثبت شده است")
    finally:
        c.close()


@app.get("/api/products")
def products(user=Depends(require_permission("products.read"))):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM products WHERE active=1 AND restaurant_id=? ORDER BY id",(user["restaurant_id"],))]; c.close(); return rows

@app.post("/api/products")
def add_product(p:dict,user=Depends(require_permission("products.write"))):
    if not p.get("name") or not p.get("price"): raise HTTPException(400,"نام و قیمت الزامی است")
    c=conn(); cur=c.execute("INSERT INTO products(name,category,price,icon,restaurant_id) VALUES(?,?,?,?,?)",(p["name"],p.get("category","سایر"),int(p["price"]),p.get("icon","🍽️"),user["restaurant_id"])); c.commit(); x=dict(c.execute("SELECT * FROM products WHERE id=?",(cur.lastrowid,)).fetchone()); c.close(); return x

@app.get("/api/customers")
def customers(user=Depends(require_permission("customers.read"))):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM customers WHERE restaurant_id=? ORDER BY id DESC",(user["restaurant_id"],))]; c.close(); return rows

@app.post("/api/customers")
def add_customer(x:dict,user=Depends(require_permission("customers.write"))):
    if not x.get("name") or not x.get("phone"): raise HTTPException(400,"نام و شماره تلفن الزامی است")
    c=conn()
    try:
        s=require_active_subscription(c,user["restaurant_id"]); limits=plan_limits(s); count=c.execute("SELECT COUNT(*) FROM customers WHERE restaurant_id=?",(user["restaurant_id"],)).fetchone()[0]
        if count>=limits["customer_limit"]: raise HTTPException(402,"سقف مشتری پلن شما تکمیل شده است")
        cur=c.execute("INSERT INTO customers(name,phone,address,restaurant_id) VALUES(?,?,?,?)",(x["name"],x["phone"],x.get("address",""),user["restaurant_id"])); c.commit()
    except sqlite3.IntegrityError: c.close(); raise HTTPException(400,"این شماره قبلاً ثبت شده است")
    finally:
        try: c.close()
        except Exception: pass
    return {"id":cur.lastrowid,"name":x["name"],"phone":x["phone"],"address":x.get("address","")}

@app.get("/api/orders")
def orders(user=Depends(require_permission("orders.read"))):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM orders WHERE restaurant_id=? ORDER BY id DESC",(user["restaurant_id"],))]; c.close(); return rows

@app.post("/api/orders")
def create_order(payload:dict,user=Depends(require_permission("orders.write"))):
    items=payload.get("items",[])
    if not items: raise HTTPException(400,"سبد سفارش خالی است")
    c=conn()
    try:
        s=require_active_subscription(c,user["restaurant_id"]); limits=plan_limits(s); today=get_usage(c,user["restaurant_id"],"invoices_daily")
        if today>=limits["invoice_daily_limit"]: raise HTTPException(402,"سقف فاکتور روزانه پلن شما تکمیل شده است")
        lines=[]; total=0
        for item in items:
            p=c.execute("SELECT * FROM products WHERE id=? AND active=1 AND restaurant_id=?",(item.get("product_id"),user["restaurant_id"])).fetchone()
            if not p: continue
            q=max(1,int(item.get("quantity",1))); total+=p["price"]*q; lines.append((p,q))
        if not lines: raise HTTPException(400,"محصول معتبر وجود ندارد")
        customer_id=payload.get("customer_id")
        if customer_id and not c.execute("SELECT 1 FROM customers WHERE id=? AND restaurant_id=?",(customer_id,user["restaurant_id"])).fetchone(): customer_id=None
        cur=c.execute("INSERT INTO orders(customer_id,restaurant_id,status,total,payment_method,created_at) VALUES(?,?,?,?,?,?)",(customer_id,user["restaurant_id"],"جدید",total,payload.get("payment_method","نقدی"),datetime.now(timezone.utc).isoformat())); oid=cur.lastrowid
        for p,q in lines: c.execute("INSERT INTO order_items(order_id,product_id,name,price,quantity) VALUES(?,?,?,?,?)",(oid,p["id"],p["name"],p["price"],q))
        increment_usage(c,user["restaurant_id"],"invoices_daily",1)
        c.commit(); return dict(c.execute("SELECT * FROM orders WHERE id=?",(oid,)).fetchone())
    finally: c.close()

@app.get("/api/dashboard")
def dashboard(user=Depends(require_permission("dashboard.read"))):
    c=conn(); rid=user["restaurant_id"]; sales=c.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE restaurant_id=?",(rid,)).fetchone()[0]; order_count=c.execute("SELECT COUNT(*) FROM orders WHERE restaurant_id=?",(rid,)).fetchone()[0]; customers_count=c.execute("SELECT COUNT(*) FROM customers WHERE restaurant_id=?",(rid,)).fetchone()[0]; c.close(); return {"orders":order_count,"sales":sales,"customers":customers_count}
