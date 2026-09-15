"""First-run bootstrap for local Emperator development."""
from __future__ import annotations

from datetime import datetime, timezone


def ensure_initial_owner(c, hash_password):
    """Create the initial owner only when the database contains no users."""
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
        ("مدیر امپراتور", "09120000000", hash_password("12345678"), now),
    ).lastrowid
    c.execute(
        "INSERT INTO user_restaurants(user_id,restaurant_id,role_id) VALUES(?,?,?)",
        (user_id, restaurant_id, owner_id),
    )
    return True
