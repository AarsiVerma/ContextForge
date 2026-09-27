"""Configuration system for ContextForge."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="CONTEXTFORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Storage
    database_path: Path = Field(
        default=Path("contextforge.db"),
        description="Path to SQLite database file",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="json",
        description="Log format: json or text",
    )

    # Ranking
    ranking_enabled: bool = Field(default=True, description="Enable ranking")
    freshness_decay_hours: float = Field(
        default=24.0,
        description="Hours after which freshness starts decaying",
    )

    # Compilation
    max_context_tokens: int = Field(
        default=12000,
        description="Maximum tokens in compiled context package",
    )
    section_priority_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "CURRENT TASK": 1.0,
            "VERIFIED EVIDENCE": 0.9,
            "RELEVANT FILES": 0.8,
            "CURRENT HYPOTHESIS": 0.7,
            "REJECTED HYPOTHESES": 0.6,
            "OPEN QUESTIONS": 0.5,
            "PROJECT STATE": 0.4,
            "PROVENANCE": 0.3,
        },
        description="Priority weights for compiler sections",
    )

    # Development
    debug: bool = Field(default=False, description="Enable debug mode")


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config() -> None:
    """Reset the global configuration (mainly for testing)."""
    global _config
    _config = None
