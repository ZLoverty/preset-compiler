"""OrcaSlicer compiler implementation."""

from ..base import JsonSlicerCompiler, SlicerArtifact


class OrcaSlicerCompiler(JsonSlicerCompiler):
    target = "OrcaSlicer"


OrcaSlicerArtifact = SlicerArtifact

__all__ = ["OrcaSlicerArtifact", "OrcaSlicerCompiler"]
