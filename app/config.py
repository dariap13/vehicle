"""Konfiguracja aplikacji oparta o zmienne środowiskowe."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INITIAL_ENV = dict(os.environ)


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
        dotenv_overrides = self._dotenv_overrides()
        default_db_path = self.project_root / "data" / "vehicles.db"
        self.database_url = self._env_value(
            "DATABASE_URL",
            _sqlite_url(default_db_path),
            dotenv_overrides,
        )
        self.images_dir = _resolve_path(
            self._env_value("IMAGES_DIR", None, dotenv_overrides),
            self.project_root / "images",
        )
        self.log_level = self._env_value("LOG_LEVEL", "INFO", dotenv_overrides).upper()

        self.llm_provider = (
            self._env_value("LLM_PROVIDER", "openai", dotenv_overrides).strip().lower() or "openai"
        )
        defaults = provider_defaults.get(
            self.llm_provider,
            provider_defaults["openai"],
        )

        self.openai_api_key = self._env_value("OPENAI_API_KEY", None, dotenv_overrides) or None
        self.openai_model = self._env_value(
            "OPENAI_MODEL",
            defaults["model"],
            dotenv_overrides,
        )
        self.llm_api_key = (
            self._env_value("LLM_API_KEY", None, dotenv_overrides) or self.openai_api_key
        )
        self.llm_model = (
            self._env_value("LLM_MODEL", None, dotenv_overrides)
            or self.openai_model
            or defaults["model"]
        )
        self.llm_base_url = self._env_value(
            "LLM_BASE_URL",
            defaults["base_url"],
            dotenv_overrides,
        )
        self.llm_site_url = self._env_value(
            "LLM_SITE_URL",
            "http://localhost:8501",
            dotenv_overrides,
        )
        self.llm_app_name = self._env_value(
            "LLM_APP_NAME",
            "Vehicle AI Agent",
            dotenv_overrides,
        )
        self.enable_llm_agent = self._env_value(
            "ENABLE_LLM_AGENT",
            "true",
            dotenv_overrides,
        ).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    @property
    def llm_enabled(self) -> bool:
        return self.enable_llm_agent and bool(self.llm_api_key)

    def _dotenv_overrides(self) -> dict[str, str]:
        env_path = self.project_root / ".env"
        if not env_path.exists():
            return {}
        return {
            key: value
            for key, value in dotenv_values(env_path).items()
            if value is not None
        }

    @staticmethod
    def _env_value(
        key: str,
        default: str | None,
        dotenv_overrides: dict[str, str],
    ) -> str | None:
        current_value = os.getenv(key)
        initial_value = INITIAL_ENV.get(key)

        if current_value is not None and current_value != initial_value:
            return current_value
        if key in dotenv_overrides:
            return dotenv_overrides[key]
        if current_value is not None:
            return current_value
        return default


settings = Settings()
