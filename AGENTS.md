# pico-boot

Thin orchestration layer for pico-ioc. Plugin auto-discovery via entry points and scanner harvesting.

## Commands

```bash
pip install -e ".[test]"          # Install in dev mode
pytest tests/ -v                  # Run tests
pytest --cov=pico_boot --cov-report=term-missing tests/  # Coverage
tox                               # Full matrix (3.11-3.14)
mkdocs serve -f mkdocs.yml        # Local docs
```

## Project Structure

```
src/pico_boot/
  __init__.py          # init() function - main entry point
```

Single-file package. `init()` is a drop-in replacement for `pico_ioc.init()` that adds:
1. Auto-discovery of modules via `pico_boot.modules` entry point group
2. Scanner harvesting from `PICO_SCANNERS` module-level lists

## Key Concepts

- **`init(modules=[], config=None, custom_scanners=[])`**: Bootstraps container. Discovers plugins, harvests scanners, delegates to `pico_ioc.init()`
- **Entry point group**: `pico_boot.modules` - packages register themselves in `pyproject.toml`
- **Scanner harvesting**: Modules can export `PICO_SCANNERS = [ScannerClass, ...]` lists. `init()` collects all and passes to `pico_ioc.init(custom_scanners=...)`
- **`_load_plugin_modules()`**: Reads `pico_boot.modules` entry points
- **`_harvest_scanners(modules)`**: Collects `PICO_SCANNERS` from loaded modules

## Code Style

- Python 3.11+
- Minimal code - this is intentionally thin
- All logic in `__init__.py`
- No additional dependencies beyond pico-ioc

## Testing

- pytest + pytest-asyncio
- `pytest.importorskip("pico_boot")` for integration tests
- Mock entry points with `unittest.mock.patch`

## Boundaries

- Do not add complexity - pico-boot must stay thin
- Do not duplicate pico-ioc functionality
- Do not modify `_version.py`
