# Vehicle AI Agent

Aplikacja realizuje pełny przeplyw wymagany w zadaniu:
- klasyfikuje obrazy pojazdow przy pomocy pretrained MobileNetV2,
- przyjmuje pytania w jezyku naturalnym i zamienia je na SQL,
- wykonuje zapytanie na bazie SQLite z 4 tabelami,
- dla kazdego zwroconego pojazdu dolacza wynik klasyfikacji jako dodatkowe kolumny,
- wystawia REST API i prosty frontend Streamlit.

## Architektura

```text
Streamlit -> FastAPI -> SQLAlchemy/SQLite
                    -> MobileNetV2 (torchvision)
                    -> Agent NL->SQL (OpenAI-compatible provider optional + deterministic fallback)
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
uv sync --extra dev
uv run python -m app.download_images
uv run uvicorn app.main:app --reload --port 8000
```

W osobnym terminalu:

```bash
uv run streamlit run frontend/app.py --server.port 8501
```

Aplikacja seeduje baze danych automatycznie przy starcie backendu.

Mozesz tez uzywac prostszych komend:

```bash
make setup
make lint
make test
make api
make ui
```

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
- Frontend: http://localhost:8501
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

## Przykladowe wywolania

```bash
curl -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"image_url":"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/2019_Toyota_Corolla_Hybrid_1.8.jpg/640px-2019_Toyota_Corolla_Hybrid_1.8.jpg"}'
```

```bash
curl -X POST http://localhost:8000/api/classify/upload \
  -F "file=@my_car.jpg"
```

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"co ma Kowalski?"}'
```

W odpowiedzi `/api/ask` SQL jest jawnie zwracany oraz logowany po stronie backendu.

## Testy

```bash
uv run pytest
```

Testy pokrywaja:
- logike mapowania klas ImageNet -> typ pojazdu,
- dzialanie agenta NL→SQL,
- integracje endpointow API.

## Provider recommendation

Do tego projektu najpraktyczniejsze sa dwa warianty:
- `Groq` - najprostszy do demo, bardzo szybki i latwy do podpietia przez OpenAI-compatible API.
- `OpenRouter` - najlepszy, jezeli chcesz tanio lub darmowo przelaczac sie miedzy wieloma modelami bez zmiany integracji.

## Struktura projektu

```text
app/
  api/routes.py
  agent/sql_agent.py
  classifier/vehicle_classifier.py
  config.py
  database.py
  download_images.py
  main.py
  models.py
  schemas.py
  seed.py
frontend/app.py
tests/
Dockerfile
docker-compose.yml
requirements.txt
```
