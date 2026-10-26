import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "erp.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_name TEXT NOT NULL,
        invoice_number TEXT UNIQUE NOT NULL,
        amount REAL NOT NULL,
        due_date TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'PENDING_APPROVAL',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def reset_db():
    """Resets the database with seeded mock data for tests."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS invoices")
    conn.commit()
    conn.close()
    init_db()

    # Seed 2 historical invoices
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO invoices (vendor_name, invoice_number, amount, due_date, category, description, status)
    VALUES 
    ('AWS Cloud Services', 'INV-AWS-2026-001', 1240.50, '2026-10-15', 'Cloud Infrastructure', 'Production EC2 and S3 usage', 'PAID'),
    ('Slack Technologies', 'INV-SLK-9921', 480.00, '2026-10-20', 'Software Subscriptions', 'Annual team workspace plan', 'APPROVED')
    """)
    conn.commit()
    conn.close()

def list_invoices() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_invoice_by_number(invoice_number: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices WHERE invoice_number = ?", (invoice_number,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def insert_invoice(vendor_name: str, invoice_number: str, amount: float, due_date: str, category: str, description: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO invoices (vendor_name, invoice_number, amount, due_date, category, description, status)
    VALUES (?, ?, ?, ?, ?, ?, 'ENTERED')
    """, (vendor_name, invoice_number, amount, due_date, category, description))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "status": "ENTERED", "invoice_number": invoice_number}

# Initialize on import
init_db()
