# Root Makefile — convenience targets that wrap ./run.sh
# All real work lives in run.sh and apps/api/Makefile

.PHONY: start setup stop infra clean types test help

help:
	@echo "AutoApply AI — root targets:"
	@echo "  make start       Start everything (docker + api + worker + beat + web)"
	@echo "  make setup       First-time install: deps, playwright, migrations"
	@echo "  make infra       Start only docker services (postgres/redis/minio/...)"
	@echo "  make stop        Tear down all docker services"
	@echo "  make types       Regenerate frontend types from FastAPI's OpenAPI"
	@echo "  make test        Run all tests (Python + TS)"
	@echo "  make clean       Delete node_modules, build outputs, caches"
	@echo ""
	@echo "See GETTING_STARTED.md for the full guide."

start:
	@./run.sh

setup:
	@./run.sh --setup

stop:
	@./run.sh --stop

infra:
	@./run.sh --infra-only

types:
	@pnpm --filter shared-types generate

test:
	@cd apps/api && uv run pytest -v
	@pnpm --filter web type-check

clean:
	@pnpm clean || true
	@rm -rf .turbo apps/web/.next apps/api/.venv apps/api/__pycache__
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"
