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
                    -> Agent NL→SQL (OpenAI optional + deterministic fallback)
```

Klucz OpenAI jest opcjonalny. Jezeli `OPENAI_API_KEY` jest ustawiony, agent najpierw probuje wygenerowac SQL przez OpenAI Responses API. Bez klucza projekt nadal dziala lokalnie dzieki bezpiecznemu fallbackowi opartemu o reguly.

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
- `OPENAI_API_KEY` - opcjonalne
- `OPENAI_MODEL` - opcjonalne, domyslnie `gpt-4o-mini`
- `ENABLE_LLM_AGENT` - `true` lub `false`

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
