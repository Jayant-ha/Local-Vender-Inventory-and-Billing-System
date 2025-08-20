import sqlite3
import os

# Get the base directory of our application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Create the database in the project root instead of instance folder
DB_NAME = os.path.join(BASE_DIR, "app.db")

# ----------------- Helpers -----------------
def get_connection():
    # Create the database directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# The rest of your db.py code remains the same...

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Create tables if not exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT NOT NULL,
            address TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            product_id INTEGER,
            qty INTEGER,
            price REAL,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)
    conn.commit()
    conn.close()

# ----------------- Products -----------------
def add_product(name, price, stock):
    conn = get_connection()
    conn.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", (name, price, stock))
    conn.commit()
    conn.close()

def get_products():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return rows

# ----------------- Customers -----------------
def add_customer(name, contact, address):
    conn = get_connection()
    conn.execute("INSERT INTO customers (name, contact, address) VALUES (?, ?, ?)", (name, contact, address))
    conn.commit()
    conn.close()

def get_customers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM customers").fetchall()
    conn.close()
    return rows

def get_customer(customer_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
    conn.close()
    return row

# ----------------- Invoices -----------------
def create_invoice(customer_id, items):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO invoices (customer_id) VALUES (?)", (customer_id,))
    invoice_id = cur.lastrowid

    grand_total = 0
    for item in items:
        total = item["qty"] * item["price"]
        grand_total += total
        cur.execute(
            "INSERT INTO invoice_items (invoice_id, product_id, qty, price) VALUES (?, ?, ?, ?)",
            (invoice_id, item["id"], item["qty"], item["price"])
        )
        # Update stock
        cur.execute("UPDATE products SET stock = stock - ? WHERE id=?", (item["qty"], item["id"]))

    conn.commit()
    conn.close()
    return invoice_id, grand_total

def get_invoice(invoice_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
    conn.close()
    return row

def get_invoice_items(invoice_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT ii.qty, ii.price, p.name
        FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id
        WHERE ii.invoice_id=?
    """, (invoice_id,)).fetchall()
    conn.close()
    return rows

