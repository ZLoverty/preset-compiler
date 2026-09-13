"""BambuStudio profile inheritance/include resolution."""

from __future__ import annotations

from typing import Any

from ...core import contracts as vp
from .errors import BuildError


class BambuStudioPresetResolver:
    def __init__(self, profile_set: vp.ProfileSet, defaults: dict[str, list]):
        self.profile_set = profile_set
        self.defaults = defaults

    def resolve(self, name: str) -> dict[str, Any]:
        return self._flatten(name)

    def _flatten(self, name: str, stack: tuple[str, ...] = ()) -> dict[str, Any]:
        if name in stack:
            raise BuildError(f"继承链成环：{' → '.join(stack + (name,))}")
        doc = self.profile_set.load(name)
        parent = doc.get("inherits")
        config = dict(self._flatten(parent, stack + (name,))) if parent else {}
        for template_name in vp.include_names(doc):
            template = self._flatten(template_name, stack + (name,))
            uncovered = [key for key in template
                         if key not in self.defaults and key not in vp.PROFILE_META_KEYS]
            if uncovered:
                raise BuildError(f"include 目标 `{template_name}` 用了 {len(uncovered)} 个不在 "
                                 f"bbs_filament_defaults.json 里的键 {sorted(uncovered)} —— "
                                 "无法判定它们是否生效。跑 tools/extract_filament_defaults.py 重新生成。")
            for key, value in template.items():
                if key not in vp.PROFILE_META_KEYS and not vp.config_values_equal(value, self.defaults[key]):
                    config[key] = value
        config.update({k: v for k, v in doc.items() if k not in vp.PROFILE_META_KEYS})
        return config
