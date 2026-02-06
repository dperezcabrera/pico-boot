Read and follow ./AGENTS.md for project conventions.

## Pico Ecosystem Context

pico-boot is the orchestration layer. It wraps `pico_ioc.init()` adding plugin auto-discovery and scanner harvesting. All pico-* packages register via `pico_boot.modules` entry point.

## Key Reminders

- pico-ioc dependency: `>= 2.2.0`
- `version_scheme = "guess-next-dev"` (clean versions on tag)
- requires-python >= 3.11
- Commit messages: one line only
- This is a single-file package (`__init__.py` only) - keep it that way
