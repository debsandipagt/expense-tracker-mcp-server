# Expense Tracker MCP Server — Dev Log

## Setup
1. `pip install uv` — install the uv package/project manager.
2. `uv init .` — initialize a new uv project in the current directory.
3. `uv add fastmcp` — install FastMCP (via uv instead of pip).

## Local Development & Testing
4. `uv run fastmcp dev inspector main.py` — launch the MCP Inspector to test the server interactively.
5. `uv run python server.py` — run the FastMCP server directly.

## Structuring Tool Inputs
6. Create a `categories.json` file to define a fixed set of expense categories, so Claude is constrained to use consistent, structured category values instead of free text.

## API Design
7. Prototype a REST API for travel expenses using FastAPI, and test it in `app.py`.
8. Convert the working REST API logic into MCP tools inside `server.py` (i.e., wrap the same logic as `@mcp.tool()` functions instead of FastAPI routes).

## Dependencies
9. `uv sync` — install/lock all project dependencies from `pyproject.toml`.
10. `uv add fastapi uvicorn pydantic` — add FastAPI, Uvicorn, and Pydantic to the existing uv project.

## Database & Deployment Fixes
11. **Diagnosed "attempt to write a readonly database" error** on FastMCP Cloud — traced to `DB_PATH` defaulting to `BASE_DIR` (the script's own directory), which is deployed as a **read-only** bundle in most container/serverless platforms.
12. **Fixed by pointing `DB_PATH` at `/tmp/expenses.db`**:
```python
    DB_PATH = os.environ.get("DB_PATH", "/tmp/expenses.db")
```
    `/tmp` is writable in virtually all containerized environments, since platforms mount it as a separate writable layer even when the rest of the filesystem is locked.
13. **Removed bundled-DB seeding logic** — server now starts fresh against `/tmp/expenses.db` every deploy, rather than copying over old data from the read-only bundle.
14. **Note on ephemeral storage**: `/tmp` is wiped on every restart/redeploy and isn't shared across multiple instances — fine for testing, not a long-term data store. Future improvement: move to a persistent volume or external DB (e.g., Turso/Postgres) if data needs to survive redeploys.
15. **Debugged local Windows port conflict** (`WinError 10048`) — caused by a leftover process still bound to port 8000 from a previous `fastmcp dev inspector` session. Resolved via:
```powershell
    netstat -ano | findstr :8000
    taskkill /PID <pid> /F
```
16. **Confirmed end-to-end via `add_expense` / `list_expenses`** through the deployed FastMCP Cloud connector — verified writes and reads both work against the corrected `/tmp` path.

## Git Workflow (reference)
```powershell
git add .
git commit -m "message"
git push -u origin master   # repo's default branch is `master`, not `main`
```