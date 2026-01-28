from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel


def utc_now():
    return datetime.now(UTC)


class BenchmarkJob(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    status: str = Field(default="pending")  # pending, running, completed, failed
    endpoint_url: str
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True)))

    results: list["BenchmarkResult"] = Relationship(back_populates="job")


class BenchmarkResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    job_id: UUID = Field(foreign_key="benchmarkjob.id")
    instance_id: str
    database_name: str
    question: str
    generated_sql: str | None = None
    expected_sql: str | None = None
    is_correct: bool | None = None
    error: str | None = None
    latency_ms: float | None = None

    job: BenchmarkJob = Relationship(back_populates="results")
