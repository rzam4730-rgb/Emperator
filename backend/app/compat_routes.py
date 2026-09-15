"""Compatibility and core route activation for the Emperator API."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException


def seed_core(c):
    for role in ("owner", "manager", "cashier", "kitchen", "accountant"):
        c.execute("INSERT OR IGNORE INTO roles(name) VALUES(?)", (role,))
    permissions = (
        "dashboard.read", "orders.read", "orders.write", "products.read", "products.write",
        "customers.read", "customers.write", "inventory.read", "inventory.write",
        "finance.read", "reports.read", "settings.write", "users.manage",
    )
    for permission in permissions:
        c.execute("INSERT OR IGNORE INTO permissions(name) VALUES(?)", (permission,))
    owner_id = c.execute("SELECT id FROM roles WHERE name='owner'").fetchone()[0]
    for row in c.execute("SELECT id FROM permissions").fetchall():
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

    # First-run bootstrap: create one owner account only when the database has
    # no users. This makes a fresh local installation immediately usable.
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        now = datetime.now(timezone.utc).isoformat()
        restaurant_id = c.execute(
            "INSERT INTO restaurants(name,status,created_at) VALUES(?,?,?)",
            ("مجموعه اولیه امپراتور", "active", now),
        ).lastrowid
        password_hash = bcrypt.hashpw(b"1234", bcrypt.gensalt()).decode("utf-8")
        user_id = c.execute(
            "INSERT INTO users(name,phone,password_hash,created_at) VALUES(?,?,?,?)",
            ("مدیر امپراتور", "09120000000", password_hash, now),
        ).lastrowid
        c.execute(
            "INSERT INTO user_restaurants(user_id,restaurant_id,role_id) VALUES(?,?,?)",
            (user_id, restaurant_id, owner_id),
        )


def mount_core_routes(app, conn, current_user, require_permission, hash_password, verify_password,
                      create_access_token, issue_refresh_token, hash_refresh_token,
                      ensure_subscription, plan_limits, get_usage, utcnow, audit):
    @app.post("/api/auth/login")
    def login(payload: dict):
        phone = str(payload.get("phone", "")).strip()
        password = str(payload.get("password", ""))
        c = conn()
        row = c.execute("SELECT u.id,u.name,u.phone,u.password_hash,u.status,ur.restaurant_id,r.name role FROM users u JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id WHERE u.phone=? LIMIT 1", (phone,)).fetchone()
        if not row or row["status"] != "active" or not verify_password(password, row["password_hash"]):
            c.close(); raise HTTPException(401, "شماره موبایل یا رمز عبور اشتباه است")
        ensure_subscription(c, row["restaurant_id"])
        access = create_access_token(row["id"], row["restaurant_id"], row["role"])
        refresh = issue_refresh_token(c, row["id"], row["restaurant_id"])
        c.commit(); c.close()
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

    @app.post("/api/auth/refresh")
    def refresh(payload: dict):
        token = str(payload.get("refresh_token", ""))
        c = conn(); row = c.execute("SELECT * FROM refresh_tokens WHERE token_hash=? AND revoked_at IS NULL", (hash_refresh_token(token),)).fetchone()
        if not row:
            c.close(); raise HTTPException(401, "Refresh token نامعتبر است")
        try: expires = datetime.fromisoformat(row["expires_at"])
        except ValueError: expires = datetime.min.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc):
            c.close(); raise HTTPException(401, "Refresh token منقضی شده است")
        user = c.execute("SELECT u.id,u.status,r.name role FROM users u JOIN user_restaurants ur ON ur.user_id=u.id JOIN roles r ON r.id=ur.role_id WHERE u.id=? AND ur.restaurant_id=?", (row["user_id"], row["restaurant_id"])).fetchone()
        if not user or user["status"] != "active":
            c.close(); raise HTTPException(401, "کاربر فعال نیست")
        c.execute("UPDATE refresh_tokens SET revoked_at=? WHERE id=?", (datetime.now(timezone.utc).isoformat(), row["id"]))
        new_refresh = issue_refresh_token(c, user["id"], row["restaurant_id"])
        access = create_access_token(user["id"], row["restaurant_id"], user["role"])
        c.commit(); c.close()
        return {"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"}

    @app.post("/api/auth/logout")
    def logout(payload: dict, user=Depends(current_user)):
        token = str(payload.get("refresh_token", ""))
        c = conn()
        if token:
            c.execute("UPDATE refresh_tokens SET revoked_at=? WHERE token_hash=? AND user_id=?", (datetime.now(timezone.utc).isoformat(), hash_refresh_token(token), user["id"]))
        c.commit(); c.close(); return {"status": "ok"}

    @app.get("/api/auth/me")
    def me(user=Depends(current_user)): return user

    @app.get("/api/plans")
    def list_plans(user=Depends(current_user)):
        c = conn(); rows=[]
        for p in c.execute("SELECT * FROM plans WHERE active=1 ORDER BY price_monthly").fetchall():
            rows.append({"code":p["code"],"name":p["name"],"price_monthly":p["price_monthly"],"limits":plan_limits(p)})
        c.close(); return rows

    @app.get("/api/subscription")
    def subscription(user=Depends(current_user)):
        c=conn(); s=ensure_subscription(c,user["restaurant_id"]); rid=user["restaurant_id"]
        customers=c.execute("SELECT COUNT(*) FROM customers WHERE restaurant_id=?",(rid,)).fetchone()[0]
        result={"id":s["id"],"plan_code":s["code"],"plan_name":s["name"],"price_monthly":s["price_monthly"],"status":s["status"],"starts_at":s["starts_at"],"expires_at":s["expires_at"],"auto_renew":bool(s["auto_renew"]),"limits":plan_limits(s),"usage":{"customers":customers,"invoices_today":get_usage(c,rid,"invoices_daily"),"sms_used":get_usage(c,rid,"sms_monthly"),"ai_used":get_usage(c,rid,"ai_monthly")}}
        c.close(); return result

    @app.get("/api/usage")
    def usage(user=Depends(current_user)):
        c=conn(); s=ensure_subscription(c,user["restaurant_id"]); l=plan_limits(s); rid=user["restaurant_id"]
        result={"invoices_today":{"used":get_usage(c,rid,"invoices_daily"),"limit":l["invoice_daily_limit"]},"customers":{"used":c.execute("SELECT COUNT(*) FROM customers WHERE restaurant_id=?",(rid,)).fetchone()[0],"limit":l["customer_limit"]},"sms":{"used":get_usage(c,rid,"sms_monthly"),"limit":l["sms_credits"]},"ai":{"used":get_usage(c,rid,"ai_monthly"),"limit":l["ai_credits"]}}
        c.close(); return result

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

    @app.post("/api/users")
    def create_user(payload:dict,user=Depends(require_permission("users.manage"))):
        name=str(payload.get("name","")).strip(); phone=str(payload.get("phone","")).strip(); password=str(payload.get("password","")); role_name=str(payload.get("role","cashier")).strip().lower()
        if len(name)<2 or len(phone)<7 or len(password)<8: raise HTTPException(400,"نام، شماره موبایل و رمز حداقل ۸ کاراکتری الزامی است")
        c=conn(); role=c.execute("SELECT id,name FROM roles WHERE name=?",(role_name,)).fetchone()
        if not role: c.close(); raise HTTPException(400,"نقش نامعتبر است")
        if role_name=="owner" and user["role"]!="owner": c.close(); raise HTTPException(403,"فقط مالک می‌تواند مالک جدید ایجاد کند")
        try:
            uid=c.execute("INSERT INTO users(name,phone,password_hash,created_at) VALUES(?,?,?,?)",(name,phone,hash_password(password),datetime.now(timezone.utc).isoformat())).lastrowid
            c.execute("INSERT INTO user_restaurants(user_id,restaurant_id,role_id) VALUES(?,?,?)",(uid,user["restaurant_id"],role["id"])); audit(c,user,"user.create","user",uid,f"role={role_name}"); c.commit()
            return {"id":uid,"name":name,"phone":phone,"role":role_name,"status":"active"}
        except sqlite3.IntegrityError:
            c.rollback(); raise HTTPException(409,"این شماره موبایل قبلاً ثبت شده است")
        finally: c.close()
