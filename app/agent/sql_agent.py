"""Agent tłumaczący pytania natural language na bezpieczne SQL.

Uproszczenia:
- Tryb regułowy (fallback) oparty o pattern matching — pokrywa najczestsze wzorce
  pytan z zadania, ale nie obsluguje dowolnych zapytan. W produkcji: fine-tuning
  LLM na domenowych przykladach lub few-shot prompting z wiekszym bankiem pytan.
- Walidacja SQL ograniczona do blacklisty slow kluczowych. W produkcji lepiej:
  parsowanie AST zapytania (np. sqlglot) i whitelisting dozwolonych operacji.
- Brak historii konwersacji — kazde pytanie traktowane niezaleznie.
  Mozna dodac kontekst sesji dla pytan wieloetapowych.
- Prompt systemowy zawiera hardcoded schemat bazy. W produkcji lepiej generowac
  go dynamicznie z metadanych SQLAlchemy (inspection).
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BuiltQuery:
    sql_query: str
    explanation: str
    params: dict[str, Any]


@dataclass(slots=True)
class AgentResult:
    sql_query: str
    explanation: str
    columns: list[str]
    rows: list[dict[str, Any]]
    error: str | None = None


class SQLAgent:
    """Bezpieczny agent SQL z opcjonalnym wsparciem OpenAI i lokalnym fallbackiem."""

    def __init__(self) -> None:
        settings.reload()
        self._provider = settings.llm_provider
        self._model = settings.llm_model
        self._client = self._build_client()

    @property
    def is_available(self) -> bool:
        return True

    @property
    def mode(self) -> str:
        return f"{self._provider}+fallback" if self._client else "rule-based"

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str | None:
        return self._model if self._client else None

    def ask(self, question: str, db: Session) -> AgentResult:
        cleaned_question = question.strip()
        if not cleaned_question:
            return AgentResult("", "", [], [], "Pytanie nie moze byc puste.")

        built_query = self._build_with_llm(cleaned_question)
        if built_query is None:
            built_query = self._build_rule_based_query(cleaned_question, db)

        if built_query is None:
            return AgentResult(
                "",
                "Nie rozpoznano intentu pytania.",
                [],
                [],
                (
                    "Nie rozumiem pytania. Sprobuj zapytac o wlasciciela, "
                    "cene, dostepnosc, marke/model albo rok transakcji."
                ),
            )

        if not self._is_safe_sql(built_query.sql_query):
            return AgentResult(
                built_query.sql_query,
                built_query.explanation,
                [],
                [],
                "Wygenerowane zapytanie nie przeszlo walidacji bezpieczenstwa.",
            )

        try:
            result = db.execute(text(built_query.sql_query), built_query.params)
            columns = list(result.keys())
            rows = [dict(row._mapping) for row in result]
            return AgentResult(built_query.sql_query, built_query.explanation, columns, rows)
        except Exception as exc:
            logger.exception("Blad wykonania zapytania SQL")
            return AgentResult(
                built_query.sql_query,
                built_query.explanation,
                [],
                [],
                f"Blad wykonania zapytania: {exc}",
            )

    def _build_client(self) -> OpenAI | None:
        if not (settings.llm_enabled and OpenAI):
            return None

        default_headers: dict[str, str] = {}
        if self._provider == "openrouter":
            default_headers["HTTP-Referer"] = settings.llm_site_url or "http://localhost:8000"
            default_headers["X-Title"] = settings.llm_app_name

        return OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            default_headers=default_headers or None,
            max_retries=0,
        )

    def _build_with_llm(self, question: str) -> BuiltQuery | None:
        if self._client is None:
            return None

        system_prompt = """
You translate Polish user questions into a single safe SQLite SELECT query.
Return ONLY valid JSON with keys: sql_query, explanation.

Schema:
- vehicles(vehicle_id, brand, model, year, price DECIMAL, availability TEXT)
  availability values: 'available' or 'sold' (text, NOT boolean/integer)
- owners(owner_id, first_name, last_name, city)
- transaction_history(
    transaction_id, vehicle_id, buyer_id, seller_id NULLABLE, transaction_date DATE, price DECIMAL
  )
  seller_id is NULL when bought from a dealer (first purchase)
- vehicle_images(image_id, vehicle_id, image_url)

