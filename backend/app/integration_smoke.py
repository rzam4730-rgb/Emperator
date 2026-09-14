"""Deterministic integration smoke checks for the Emperator business flow."""
import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile


def run():
    from .accounting import install_accounting_schema, seed_accounting
    from .customer_club import install_customer_club_schema, award_order_points
    from .order_inventory import install_order_inventory_schema, consume_order_inventory
    from .order_lifecycle import install_lifecycle_schema

    with NamedTemporaryFile(suffix='.db', delete=False) as f:
        db = Path(f.name)
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    try:
        c.executescript('''
        CREATE TABLE restaurants(id INTEGER PRIMARY KEY, name TEXT, status TEXT DEFAULT 'active');
        CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, status TEXT DEFAULT 'active');
        CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, phone TEXT, points INTEGER DEFAULT 0, restaurant_id INTEGER);
        CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, price INTEGER, active INTEGER DEFAULT 1, restaurant_id INTEGER);
        CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER, restaurant_id INTEGER, status TEXT, total INTEGER, payment_method TEXT, created_at TEXT);
        CREATE TABLE order_items(id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER, name TEXT, price INTEGER, quantity INTEGER);
        CREATE TABLE recipes(id INTEGER PRIMARY KEY, restaurant_id INTEGER, product_id INTEGER, yield_quantity REAL DEFAULT 1, active INTEGER DEFAULT 1);
        CREATE TABLE recipe_items(id INTEGER PRIMARY KEY, recipe_id INTEGER, inventory_item_id INTEGER, quantity REAL);
        CREATE TABLE inventory_items(id INTEGER PRIMARY KEY, restaurant_id INTEGER, name TEXT, unit TEXT, stock REAL DEFAULT 0, cost_per_unit INTEGER DEFAULT 0, min_stock REAL DEFAULT 0);
        CREATE TABLE inventory_movements(id INTEGER PRIMARY KEY, restaurant_id INTEGER, inventory_item_id INTEGER, quantity REAL, movement_type TEXT, reference_id TEXT, created_at TEXT);
        ''')
        install_accounting_schema(c); install_customer_club_schema(c); install_order_inventory_schema(c); install_lifecycle_schema(c)
        c.execute("INSERT INTO restaurants VALUES(1,'Test', 'active')")
        c.execute("INSERT INTO users VALUES(1,'Owner','active')")
        c.execute("INSERT INTO customers VALUES(1,'Test Customer','09120000000',0,1)")
        c.execute("INSERT INTO products VALUES(1,'Test Food',100000,1,1)")
        c.execute("INSERT INTO orders VALUES(1,1,1,'جدید',100000,'نقدی','2026-01-01T00:00:00+00:00')")
        c.execute("INSERT INTO order_items VALUES(1,1,1,'Test Food',100000,1)")
        c.execute("INSERT INTO inventory_items VALUES(1,1,'Rice','kg',2,50000,0.5)")
        c.execute("INSERT INTO recipes VALUES(1,1,1,1,1)")
        c.execute("INSERT INTO recipe_items VALUES(1,1,1,0.5)")
        c.commit()
        user={'id':1,'restaurant_id':1}
        cost, status = consume_order_inventory(c,1,user)
        assert status in ('consumed','already_consumed')
        assert cost == 25000
        assert c.execute('SELECT stock FROM inventory_items WHERE id=1').fetchone()[0] == 1.5
        award_order_points(c,1,1,1)
        assert c.execute('SELECT points FROM customers WHERE id=1').fetchone()[0] == 100
        seed_accounting(c,1)
        cash=c.execute("SELECT id FROM accounting_accounts WHERE restaurant_id=1 AND account_type='cash'").fetchone()[0]
        c.execute("INSERT INTO accounting_transactions(restaurant_id,account_id,direction,amount,description,created_by,created_at) VALUES(1,?,?,?,?,1,'2026-01-01T00:00:00+00:00')",(cash,'in',100000,'test sale'))
        c.commit()
        assert c.execute("SELECT balance FROM accounting_accounts WHERE id=?",(cash,)).fetchone()[0] == 100000
        return {'ok': True, 'inventory_cost': cost, 'loyalty_points': 100, 'cash_balance': 100000}
    finally:
        c.close()
        db.unlink(missing_ok=True)


if __name__ == '__main__':
    print(run())
