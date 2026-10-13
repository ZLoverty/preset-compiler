# preset-compiler

`preset-compiler` is a standalone Python package that turns a loaded preset
source model into a slicer artifact. It supports BambuStudio, OrcaSlicer,
CrealityPrint, ElegooSlicer, and PrusaSlicer.

Install the compiler for local development with:

```bash
python -m pip install -e .
python -m preset_compiler --version
python -m unittest discover -s tests
```

The public target APIs are `BambuStudioCompiler`, `OrcaSlicerCompiler`,
`CrealityPrintCompiler`, `ElegooSlicerCompiler`, and `PrusaSlicerCompiler`.
The first four return JSON artifacts; the PrusaSlicer artifact also provides
`to_ini()` for its native preset format. Callers provide the target's profile
set (`load(name)`) and remain responsible for locating source files and
writing output.

See [the architecture boundary](docs/architecture.md) for ownership and
integration details.
