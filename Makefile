.PHONY: setup lint test api download-images docker-up

setup:
	uv sync --extra dev

lint:
	uv run ruff check

test:
	uv run pytest -v

api:
	uv run uvicorn app.main:app --reload --port 8000

download-images:
	uv run python -m app.download_images

docker-up:
	docker compose up --build
