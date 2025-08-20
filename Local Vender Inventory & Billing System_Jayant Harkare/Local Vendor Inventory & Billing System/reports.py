# reports.py - updated with error handling
import db
import sqlite3

def get_revenue():
    try:
        conn = db.get_connection()
        row = conn.execute("SELECT SUM(qty * price) AS total FROM invoice_items").fetchone()
        conn.close()
        return row if row else {"total": 0}
    except sqlite3.Error as e:
        print(f"Database error in get_revenue: {e}")
        return {"total": 0}
    except Exception as e:
        print(f"Error in get_revenue: {e}")
        return {"total": 0}

# Apply similar error handling to other functions in reports.py

def get_sales_report():
    conn = db.get_connection()
    rows = conn.execute("""
        SELECT p.name, SUM(ii.qty) as total_sold
        FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id
        GROUP BY p.id
    """).fetchall()
    conn.close()
    return rows

def get_stock_report():
    conn = db.get_connection()
    rows = conn.execute("SELECT name, stock FROM products").fetchall()
    conn.close()
    return rows
