import os
import json
import sqlite3
# from typing import Optional

from fastapi import FastAPI, HTTPException, Body
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

from pydantic import BaseModel

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
                expenses.note,
            ),
        )

        conn.commit()

    return {
        "status": "success",
        "id": cur.lastrowid,
        "message": "Expense added successfully",
    }
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
    
@app.get("/expenses/summary")
def summarize(category: str = None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        if category:
            cursor = conn.execute(
                """
                SELECT category,
                       COUNT(*) AS total_entries,
                       COALESCE(SUM(amount), 0) AS total_amount
                FROM expenses
                WHERE category = ?
                GROUP BY category
                """,
                (category,),
            )
        else:
            cursor = conn.execute(
                """
                SELECT category,
                       COUNT(*) AS total_entries,
                       COALESCE(SUM(amount), 0) AS total_amount
                FROM expenses
                GROUP BY category
                """
            )

        return [dict(row) for row in cursor.fetchall()]