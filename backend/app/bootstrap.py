"""First-run bootstrap for local Emperator development."""
from __future__ import annotations

from datetime import datetime, timezone


def ensure_initial_owner(c, hash_password):
    """Ensure the local bootstrap owner can log in and has demo products."""
    phone = "09120000000"
    password_hash = hash_password("12345678")

    existing = c.execute(
        "SELECT id FROM users WHERE phone=? LIMIT 1", (phone,)
    ).fetchone()
    if existing:
        c.execute(
            "UPDATE users SET password_hash=?, status='active' WHERE id=?",
            (password_hash, existing["id"]),
        )
        restaurant = c.execute(
            "SELECT restaurant_id FROM user_restaurants WHERE user_id=? LIMIT 1",
            (existing["id"],),
        ).fetchone()
        if restaurant:
            _ensure_demo_products(c, restaurant["restaurant_id"])
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
    _ensure_demo_products(c, restaurant_id)
    return True


def _ensure_demo_products(c, restaurant_id):
    """Create the initial product catalog for the local bootstrap restaurant."""
    count = c.execute(
        "SELECT COUNT(*) FROM products WHERE restaurant_id=?",
        (restaurant_id,),
    ).fetchone()[0]
    if count:
        return
    products = [
        ("چلوکباب مخصوص", "غذا", 285000, "🥩"),
        ("زرشک‌پلو با مرغ", "غذا", 190000, "🍗"),
        ("قورمه‌سبزی", "غذا", 175000, "🍲"),
        ("جوجه کباب", "غذا", 210000, "🍢"),
        ("نوشابه", "نوشیدنی", 25000, "🥤"),
        ("دوغ محلی", "نوشیدنی", 35000, "🥛"),
    ]
    c.executemany(
        "INSERT INTO products(name,category,price,icon,restaurant_id) VALUES(?,?,?,?,?)",
        [(name, category, price, icon, restaurant_id) for name, category, price, icon in products],
    )
