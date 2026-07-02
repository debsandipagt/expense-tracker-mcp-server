import os
import asyncio
import aiosqlite
from fastmcp import FastMCP

mcp = FastMCP(
    name="Expense Tracker Server",
    instructions="""
    This MCP server manages personal expense records.

    Use this server to:
    - Add a new expense with date, amount, category, subcategory, and note.
    - View all saved expenses from newest to oldest.

    Dates should be provided in YYYY-MM-DD format.
    Amount should be a positive number.
    """
)

# Local: creates expenses.db beside this file
# Docker / Cloud Run: set DB_PATH=/tmp/expenses.db
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "expenses.db"))
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")


async def init_db():
    """Create the expenses table if it does not already exist."""
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
    """
    Add a new expense record to the expense tracker.

    Use this tool when the user wants to record spending, payment, purchase,
    bill, travel cost, food expense, shopping expense, or any other outgoing amount.

    Args:
        date: Expense date in YYYY-MM-DD format. Example: 2026-07-02.
        amount: Expense amount as a positive number. Example: 250.50.
        category: Main expense category. Example: Food, Travel, Shopping, Bills.
        subcategory: Optional detailed category. Example: Lunch, Taxi, Electricity.
        note: Optional description of the expense. Example: Lunch with colleagues.

    Returns:
        A success response with the generated expense ID, or an error response.
    """
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
    """
    Retrieve all saved expenses from newest to oldest.

    Use this tool when the user wants to view, review, check, or list
    their expense history.

    Returns:
        A list of expense records containing ID, date, amount, category,
        subcategory, and note. Returns an empty list if no expenses exist.
    """
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
    asyncio.run(init_db())
    mcp.run(transport="http", host="0.0.0.0", port=8000)