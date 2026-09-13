# Compiler boundary

`preset-db` owns source files, their directory layout, database validation,
filesystem traversal, output paths, and database build provenance.

`preset-compiler` owns the source model contract, profile inheritance
resolution, BambuStudio compilation, compiler diagnostics, and artifact
representation. It receives all profile/default/version inputs explicitly and
does not inspect a `preset-db` checkout.

The supported public entry point is:

```python
from preset_compiler import BambuStudioCompiler, MaterialPreset

compiler = BambuStudioCompiler(profile_set=profiles, defaults=defaults,
                                version="02.08.02.60")
artifact = compiler.compile(source)
```

`artifact.config` is an in-memory representation. Serializing JSON and writing
files remain caller responsibilities. BambuStudio is the only target in this
phase; no plugin framework or second slicer is introduced.
