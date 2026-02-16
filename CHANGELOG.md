# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.1] - 2026-02-06

### Added
- **Ecosystem**: Added `pico-agent` to ecosystem documentation (README table, architecture diagram, version compatibility).

### Changed
- **Simplified Plugin Loading**: Removed legacy `entry_points()` API fallback — now only uses `eps.select(group=group)`.
- **Cleanup**: Removed unused `KeyT` type alias and redundant imports (`Dict`, `Optional`, `Tuple`).
- **pyproject.toml**: Removed `async` optional dependency group.

### Fixed
- **Test Isolation**: Added `autouse` fixture to disable auto-plugins during integration tests via `PICO_BOOT_AUTO_PLUGINS=false`.

---

## [0.1.0] - 2025-02-04

### Added
- Initial release of Pico-Boot
- Plugin auto-discovery via `pico_boot.modules` entry points
- Custom scanner harvesting from modules
- `PICO_BOOT_AUTO_PLUGINS` environment variable to control auto-discovery
- Full documentation with MkDocs Material
- GitHub Actions workflows (CI, docs, PyPI publish)

### Compatibility
- Python 3.11 - 3.14
- pico-ioc >= 2.2.0

[0.1.1]: https://github.com/dperezcabrera/pico-boot/releases/tag/v0.1.1
[0.1.0]: https://github.com/dperezcabrera/pico-boot/releases/tag/v0.1.0
