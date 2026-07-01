import os
import json
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

#-------------------------------------------------------------
#Paths
#-------------------------------------------------------------

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")

app = FastAPI(
    title="expenseTrackerAPI",
    version="1.0.1"
)

#--------------------------------------------------------------
# Database Initialize
#--------------------------------------------------------------

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

init_db()

#--------------------------------------------------------------
# Pydantic Model
#--------------------------------------------------------------

class Expenses(BaseModel):
    date: str
    amount: float
    category: str
    subcategory: str = ""
    note: str = ""

#-------------------------------------------------------------
# Add expenses
#-------------------------------------------------------------

@app.post("/expenses")
def add_expenses(expenses: Expenses):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            INSERT INTO expenses
            (date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                expenses.date,
                expenses.amount,
                expenses.category,
                expenses.subcategory,   
                expenses.note
            )
        )

    return {"status": "success", "id": cur.lastrowid}

@app.get("/expenses")
def get_expenses():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT id, date, amount, category, subcategory, note FROM expenses ORDER BY id ASC"
            )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@app.get("/expenses/date-range")
def expenses_between_dates(
    start_date: str,
    end_date: str,
):

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
    
@app.get("/summary")
def summarize(
    start_date: str,
    end_date: str,
    category: Optional[str] = None,
):

    query = """
        SELECT
            category,
            SUM(amount) AS total_amount
        FROM expenses
        WHERE date BETWEEN ? AND ?
    """

    params = [start_date, end_date]

    if category:
        query += " AND category = ?"
        params.append(category)

    query += """
        GROUP BY category
        ORDER BY category
    """

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


# --------------------------------------------------
# Categories
# --------------------------------------------------

@app.get("/categories")
def categories():

    if not os.path.exists(CATEGORIES_PATH):
        raise HTTPException(404, "categories.json not found")

    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)