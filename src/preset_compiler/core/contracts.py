"""Slicer-neutral contracts used by the compiler and its callers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


class ProfileSetError(RuntimeError):
    """The requested upstream profile set is unavailable."""


class ChainError(RuntimeError):
    """An upstream profile inheritance chain cannot be resolved."""


@dataclass(frozen=True)
class Finding:
    """A structured compiler diagnostic; presentation belongs to the caller."""

    path: str
    key: str
    rule: str
    message: str


PROFILE_META_KEYS = frozenset({
    "type", "name", "inherits", "from", "setting_id", "filament_id",
    "instantiation", "description", "include", "version", "alias",
    "filament_settings_id", "compatible_printers",
})

DATA_KEYS = (
    "textured_plate_temp", "nozzle_temperature", "fan_cooling_layer_time",
    "fan_max_speed", "fan_min_speed", "slow_down_layer_time",
    "filament_flow_ratio", "filament_max_volumetric_speed",
    "filament_density", "temperature_vitrification",
    "filament_retraction_length", "pressure_advance",
)


def include_names(doc: dict[str, Any]) -> list[str]:
    inc = doc.get("include")
    if not inc:
        return []
    if isinstance(inc, list):
        return [str(x) for x in inc]
    text = str(inc).strip()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return [text]
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    return [part.strip() for part in text.split(",") if part.strip()]


def norm(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        if value == "nil":
            return None
        if value in ("true", "false"):
            return value == "true"
        try:
            number = float(value)
            return int(number) if number.is_integer() else number
        except ValueError:
            return value
    return value


def config_values_equal(a: Any, b: Any) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(norm(x) == norm(y) for x, y in zip(a, b))
    if isinstance(a, list) or isinstance(b, list):
        return False
    return norm(a) == norm(b)


class ProfileSet:
    """Read-only BambuStudio profile set supplied by the caller."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.manifest_path = root / "BBL.json"
        if not self.manifest_path.is_file():
            raise ProfileSetError(f"{root} 下没有 BBL.json —— 这不是 profile 集根目录")
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.vendor_dir = root / "BBL"
        self.version = self.manifest.get("version")
        self._index: dict[str, Path] | None = None
        self._cache: dict[str, dict[str, Any]] = {}
        self._filament_keys: set[str] | None = None

    @property
    def index(self) -> dict[str, Path]:
        if self._index is None:
            self._index = {
                entry["name"]: self.vendor_dir / entry["sub_path"]
                for entry in self.manifest.get("filament_list", ())
                if entry.get("name") and entry.get("sub_path")
            }
        return self._index

    def has(self, name: str) -> bool:
        return name in self.index

    @property
    def machine_index(self) -> dict[str, Path]:
        return {
            entry["name"]: self.vendor_dir / entry["sub_path"]
            for entry in self.manifest.get("machine_list", ())
            if entry.get("name") and entry.get("sub_path")
        }

    @property
    def machine_names(self) -> set[str]:
        return set(self.machine_index)

    def declared_machines(self, chain: Sequence[str]) -> tuple[str, list[str]] | None:
        for name in chain:
            machines = self.load(name).get("compatible_printers")
            if machines:
                return name, list(machines)
        return None

    def load_machine(self, name: str) -> dict[str, Any]:
        path = self.machine_index.get(name)
        if path is None:
            raise ChainError(f"机型预设 `{name}` 不在 pin 的 machine_list 里")
        return self._load_path(name, path)

    def load(self, name: str) -> dict[str, Any]:
        path = self.index.get(name)
        if path is None:
            raise ChainError(f"`{name}` 不在 pin 的 manifest 里")
        if not path.is_file():
            raise ChainError(f"`{name}` 在 manifest 里但文件缺失：{path}")
        return self._load_path(name, path)

    def _load_path(self, name: str, path: Path) -> dict[str, Any]:
        if name not in self._cache:
            self._cache[name] = json.loads(path.read_text(encoding="utf-8"))
        return self._cache[name]

    def chain(self, leaf: str) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()
        current: str | None = leaf
        while current:
            if current in seen:
                raise ChainError(f"继承链成环：{' → '.join(names + [current])}")
            seen.add(current)
            names.append(current)
            current = self.load(current).get("inherits") or None
        return names

    def check_includes(self, chain: Sequence[str]) -> None:
        for name in chain:
            for template in include_names(self.load(name)):
                if not self.has(template):
                    raise ChainError(f"`{name}` 的 include 目标 `{template}` 不在 pin 的 manifest 里")

    @property
    def filament_keys(self) -> set[str]:
        if self._filament_keys is None:
            keys: set[str] = set()
            for name in self.index:
                try:
                    keys |= set(self.load(name))
                except (ChainError, json.JSONDecodeError):
                    continue
            self._filament_keys = keys
        return self._filament_keys

    @classmethod
    def find(cls, explicit: str | os.PathLike[str] | None = None) -> "ProfileSet":
        if explicit:
            return cls(Path(explicit).expanduser())
        env = os.environ.get("BBS_PROFILE_ROOT")
        candidates = ([env] if env else []) + [
            "/Applications/BambuStudio.app/Contents/Resources/profiles",
            "~/Library/Application Support/BambuStudio/system",
        ]
        tried = []
        for candidate in candidates:
            path = Path(candidate).expanduser()
            tried.append(str(path))
            if (path / "BBL.json").is_file():
                return cls(path)
        raise ProfileSetError("找不到 pin 的 BBS profile 集。用 --profile-root 指定，或设 BBS_PROFILE_ROOT。\n"
                              "  试过：\n    " + "\n    ".join(tried))
