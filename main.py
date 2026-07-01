# Uses Fast API

import os
import sqlite3
from fastmcp import FastMCP

# Define Database file path in project directory
DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

# Create fastmcp server instance
mcp = FastMCP(name="expenseTracker")
    
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

# Initialize database
init_db()

# Insert values into table
@mcp.tool
def add_expenses(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to datatbase'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
            (date, amount, category, subcategory, note)                                                                        
        )
        return {"status": "ok", "id": cur.lastrowid}
    
@mcp.tool
def list_expenses():
    """
    List all expense entries from the database.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "SELECT id, date, amount, category, subcategory, note FROM expenses ORDER BY id ASC"
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    
@mcp.tool
def list_expenses_date_wise(start_date, end_date):
    """
    List expense entries between two dates (inclusive).
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


@mcp.tool
def summarize(start_date, end_date, category=None):
    "Summarize expenses by category with in an inclusive date range"
    with sqlite3.connect(DB_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
            """
        )
        param = [start_date, end_date]

        if category:
            query += " AND category = ?"
            param.append(category)

        query += " GROUP BY category ORDER BY category ASC"
        cur = c.execute(query, param)

        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    
@mcp.resource("expenses://categories", mime_type="application/json")
def categories():
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

    

if __name__ == "__main__":
    mcp.run()

