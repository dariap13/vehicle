# Vehicle AI Agent

Aplikacja realizuje pełny przepływ wymagany w zadaniu rekrutacyjnym:
- klasyfikuje obrazy pojazdów przy pomocy pretrenowanego MobileNetV2,
- przyjmuje pytania w języku naturalnym i zamienia je na SQL,
- wykonuje zapytanie na bazie SQLite z 4 tabelami,
- dla każdego zwróconego pojazdu dołącza wynik klasyfikacji jako dodatkowe kolumny,
- wystawia REST API i frontend webowy.

## Architektura

```text
Frontend (HTML) → FastAPI → SQLAlchemy/SQLite
                         → MobileNetV2 (torchvision)
                         → Agent NL→SQL (OpenAI-compatible LLM + deterministyczny fallback)
```

Warstwa LLM jest opcjonalna. Backend obsługuje dostawców kompatybilnych z klientem OpenAI, więc można podpiąć:
- `OpenAI`
- `Groq`
- `OpenRouter`
- inny endpoint OpenAI-compatible przez `LLM_BASE_URL`

Bez klucza projekt nadal działa lokalnie dzięki bezpiecznemu fallbackowi opartemu o reguły.

## Wymagania

- Python 3.11+
- `uv` lub `pip`
- Docker (opcjonalnie)

## Szybki start

### Lokalnie

```bash
make setup          # instalacja zależności
make api            # uruchom backend na http://localhost:8000
```

Lub ręcznie:

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000
```

Baza danych seeduje się automatycznie przy starcie. Frontend dostępny pod http://localhost:8000.

### Zmienna `.env`

Projekt nie wymaga `.env`, ale można skopiować przykład:

```bash
cp .env.example .env
```

Najważniejsze pola:
- `LLM_PROVIDER` – np. `groq`, `openai`, `openrouter`
- `LLM_API_KEY` – klucz do wybranego providera
- `LLM_MODEL` – model dla wybranego providera
- `LLM_BASE_URL` – endpoint API; dla Groq i OpenRouter ma sensowne domyślne wartości
- `ENABLE_LLM_AGENT` – `true` lub `false`

Przykładowy darmowy setup dla Groq:

```env
LLM_PROVIDER=groq
LLM_API_KEY=twoj_klucz
LLM_MODEL=qwen/qwen3-32b
LLM_BASE_URL=https://api.groq.com/openai/v1
ENABLE_LLM_AGENT=true
```

Przykładowy setup dla OpenRouter:

```env
LLM_PROVIDER=openrouter
LLM_API_KEY=twoj_klucz
LLM_MODEL=openrouter/free
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_SITE_URL=http://localhost:8501
LLM_APP_NAME=Vehicle AI Agent
ENABLE_LLM_AGENT=true
```

### Docker Compose

```bash
docker compose up --build
```

Adresy:
- Frontend: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Baza danych

Seed obejmuje wymagane tabele:
- `vehicles`
- `owners`
- `transaction_history`
- `vehicle_images`

Jeśli zewnętrzne URL-e obrazów są chwilowo blokowane, aplikacja tworzy lokalne placeholdery i zachowuje stabilne wyniki klasyfikacji. Projekt uruchamia się lokalnie bez ręcznego ratowania assetów.

Przykładowe dane odpowiadają treści zadania rekrutacyjnego:
- Toyota Corolla
- BMW X5
- MAN TGS
- Honda CBR600RR
- Skoda Octavia

## Endpointy API

| Metoda | Endpoint | Opis |
|--------|----------|------|
| `POST` | `/api/classify` | Klasyfikuj obraz z URL |
| `POST` | `/api/classify/upload` | Klasyfikuj przesłany plik |
| `POST` | `/api/ask` | Pytanie NL → SQL → wynik + klasyfikacja |
| `GET` | `/api/vehicles` | Lista pojazdów (z paginacją) |
| `GET` | `/api/health` | Status usługi |
| `GET` | `/assets/images/{filename}` | Lokalne obrazki seeded demo |

W odpowiedzi `/api/ask` SQL jest jawnie zwracany w JSON oraz logowany po stronie backendu.

## Jak testować

### 1. Testy automatyczne (pytest)

```bash
make test
# lub
uv run pytest -v
```

34 testy pokrywają:
- mapowanie klas ImageNet na typy pojazdów,
- działanie agenta NL→SQL (różne wzorce pytań),
- integrację endpointów API (health, classify, ask),
- edge-case'y: SQL injection, puste pytania, nieznane pytania, walidacja danych,
- paginację endpointu `/api/vehicles`.

Testy nie wymagają klucza LLM — używają trybu reguł i dummy classifiera.

### 2. Ręczne testowanie (curl)

Uruchom backend:

```bash
make api
```

Pytanie do agenta:

```bash
curl -s -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Co ma Kowalski?"}' | python3 -m json.tool
```

Klasyfikacja obrazu z URL:

```bash
curl -s -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"image_url":"http://localhost:8000/assets/images/vehicle_1.jpg"}' | python3 -m json.tool
```

Upload pliku:

```bash
curl -s -X POST http://localhost:8000/api/classify/upload \
  -F "file=@zdjecie.jpg" | python3 -m json.tool
```

Lista pojazdów (z paginacją):

```bash
curl -s "http://localhost:8000/api/vehicles?limit=2&offset=0" | python3 -m json.tool
```

Health check:

```bash
curl -s http://localhost:8000/api/health | python3 -m json.tool
```

### 3. Testowanie przez przeglądarkę

```bash
make api
```

- Frontend: http://localhost:8000 — zakładki Agent / Klasyfikator / Flota
- Swagger UI (interaktywne API): http://localhost:8000/docs

### 4. Testowanie przez Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:8000
- API docs: http://localhost:8000/docs

### 5. Lint

```bash
uv run ruff check
```

## Struktura projektu

```text
app/
  api/routes.py            # endpointy REST
  agent/sql_agent.py       # agent NL→SQL (LLM + fallback)
  classifier/              # klasyfikator MobileNetV2
  config.py                # konfiguracja (.env)
  database.py              # SQLAlchemy setup
  models.py                # ORM: vehicles, owners, transactions, images
  schemas.py               # Pydantic request/response
  seed.py                  # dane startowe
  main.py                  # FastAPI app
frontend/
  index.html               # frontend webowy (dark theme)
tests/                     # pytest (34 testy)
Dockerfile
docker-compose.yml
```
