"""Konfiguracja aplikacji oparta o zmienne środowiskowe."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolve_path(raw_value: str | None, default: Path) -> Path:
    value = raw_value.strip() if raw_value else ""
    path = Path(value) if value else default
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve()}"


@dataclass(slots=True)
class Settings:
    project_root: Path = field(default_factory=lambda: PROJECT_ROOT)
    database_url: str = field(init=False)
    images_dir: Path = field(init=False)
    log_level: str = field(init=False)
    llm_provider: str = field(init=False)
    llm_api_key: str | None = field(init=False)
    llm_model: str = field(init=False)
    llm_base_url: str | None = field(init=False)
    llm_site_url: str | None = field(init=False)
    llm_app_name: str = field(init=False)
    openai_api_key: str | None = field(init=False)
    openai_model: str = field(init=False)
    enable_llm_agent: bool = field(init=False)

    def __post_init__(self) -> None:
        self.reload()

    def reload(self) -> None:
        provider_defaults = {
            "openai": {
                "model": "gpt-4o-mini",
                "base_url": None,
            },
            "groq": {
                "model": "qwen/qwen3-32b",
                "base_url": "https://api.groq.com/openai/v1",
            },
            "openrouter": {
                "model": "openrouter/free",
                "base_url": "https://openrouter.ai/api/v1",
            },
        }
        default_db_path = self.project_root / "data" / "vehicles.db"
        self.database_url = os.getenv("DATABASE_URL") or _sqlite_url(default_db_path)
        self.images_dir = _resolve_path(os.getenv("IMAGES_DIR"), self.project_root / "images")
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").strip().lower() or "openai"
        defaults = provider_defaults.get(
            self.llm_provider,
            provider_defaults["openai"],
        )

        self.openai_api_key = os.getenv("OPENAI_API_KEY") or None
        self.openai_model = os.getenv("OPENAI_MODEL", defaults["model"])
        self.llm_api_key = os.getenv("LLM_API_KEY") or self.openai_api_key
        self.llm_model = os.getenv("LLM_MODEL") or self.openai_model or defaults["model"]
        self.llm_base_url = os.getenv("LLM_BASE_URL") or defaults["base_url"]
        self.llm_site_url = os.getenv("LLM_SITE_URL") or "http://localhost:8501"
        self.llm_app_name = os.getenv("LLM_APP_NAME", "Vehicle AI Agent")
        self.enable_llm_agent = os.getenv("ENABLE_LLM_AGENT", "true").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    @property
    def llm_enabled(self) -> bool:
        return self.enable_llm_agent and bool(self.llm_api_key)


settings = Settings()
