# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2025-02-04

### Added
- Initial release of Pico-Boot
- Plugin auto-discovery via `pico_boot.modules` entry points
- Automatic configuration file loading (YAML/JSON)
- Environment variable configuration support
- Custom scanner harvesting from modules
- `PICO_BOOT_AUTO_PLUGINS` environment variable to control auto-discovery
- `PICO_BOOT_CONFIG_FILE` environment variable for custom config path
- Full documentation with MkDocs Material
- GitHub Actions workflows (CI, docs, PyPI publish)

### Compatibility
- Python 3.11 - 3.14
- pico-ioc >= 2.1.3

[0.1.0]: https://github.com/dperezcabrera/pico-boot/releases/tag/v0.1.0
