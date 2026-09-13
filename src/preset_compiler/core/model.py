"""Compiler input domain models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class MaterialPreset:
    """A material preset, independent of its source repository layout."""

    rel: str
    name: str
    pi_code: str
    printer: str
    inherits: str
    values: Mapping[str, Any]
    metadata: Mapping[str, Any]

    @classmethod
    def from_data_file(cls, data_file: Any) -> "MaterialPreset":
        doc = data_file.doc
        metadata_keys = {"name", "pi_code", "printer", "inherits", "pm_method_version"}
        return cls(
            rel=data_file.rel,
            name=doc["name"],
            pi_code=doc["pi_code"],
            printer=doc["printer"],
            inherits=doc["inherits"],
            values={k: v for k, v in doc.items() if k not in metadata_keys},
            metadata={k: doc[k] for k in metadata_keys if k in doc},
        )
