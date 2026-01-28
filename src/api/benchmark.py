from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from models.schemas import BenchmarkCreate, JobDetail, JobStatus
from services import benchmark_service

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


@router.post("/", response_model=JobStatus)
async def start_benchmark(
    payload: BenchmarkCreate, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_session)
):
    job = await benchmark_service.create_job(session, payload.endpoint_url)
    background_tasks.add_task(benchmark_service.run_benchmark, job.id, payload.endpoint_url)
    return job


@router.get("/", response_model=list[JobStatus])
async def list_benchmarks(session: AsyncSession = Depends(get_session)):
    return await benchmark_service.get_all_jobs(session)


@router.get("/{job_id}", response_model=JobDetail)
async def get_benchmark_status(job_id: UUID, session: AsyncSession = Depends(get_session)):
    job = await benchmark_service.get_job_with_results(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
