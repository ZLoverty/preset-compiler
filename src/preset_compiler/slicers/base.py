"""Small shared implementation for slicer targets.

The target modules deliberately remain thin.  A caller supplies a profile set
with ``load(name)`` and optionally ``chain(name)``; the compiler never looks
at an installed slicer or at a repository layout.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from ..core import contracts as vp
from ..core.model import MaterialPreset


@dataclass
class SlicerArtifact:
    source: MaterialPreset
    config: dict[str, Any]
    target: str
    format: str = "json"
    findings: list[vp.Finding] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Return a copy suitable for a caller's serializer."""
        return dict(self.config)

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.config, ensure_ascii=False, indent=indent, sort_keys=True) + "\n"

    def to_ini(self, section: str | None = None) -> str:
        """Serialize the flat config as a Prusa-family INI preset."""
        section = section or f"filament:{self.config.get('name', self.source.name)}"
        lines = [f"[{section}]\n"]
        for key, value in self.config.items():
            if key in {"name", "type"}:
                continue
            if isinstance(value, list):
                value = ";".join(str(item) for item in value)
            elif value is None:
                value = "nil"
            lines.append(f"{key} = {value}\n")
        return "".join(lines)


class ProfileResolver:
    """Resolve the common ``inherits``/``include`` profile convention."""

    def __init__(self, profile_set: Any, defaults: Mapping[str, Any] | None = None,
                 preserve_meta_keys: set[str] | None = None):
        self.profile_set = profile_set
        self.defaults = defaults or {}
        self.preserve_meta_keys = preserve_meta_keys or set()

    def chain(self, name: str) -> list[str]:
        if hasattr(self.profile_set, "chain"):
            return list(self.profile_set.chain(name))
        result: list[str] = []
        seen: set[str] = set()
        current: str | None = name
        while current:
            if current in seen:
                raise ValueError(f"继承链成环：{' → '.join(result + [current])}")
            seen.add(current)
            result.append(current)
            current = self.profile_set.load(current).get("inherits") or None
        return result

    def resolve(self, name: str) -> dict[str, Any]:
        return self._flatten(name)

    def _flatten(self, name: str, stack: tuple[str, ...] = ()) -> dict[str, Any]:
        if name in stack:
            raise ValueError(f"继承链成环：{' → '.join(stack + (name,))}")
        doc = self.profile_set.load(name)
        result = self._flatten(doc["inherits"], stack + (name,)) if doc.get("inherits") else {}
        for include in vp.include_names(doc):
            included = self._flatten(include, stack + (name,))
            for key, value in included.items():
                if key not in vp.PROFILE_META_KEYS or key in self.preserve_meta_keys:
                    result[key] = value
        result.update({key: value for key, value in doc.items()
                       if key not in vp.PROFILE_META_KEYS or key in self.preserve_meta_keys})
        return result


class JsonSlicerCompiler:
    """Base for slicers whose native filament preset is a JSON object."""

    target = ""

    def __init__(self, profile_set: Any, defaults: Mapping[str, Any] | None = None,
                 version: str | None = None):
        self.profile_set = profile_set
        self.resolver = ProfileResolver(
            profile_set, defaults,
            preserve_meta_keys={"compatible_printers", "compatible_printers_condition"},
        )
        self.version = version

    @staticmethod
    def encode_value(chain_value: Any, value: Any) -> Any:
        value = vp.norm(value)
        if isinstance(chain_value, list):
            text = value if isinstance(value, str) else str(value)
            return [text] * len(chain_value)
        return value

    def compile(self, source: MaterialPreset) -> SlicerArtifact:
        config = self.resolver.resolve(source.inherits)
        findings: list[vp.Finding] = []
        for key, value in source.values.items():
            if key not in config:
                findings.append(vp.Finding(source.rel, key, "build.encode",
                    "这个键不在目标继承链上，未写入产物。"))
                continue
            config[key] = self.encode_value(config[key], value)
        self.apply_identity(config, source)
        return SlicerArtifact(source, config, self.target, "json", findings)

    def apply_identity(self, config: dict[str, Any], source: MaterialPreset) -> None:
        config.update({
            "type": "filament",
            "name": source.name,
            "inherits": "",
            "from": "User",
        })
        if self.version is not None:
            config["version"] = self.version


class PrusaSlicerCompiler(JsonSlicerCompiler):
    """Compile the shared model to a Prusa-family filament config.

    ``config`` remains a flat mapping for consistency; call ``to_ini()`` on
    the returned artifact when writing the native ``.ini`` representation.
    """

    target = "PrusaSlicer"

    def compile(self, source: MaterialPreset) -> SlicerArtifact:
        artifact = super().compile(source)
        artifact.format = "ini"
        return artifact
