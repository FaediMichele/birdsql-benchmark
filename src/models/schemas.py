from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BenchmarkCreate(BaseModel):
    endpoint_url: str


class JobStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class BenchmarkResultSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    instance_id: str
    database_name: str
    question: str
    generated_sql: str | None
    is_correct: bool | None
    error: str | None
    latency_ms: float | None


class BenchmarkStats(BaseModel):
    total: int
    correct: int
    execution_error: int
    wrong_result: int
    accuracy_score: float
    valid_sql_rate: float
    avg_latency_ms: float


class JobDetail(JobStatus):
    stats: BenchmarkStats


class ColumnMeaning(BaseModel):
    table_name: str
    column_name: str
    description: str


class KnowledgeBaseItem(BaseModel):
    id: int
    knowledge: str
    description: str
    definition: str | None
    type: str


class DatabaseMetadata(BaseModel):
    database_name: str
    schema_ddl: str
    column_meanings: list[ColumnMeaning]
    knowledge_base: list[KnowledgeBaseItem]


class BenchmarkDataItem(BaseModel):
    instance_id: str
    selected_database: str
    sol_sql: list[str]


class ManualEvaluationStats(BaseModel):
    total: int = 1
    correct: int
    execution_error: int
    wrong_result: int
    accuracy_score: float
    valid_sql_rate: float
    is_correct: bool
    error: str | None
