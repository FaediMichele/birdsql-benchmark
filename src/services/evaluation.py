from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config import settings
from models.schemas import ManualEvaluationStats
from services.dataset import get_benchmark_data


class EvaluationError(Exception):
    pass


class InstanceNotFoundError(EvaluationError):
    pass


class GroundTruthQueryError(EvaluationError):
    pass


async def manual_evaluate_query(instance_id: str, generated_sql: str) -> ManualEvaluationStats:
    """
    Service function to manually evaluate a generated SQL query against the ground truth.
    """
    dataset = get_benchmark_data()
    instance = next((item for item in dataset if item["instance_id"] == instance_id), None)

    if not instance:
        raise InstanceNotFoundError("Instance not found")

    db_name = cast(str, instance.get("selected_database"))
    print(f"DATABASE USED FOR EVALUATION: {db_name}")  # Temporary debug log
    sol_sql_list = cast(list[str], instance.get("sol_sql", []))

    if not db_name:
        raise InstanceNotFoundError("Database name not found for instance")

    if not sol_sql_list:
        raise InstanceNotFoundError("Ground truth SQL not found for instance")

    ground_truth_sql = sol_sql_list[0]

    # Execute ground truth query
    gt_result, gt_error = await execute_query(db_name, ground_truth_sql)
    if gt_error:
        raise GroundTruthQueryError(f"Error executing ground truth query: {gt_error}")

    # Execute generated query
    gen_result, gen_error = await execute_query(db_name, generated_sql)
    if gen_error:
        return ManualEvaluationStats(
            correct=0,
            execution_error=1,
            wrong_result=0,
            accuracy_score=0.0,
            valid_sql_rate=0.0,
            is_correct=False,
            error=gen_error,
        )

    is_correct = compare_results(gt_result, gen_result)

    if is_correct:
        return ManualEvaluationStats(
            correct=1,
            execution_error=0,
            wrong_result=0,
            accuracy_score=1.0,
            valid_sql_rate=1.0,
            is_correct=True,
            error=None,
        )
    else:
        return ManualEvaluationStats(
            correct=0,
            execution_error=0,
            wrong_result=1,
            accuracy_score=0.0,
            valid_sql_rate=1.0,
            is_correct=False,
            error="The result of the query is not correct",
        )


async def execute_query(database_name: str, query: str) -> tuple[list[Any] | None, str | None]:
    """
    Executes a query on the specified benchmark database.
    Returns a tuple of (result_rows, error_message).
    """
    # Construct connection string for the specific database
    base_url = settings.BENCHMARK_DB_URL
    if "/postgres" in base_url:
        db_url = base_url.replace("/postgres", f"/{database_name}")
    else:
        return None, f"Invalid BENCHMARK_DB_URL format: {base_url}"

    try:
        engine = create_async_engine(db_url, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            rows = result.fetchall()
            return [tuple(row) for row in rows], None
    except Exception as e:
        return None, str(e)
    finally:
        await engine.dispose()


def compare_results(expected_rows: list[Any] | None, generated_rows: list[Any] | None) -> bool:
    """
    Compares two sets of results.
    """
    if expected_rows is None or generated_rows is None:
        return False

    if len(expected_rows) != len(generated_rows):
        return False

    try:
        return set(expected_rows) == set(generated_rows)
    except TypeError:
        try:
            return sorted(expected_rows, key=lambda x: str(x)) == sorted(generated_rows, key=lambda x: str(x))
        except Exception:
            return expected_rows == generated_rows