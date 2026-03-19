# Vehicle AI Agent

Aplikacja realizuje pełny przeplyw wymagany w zadaniu:
- klasyfikuje obrazy pojazdow przy pomocy pretrained MobileNetV2,
- przyjmuje pytania w jezyku naturalnym i zamienia je na SQL,
- wykonuje zapytanie na bazie SQLite z 4 tabelami,
- dla kazdego zwroconego pojazdu dolacza wynik klasyfikacji jako dodatkowe kolumny,
- wystawia REST API i frontend webowy.

## Architektura

```text
Frontend (HTML) -> FastAPI -> SQLAlchemy/SQLite
                          -> MobileNetV2 (torchvision)
                          -> Agent NL->SQL (OpenAI-compatible LLM + deterministic fallback)
```

Warstwa LLM jest opcjonalna. Backend obsluguje dostawcow kompatybilnych z klientem OpenAI, wiec mozna podpiac:
- `OpenAI`
- `Groq`
- `OpenRouter`
- inny endpoint OpenAI-compatible przez `LLM_BASE_URL`

Bez klucza projekt nadal dziala lokalnie dzieki bezpiecznemu fallbackowi opartemu o reguly.

## Wymagania

- Python 3.11+
- `uv` lub `pip`
- Docker opcjonalnie

## Szybki start

### Lokalnie

```bash
make setup          # instalacja zaleznosci
make api            # uruchom backend na http://localhost:8000
```

Lub recznie:

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000
```

Baza danych seeduje sie automatycznie przy starcie. Frontend dostepny pod http://localhost:8000.

### Zmienna `.env`

Projekt nie wymaga `.env`, ale mozna skopiowac przyklad:

```bash
cp .env.example .env
```

Najwazniejsze pola:
- `LLM_PROVIDER` - np. `groq`, `openai`, `openrouter`
- `LLM_API_KEY` - klucz do wybranego providera
- `LLM_MODEL` - model dla wybranego providera
- `LLM_BASE_URL` - endpoint API; dla Groq i OpenRouter ma sensowne domyslne wartosci
- `ENABLE_LLM_AGENT` - `true` lub `false`

Przykladowy darmowy setup dla Groq:

```env
LLM_PROVIDER=groq
LLM_API_KEY=twoj_klucz
LLM_MODEL=qwen/qwen3-32b
LLM_BASE_URL=https://api.groq.com/openai/v1
ENABLE_LLM_AGENT=true
```

Przykladowy setup dla OpenRouter free router:

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

Jesli zewnetrzne URL-e obrazow sa chwilowo blokowane, aplikacja tworzy lokalne placeholdery dla seeded demo i zachowuje stabilne wyniki dla danych katalogowych. Dzięki temu projekt nadal uruchamia sie lokalnie bez recznego ratowania assetow.

Przykladowe dane odpowiadaja tresci zadania rekrutacyjnego, w tym:
- Toyota Corolla
- BMW X5
- MAN TGS
- Honda CBR600RR
- Skoda Octavia

## Endpointy API

| Metoda | Endpoint | Opis |
|--------|----------|------|
| `POST` | `/api/classify` | Klasyfikuj obraz z URL |
| `POST` | `/api/classify/upload` | Klasyfikuj przeslany plik |
| `POST` | `/api/ask` | Pytanie natural language -> SQL -> wynik + klasyfikacja |
| `GET` | `/api/vehicles` | Lista pojazdow |
| `GET` | `/api/health` | Status uslugi |
| `GET` | `/assets/images/{filename}` | Lokalne obrazki seeded demo |

W odpowiedzi `/api/ask` SQL jest jawnie zwracany w JSON oraz logowany po stronie backendu.

## Testowanie

### Testy automatyczne (pytest)

```bash
make test
# lub
uv run pytest -v
```

34 testy pokrywaja:
- mapowanie klas ImageNet na typy pojazdow,
- dzialanie agenta NL->SQL (rozne wzorce pytan),
- integracje endpointow API (health, classify, ask),
- edge-case'y: SQL injection, puste pytania, nieznane pytania, walidacja danych,
- paginacje endpointu `/api/vehicles`.

Testy nie wymagaja klucza LLM — uzywaja trybu regul i dummy classifiera.

### Reczne testowanie (curl)

Uruchom backend:

```bash
make api
```

Pytanie do agenta:

```bash
curl -s -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"co ma Kowalski?"}' | python3 -m json.tool
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

Lista pojazdow (z paginacja):

```bash
curl -s "http://localhost:8000/api/vehicles?limit=2&offset=0" | python3 -m json.tool
```

Health check:

```bash
curl -s http://localhost:8000/api/health | python3 -m json.tool
```

### Testowanie przez przegladarke

```bash
make api
```

- Frontend: http://localhost:8000
- Swagger UI (interaktywne API): http://localhost:8000/docs

### Testowanie przez Docker

```bash
docker compose up --build
```

Frontend: http://localhost:8000, API docs: http://localhost:8000/docs

## Finalna checklista przed wysylka

1. Uruchom testy:

```bash
uv run pytest -v
```

2. Zweryfikuj lint:

```bash
uv run ruff check
```

3. Szybki smoke test API:

```bash
curl -s http://localhost:8000/api/health | python3 -m json.tool
curl -s -X POST http://localhost:8000/api/ask -H "Content-Type: application/json" -d '{"question":"co ma Kowalski?"}' | python3 -m json.tool
```

4. Upewnij sie, ze repo nie zawiera lokalnych artefaktow:
- brak `.env` w commitach,
- brak plikow tymczasowych i duplikatow,
- czysty `git status`.

## Struktura projektu

```text
app/
  api/routes.py            # endpointy REST
  agent/sql_agent.py       # agent NL->SQL (LLM + fallback)
  classifier/              # klasyfikator MobileNetV2
  config.py                # konfiguracja (.env)
  database.py              # SQLAlchemy setup
  models.py                # ORM: vehicles, owners, transactions, images
  schemas.py               # Pydantic request/response
  seed.py                  # dane startowe
  main.py                  # FastAPI app
frontend/
  index.html               # frontend webowy
tests/                     # pytest (34 testy)
Dockerfile
docker-compose.yml
```
