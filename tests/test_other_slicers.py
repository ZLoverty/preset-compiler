import unittest

from preset_compiler import (
    CrealityPrintCompiler,
    ElegooSlicerCompiler,
    MaterialPreset,
    OrcaSlicerCompiler,
    PrusaSlicerCompiler,
)


class Profiles:
    def load(self, name):
        if name == "Generic PLA":
            return {"inherits": "", "nozzle_temperature": ["200"], "filament_type": "PLA"}
        raise KeyError(name)

    def chain(self, name):
        return [name]


def source():
    return MaterialPreset(
        rel="PLA.json", name="Polymaker PLA", pi_code="PLA01", printer="Generic",
        inherits="Generic PLA", values={"nozzle_temperature": 225},
        metadata={"pm_method_version": "v1"},
    )


class TargetTests(unittest.TestCase):
    def test_json_targets_compile_and_preserve_profile_shape(self):
        for compiler_type, target in (
            (OrcaSlicerCompiler, "OrcaSlicer"),
            (CrealityPrintCompiler, "CrealityPrint"),
            (ElegooSlicerCompiler, "ElegooSlicer"),
        ):
            with self.subTest(target=target):
                artifact = compiler_type(Profiles(), version="1").compile(source())
                self.assertEqual(artifact.target, target)
                self.assertEqual(artifact.config["nozzle_temperature"], ["225"])
                self.assertEqual(artifact.config["name"], "Polymaker PLA")
                self.assertEqual(artifact.format, "json")

    def test_prusa_target_serializes_native_ini(self):
        artifact = PrusaSlicerCompiler(Profiles()).compile(source())
        self.assertEqual(artifact.format, "ini")
        self.assertIn("[filament:Polymaker PLA]", artifact.to_ini())
        self.assertIn("nozzle_temperature = 225", artifact.to_ini())


if __name__ == "__main__":
    unittest.main()