Rules:
- Return a single read-only query starting with SELECT or WITH.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, ATTACH, PRAGMA, CREATE, REPLACE.
- Prefer parameter-free SQL because the API executes the generated SQL directly.
- If the query returns vehicles, include vehicle_id and image_url
  via LEFT JOIN vehicle_images.
- Use LEFT JOIN vehicle_images vi ON vi.vehicle_id = v.vehicle_id when appropriate.
- Use LEFT JOIN (not JOIN) for seller in transaction_history because seller_id can be NULL.
- availability is TEXT: use availability = 'available' or availability = 'sold', never 1 or 0.
- Use COLLATE NOCASE for case-insensitive text matching.
- Known data (ASCII, no diacritics in DB):
  Owners: Kowalski, Nowak, Zielinski, Wisniewska. Cities: Warszawa, Krakow, Gdansk, Poznan.
  Vehicles: Toyota Corolla, BMW X5, MAN TGS, Honda CBR600RR, Skoda Octavia.
- Keep explanation short, in Polish.
""".strip()

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
            )
            message = response.choices[0].message.content or ""
            payload = self._extract_json_payload(message)
            parsed = json.loads(payload)
            sql_query = str(parsed["sql_query"]).strip()
            explanation = str(
                parsed.get("explanation", "Zapytanie wygenerowane przez model."),
            ).strip()
            return BuiltQuery(sql_query=sql_query, explanation=explanation, params={})
        except Exception as exc:
            logger.warning("LLM fallback do trybu regułowego (%s): %s", self._provider, exc)
            return None

    def _build_rule_based_query(self, question: str, db: Session) -> BuiltQuery | None:
        normalized = _normalize_text(question)
        owner = _match_owner(question, db)
        vehicle = _match_vehicle(question, db)
        year = _extract_year(normalized)
        amount = _extract_amount(normalized)

        if "ile" in normalized and any(
            keyword in normalized for keyword in {"dostep", "dostęp"}
        ):
            return BuiltQuery(
                """
                SELECT COUNT(*) AS available_vehicle_count
                FROM vehicles
                WHERE availability = 'available'
                """.strip(),
                "Licze pojazdy oznaczone jako dostepne.",
                {},
            )

        if owner and any(
            keyword in normalized for keyword in {"byl", "byla", "kiedykolwiek"}
        ):
            return BuiltQuery(
                """
                SELECT DISTINCT
                    v.vehicle_id,
                    v.brand,
                    v.model,
                    v.year,
                    v.price,
                    v.availability,
                    vi.image_url
                FROM vehicles v
                JOIN transaction_history t ON t.vehicle_id = v.vehicle_id
                LEFT JOIN vehicle_images vi ON vi.vehicle_id = v.vehicle_id
                WHERE t.buyer_id = :owner_id
                ORDER BY v.brand, v.model
                """.strip(),
                f"Pokazuje pojazdy, ktore kiedykolwiek nalezaly do {owner['display_name']}.",
                {"owner_id": owner["owner_id"]},
            )

        if owner and any(
            keyword in normalized
            for keyword in {"co ma", "jakie ma", "nalezy do", "należą do"}
        ):
            return BuiltQuery(
                """
                WITH latest_owner AS (
                    SELECT
                        t.vehicle_id,
                        t.buyer_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY t.vehicle_id
                            ORDER BY t.transaction_date DESC, t.transaction_id DESC
                        ) AS rn
                    FROM transaction_history t
                )
                SELECT
                    v.vehicle_id,
                    v.brand,
                    v.model,
                    v.year,
                    v.price,
                    v.availability,
                    o.first_name || ' ' || o.last_name AS current_owner,
                    vi.image_url
                FROM vehicles v
                JOIN latest_owner lo ON lo.vehicle_id = v.vehicle_id AND lo.rn = 1
                JOIN owners o ON o.owner_id = lo.buyer_id
                LEFT JOIN vehicle_images vi ON vi.vehicle_id = v.vehicle_id
                WHERE o.owner_id = :owner_id
                ORDER BY v.brand, v.model
                """.strip(),
                f"Pokazuje aktualne pojazdy nalezace do {owner['display_name']}.",
                {"owner_id": owner["owner_id"]},
            )

        if vehicle and any(
            keyword in normalized for keyword in {"do kogo poszlo", "kto ma", "czyje"}
        ):
            return BuiltQuery(
                """
                WITH latest_owner AS (
                    SELECT
                        t.vehicle_id,
                        t.buyer_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY t.vehicle_id
                            ORDER BY t.transaction_date DESC, t.transaction_id DESC
                        ) AS rn
                    FROM transaction_history t
                )
                SELECT
                    v.vehicle_id,
                    v.brand,
                    v.model,
                    o.first_name || ' ' || o.last_name AS current_owner,
                    o.city AS owner_city,
                    vi.image_url
                FROM vehicles v
                JOIN latest_owner lo ON lo.vehicle_id = v.vehicle_id AND lo.rn = 1
                JOIN owners o ON o.owner_id = lo.buyer_id
                LEFT JOIN vehicle_images vi ON vi.vehicle_id = v.vehicle_id
                WHERE v.vehicle_id = :vehicle_id
                """.strip(),
                f"Sprawdzam, kto jest aktualnym wlascicielem pojazdu {vehicle['display_name']}.",
                {"vehicle_id": vehicle["vehicle_id"]},
            )

        if vehicle and any(
            keyword in normalized
            for keyword in {"kupow", "sprzedaw", "historia", "transakc"}
        ):
            return BuiltQuery(
                """
                SELECT
                    t.transaction_id,
                    t.transaction_date,
                    v.vehicle_id,
                    v.brand,
                    v.model,
                    b.first_name || ' ' || b.last_name AS buyer,
                    COALESCE(s.first_name || ' ' || s.last_name, 'salon') AS seller,
                    t.price AS transaction_price,
                    vi.image_url
                FROM transaction_history t
                JOIN vehicles v ON v.vehicle_id = t.vehicle_id
                JOIN owners b ON b.owner_id = t.buyer_id
                LEFT JOIN owners s ON s.owner_id = t.seller_id
                LEFT JOIN vehicle_images vi ON vi.vehicle_id = v.vehicle_id
                WHERE v.vehicle_id = :vehicle_id
                ORDER BY t.transaction_date ASC, t.transaction_id ASC
                """.strip(),
                f"Pokazuje historie transakcji dla {vehicle['display_name']}.",
                {"vehicle_id": vehicle["vehicle_id"]},
            )

        if year and any(
            keyword in normalized
            for keyword in {"kupiono", "kupil", "kupila", "kupił", "kupiła", "transakc"}
        ):
            return BuiltQuery(
                """
                SELECT
                    t.transaction_id,
                    t.transaction_date,
                    v.vehicle_id,
                    v.brand,
                    v.model,
                    b.first_name || ' ' || b.last_name AS buyer,
                    COALESCE(s.first_name || ' ' || s.last_name, 'salon') AS seller,
                    t.price AS transaction_price,
                    vi.image_url
                FROM transaction_history t
                JOIN vehicles v ON v.vehicle_id = t.vehicle_id
                JOIN owners b ON b.owner_id = t.buyer_id
                LEFT JOIN owners s ON s.owner_id = t.seller_id
                LEFT JOIN vehicle_images vi ON vi.vehicle_id = v.vehicle_id
                WHERE strftime('%Y', t.transaction_date) = :year
                ORDER BY t.transaction_date ASC, t.transaction_id ASC
                """.strip(),
                f"Pokazuje transakcje z roku {year}.",
                {"year": str(year)},
            )

        if amount is not None and any(
            keyword in normalized
            for keyword in {"powyzej", "ponad", "co najmniej", "drozsze"}
        ):
            return BuiltQuery(
                """
                SELECT
                    v.vehicle_id,
                    v.brand,
                    v.model,
                    v.year,
                    v.price,
                    v.availability,
                    vi.image_url
                FROM vehicles v
                LEFT JOIN vehicle_images vi ON vi.vehicle_id = v.vehicle_id
                WHERE v.price > :amount
                ORDER BY v.price DESC
                """.strip(),
                f"Pokazuje pojazdy drozsze niz {amount:.0f} PLN.",
                {"amount": amount},
            )

        if amount is not None and any(
            keyword in normalized
            for keyword in {"ponizej", "poniżej", "mniej niz", "tansze"}
        ):
            return BuiltQuery(
                """
                SELECT
                    v.vehicle_id,
                    v.brand,
                    v.model,
                    v.year,
                    v.price,
                    v.availability,
                    vi.image_url
                FROM vehicles v
                LEFT JOIN vehicle_images vi ON vi.vehicle_id = v.vehicle_id
                WHERE v.price < :amount
                ORDER BY v.price ASC
                """.strip(),
                f"Pokazuje pojazdy tansze niz {amount:.0f} PLN.",
                {"amount": amount},
            )

        if any(
            keyword in normalized
            for keyword in {"wszystkie pojazdy", "lista pojazdow", "lista pojazdów"}
        ):
            return BuiltQuery(
                """
                SELECT
                    v.vehicle_id,
                    v.brand,
                    v.model,
                    v.year,
                    v.price,
                    v.availability,
                    vi.image_url
                FROM vehicles v
                LEFT JOIN vehicle_images vi ON vi.vehicle_id = v.vehicle_id
                ORDER BY v.brand, v.model
                """.strip(),
                "Pokazuje pelna liste pojazdow.",
                {},
            )

        return None

    @staticmethod
    def _strip_code_fences(payload: str) -> str:
        stripped = payload.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
            stripped = re.sub(r"```$", "", stripped).strip()
        return stripped

    @classmethod
    def _extract_json_payload(cls, payload: str) -> str:
        stripped = cls._strip_code_fences(payload)
        if stripped.startswith("{") and stripped.endswith("}"):
            return stripped

        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        return match.group(0).strip() if match else stripped

    @staticmethod
    def _is_safe_sql(sql_query: str) -> bool:
        normalized = sql_query.strip().lower()
        if not normalized.startswith(("select", "with")):
            return False

        forbidden = {
            " insert ",
            " update ",
            " delete ",
            " drop ",
            " alter ",
            " attach ",
            " pragma ",
            " create ",
            " replace ",
        }
        padded = f" {normalized} "
        return not any(keyword in padded for keyword in forbidden)


def _normalize_text(value: str) -> str:
    simplified = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    simplified = simplified.lower()
    simplified = re.sub(r"\s+", " ", simplified)
    return simplified.strip()


def _extract_year(question: str) -> int | None:
    match = re.search(r"\b(19\d{2}|20\d{2}|21\d{2})\b", question)
    return int(match.group(1)) if match else None


def _extract_amount(question: str) -> float | None:
    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(k|tys|tys\.|tysiecy|tysiac(?:e|y)?|000)?",
        question,
    )
    if not match:
        return None

    value = float(match.group(1).replace(",", "."))
    suffix = (match.group(2) or "").strip(".")
    if suffix in {"k", "tys", "tysiecy", "tysiace", "tysiacy", "000"}:
        value *= 1000
    return value


def _match_owner(question: str, db: Session) -> dict[str, Any] | None:
    rows = db.execute(
        text("SELECT owner_id, first_name, last_name FROM owners ORDER BY owner_id")
    )
    normalized_question = _normalize_text(question)
    candidates: list[dict[str, Any]] = []

    for row in rows:
        mapping = dict(row._mapping)
        full_name = f"{mapping['first_name']} {mapping['last_name']}"
        full_name_normalized = _normalize_text(full_name)
        last_name_normalized = _normalize_text(mapping["last_name"])
        if (
            full_name_normalized in normalized_question
            or last_name_normalized in normalized_question
        ):
            candidates.append(
                {
                    "owner_id": mapping["owner_id"],
                    "display_name": full_name,
                    "score": max(len(full_name_normalized), len(last_name_normalized)),
                }
            )

    if not candidates:
        return None

    return max(candidates, key=lambda candidate: candidate["score"])


def _match_vehicle(question: str, db: Session) -> dict[str, Any] | None:
    rows = db.execute(
        text("SELECT vehicle_id, brand, model FROM vehicles ORDER BY vehicle_id")
    )
    normalized_question = _normalize_text(question)
    candidates: list[dict[str, Any]] = []

    for row in rows:
        mapping = dict(row._mapping)
        full_name = f"{mapping['brand']} {mapping['model']}"
        full_name_normalized = _normalize_text(full_name)
        model_normalized = _normalize_text(mapping["model"])
        if full_name_normalized in normalized_question or model_normalized in normalized_question:
            candidates.append(
                {
                    "vehicle_id": mapping["vehicle_id"],
                    "display_name": full_name,
                    "score": max(len(full_name_normalized), len(model_normalized)),
                }
            )

    if not candidates:
        return None

    return max(candidates, key=lambda candidate: candidate["score"])


@lru_cache(maxsize=1)
def get_agent() -> SQLAgent:
    return SQLAgent()


def reset_agent_cache() -> None:
    get_agent.cache_clear()
