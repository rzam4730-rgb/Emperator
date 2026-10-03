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
        CREATE TABLE recipes(id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, product_id INTEGER NOT NULL, name TEXT NOT NULL, yield_quantity REAL NOT NULL DEFAULT 1, active INTEGER NOT NULL DEFAULT 1, UNIQUE(restaurant_id,product_id));
        CREATE TABLE recipe_items(id INTEGER PRIMARY KEY AUTOINCREMENT, recipe_id INTEGER NOT NULL, item_id INTEGER NOT NULL, quantity REAL NOT NULL, FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE, FOREIGN KEY(item_id) REFERENCES inventory_items(id));
        CREATE TABLE inventory_items(id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, name TEXT NOT NULL, unit TEXT NOT NULL DEFAULT '\u0639\u062f\u062f', sku TEXT, min_stock REAL NOT NULL DEFAULT 0, cost_per_unit INTEGER NOT NULL DEFAULT 0, current_stock REAL NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1, UNIQUE(restaurant_id,name));
        CREATE TABLE inventory_movements(id INTEGER PRIMARY KEY AUTOINCREMENT, restaurant_id INTEGER NOT NULL, item_id INTEGER NOT NULL, movement_type TEXT NOT NULL CHECK(movement_type IN ('purchase','sale_consumption','adjustment_in','adjustment_out','waste','return')), quantity REAL NOT NULL, unit_cost INTEGER NOT NULL DEFAULT 0, reference_type TEXT, reference_id INTEGER, note TEXT, created_by INTEGER NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(item_id) REFERENCES inventory_items(id));
        ''')
        install_accounting_schema(c); install_customer_club_schema(c); install_order_inventory_schema(c); install_lifecycle_schema(c)
        c.execute("INSERT INTO restaurants VALUES(1,'Test', 'active')")
        c.execute("INSERT INTO users VALUES(1,'Owner','active')")
        c.execute("INSERT INTO customers VALUES(1,'Test Customer','09120000000',0,1)")
        c.execute("INSERT INTO products VALUES(1,'Test Food',100000,1,1)")
        c.execute("INSERT INTO orders VALUES(1,1,1,'جدید',100000,'نقدی','2026-01-01T00:00:00+00:00')")
        c.execute("INSERT INTO order_items VALUES(1,1,1,'Test Food',100000,1)")
        c.execute("INSERT INTO inventory_items(id,restaurant_id,name,unit,current_stock,cost_per_unit,min_stock) VALUES(1,1,'Rice','kg',2,50000,0.5)")
        c.execute("INSERT INTO recipes(id,restaurant_id,product_id,name,yield_quantity,active) VALUES(1,1,1,'Smoke recipe',1,1)")
        c.execute("INSERT INTO recipe_items VALUES(1,1,1,0.5)")
        c.commit()
        user={'id':1,'restaurant_id':1}
        cost, status = consume_order_inventory(c,1,user)
        assert status in ('consumed','already_consumed')
        assert cost == 25000
        assert c.execute('SELECT current_stock FROM inventory_items WHERE id=1').fetchone()[0] == 1.5
        award_order_points(c,1,1,1)
        assert c.execute('SELECT points FROM customers WHERE id=1').fetchone()[0] == 100
        seed_accounting(c,1)
        cash=c.execute("SELECT id FROM accounting_accounts WHERE restaurant_id=1 AND account_type='cash'").fetchone()[0]
        c.execute("INSERT INTO accounting_transactions(restaurant_id,account_id,direction,amount,description,created_by,created_at) VALUES(1,?,?,?,?,1,'2026-01-01T00:00:00+00:00')",(cash,'in',100000,'test sale'))
        c.execute("UPDATE accounting_accounts SET balance=balance+? WHERE id=?", (100000,cash))
        c.commit()
        assert c.execute("SELECT balance FROM accounting_accounts WHERE id=?",(cash,)).fetchone()[0] == 100000
        return {'ok': True, 'inventory_cost': cost, 'loyalty_points': 100, 'cash_balance': 100000}
    finally:
        c.close()
        db.unlink(missing_ok=True)


if __name__ == '__main__':
    print(run())
