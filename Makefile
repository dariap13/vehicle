PYTHON := /Users/daria/.local/share/uv/python/cpython-3.11.13-macos-aarch64-none/bin/python3.11

.PHONY: setup lint test api ui download-images docker-up

setup:
	uv sync --python $(PYTHON) --extra dev

lint:
	uv run ruff check

test:
	uv run pytest

api:
	uv run uvicorn app.main:app --reload --port 8000

ui:
	uv run streamlit run frontend/app.py --server.port 8501

download-images:
	uv run python -m app.download_images

docker-up:
	docker compose up --build
