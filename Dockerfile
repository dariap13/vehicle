FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY requirements.txt ./

RUN uv pip install --system --no-cache -r requirements.txt

COPY app/ ./app/
COPY frontend/ ./frontend/
COPY README.md ./
COPY .env.example ./

RUN mkdir -p ./images ./data
RUN python -m app.download_images || echo "Zdjecia zostana pobrane przy pierwszym uruchomieniu"

EXPOSE 8000 8501

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
