"""Compiler exceptions."""

class PresetCompilerError(Exception):
    """Base exception for library-level compiler failures."""


class BuildError(PresetCompilerError):
    """The source/profile combination cannot produce a valid artifact."""
