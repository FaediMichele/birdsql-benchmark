from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config import settings


async def execute_query(database_name: str, query: str) -> tuple[list[Any] | None, str | None]:
    """
    Executes a query on the specified benchmark database.
    Returns a tuple of (result_rows, error_message).
    """
    # Construct connection string for the specific database
    # Assuming the same credentials as the main benchmark connection
    base_url = settings.BENCHMARK_DB_URL
    # Replace the database name (last part of the URL)
    # This is a simple string manipulation, ideally we'd use a URL parser
    # But given the fixed structure "postgresql+asyncpg://user:pass@host:port/dbname"
    # we can just replace the path.

    # Better approach: Use SQLAlchemy's make_url or URL object, but string replace is faster for this context
    # provided the format is consistent.
    if "/postgres" in base_url:
        db_url = base_url.replace("/postgres", f"/{database_name}")
    else:
        # Fallback or error if URL structure isn't as expected
        return None, f"Invalid BENCHMARK_DB_URL format: {base_url}"

    try:
        engine = create_async_engine(db_url, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            # fetchall returns a list of Row objects
            rows = result.fetchall()
            # Convert to list of tuples for easier comparison
            return [tuple(row) for row in rows], None
    except Exception as e:
        return None, str(e)
    finally:
        await engine.dispose()


def compare_results(expected_rows: list[Any] | None, generated_rows: list[Any] | None) -> bool:
    """
    Compares two sets of results.
    Currently implements a simple set comparison (ignoring order).
    """
    if expected_rows is None or generated_rows is None:
        return False

    # Simple length check
    if len(expected_rows) != len(generated_rows):
        return False

    # Convert to sets for order-independent comparison
    # Note: This assumes rows contain hashable types.
    # If rows contain lists/dicts, this will fail.
    try:
        return set(expected_rows) == set(generated_rows)
    except TypeError:
        # Fallback to sorted list comparison if possible, or just strict list comparison
        # if elements are not sortable.
        try:
            return sorted(expected_rows, key=lambda x: str(x)) == sorted(generated_rows, key=lambda x: str(x))
        except Exception:
            return expected_rows == generated_rows
