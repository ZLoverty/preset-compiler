# Compiler boundary

`preset-db` owns source files, their directory layout, database validation,
filesystem traversal, output paths, and database build provenance.

`preset-compiler` owns the source model contract, profile inheritance
resolution, slicer compilation, compiler diagnostics, and artifact
representation. It receives all profile/default/version inputs explicitly and
does not inspect a `preset-db` checkout.

The supported public entry point is:

```python
from preset_compiler import OrcaSlicerCompiler, MaterialPreset

compiler = OrcaSlicerCompiler(profile_set=profiles, defaults=defaults,
                               version="2.2.0")
artifact = compiler.compile(source)
```

`artifact.config` is an in-memory representation. Serializing JSON/INI and
writing files remain caller responsibilities. No plugin registry or slicer
installation discovery is performed by the compiler.
