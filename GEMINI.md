# Gemini CLI - Project Context

## 1. Project Overview

*   **Name:** `t2sql-benchmark`
*   **Description:** A comprehensive, asynchronous benchmarking system designed to evaluate Text-to-SQL (T2SQL) agents against the BirdSQL LiveBench dataset (`LiveSQLBench`). It automates the process of sending natural language queries to an AI agent, executing the generated SQL against real domain-specific PostgreSQL databases, and comparing the results with ground truth executions to measure "Execution Accuracy" (EX) and "Valid SQL Rate".
*   **License:** MIT License
*   **Version:** 0.1.0 (from `pyproject.toml`)

## 2. Tech Stack

*   **Language:** Python 3.13+
*   **Web Framework:** FastAPI (Async)
*   **Database ORM:** SQLModel (Pydantic + SQLAlchemy Core)
*   **Database Driver:** `asyncpg` (Asynchronous PostgreSQL driver)
*   **Package Manager:** `uv`
*   **Infrastructure:** Docker & Docker Compose
*   **Databases:**
    *   **Results DB:** PostgreSQL 17 (pgvector image) - Stores jobs, logs, and metrics.
    *   **Benchmark DB:** PostgreSQL 17 (pgvector image) - Hosts the actual domain-specific schemas.

## 3. System Architecture

The system is orchestrated via `docker-compose.yml` and consists of four main services connected to a shared network `birdsql-benchmark`:

1.  **`app` (Benchmark Service)**:
    *   **Port:** 8000
    *   **Image:** Built from root `Dockerfile`.
    *   **Role:** Exposes REST API, manages async jobs, and performs evaluation.
    *   **Dependencies:** `db_results`, `db_bench`.
    *   **Mounts:** `./data:/app/data` for access to local datasets.
2.  **`db_results`**:
    *   **Port:** 5433 (mapped to 5432 internally)
    *   **Image:** `pgvector/pgvector:pg17`
    *   **Role:** Persistence layer for `BenchmarkJob` and `BenchmarkResult`.
3.  **`db_bench`**:
    *   **Port:** 5434 (mapped to 5432 internally)
    *   **Image:** `pgvector/pgvector:pg17`
    *   **Role:** The target database for SQL execution.
    *   **Initialization:** Loads dumps from `data/bird-interact-full-dumps` via `init-databases_postgresql.sh`.
4.  **`ai_mock`**:
    *   **Port:** 8001
    *   **Image:** Built from `ai_mock/Dockerfile`.
    *   **Role:** A lightweight FastAPI service that returns dummy SQL responses (`SELECT 1;`) to facilitate end-to-end pipeline testing without an expensive LLM.

## 4. Key Components & Logic

### A. API Layer (`src/api/`)
*   **`benchmark.py`**:
    *   `POST /`: Starts a new benchmark job. Accepts `endpoint_url` (address of the AI agent).
    *   `GET /{id}`: Returns job status and aggregated statistics (Accuracy, Valid SQL Rate, Latency).
    *   `GET /`: Lists all benchmark jobs.
*   **`metadata.py`**:
    *   `GET /`: Lists available databases (e.g., "solar_panel").
    *   `GET /{name}`: Returns schema DDL, column meanings, and knowledge base entries for a specific domain.

### B. Core Services (`src/services/`)
*   **`benchmark_service.py`**:
    *   **Job Management**: Creates and updates `BenchmarkJob` records.
    *   **Execution Loop**: Iterates through the merged dataset.
    *   **Agent Interaction**: Sends HTTP POST requests to the user-provided `endpoint_url` with the `query` and `database` context.
    *   **Result Handling**: Captures generated SQL, latency, and errors.
*   **`evaluation.py`**:
    *   **Dynamic Connection**: Constructs connection strings on-the-fly to query the specific target database (e.g., connecting to `db_bench/solar_panel` context).
    *   **Execution**: Runs both the *Ground Truth SQL* and the *Generated SQL*.
    *   **Comparison**: Compares the result sets (rows) using set logic to determine correctness (order-agnostic).
*   **`metadata_service.py`**:
    *   Reads static files from `data/livesqlbench-base-full-v1` (DDL, JSON descriptions) to provide context about the databases.
*   **`dataset.py`**:
    *   Merges input questions (`livesqlbench_data.jsonl`) with ground truth (`livesqlbench_base_full_v1_gt_kg_testcases_0904.jsonl`).

### C. Data Models (`src/models/`)
*   **`BenchmarkJob`**: Tracks the overall run (ID, status, timestamps, target URL).
*   **`BenchmarkResult`**: Granular record for each test case.
    *   `instance_id`: Unique ID from the dataset.
    *   `generated_sql`: The SQL returned by the AI.
    *   `is_correct`: Boolean result of the evaluation.
    *   `error`: Captures execution errors or HTTP failures.
    *   `latency_ms`: Time taken by the AI to respond.

## 5. Development Workflow

### Setup
1.  **Initialize Environment**:
    ```bash
    make setup  # Downloads DB dumps (GDrive) and Dataset (HuggingFace)
    ```
2.  **Start Infrastructure**:
    ```bash
    make up     # Builds and starts all docker containers
    ```

### Running Locally
*   **Start API**: `make run` (Uses `uv` and `uvicorn` with hot-reload).
*   **Lint/Format**: `make lint`, `make format`.
*   **Clean**: `make clean` (removes cache and venv).

### Testing
*   **End-to-End**: `make test-benchmark`
    *   Triggers a job against the `ai_mock` service.
    *   Verifies that the job is created and processed.
*   **Metadata**: `make test`
    *   Checks if the metadata endpoints are returning data correctly.

## 6. Directory Structure
```
/
├── ai_mock/                # Mock AI service (FastAPI)
│   ├── Dockerfile
│   └── main.py
├── data/                   # Data storage (ignored by git usually)
│   ├── bird-interact-full-dumps/  # SQL dumps for db_bench
│   └── livesqlbench-base-full-v1/ # Metadata and schemas
├── scripts/                # Utility scripts
│   ├── download_resources.sh # Fetches datasets
│   └── parse_data.py         # Parses raw data to JSONL
├── src/
│   ├── api/                # FastAPI Routers
│   ├── db/                 # Database session & config
│   ├── models/             # SQLModel & Pydantic schemas
│   ├── services/           # Business logic (benchmark, evaluation, metadata)
│   ├── config.py           # Application settings
│   └── main.py             # App entry point
├── docker-compose.yml      # Service orchestration
├── Dockerfile              # Main app container definition
├── Makefile                # Task runner
├── pyproject.toml          # Python dependencies & config
├── README.md               # Project documentation
└── .python-version         # Python version lock (3.13)
```

## 7. Current Status & Roadmap

### Completed Features
*   [x] Full async pipeline for benchmarking.
*   [x] Dockerized infrastructure with dual-database setup (Results + Benchmark).
*   [x] Execution Accuracy (EX) evaluation logic.
*   [x] Metadata service for context retrieval.
*   [x] Mock AI integration for pipeline verification.
*   [x] Comprehensive Makefile for dev workflow.
*   [x] Type-safe codebase with `mypy` and `ruff`.

### Upcoming Tasks
1.  **Real Agent Integration**: Connect to actual LLM endpoints (OpenAI, Anthropic, Local models).
2.  **Advanced Error Analysis**: Distinguish between syntax errors, schema errors, and logic errors.
3.  **Visualization**: Build a frontend or CLI dashboard to visualize results in real-time.
4.  **Parallelization**: Optimize the benchmark loop to run queries concurrently (currently sequential).