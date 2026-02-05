# Pico-Boot Documentation

Welcome to the official documentation for **Pico-Boot**, the zero-configuration bootstrap layer for the Pico ecosystem.

## What is Pico-Boot?

Pico-Boot is a thin orchestration layer that wraps [pico-ioc](https://github.com/dperezcabrera/pico-ioc) to provide:

- **Automatic plugin discovery** via Python entry points
- **Zero-configuration initialization** for multi-package applications
- **Seamless integration** with the Pico ecosystem

Think of it as the "Spring Boot" to pico-ioc's "Spring Framework" - it eliminates boilerplate and provides sensible defaults.

## Quick Links

| Document | Description |
|----------|-------------|
| [Getting Started](./getting-started.md) | Your first Pico-Boot application |
| [Configuration](./configuration.md) | Configuration file loading |
| [Plugins Overview](./plugins.md) | How plugin discovery works |
| [Creating Plugins](./creating-plugins.md) | Build your own Pico-Boot plugin |
| [Architecture](./architecture.md) | Internal design and decisions |
| [API Reference](./api-reference.md) | Complete API documentation |
| [Ecosystem](./ecosystem.md) | Compatible packages |
| [FAQ](./faq.md) | Frequently asked questions |
| [Troubleshooting](./troubleshooting.md) | Common issues and solutions |

## Installation

```bash
pip install pico-boot
```

This automatically installs `pico-ioc` as a dependency.

## Minimal Example

```python
from pico_ioc import component
from pico_boot import init

@component
class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

# Initialize container with auto-discovery
container = init(modules=[__name__])

# Use your services
service = container.get(GreetingService)
print(service.greet("World"))

# Clean shutdown
container.shutdown()
```

## When to Use Pico-Boot

| Scenario | Recommendation |
|----------|----------------|
| Simple app, few dependencies | Use `pico-ioc` directly |
| Multiple pico-* integrations | **Use `pico-boot`** |
| Library/package development | Use `pico-ioc` directly |
| Application development | **Use `pico-boot`** |
| Want auto-discovery | **Use `pico-boot`** |
| Need fine-grained control | Use `pico-ioc` directly |

## Key Concepts

### 1. Drop-in Replacement

`pico_boot.init()` is a drop-in replacement for `pico_ioc.init()`:

```python
# Before (pico-ioc)
from pico_ioc import init
container = init(modules=["myapp"])

# After (pico-boot)
from pico_boot import init
container = init(modules=["myapp"])  # Same API!
```

### 2. Automatic Plugin Discovery

When you install a Pico ecosystem package, it's automatically discovered:

```bash
pip install pico-fastapi pico-sqlalchemy
```

```python
from pico_boot import init

# Both pico-fastapi and pico-sqlalchemy are loaded automatically!
container = init(modules=["myapp"])
```

### 3. Entry Point Convention

Plugins register via the `pico_boot.modules` entry point group:

```toml
# pyproject.toml
[project.entry-points."pico_boot.modules"]
my_plugin = "my_plugin"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PICO_BOOT_AUTO_PLUGINS` | `true` | Enable/disable plugin auto-discovery |

## Version Compatibility

- **Python:** 3.11+
- **pico-ioc:** >= 2.2.0

## License

MIT - See [LICENSE](https://github.com/dperezcabrera/pico-boot/blob/main/LICENSE)

## Links

- [GitHub Repository](https://github.com/dperezcabrera/pico-boot)
- [PyPI Package](https://pypi.org/project/pico-boot/)
- [Issue Tracker](https://github.com/dperezcabrera/pico-boot/issues)
