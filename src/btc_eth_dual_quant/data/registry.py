"""Machine-readable data lineage registry for M0.

The registry is intentionally broader than the current implementation: all V1.1
section 4.1 datasets must be registered, while `enabled=true` marks the M0
collector surface.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Phase = Literal["M0", "M1", "M2", "M3", "optional"]


class RegistryRecord(BaseModel):
    """One data lineage item from V1.1 section 4.1."""

    model_config = ConfigDict(extra="forbid")

    name: str
    source: str
    endpoint: list[str]
    fields: list[str]
    granularity: str
    history_start: str | None
    retention_limit: str | None
    update_freq: str
    table: str
    validations: list[str]
    fallback: list[str]
    consumers: list[str]
    phase: Phase = "M0"
    enabled: bool = False

    @field_validator("name", "source", "granularity", "update_freq", "table")
    @classmethod
    def _non_empty_str(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value

    @field_validator("endpoint", "fields", "validations", "consumers")
    @classmethod
    def _non_empty_list(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("must not be empty")
        if any(not item.strip() for item in value):
            raise ValueError("items must not be empty")
        return value


class DataRegistry(BaseModel):
    """Collection wrapper for registry records."""

    model_config = ConfigDict(extra="forbid")

    datasets: list[RegistryRecord] = Field(min_length=1)

    @field_validator("datasets")
    @classmethod
    def _unique_names_and_tables(cls, value: list[RegistryRecord]) -> list[RegistryRecord]:
        names = [record.name for record in value]
        if len(names) != len(set(names)):
            raise ValueError("dataset names must be unique")
        tables = [record.table for record in value]
        if len(tables) != len(set(tables)):
            raise ValueError("dataset tables must be unique")
        return value

    def enabled_records(self) -> list[RegistryRecord]:
        return [record for record in self.datasets if record.enabled]

    def by_name(self, name: str) -> RegistryRecord:
        for record in self.datasets:
            if record.name == name:
                return record
        raise KeyError(name)


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Registry is not JSON-compatible YAML and PyYAML is not installed."
            ) from exc
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise ValueError("registry root must be a mapping")
        return loaded


def load_registry(path: str | Path = "data_registry.yaml") -> DataRegistry:
    """Load and validate the registry file."""

    return DataRegistry.model_validate(_load_mapping(Path(path)))
