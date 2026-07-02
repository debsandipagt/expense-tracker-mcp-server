import os
import asyncio
import libsql_client
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

BASE_DIR = os.path.dirname(__file__)
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")

# Turso (libSQL) connection details — set these as environment variables
# in FastMCP Cloud's project settings, NOT hardcoded here.
# TURSO_DATABASE_URL looks like: libsql://your-db-name.turso.io
# TURSO_AUTH_TOKEN is the token from `turso db tokens create <db-name>`
TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")


def get_client() -> libsql_client.Client:
    """Create a new libsql client for a single operation."""
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        raise RuntimeError(
            "TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set as environment "
            "variables. Set them in FastMCP Cloud's project settings."
        )
    return libsql_client.create_client(
        url=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN,
    )


async def init_db():
    """Create the expenses table in Turso if it does not already exist."""
    async with get_client() as client:
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
        async with get_client() as client:
            result = await client.execute(
                """
                INSERT INTO expenses (date, amount, category, subcategory, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                [date, amount, category, subcategory, note]
            )

            return {
                "status": "success",
                "message": "Expense added successfully.",
                "expense_id": result.last_insert_rowid
            }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not add expense: {error}"
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
    async with get_client() as client:
        result = await client.execute("""
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            ORDER BY id DESC
        """)
        return [
            dict(zip(result.columns, row))
            for row in result.rows
        ]


if __name__ == "__main__":
    asyncio.run(init_db())
    mcp.run(transport="http", host="0.0.0.0", port=8000)