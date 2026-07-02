import os
import libsql_client
import asyncio
import aiosqlite
from fastmcp import FastMCP

TURSO_AUTH_TOKEN = os.environ["TURSO_AUTH_TOKEN"]
TURSO_DATABASE_URL = os.environ["TURSO_DATABASE_URL"]

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cloud/container-safe writable location.
# You can override this using an environment variable.
DB_PATH = os.environ.get("DB_PATH", "/tmp/expenses.db")

CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")


async def init_db():
    """Create the expenses table if it does not already exist."""
    async with libsql_client.create_client(url=TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN) as client:
        await client.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        await client.commit()


@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
) -> dict:
    """
    Add a new expense record.

    Args:
        date: Expense date in YYYY-MM-DD format.
        amount: Expense amount as a positive number.
        category: Main expense category.
        subcategory: Optional detailed category.
        note: Optional description of the expense.
    """
    try:
        # Important: ensures the table exists in cloud deployments.
        await init_db()

        if amount <= 0:
            return {
                "status": "error",
                "message": "Amount must be greater than zero."
            }

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
    """
    # Important: ensures the table exists before SELECT runs.
    await init_db()

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