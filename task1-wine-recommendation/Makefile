.PHONY: dev test lint format

dev:
	uvicorn app.main:app --reload --port 8000

test:
	pytest tests/ -v

lint:
	ruff check app/ tests/

format:
	ruff format app/ tests/
