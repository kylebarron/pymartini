## Install

Install the package and development dependencies:

```
uv sync
```

This compiles the Cython extension in `pymartini/martini.pyx`. After changing
it, rebuild with:

```
uv sync --reinstall-package pymartini
```

## Benchmark

```
uv run python bench.py
```
