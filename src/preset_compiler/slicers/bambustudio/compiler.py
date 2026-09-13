"""Transformation from a source material preset to a BambuStudio artifact."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core import contracts as vp
from ...core.model import MaterialPreset
from .errors import BuildError
from .resolver import BambuStudioPresetResolver

NOZZLE = "0.4 nozzle"


@dataclass
class BambuStudioArtifact:
    source: MaterialPreset
    config: dict[str, Any]
    findings: list[vp.Finding] = field(default_factory=list)


class BambuStudioCompiler:
    """Compile one source preset using an explicitly supplied profile context."""

    def __init__(self, profile_set: vp.ProfileSet, defaults: dict[str, list], version: str):
        self.profile_set = profile_set
        self.resolver = BambuStudioPresetResolver(profile_set, defaults)
        self.version = version

    def compile(self, source: MaterialPreset) -> BambuStudioArtifact:
        config = self.resolver.resolve(source.inherits)
        findings = self.check_closure(source, config)
        findings.extend(self.apply_material_values(config, source))
        self.apply_identity(config, source)
        self.apply_compatibility(config, source)
        artifact = BambuStudioArtifact(source, config, findings)
        artifact.findings.extend(self.check_values(artifact))
        return artifact

    @staticmethod
    def encode_value(chain_value: Any, value: Any) -> Any:
        scalar = vp.norm(value) if isinstance(value, float) else value
        if isinstance(chain_value, list):
            text = scalar if isinstance(scalar, str) else str(scalar)
            return [text] * len(chain_value)
        return scalar

    def apply_material_values(self, config: dict[str, Any], source: MaterialPreset) -> list[vp.Finding]:
        return self._apply_material_values_compat(config, source)

    @staticmethod
    def _apply_material_values_compat(config: dict[str, Any], source: MaterialPreset) -> list[vp.Finding]:
        findings: list[vp.Finding] = []
        for key in vp.DATA_KEYS:
            if key not in source.values:
                continue
            if key not in config:
                findings.append(vp.Finding(source.rel, key, "build.encode",
                    "这个键不在链上，无法判断该写成数组还是标量（§3.2 靠链上形态判定）。"))
                continue
            config[key] = BambuStudioCompiler.encode_value(config[key], source.values[key])
        return findings

    def apply_identity(self, config: dict[str, Any], source: MaterialPreset) -> None:
        self._apply_identity(config, source, self.version)

    @staticmethod
    def _apply_identity(config: dict[str, Any], source: MaterialPreset, version: str) -> None:
        config.update({
            "type": "filament", "name": source.name,
            "filament_settings_id": [source.name], "from": "User", "inherits": "",
            "version": version, "filament_id": "J" + source.pi_code,
            "description": "", "pm_method_version": source.metadata["pm_method_version"],
            "pm_source_inherits": source.inherits,
        })
        config.pop("setting_id", None)

    # Kept as a migration shim for the legacy caller helper API.
    _apply_identity_compat = _apply_identity

    def apply_compatibility(self, config: dict[str, Any], source: MaterialPreset) -> None:
        machine = f"Bambu Lab {source.printer.split(' ', 1)[1]} {NOZZLE}"
        chain = self.profile_set.chain(source.inherits)
        declared = self.profile_set.declared_machines(chain)
        if declared is None:
            raise BuildError(f"链 `{' → '.join(chain)}` 上没有任何一跳写了 `compatible_printers`，"
                             f"无法判定它是给哪台机器用的，`{machine}` 也就无从验起。")
        hop, machines = declared
        if machine not in machines:
            raise BuildError(f"跨机型继承：产物要绑 `{machine}`，但链上第一处声明在 `{hop}`，"
                             f"它只绑 {machines} —— 展平出来的值是那台机器的，产物却叫 `{source.name}`。")
        if machine not in self.profile_set.machine_names:
            raise BuildError(f"`{machine}` 不在 pin 的 machine_list 里，写进产物 BBS 解析不出机型。")
        config["compatible_printers"] = [machine]
        config["compatible_printers_condition"] = ""

    def expected_keys(self, source: MaterialPreset) -> set[str]:
        expected: set[str] = set()
        for hop in self.profile_set.chain(source.inherits):
            expected |= set(self.profile_set.load(hop)) - vp.PROFILE_META_KEYS
            for template in vp.include_names(self.profile_set.load(hop)):
                expected |= set(self.profile_set.load(template)) - vp.PROFILE_META_KEYS
        return expected | (set(vp.DATA_KEYS) & set(source.values))

    def check_closure(self, source: MaterialPreset, config: dict[str, Any]) -> list[vp.Finding]:
        return [vp.Finding(source.rel, key, "build.closure",
            "展平结果里没有这个键 —— 导入后它会掉到全局默认值（不是父预设的值），静默错。")
            for key in sorted(self.expected_keys(source) - set(config))]

    @staticmethod
    def check_values(artifact: BambuStudioArtifact) -> list[vp.Finding]:
        out: list[vp.Finding] = []
        for key in vp.DATA_KEYS:
            if key not in artifact.source.values:
                continue
            want = vp.norm(artifact.source.values[key])
            raw = artifact.config.get(key)
            got = vp.norm(raw[0]) if isinstance(raw, list) and raw else vp.norm(raw)
            if want != got:
                out.append(vp.Finding(artifact.source.rel, key, "build.value",
                    f"产物里是 {got!r}，数据文件里是 {want!r} —— 构建把值改坏了。"))
        return out
