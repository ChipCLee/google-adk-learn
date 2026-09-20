"""
Real MCP Server providing portfolio database queries via Model Context Protocol (MCP).
Transport: stdio (JSON-RPC 2.0)
"""

import sqlite3
from typing import List, Dict, Any
from mcp.server.mcpserver import MCPServer

# Initialize the MCP Server
server = MCPServer(name="sqlite_portfolio_server")


def _init_sqlite_db() -> sqlite3.Connection:
    """Initializes an in-memory SQLite database with sample portfolio holdings."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE portfolio (
            ticker TEXT PRIMARY KEY,
            company_name TEXT,
            shares INTEGER,
            avg_cost REAL,
            sector TEXT
        )
    """)
    cur.executemany("""
        INSERT INTO portfolio VALUES (?, ?, ?, ?, ?)
    """, [
        ("GOOGL", "Alphabet Inc.", 150, 142.10, "Technology"),
        ("AAPL", "Apple Inc.", 200, 180.50, "Consumer Tech"),
        ("MSFT", "Microsoft Corp.", 100, 410.20, "Cloud / AI"),
        ("NVDA", "Nvidia Corp.", 80, 115.00, "Semiconductors")
    ])
    conn.commit()
    return conn


# Persistent DB connection for the server session
_DB_CONN = _init_sqlite_db()


@server.tool()
def query_portfolio_database(query: str = "all") -> List[Dict[str, Any]]:
    """Queries the user's investment portfolio database and returns holding details.

    Args:
        query: Optional search keyword or ticker to filter holdings (default is 'all').

    Returns:
        List of portfolio holding records with ticker, company name, shares, average cost, and sector.
    """
    cur = _DB_CONN.cursor()
    if query and query.lower() != "all":
        pattern = f"%{query.strip()}%"
        cur.execute(
            "SELECT ticker, company_name, shares, avg_cost, sector FROM portfolio WHERE ticker LIKE ? OR company_name LIKE ?",
            (pattern, pattern)
        )
    else:
        cur.execute("SELECT ticker, company_name, shares, avg_cost, sector FROM portfolio")

    rows = cur.fetchall()
    return [
        {
            "ticker": r[0],
            "company_name": r[1],
            "shares": r[2],
            "avg_cost": r[3],
            "sector": r[4]
        }
        for r in rows
    ]


if __name__ == "__main__":
    # Runs the MCP Server listening on standard input/output (stdio JSON-RPC)
    server.run(transport="stdio")
