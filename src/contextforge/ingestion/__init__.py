"""Ingestion interface."""

from contextforge.ingestion.base import ContextSource
from contextforge.ingestion.normalize import Normalizer, normalize_sources
from contextforge.ingestion.sources import (
    FileSource,
    TaskSource,
    TestResultSource,
    TextSource,
    ToolOutputSource,
)

__all__ = [
    "ContextSource",
    "FileSource",
    "TextSource",
    "TaskSource",
    "ToolOutputSource",
    "TestResultSource",
    "Normalizer",
    "normalize_sources",
]
