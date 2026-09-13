# preset-compiler

`preset-compiler` is a standalone Python package that turns a loaded preset
source model into a BambuStudio artifact. BambuStudio is the only supported
target in this phase.

Install the compiler for local development with:

```bash
python -m pip install -e .
python -m preset_compiler --version
python -m unittest discover -s tests
```

The primary API is `preset_compiler.BambuStudioCompiler`; the convenience target
namespace `preset_compiler.bambustudio` is also supported. `preset-db` remains a
separate caller responsible for locating source files and writing output.

See [the architecture boundary](docs/architecture.md) for ownership and
integration details.
