# T2SQL Benchmark

A comprehensive benchmarking tool for Text-to-SQL systems, designed to evaluate the performance of AI agents against the BirdSQL LiveBench dataset.

## Features

- **Asynchronous Execution**: Run benchmarks in the background using FastAPI and `asyncpg`.
- **Dual Evaluation**:
  - **Execution Accuracy (EX)**: Compares the results of the generated SQL against the ground truth execution on actual PostgreSQL databases.
  - **Valid SQL Rate**: Tracks the percentage of generated queries that execute without syntax errors.
- **Detailed Metadata**: Provides schema, column descriptions, and domain knowledge for each database in the benchmark.
- **Mock AI Support**: Includes a mock AI service for testing the pipeline without incurring LLM costs.
- **Dockerized**: Fully containerized environment with separate services for the app, benchmark databases, and result storage.

## Prerequisites

- Docker & Docker Compose
- `uv` (optional, for local python management)
- `make` (optional, for convenience commands)

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository_url>
   cd t2sql_benchmark2
   ```

2. **Download Resources**
   This command downloads the dataset, metadata, and PostgreSQL database dumps required for the benchmark.
   ```bash
   make setup
   ```
   *Note: This downloads ~17MB of data and extracts it to the `data/` directory.*

3. **Start the Environment**
   Builds and starts all services (App, Results DB, Benchmark DBs, Mock AI).
   ```bash
   make up
   ```

## Configuration

The application is configured via environment variables or a `.env` file.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | Connection string for the results database | `postgresql+asyncpg://user:password@db_results:5432/results_db` |
| `BENCHMARK_DB_URL` | Base connection string for benchmark databases | `postgresql+asyncpg://root:password@db_bench:5432/postgres` |
| `BENCHMARK_INPUT_FILE_PATH` | Path to the test questions file | `data/livesqlbench_data.jsonl` |
| `BENCHMARK_GT_FILE_PATH` | Path to the ground truth file | `data/livesqlbench_base_full_v1_gt_kg_testcases_0904.jsonl` |
| `METADATA_PATH` | Directory containing database metadata | `data/livesqlbench-base-full-v1` |

## Usage

### Makefile Commands

- `make setup`: Download required datasets and database dumps.
- `make up`: Start the full Docker environment.
- `make down`: Stop and remove containers.
- `make test`: Verify metadata API endpoints.
- `make test-benchmark`: Trigger a benchmark run using the Mock AI.
- `make lint`: Run code linting and type checking.
- `make format`: Auto-format code.

### API Endpoints

The server runs on `http://localhost:8000`.

#### Benchmark

- **POST** `/benchmark/`
  Trigger a new benchmark run.
  ```json
  {
    "endpoint_url": "http://ai_mock:8001/"
  }
  ```

- **GET** `/benchmark/{job_id}`
  Get the status and statistics of a benchmark job.
  ```json
  {
    "id": "...",
    "status": "completed",
    "stats": {
      "total": 600,
      "correct": 2,
      "accuracy_score": 0.0033,
      ...
    }
  }
  ```

- **GET** `/benchmark/`
  List all benchmark jobs.

#### Metadata

- **GET** `/metadata/`
  List all available benchmark databases.

- **GET** `/metadata/{database_name}`
  Get detailed metadata for a specific database (Schema, Column Meanings, Knowledge Base).

## Development

The project uses `uv` for dependency management.

```bash
# Install dependencies
uv sync

# Run locally (requires local Postgres)
make run
```
