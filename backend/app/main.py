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
    for role in ("owner", "manager", "cashier", "kitchen", "accountant"):
        c.execute("INSERT OR IGNORE INTO roles(name) VALUES(?)", (role,))
    permissions = ("dashboard.read","orders.read","orders.write","products.read","products.write","customers.read","customers.write","inventory.read","inventory.write","finance.read","reports.read","settings.write","users.manage")
    for permission in permissions:
        c.execute("INSERT OR IGNORE INTO permissions(name) VALUES(?)", (permission,))
    owner_id = c.execute("SELECT id FROM roles WHERE name='owner'").fetchone()[0]
    for row in c.execute("SELECT id FROM permissions").fetchall():
        c.execute("INSERT OR IGNORE INTO role_permissions(role_id,permission_id) VALUES(?,?)", (owner_id, row[0]))
    role_permissions = {"manager": permissions, "cashier": ("dashboard.read","orders.read","orders.write","products.read","customers.read","customers.write"), "kitchen": ("dashboard.read","orders.read","orders.write"), "accountant": ("dashboard.read","finance.read","reports.read")}
    for role_name, names in role_permissions.items():
        role_id = c.execute("SELECT id FROM roles WHERE name=?", (role_name,)).fetchone()[0]
        for name in names:
            pid = c.execute("SELECT id FROM permissions WHERE name=?", (name,)).fetchone()[0]
            c.execute("INSERT OR IGNORE INTO role_permissions(role_id,permission_id) VALUES(?,?)", (role_id, pid))
    if not c.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
        c.executemany("INSERT INTO products(name,category,price,icon,restaurant_id) VALUES(?,?,?,?,NULL)", [("چلوکباب مخصوص","غذا",285000,"🥩"),("زرشک‌پلو با مرغ","غذا",190000,"🍗"),("قورمه‌سبزی","غذا",175000,"🍲"),("جوجه کباب","غذا",210000,"🍢"),("نوشابه","نوشیدنی",25000,"🥤"),("دوغ محلی","نوشیدنی",35000,"🥛")])
    c.commit(); c.close()


init_db()
app = FastAPI(title="Emperator API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"], allow_headers=["Authorization","Content-Type"])


