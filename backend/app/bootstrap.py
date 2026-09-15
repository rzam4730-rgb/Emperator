"""First-run bootstrap for local Emperator development."""
from __future__ import annotations

from datetime import datetime, timezone


def ensure_initial_owner(c, hash_password):
    """Ensure the local bootstrap owner can log in on a fresh development DB."""
    phone = "09120000000"
    password_hash = hash_password("12345678")

    existing = c.execute(
        "SELECT id FROM users WHERE phone=? LIMIT 1", (phone,)
    ).fetchone()
    if existing:
        # Repair the earlier development bootstrap account, which was created
        # with a 4-character password that the frontend correctly rejects.
        c.execute(
            "UPDATE users SET password_hash=?, status='active' WHERE id=?",
            (password_hash, existing["id"]),
        )
        return False

    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] != 0:
        return False

    now = datetime.now(timezone.utc).isoformat()
    restaurant_id = c.execute(
        "INSERT INTO restaurants(name,status,created_at) VALUES(?,?,?)",
        ("مجموعه اولیه امپراتور", "active", now),
    ).lastrowid
    owner_id = c.execute("SELECT id FROM roles WHERE name='owner'").fetchone()[0]
    user_id = c.execute(
        "INSERT INTO users(name,phone,password_hash,created_at) VALUES(?,?,?,?)",
        ("مدیر امپراتور", phone, password_hash, now),
    ).lastrowid
    c.execute(
        "INSERT INTO user_restaurants(user_id,restaurant_id,role_id) VALUES(?,?,?)",
        (user_id, restaurant_id, owner_id),
    )
    return True
