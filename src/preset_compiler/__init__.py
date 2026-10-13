"""Public API for compiling preset source data."""

from .core.model import MaterialPreset
from .slicers.bambustudio import BambuStudioArtifact, BambuStudioCompiler
from .slicers.crealityprint import CrealityPrintArtifact, CrealityPrintCompiler
from .slicers.elegoo import ElegooSlicerArtifact, ElegooSlicerCompiler
from .slicers.orcaslicer import OrcaSlicerArtifact, OrcaSlicerCompiler
from .slicers.prusaslicer import PrusaSlicerArtifact, PrusaSlicerCompiler
from .slicers.bambustudio.errors import BuildError, PresetCompilerError

__version__ = "0.1.0"

__all__ = [
    "BambuStudioArtifact",
    "BambuStudioCompiler",
    "CrealityPrintArtifact",
    "CrealityPrintCompiler",
    "ElegooSlicerArtifact",
    "ElegooSlicerCompiler",
    "BuildError",
    "MaterialPreset",
    "PresetCompilerError",
    "OrcaSlicerArtifact",
    "OrcaSlicerCompiler",
    "PrusaSlicerArtifact",
    "PrusaSlicerCompiler",
    "__version__",
]
