.PHONY: setup test run docker

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"

test:
	. .venv/bin/activate && pytest

run:
	. .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000

docker:
	docker compose up --build

