"""Creality Print compiler implementation."""

from ..base import JsonSlicerCompiler, SlicerArtifact


class CrealityPrintCompiler(JsonSlicerCompiler):
    target = "CrealityPrint"


CrealityPrintArtifact = SlicerArtifact

__all__ = ["CrealityPrintArtifact", "CrealityPrintCompiler"]
