"""First-run bootstrap for local Emperator development."""
from __future__ import annotations

from datetime import datetime, timezone
import os


def ensure_initial_owner(c, hash_password):
    """Optionally create a first-run owner from explicit environment variables.

    No default credentials are created or reset automatically.
    """
    existing_count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing_count != 0:
        return False

    phone = os.getenv("EMPERATOR_BOOTSTRAP_PHONE", "").strip()
    password = os.getenv("EMPERATOR_BOOTSTRAP_PASSWORD", "")
    name = os.getenv("EMPERATOR_BOOTSTRAP_NAME", "مدیر امپراتور").strip()
    restaurant_name = os.getenv("EMPERATOR_BOOTSTRAP_RESTAURANT", "مجموعه امپراتور").strip()
    if len(phone) < 7 or len(password) < 8 or len(name) < 2 or len(restaurant_name) < 2:
        return False

    now = datetime.now(timezone.utc).isoformat()
    restaurant_id = c.execute(
        "INSERT INTO restaurants(name,status,created_at) VALUES(?,?,?)",
        (restaurant_name, "active", now),
    ).lastrowid
    owner_id = c.execute("SELECT id FROM roles WHERE name='owner'").fetchone()[0]
    user_id = c.execute(
        "INSERT INTO users(name,phone,password_hash,created_at) VALUES(?,?,?,?)",
        (name, phone, hash_password(password), now),
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
