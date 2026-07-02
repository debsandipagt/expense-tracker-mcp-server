import os
import aiosqlite
from fastmcp import FastMCP

mcp = FastMCP(name="Expense Tracker Server")

# Local: creates expenses.db beside this file
# Docker / Cloud Run: set DB_PATH=/tmp/expenses.db
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        await db.commit()

@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
) -> dict:
    """Add one expense to the expense tracker."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                """
                INSERT INTO expenses (date, amount, category, subcategory, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (date, amount, category, subcategory, note)
            )
            await db.commit()

            return {
                "status": "success",
                "message": "Expense added successfully.",
                "expense_id": cursor.lastrowid
            }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not add expense: {error}",
            "database_path": DB_PATH
        }

@mcp.tool()
async def list_expenses() -> list[dict]:
    """List all expenses from newest to oldest."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("""
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            ORDER BY id DESC
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())
    mcp.run(transport="http", host="0.0.0.0", port=8000)