.PHONY: run build test lint clean format setup

run:
	uv run uvicorn src.main:app --reload

build:
	docker compose build

setup:
	./scripts/download_resources.sh

test:
	@echo "Testing Metadata List..."
	@curl -s -f http://localhost:8000/metadata/ | jq -e '. | length > 0' > /dev/null
	@echo "Testing Metadata for solar_panel..."
	@curl -s -f http://localhost:8000/metadata/solar_panel | jq -e '.database_name == "solar_panel"' > /dev/null
	@echo "✅ API Metadata tests passed."

test-benchmark:
	@echo "Triggering Benchmark with mock..."
	@curl -s -f -X POST http://localhost:8000/benchmark/ \
		-H "Content-Type: application/json" \
		-d '{"endpoint_url": "http://ai_mock:8001/"}' | jq .
	@echo "✅ Benchmark triggered successfully."

up:
	docker compose up -d --build

down:
	docker compose down

lint:
	uv run ruff check .
	uv run mypy .

format:
	uv run ruff check --fix .
	uv run ruff format .

clean:
	rm -rf .venv
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -r {} +
