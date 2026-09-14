import os
import secrets
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

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
    payload = {
        "sub": str(user_id),
        "rid": restaurant_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_MINUTES),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def issue_refresh_token(c, user_id: int, restaurant_id: int) -> str:
    token = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS)
    c.execute(
        "INSERT INTO refresh_tokens(user_id,restaurant_id,token_hash,expires_at,created_at) VALUES(?,?,?,?,?)",
        (user_id, restaurant_id, hash_refresh_token(token), expires.isoformat(), datetime.now(timezone.utc).isoformat()),
    )
    return token


def init_db():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,category TEXT,price INTEGER NOT NULL,icon TEXT DEFAULT '🍽️',active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT UNIQUE,address TEXT,points INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER,status TEXT DEFAULT 'جدید',total INTEGER DEFAULT 0,payment_method TEXT DEFAULT 'نقدی',created_at TEXT);
    CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER,product_id INTEGER,name TEXT,price INTEGER,quantity INTEGER);

    CREATE TABLE IF NOT EXISTS restaurants(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS permissions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS role_permissions(
        role_id INTEGER NOT NULL,
        permission_id INTEGER NOT NULL,
        PRIMARY KEY(role_id, permission_id),
        FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE,
        FOREIGN KEY(permission_id) REFERENCES permissions(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS user_restaurants(
        user_id INTEGER NOT NULL,
        restaurant_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        PRIMARY KEY(user_id, restaurant_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
        FOREIGN KEY(role_id) REFERENCES roles(id)
    );
    CREATE TABLE IF NOT EXISTS refresh_tokens(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        restaurant_id INTEGER NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        revoked_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
    );
    """)

    for role in ("owner", "manager", "cashier", "kitchen", "accountant"):
        c.execute("INSERT OR IGNORE INTO roles(name) VALUES(?)", (role,))

    permissions = (
        "dashboard.read", "orders.read", "orders.write", "products.read", "products.write",
        "customers.read", "customers.write", "inventory.read", "inventory.write",
        "finance.read", "reports.read", "settings.write", "users.manage"
    )
    for permission in permissions:
        c.execute("INSERT OR IGNORE INTO permissions(name) VALUES(?)", (permission,))

    # Owner gets all permissions; other roles receive a minimal operational set.
    owner_id = c.execute("SELECT id FROM roles WHERE name='owner'").fetchone()[0]
    all_permissions = c.execute("SELECT id FROM permissions").fetchall()
    for row in all_permissions:
        c.execute("INSERT OR IGNORE INTO role_permissions(role_id,permission_id) VALUES(?,?)", (owner_id, row[0]))

    role_permissions = {
        "manager": permissions,
        "cashier": ("dashboard.read", "orders.read", "orders.write", "products.read", "customers.read", "customers.write"),
        "kitchen": ("dashboard.read", "orders.read", "orders.write"),
        "accountant": ("dashboard.read", "finance.read", "reports.read"),
    }
    for role_name, names in role_permissions.items():
        role_id = c.execute("SELECT id FROM roles WHERE name=?", (role_name,)).fetchone()[0]
        for name in names:
            pid = c.execute("SELECT id FROM permissions WHERE name=?", (name,)).fetchone()[0]
            c.execute("INSERT OR IGNORE INTO role_permissions(role_id,permission_id) VALUES(?,?)", (role_id, pid))

    if not c.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
        c.executemany("INSERT INTO products(name,category,price,icon) VALUES(?,?,?,?)", [
            ("چلوکباب مخصوص", "غذا", 285000, "🥩"), ("زرشک‌پلو با مرغ", "غذا", 190000, "🍗"),
            ("قورمه‌سبزی", "غذا", 175000, "🍲"), ("جوجه کباب", "غذا", 210000, "🍢"),
            ("نوشابه", "نوشیدنی", 25000, "🥤"), ("دوغ محلی", "نوشیدنی", 35000, "🥛")
        ])
    c.commit()
    c.close()


init_db()
app = FastAPI(title="Emperator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


def current_user(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "احراز هویت لازم است")
    token = authorization[7:].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(401, "توکن نامعتبر است")
        user_id = int(payload["sub"])
        restaurant_id = int(payload["rid"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(401, "توکن نامعتبر یا منقضی شده است")

    c = conn()
    row = c.execute("""
        SELECT u.id, u.name, u.phone, u.status, ur.restaurant_id, r.name AS role
        FROM users u
        JOIN user_restaurants ur ON ur.user_id=u.id
        JOIN roles r ON r.id=ur.role_id
        WHERE u.id=? AND ur.restaurant_id=?
    """, (user_id, restaurant_id)).fetchone()
    c.close()
    if not row or row["status"] != "active":
        raise HTTPException(401, "کاربر فعال نیست")
    return dict(row)


def require_permission(permission: str):
    def dependency(user=Depends(current_user)):
        c = conn()
        allowed = c.execute("""
            SELECT 1 FROM user_restaurants ur
            JOIN role_permissions rp ON rp.role_id=ur.role_id
            JOIN permissions p ON p.id=rp.permission_id
            WHERE ur.user_id=? AND ur.restaurant_id=? AND p.name=?
        """, (user["id"], user["restaurant_id"], permission)).fetchone()
        c.close()
        if not allowed:
            raise HTTPException(403, "دسترسی کافی ندارید")
        return user
    return dependency


@app.get("/api/health")
def health():
    return {"status": "ok", "database": str(DB)}


@app.post("/api/auth/register")
def register(payload: dict):
    name = str(payload.get("name", "")).strip()
    phone = str(payload.get("phone", "")).strip()
    password = str(payload.get("password", ""))
    restaurant_name = str(payload.get("restaurant_name", "")).strip()
    if len(name) < 2 or len(phone) < 7 or len(password) < 8 or len(restaurant_name) < 2:
        raise HTTPException(400, "نام، نام کسب‌وکار، شماره موبایل و رمز عبور حداقل ۸ کاراکتری الزامی است")

    c = conn()
    try:
        now = datetime.now(timezone.utc).isoformat()
        c.execute("BEGIN")
        cur = c.execute("INSERT INTO users(name,phone,password_hash,created_at) VALUES(?,?,?,?)", (name, phone, hash_password(password), now))
        user_id = cur.lastrowid
        cur = c.execute("INSERT INTO restaurants(name,created_at) VALUES(?,?)", (restaurant_name, now))
        restaurant_id = cur.lastrowid
        role_id = c.execute("SELECT id FROM roles WHERE name='owner'").fetchone()[0]
        c.execute("INSERT INTO user_restaurants(user_id,restaurant_id,role_id) VALUES(?,?,?)", (user_id, restaurant_id, role_id))
        access = create_access_token(user_id, restaurant_id, "owner")
        refresh = issue_refresh_token(c, user_id, restaurant_id)
        c.commit()
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "expires_in": ACCESS_MINUTES * 60}
    except sqlite3.IntegrityError:
        c.rollback()
        raise HTTPException(409, "این شماره موبایل قبلاً ثبت شده است")
    finally:
        c.close()


@app.post("/api/auth/login")
def login(payload: dict):
    phone = str(payload.get("phone", "")).strip()
    password = str(payload.get("password", ""))
    c = conn()
    row = c.execute("""
        SELECT u.id, u.name, u.phone, u.password_hash, u.status, ur.restaurant_id, r.name AS role
        FROM users u JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id
        WHERE u.phone=? LIMIT 1
    """, (phone,)).fetchone()
    if not row or row["status"] != "active" or not verify_password(password, row["password_hash"]):
        c.close()
        raise HTTPException(401, "شماره موبایل یا رمز عبور اشتباه است")
    access = create_access_token(row["id"], row["restaurant_id"], row["role"])
    refresh = issue_refresh_token(c, row["id"], row["restaurant_id"])
    c.commit(); c.close()
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "expires_in": ACCESS_MINUTES * 60}


@app.post("/api/auth/refresh")
def refresh(payload: dict):
    token = str(payload.get("refresh_token", ""))
    if not token:
        raise HTTPException(401, "Refresh token الزامی است")
    c = conn()
    row = c.execute("SELECT * FROM refresh_tokens WHERE token_hash=? AND revoked_at IS NULL", (hash_refresh_token(token),)).fetchone()
    if not row:
        c.close(); raise HTTPException(401, "Refresh token نامعتبر است")
    expires = datetime.fromisoformat(row["expires_at"])
    if expires <= datetime.now(timezone.utc):
        c.close(); raise HTTPException(401, "Refresh token منقضی شده است")
    user = c.execute("""
        SELECT u.id, u.status, r.name AS role FROM users u
        JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id
        WHERE u.id=? AND ur.restaurant_id=?
    """, (row["user_id"], row["restaurant_id"])).fetchone()
    if not user or user["status"] != "active":
        c.close(); raise HTTPException(401, "کاربر فعال نیست")
    c.execute("UPDATE refresh_tokens SET revoked_at=? WHERE id=?", (datetime.now(timezone.utc).isoformat(), row["id"]))
    new_refresh = issue_refresh_token(c, user["id"], row["restaurant_id"])
    access = create_access_token(user["id"], row["restaurant_id"], user["role"])
    c.commit(); c.close()
    return {"access_token": access, "refresh_token": new_refresh, "token_type": "bearer", "expires_in": ACCESS_MINUTES * 60}


@app.post("/api/auth/logout")
def logout(payload: dict, user=Depends(current_user)):
    token = str(payload.get("refresh_token", ""))
    c = conn()
    if token:
        c.execute("UPDATE refresh_tokens SET revoked_at=? WHERE token_hash=? AND user_id=?", (datetime.now(timezone.utc).isoformat(), hash_refresh_token(token), user["id"]))
    c.commit(); c.close()
    return {"status": "ok"}


@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return user


@app.get("/api/products")
def products(user=Depends(require_permission("products.read"))):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM products WHERE active=1 ORDER BY id")]; c.close(); return rows

@app.post("/api/products")
def add_product(p:dict, user=Depends(require_permission("products.write"))):
    if not p.get("name") or not p.get("price"): raise HTTPException(400,"نام و قیمت الزامی است")
    c=conn(); cur=c.execute("INSERT INTO products(name,category,price,icon) VALUES(?,?,?,?)",(p["name"],p.get("category","سایر"),int(p["price"]),p.get("icon","🍽️"))); c.commit(); x=dict(c.execute("SELECT * FROM products WHERE id=?",(cur.lastrowid,)).fetchone()); c.close(); return x

@app.get("/api/customers")
def customers(user=Depends(require_permission("customers.read"))):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM customers ORDER BY id DESC")]; c.close(); return rows

@app.post("/api/customers")
def add_customer(x:dict, user=Depends(require_permission("customers.write"))):
    if not x.get("name") or not x.get("phone"): raise HTTPException(400,"نام و شماره تلفن الزامی است")
    c=conn()
    try:
        cur=c.execute("INSERT INTO customers(name,phone,address) VALUES(?,?,?)",(x["name"],x["phone"],x.get("address",""))); c.commit()
    except sqlite3.IntegrityError:
        c.close(); raise HTTPException(400,"این شماره قبلاً ثبت شده است")
    row=dict(c.execute("SELECT * FROM customers WHERE id=?",(cur.lastrowid,)).fetchone()); c.close(); return row

@app.get("/api/orders")
def orders(user=Depends(require_permission("orders.read"))):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM orders ORDER BY id DESC")]; c.close(); return rows

@app.post("/api/orders")
def create_order(payload:dict, user=Depends(require_permission("orders.write"))):
    items=payload.get("items",[])
    if not items: raise HTTPException(400,"سبد سفارش خالی است")
    c=conn(); lines=[]; total=0
    for item in items:
        p=c.execute("SELECT * FROM products WHERE id=? AND active=1",(item.get("product_id"),)).fetchone()
        if not p: continue
        q=max(1,int(item.get("quantity",1))); total+=p["price"]*q; lines.append((p,q))
    if not lines: c.close(); raise HTTPException(400,"محصول معتبر وجود ندارد")
    cur=c.execute("INSERT INTO orders(customer_id,status,total,payment_method,created_at) VALUES(?,?,?,?,?)",(payload.get("customer_id"),"جدید",total,payload.get("payment_method","نقدی"),datetime.now(timezone.utc).isoformat()))
    oid=cur.lastrowid
    for p,q in lines:c.execute("INSERT INTO order_items(order_id,product_id,name,price,quantity) VALUES(?,?,?,?,?)",(oid,p["id"],p["name"],p["price"],q))
    c.commit(); row=dict(c.execute("SELECT * FROM orders WHERE id=?",(oid,)).fetchone()); c.close(); return row

@app.get("/api/dashboard")
def dashboard(user=Depends(require_permission("dashboard.read"))):
    c=conn(); sales=c.execute("SELECT COALESCE(SUM(total),0) FROM orders").fetchone()[0]; order_count=c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]; customers_count=c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]; c.close(); return {"orders":order_count,"sales":sales,"customers":customers_count}
