FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy the project definition
COPY pyproject.toml uv.lock ./

# Install the project's dependencies
RUN uv sync --frozen --no-install-project

# Copy the source code
COPY . .

# Install the project
RUN uv sync --frozen

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
