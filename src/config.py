from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@db_results:5432/results_db"
    BENCHMARK_DB_URL: str = "postgresql+asyncpg://root:password@db_bench:5432/postgres"
    BENCHMARK_INPUT_FILE_PATH: str = "data/livesqlbench-base-full-v1/livesqlbench_data.jsonl"
    BENCHMARK_GT_FILE_PATH: str = "data/livesqlbench_base_full_v1_gt_kg_testcases_0904.jsonl"
    METADATA_PATH: str = "data/livesqlbench-base-full-v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
