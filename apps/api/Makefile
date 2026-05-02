.PHONY: dev worker beat migrate lint test seed

dev:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

worker:
	uv run celery -A workers.celery_app worker --loglevel=info --concurrency=4

beat:
	uv run celery -A workers.celery_app beat --loglevel=info

migrate:
	uv run alembic upgrade head

migrate-down:
	uv run alembic downgrade -1

lint:
	uv run ruff check . && uv run ruff format --check .

format:
	uv run ruff check --fix . && uv run ruff format .

test:
	uv run pytest -v

test-unit:
	uv run pytest tests/unit -v

test-integration:
	uv run pytest tests/integration -v --timeout=60

seed:
	uv run python infrastructure/scripts/seed.py