def current_user(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "احراز هویت لازم است")
    try:
        payload = jwt.decode(authorization[7:].strip(), JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access": raise HTTPException(401, "توکن نامعتبر است")
        user_id, restaurant_id = int(payload["sub"]), int(payload["rid"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(401, "توکن نامعتبر یا منقضی شده است")
    c=conn(); row=c.execute("SELECT u.id,u.name,u.phone,u.status,ur.restaurant_id,r.name AS role,rest.name AS restaurant_name,rest.status AS restaurant_status FROM users u JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id JOIN restaurants rest ON rest.id=ur.restaurant_id WHERE u.id=? AND ur.restaurant_id=?",(user_id,restaurant_id)).fetchone(); c.close()
    if not row or row["status"]!="active" or row["restaurant_status"]!="active": raise HTTPException(401,"حساب یا کسب‌وکار فعال نیست")
    return dict(row)


def require_permission(permission: str):
    def dependency(user=Depends(current_user)):
        c=conn(); ok=c.execute("SELECT 1 FROM user_restaurants ur JOIN role_permissions rp ON rp.role_id=ur.role_id JOIN permissions p ON p.id=rp.permission_id WHERE ur.user_id=? AND ur.restaurant_id=? AND p.name=?",(user["id"],user["restaurant_id"],permission)).fetchone(); c.close()
        if not ok: raise HTTPException(403,"دسترسی کافی ندارید")
        return user
    return dependency


def audit(c, user, action, target_type=None, target_id=None, details=None):
    c.execute("INSERT INTO audit_logs(user_id,restaurant_id,action,target_type,target_id,details,created_at) VALUES(?,?,?,?,?,?,?)", (user["id"], user["restaurant_id"], action, target_type, target_id, details, datetime.now(timezone.utc).isoformat()))


def subscription_view(c, restaurant_id):
    s=ensure_subscription(c, restaurant_id)
    limits=plan_limits(s)
    now=utcnow()
    expired=datetime.fromisoformat(s["expires_at"]) <= now
    if expired and s["status"]=="active":
        c.execute("UPDATE subscriptions SET status='expired',updated_at=? WHERE id=?",(now.isoformat(),s["id"]))
        s=c.execute("SELECT s.*,p.code,p.name,p.price_monthly,p.limits_json FROM subscriptions s JOIN plans p ON p.id=s.plan_id WHERE s.id=?",(s["id"],)).fetchone()
    return {"id":s["id"],"plan_code":s["code"],"plan_name":s["name"],"price_monthly":s["price_monthly"],"status":s["status"],"starts_at":s["starts_at"],"expires_at":s["expires_at"],"auto_renew":bool(s["auto_renew"]),"limits":limits}


def require_active_subscription(c, restaurant_id):
    s=ensure_subscription(c, restaurant_id)
    if s["status"]!="active" or datetime.fromisoformat(s["expires_at"])<=utcnow():
        raise HTTPException(402,"اشتراک شما منقضی شده است. لطفاً تمدید کنید.")
    return s


@app.get("/api/health")
def health(): return {"status":"ok","database":str(DB)}

@app.post("/api/auth/register")
def register(payload: dict):
    name=str(payload.get("name","")).strip(); phone=str(payload.get("phone","")).strip(); password=str(payload.get("password","")); restaurant_name=str(payload.get("restaurant_name","")).strip()
    if len(name)<2 or len(phone)<7 or len(password)<8 or len(restaurant_name)<2: raise HTTPException(400,"نام، نام کسب‌وکار، شماره موبایل و رمز عبور حداقل ۸ کاراکتری الزامی است")
    c=conn()
    try:
        now=datetime.now(timezone.utc).isoformat(); c.execute("BEGIN")
        uid=c.execute("INSERT INTO users(name,phone,password_hash,created_at) VALUES(?,?,?,?)",(name,phone,hash_password(password),now)).lastrowid
        rid=c.execute("INSERT INTO restaurants(name,created_at) VALUES(?,?)",(restaurant_name,now)).lastrowid
        role_id=c.execute("SELECT id FROM roles WHERE name='owner'").fetchone()[0]; c.execute("INSERT INTO user_restaurants(user_id,restaurant_id,role_id) VALUES(?,?,?)",(uid,rid,role_id))
        c.execute("INSERT INTO products(name,category,price,icon,restaurant_id) SELECT name,category,price,icon,? FROM products WHERE restaurant_id IS NULL",(rid,))
        ensure_subscription(c,rid)
        access=create_access_token(uid,rid,"owner"); refresh=issue_refresh_token(c,uid,rid); c.commit(); return {"access_token":access,"refresh_token":refresh,"token_type":"bearer","expires_in":ACCESS_MINUTES*60}
    except sqlite3.IntegrityError: c.rollback(); raise HTTPException(409,"این شماره موبایل قبلاً ثبت شده است")
    finally: c.close()

@app.post("/api/auth/login")
def login(payload: dict):
    phone=str(payload.get("phone","")).strip(); password=str(payload.get("password","")); c=conn(); row=c.execute("SELECT u.id,u.name,u.phone,u.password_hash,u.status,ur.restaurant_id,r.name AS role FROM users u JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id WHERE u.phone=? LIMIT 1",(phone,)).fetchone()
    if not row or row["status"]!="active" or not verify_password(password,row["password_hash"]): c.close(); raise HTTPException(401,"شماره موبایل یا رمز عبور اشتباه است")
    ensure_subscription(c,row["restaurant_id"]); access=create_access_token(row["id"],row["restaurant_id"],row["role"]); refresh=issue_refresh_token(c,row["id"],row["restaurant_id"]); c.commit(); c.close(); return {"access_token":access,"refresh_token":refresh,"token_type":"bearer","expires_in":ACCESS_MINUTES*60}

@app.post("/api/auth/refresh")
def refresh(payload: dict):
    token=str(payload.get("refresh_token","")); c=conn(); row=c.execute("SELECT * FROM refresh_tokens WHERE token_hash=? AND revoked_at IS NULL",(hash_refresh_token(token),)).fetchone()
    if not row: c.close(); raise HTTPException(401,"Refresh token نامعتبر است")
    try: expires=datetime.fromisoformat(row["expires_at"])
    except ValueError: expires=datetime.min.replace(tzinfo=timezone.utc)
    if expires<=datetime.now(timezone.utc): c.close(); raise HTTPException(401,"Refresh token منقضی شده است")
    user=c.execute("SELECT u.id,u.status,r.name AS role FROM users u JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id WHERE u.id=? AND ur.restaurant_id=?",(row["user_id"],row["restaurant_id"])).fetchone()
    if not user or user["status"]!="active": c.close(); raise HTTPException(401,"کاربر فعال نیست")
    c.execute("UPDATE refresh_tokens SET revoked_at=? WHERE id=?",(datetime.now(timezone.utc).isoformat(),row["id"])); new_refresh=issue_refresh_token(c,user["id"],row["restaurant_id"]); access=create_access_token(user["id"],row["restaurant_id"],user["role"]); c.commit(); c.close(); return {"access_token":access,"refresh_token":new_refresh,"token_type":"bearer","expires_in":ACCESS_MINUTES*60}

@app.post("/api/auth/logout")
def logout(payload: dict,user=Depends(current_user)):
    token=str(payload.get("refresh_token","")); c=conn();
    if token: c.execute("UPDATE refresh_tokens SET revoked_at=? WHERE token_hash=? AND user_id=?",(datetime.now(timezone.utc).isoformat(),hash_refresh_token(token),user["id"]))
    c.commit(); c.close(); return {"status":"ok"}

@app.get("/api/auth/me")
def me(user=Depends(current_user)): return user

@app.get("/api/plans")
def list_plans(user=Depends(current_user)):
    c=conn(); rows=[]
    for p in c.execute("SELECT * FROM plans WHERE active=1 ORDER BY price_monthly").fetchall():
        rows.append({"code":p["code"],"name":p["name"],"price_monthly":p["price_monthly"],"limits":plan_limits(p)})
    c.close(); return rows

@app.get("/api/subscription")
def get_subscription(user=Depends(current_user)):
    c=conn(); s=subscription_view(c,user["restaurant_id"]); rid=user["restaurant_id"]
    customers=c.execute("SELECT COUNT(*) FROM customers WHERE restaurant_id=?",(rid,)).fetchone()[0]
    inv=get_usage(c,rid,"invoices_daily"); sms=get_usage(c,rid,"sms_monthly"); ai=get_usage(c,rid,"ai_monthly")
    s["usage"]={"customers":customers,"invoices_today":inv,"sms_used":sms,"ai_used":ai}
    c.commit(); c.close(); return s

@app.get("/api/usage")
def usage(user=Depends(current_user)):
    c=conn(); s=ensure_subscription(c,user["restaurant_id"]); l=plan_limits(s); rid=user["restaurant_id"]
    result={"invoices_today":{"used":get_usage(c,rid,"invoices_daily"),"limit":l["invoice_daily_limit"]},"customers":{"used":c.execute("SELECT COUNT(*) FROM customers WHERE restaurant_id=?",(rid,)).fetchone()[0],"limit":l["customer_limit"]},"sms":{"used":get_usage(c,rid,"sms_monthly"),"limit":l["sms_credits"]},"ai":{"used":get_usage(c,rid,"ai_monthly"),"limit":l["ai_credits"]}}
    c.close(); return result

@app.post("/api/subscription/upgrade")
def upgrade_subscription(payload:dict,user=Depends(current_user)):
    code=str(payload.get("plan","" )).strip().lower(); c=conn(); plan=c.execute("SELECT * FROM plans WHERE code=? AND active=1",(code,)).fetchone()
    if not plan: c.close(); raise HTTPException(404,"پلن پیدا نشد")
    old=ensure_subscription(c,user["restaurant_id"]); now=utcnow(); expires=now+timedelta(days=30)
    c.execute("UPDATE subscriptions SET plan_id=?,status='active',starts_at=?,expires_at=?,updated_at=? WHERE restaurant_id=?",(plan["id"],now.isoformat(),expires.isoformat(),now.isoformat(),user["restaurant_id"]))
    c.execute("INSERT INTO subscription_events(restaurant_id,event_type,plan_id,amount,metadata_json,created_at) VALUES(?,?,?,?,?,?)",(user["restaurant_id"],"upgrade",plan["id"],plan["price_monthly"],json.dumps({"from":old["code"]},ensure_ascii=False),now.isoformat()))
    c.commit(); result=subscription_view(c,user["restaurant_id"]); c.commit(); c.close(); return result

@app.post("/api/subscription/renew")
def renew_subscription(user=Depends(current_user)):
    c=conn(); old=ensure_subscription(c,user["restaurant_id"]); now=utcnow(); base=datetime.fromisoformat(old["expires_at"])
    start=base if base>now else now; expires=start+timedelta(days=30)
    c.execute("UPDATE subscriptions SET status='active',starts_at=?,expires_at=?,updated_at=? WHERE restaurant_id=?",(start.isoformat(),expires.isoformat(),now.isoformat(),user["restaurant_id"]))
    c.execute("INSERT INTO subscription_events(restaurant_id,event_type,plan_id,amount,metadata_json,created_at) VALUES(?,?,?,?,?,?)",(user["restaurant_id"],"renew",old["plan_id"],old["price_monthly"],json.dumps({},ensure_ascii=False),now.isoformat()))
    c.commit(); result=subscription_view(c,user["restaurant_id"]); c.close(); return result

@app.get("/api/subscription/events")
def subscription_events(user=Depends(current_user)):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT e.*,p.code plan_code,p.name plan_name FROM subscription_events e LEFT JOIN plans p ON p.id=e.plan_id WHERE e.restaurant_id=? ORDER BY e.id DESC LIMIT 100",(user["restaurant_id"],))]; c.close(); return rows

@app.get("/api/users")
def list_users(user=Depends(require_permission("users.manage"))):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT u.id,u.name,u.phone,u.status,u.created_at,r.name role,r.id role_id FROM users u JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id WHERE ur.restaurant_id=? ORDER BY u.id DESC",(user["restaurant_id"],))]; c.close(); return rows

@app.get("/api/roles")
def list_roles(user=Depends(require_permission("users.manage"))):
    c=conn(); rows=[]
    for r in c.execute("SELECT id,name FROM roles ORDER BY id").fetchall():
        perms=[x[0] for x in c.execute("SELECT p.name FROM permissions p JOIN role_permissions rp ON rp.permission_id=p.id WHERE rp.role_id=? ORDER BY p.name",(r["id"],)).fetchall()]
        rows.append({"id":r["id"],"name":r["name"],"permissions":perms})
    c.close(); return rows

@app.get("/api/permissions")
def list_permissions(user=Depends(require_permission("users.manage"))):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT id,name FROM permissions ORDER BY name")]; c.close(); return rows

@app.post("/api/users")
def create_user(payload:dict,user=Depends(require_permission("users.manage"))):
    name=str(payload.get("name","")).strip(); phone=str(payload.get("phone","")).strip(); password=str(payload.get("password","")); role_name=str(payload.get("role","cashier")).strip().lower()
    if len(name)<2 or len(phone)<7 or len(password)<8: raise HTTPException(400,"نام، شماره موبایل و رمز حداقل ۸ کاراکتری الزامی است")
    c=conn()
    try:
        role=c.execute("SELECT id,name FROM roles WHERE name=?",(role_name,)).fetchone()
        if not role: raise HTTPException(400,"نقش نامعتبر است")
        if role_name=="owner" and user["role"]!="owner": raise HTTPException(403,"فقط مالک می‌تواند مالک جدید ایجاد کند")
        c.execute("BEGIN"); uid=c.execute("INSERT INTO users(name,phone,password_hash,created_at) VALUES(?,?,?,?)",(name,phone,hash_password(password),datetime.now(timezone.utc).isoformat())).lastrowid
        c.execute("INSERT INTO user_restaurants(user_id,restaurant_id,role_id) VALUES(?,?,?)",(uid,user["restaurant_id"],role["id"])); audit(c,user,"user.create","user",uid,f"role={role_name}"); c.commit()
        return {"id":uid,"name":name,"phone":phone,"role":role_name,"status":"active"}
    except sqlite3.IntegrityError: c.rollback(); raise HTTPException(409,"این شماره موبایل قبلاً ثبت شده است")
    finally: c.close()

@app.patch("/api/users/{user_id}")
def update_user(user_id:int,payload:dict,user=Depends(require_permission("users.manage"))):
    c=conn(); target=c.execute("SELECT u.id,u.name,u.phone,u.status,r.name role FROM users u JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id WHERE u.id=? AND ur.restaurant_id=?",(user_id,user["restaurant_id"])).fetchone()
    if not target: c.close(); raise HTTPException(404,"کاربر پیدا نشد")
    if user_id==user["id"] and payload.get("status") in ("disabled","inactive"): c.close(); raise HTTPException(400,"نمی‌توانید حساب خودتان را غیرفعال کنید")
    if target["role"]=="owner" and user["role"]!="owner": c.close(); raise HTTPException(403,"فقط مالک می‌تواند مالک را ویرایش کند")
    if payload.get("status") in ("active","disabled"): c.execute("UPDATE users SET status=? WHERE id=?",(payload["status"],user_id))
    if payload.get("name"): c.execute("UPDATE users SET name=? WHERE id=?",(str(payload["name"]).strip(),user_id))
    if payload.get("password"):
        if len(str(payload["password"]))<8: c.close(); raise HTTPException(400,"رمز عبور باید حداقل ۸ کاراکتر باشد")
        c.execute("UPDATE users SET password_hash=? WHERE id=?",(hash_password(str(payload["password"])),user_id))
    if payload.get("role"):
        role=c.execute("SELECT id,name FROM roles WHERE name=?",(str(payload["role"]).lower(),)).fetchone()
        if not role: c.close(); raise HTTPException(400,"نقش نامعتبر است")
        if role["name"]=="owner" and user["role"]!="owner": c.close(); raise HTTPException(403,"فقط مالک می‌تواند نقش مالک بدهد")
        c.execute("UPDATE user_restaurants SET role_id=? WHERE user_id=? AND restaurant_id=?",(role["id"],user_id,user["restaurant_id"]))
    audit(c,user,"user.update","user",user_id); c.commit(); row=dict(c.execute("SELECT u.id,u.name,u.phone,u.status,r.name role FROM users u JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id WHERE u.id=? AND ur.restaurant_id=?",(user_id,user["restaurant_id"])).fetchone()); c.close(); return row

@app.delete("/api/users/{user_id}")
def delete_user(user_id:int,user=Depends(require_permission("users.manage"))):
    if user_id==user["id"]: raise HTTPException(400,"نمی‌توانید خودتان را حذف کنید")
    c=conn(); target=c.execute("SELECT u.id,r.name role FROM users u JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id WHERE u.id=? AND ur.restaurant_id=?",(user_id,user["restaurant_id"])).fetchone()
    if not target: c.close(); raise HTTPException(404,"کاربر پیدا نشد")
    if target["role"]=="owner" and user["role"]!="owner": c.close(); raise HTTPException(403,"فقط مالک می‌تواند مالک را حذف کند")
    c.execute("DELETE FROM user_restaurants WHERE user_id=? AND restaurant_id=?",(user_id,user["restaurant_id"])); audit(c,user,"user.remove_from_restaurant","user",user_id); c.commit(); c.close(); return {"status":"ok"}

@app.get("/api/audit-logs")
def audit_logs(user=Depends(require_permission("users.manage"))):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT a.*,u.name user_name FROM audit_logs a LEFT JOIN users u ON u.id=a.user_id WHERE a.restaurant_id=? ORDER BY a.id DESC LIMIT 100",(user["restaurant_id"],))]; c.close(); return rows

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
        if c: c.close()
    return dict(cur and {"id":cur.lastrowid,"name":x["name"],"phone":x["phone"],"address":x.get("address","")})

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