"""ElegooSlicer compiler implementation."""

from ..base import JsonSlicerCompiler, SlicerArtifact


class ElegooSlicerCompiler(JsonSlicerCompiler):
    target = "ElegooSlicer"


ElegooSlicerArtifact = SlicerArtifact

__all__ = ["ElegooSlicerArtifact", "ElegooSlicerCompiler"]
