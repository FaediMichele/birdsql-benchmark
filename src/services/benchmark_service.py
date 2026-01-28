import time
from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import desc, select

from db.session import engine
from models.models import BenchmarkJob, BenchmarkResult
from models.schemas import BenchmarkStats, JobDetail
from services.dataset import get_benchmark_data
from services.evaluation import compare_results, execute_query


async def run_benchmark(job_id: UUID, endpoint_url: str) -> None:
    # Use a fresh session for the background task
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Update status to running
            statement = select(BenchmarkJob).where(BenchmarkJob.id == job_id)
            results = await session.execute(statement)
            job = results.scalar_one()
            job.status = "running"
            job.updated_at = datetime.now(UTC)
            await session.commit()

            dataset = get_benchmark_data()

            async with httpx.AsyncClient() as client:
                for row in dataset:
                    # ... (rest of the loop)
                    instance_id = row.get("instance_id", "")
                    database_name = row.get("selected_database", "")
                    query = row.get("query", "")
                    sol_sql = row.get("sol_sql", [])
                    expected_sql = sol_sql[0] if sol_sql and isinstance(sol_sql, list) else None

                    start_time = time.time()
                    generated_sql = None
                    error_msg = None

                    try:
                        response = await client.post(
                            endpoint_url,
                            json={"database": database_name, "query": query},
                            timeout=60.0,
                        )

                        if response.status_code == 200:
                            try:
                                resp_json = response.json()
                                if isinstance(resp_json, dict):
                                    generated_sql = (
                                        resp_json.get("sql") or resp_json.get("generated_sql") or str(resp_json)
                                    )
                                else:
                                    generated_sql = str(resp_json)
                            except Exception:
                                generated_sql = response.text
                        else:
                            error_msg = f"Error: {response.status_code} - {response.text}"
                    except Exception as e:
                        error_msg = str(e)

                    latency = (time.time() - start_time) * 1000

                    # Evaluate correctness
                    is_correct = False
                    if generated_sql and expected_sql:
                        # Execute expected SQL
                        expected_res, expected_err = await execute_query(database_name, expected_sql)
                        if expected_err:
                            # If we can't execute the ground truth, we can't evaluate.
                            # We might log this or mark error.
                            # For now, append to error_msg
                            error_msg = (
                                f"{error_msg}\nGround Truth Error: {expected_err}"
                                if error_msg
                                else f"Ground Truth Error: {expected_err}"
                            )

                        # Execute generated SQL
                        generated_res, generated_err = await execute_query(database_name, generated_sql)
                        if generated_err:
                            error_msg = (
                                f"{error_msg}\nGenerated SQL Error: {generated_err}"
                                if error_msg
                                else f"Generated SQL Error: {generated_err}"
                            )

                        # Compare
                        if not expected_err and not generated_err:
                            is_correct = compare_results(expected_res, generated_res)

                    result = BenchmarkResult(
                        job_id=job_id,
                        instance_id=instance_id,
                        database_name=database_name,
                        question=query,
                        generated_sql=generated_sql,
                        expected_sql=expected_sql,
                        is_correct=is_correct,
                        error=error_msg,
                        latency_ms=latency,
                    )
                    session.add(result)
                    await session.commit()

            # Update status to completed
            job.status = "completed"
            job.updated_at = datetime.now(UTC)
            await session.commit()
        except Exception as e:
            # Re-fetch job to update status to failed
            statement = select(BenchmarkJob).where(BenchmarkJob.id == job_id)
            results = await session.execute(statement)
            job = results.scalar_one()
            job.status = "failed"
            job.updated_at = datetime.now(UTC)
            await session.commit()
            print(f"Benchmark job {job_id} failed: {e}")


async def create_job(session: AsyncSession, endpoint_url: str) -> BenchmarkJob:
    job = BenchmarkJob(endpoint_url=endpoint_url)
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_job(session: AsyncSession, job_id: UUID) -> BenchmarkJob | None:
    statement = select(BenchmarkJob).where(BenchmarkJob.id == job_id)
    results = await session.execute(statement)
    return results.scalar_one_or_none()


async def get_all_jobs(session: AsyncSession) -> list[BenchmarkJob]:
    statement = select(BenchmarkJob).order_by(desc(BenchmarkJob.created_at))
    results = await session.execute(statement)
    return list(results.scalars().all())


async def get_job_with_results(session: AsyncSession, job_id: UUID) -> JobDetail | None:
    # In SQLModel/SQLAlchemy async, we might need to load relationships explicitly
    # or use selectinload
    from sqlalchemy.orm import selectinload

    statement = (
        select(BenchmarkJob).where(BenchmarkJob.id == job_id).options(selectinload(BenchmarkJob.results))  # type: ignore
    )
    results = await session.execute(statement)
    job = results.scalar_one_or_none()

    if not job:
        return None

    # Calculate stats
    total = len(job.results)
    correct = 0
    execution_error = 0
    wrong_result = 0
    total_latency = 0.0

    for res in job.results:
        if res.is_correct:
            correct += 1

        # Check for execution error
        # Assuming "Generated SQL Error" indicates execution failure
        if res.error and "Generated SQL Error" in res.error:
            execution_error += 1
        elif not res.is_correct:
            # If not correct and no execution error (or at least generated SQL didn't fail), it's a wrong result
            # Note: If ground truth failed but generated didn't, it might fall here.
            # Ideally we want to count only where generated SQL ran but produced wrong result.
            # If generated_sql is None, it's also an error (generation failure).
            # For simplicity, if not correct and not execution error -> wrong result.
            wrong_result += 1

        if res.latency_ms:
            total_latency += res.latency_ms

    stats = BenchmarkStats(
        total=total,
        correct=correct,
        execution_error=execution_error,
        wrong_result=wrong_result,
        accuracy_score=(correct / total) if total > 0 else 0.0,
        valid_sql_rate=((total - execution_error) / total) if total > 0 else 0.0,
        avg_latency_ms=(total_latency / total) if total > 0 else 0.0,
    )

    return JobDetail(id=job.id, status=job.status, created_at=job.created_at, updated_at=job.updated_at, stats=stats)
