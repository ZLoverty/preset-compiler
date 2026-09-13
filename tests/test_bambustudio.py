import unittest

from preset_compiler import BambuStudioCompiler, MaterialPreset
from preset_compiler.slicers.bambustudio.errors import BuildError


REL = "L2002CF/BBL/A2L/BambuStudio/L2002CF@BBL A2L.json"


def source(**overrides):
    data = {
        "name": "L2002CF@BBL A2L",
        "pi_code": "L2002CF",
        "printer": "BBL A2L",
        "inherits": "Generic PLA @BBL A2L",
        "pm_method_version": "v1",
    }
    data.update(overrides)
    metadata = {k: data[k] for k in ("name", "pi_code", "printer", "inherits", "pm_method_version")}
    return MaterialPreset(REL, data["name"], data["pi_code"], data["printer"],
                          data["inherits"],
                          {k: v for k, v in data.items() if k not in metadata}, metadata)


class StubProfiles:
    def __init__(self, declared=None, machine_names=()):
        self.declared = declared
        self._machine_names = set(machine_names)

    def chain(self, leaf):
        return [leaf, "Generic PLA @base", "fdm_filament_pla"]

    def declared_machines(self, chain):
        return self.declared

    @property
    def machine_names(self):
        return self._machine_names

    def load(self, name):
        return {"nozzle_temperature": ["200"]}


class CompilerUnitTests(unittest.TestCase):
    def compiler(self, profiles=None):
        return BambuStudioCompiler(profiles or StubProfiles(), {}, "02.08.02.60")

    def test_scalar_is_repeated_to_match_chain_shape(self):
        """检测数组型 profile 被错误写成标量，导致 BambuStudio 变体值丢失。"""
        config = {"nozzle_temperature": ["200", "200", "200"]}
        findings = self.compiler().apply_material_values(config, source(nozzle_temperature=230))
        self.assertEqual(findings, [])
        self.assertEqual(config["nozzle_temperature"], ["230"] * 3)

    def test_missing_chain_key_is_a_finding(self):
        """检测 source 写入了不在继承链上的键却被静默加入产物。"""
        findings = self.compiler().apply_material_values({}, source(pressure_advance=0.04))
        self.assertEqual(findings[0].rule, "build.encode")

    def test_identity_is_applied(self):
        """检测产物身份、版本和 filament_id 没有按 source 正确重写。"""
        artifact = {"setting_id": "old", "description": "old"}
        self.compiler().apply_identity(artifact, source())
        self.assertEqual(artifact["name"], "L2002CF@BBL A2L")
        self.assertEqual(artifact["filament_id"], "JL2002CF")
        self.assertNotIn("setting_id", artifact)

    def test_compatibility_is_applied(self):
        """检测 compatible_printers 没有生成带喷嘴限定的完整机型名。"""
        profiles = StubProfiles(
            ("Generic PLA @BBL A2L", ["Bambu Lab A2L 0.4 nozzle"]),
            ["Bambu Lab A2L 0.4 nozzle"],
        )
        config = {}
        self.compiler(profiles).apply_compatibility(config, source())
        self.assertEqual(config["compatible_printers"], ["Bambu Lab A2L 0.4 nozzle"])

    def test_cross_machine_inheritance_fails(self):
        """检测 H2D source 错继承 H2C profile 时没有被拦截。"""
        profiles = StubProfiles(
            ("Generic PLA @BBL H2C 0.4 nozzle", ["Bambu Lab H2C 0.4 nozzle"]),
            ["Bambu Lab H2C 0.4 nozzle", "Bambu Lab H2D 0.4 nozzle"],
        )
        with self.assertRaises(BuildError):
            self.compiler(profiles).apply_compatibility({}, source(printer="BBL H2D"))

    def test_failed_compatibility_does_not_mutate_config(self):
        """检测兼容性校验失败时不会留下半成品字段。"""
        config = {}
        with self.assertRaises(BuildError):
            self.compiler().apply_compatibility(config, source())
        self.assertEqual(config, {})


if __name__ == "__main__":
    unittest.main()
