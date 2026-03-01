import sqlite3
from typing import Optional, List, Tuple

DB_PATH = 'products.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        price TEXT NOT NULL,
        credentials TEXT NOT NULL,
        category TEXT NOT NULL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        total_price REAL NOT NULL DEFAULT 0,
        payment_link TEXT,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

def add_product(title: str, price: str, credentials: str, category: str, description: str = '') -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO products (title, description, price, credentials, category) VALUES (?, ?, ?, ?, ?)',
                (title, description, price, credentials, category))
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid

def list_products(category: str = None) -> List[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if category:
        cur.execute('SELECT id, title, description, price FROM products WHERE category = ?', (category,))
    else:
        cur.execute('SELECT id, title, description, price FROM products')
    rows = cur.fetchall()
    conn.close()
    return rows

def get_product(pid: int) -> Optional[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, title, description, price, credentials, category FROM products WHERE id = ?', (pid,))
    row = cur.fetchone()
    conn.close()
    return row

def create_order(user_id: int, product_id: int, quantity: int, total_price: float) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO orders (user_id, product_id, quantity, total_price, status) VALUES (?, ?, ?, ?, ?)',
                (user_id, product_id, quantity, total_price, 'awaiting_payment'))
    oid = cur.lastrowid
    conn.commit()
    conn.close()
    return oid

def set_payment_link(oid: int, link: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE orders SET payment_link = ? WHERE id = ?', (link, oid))
    conn.commit()
    conn.close()

def confirm_order_paid(oid: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE orders SET status = ? WHERE id = ?', ('paid', oid))
    conn.commit()
    conn.close()

def get_order(oid: int) -> Optional[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, user_id, product_id, status, created_at FROM orders WHERE id = ?', (oid,))
    row = cur.fetchone()
    conn.close()
    return row

def set_order_status(oid: int, status: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE orders SET status = ? WHERE id = ?', (status, oid))
    conn.commit()
    conn.close()
