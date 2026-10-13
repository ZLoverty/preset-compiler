"""PrusaSlicer compiler implementation."""

from ..base import PrusaSlicerCompiler as _PrusaSlicerCompiler, SlicerArtifact


class PrusaSlicerCompiler(_PrusaSlicerCompiler):
    pass


PrusaSlicerArtifact = SlicerArtifact

__all__ = ["PrusaSlicerArtifact", "PrusaSlicerCompiler"]
