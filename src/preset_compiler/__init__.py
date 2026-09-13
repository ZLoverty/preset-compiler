"""Public API for compiling preset source data."""

from .core.model import MaterialPreset
from .slicers.bambustudio import BambuStudioArtifact, BambuStudioCompiler
from .slicers.bambustudio.errors import BuildError, PresetCompilerError

__version__ = "0.1.0"

__all__ = [
    "BambuStudioArtifact",
    "BambuStudioCompiler",
    "BuildError",
    "MaterialPreset",
    "PresetCompilerError",
    "__version__",
]
