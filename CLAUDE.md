Read and follow ./AGENTS.md for project conventions.

## Pico Ecosystem Context

pico-boot is the orchestration layer. It wraps `pico_ioc.init()` adding plugin auto-discovery and scanner harvesting. All pico-* packages register via `pico_boot.modules` entry point.

## Key Reminders

- pico-ioc dependency: `>= 2.2.0`
- **NEVER change `version_scheme`** in pyproject.toml. It MUST remain `"post-release"`. Changing it to `"guess-next-dev"` causes `.dev0` versions to leak to PyPI. This was already fixed once — do not revert it.
- requires-python >= 3.11
- Commit messages: one line only
- This is a single-file package (`__init__.py` only) - keep it that way
