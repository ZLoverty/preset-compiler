import importlib
import unittest


class PackageBoundaryTests(unittest.TestCase):
    def test_public_import_has_no_database_dependency(self):
        """检测安装后的 public API 可导入，且不隐式依赖 preset-db。"""
        package = importlib.import_module("preset_compiler")
        self.assertEqual(package.__version__, "0.1.0")
        self.assertTrue(hasattr(package, "BambuStudioCompiler"))


if __name__ == "__main__":
    unittest.main()
