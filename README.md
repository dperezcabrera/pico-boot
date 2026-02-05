# Pico-Boot

[![PyPI](https://img.shields.io/pypi/v/pico-boot.svg)](https://pypi.org/project/pico-boot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![CI (tox matrix)](https://github.com/dperezcabrera/pico-boot/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/dperezcabrera/pico-boot/branch/main/graph/badge.svg)](https://codecov.io/gh/dperezcabrera/pico-boot)
[![Docs](https://img.shields.io/badge/Docs-pico--boot-blue?style=flat&logo=readthedocs&logoColor=white)](https://dperezcabrera.github.io/pico-boot/)

**Zero-configuration bootstrap for the Pico ecosystem.**

Pico-Boot is a thin orchestration layer over [pico-ioc](https://github.com/dperezcabrera/pico-ioc) that provides:

- **Auto-discovery of plugins** via Python entry points
- **Custom scanner harvesting** from loaded modules

> 🐍 Requires Python 3.11+

---

## When to Use Pico-Boot vs Pico-IoC

| Use Case | Recommendation |
|----------|----------------|
| Simple app, manual control | Use `pico-ioc` directly |
| Multiple pico-* integrations (fastapi, sqlalchemy, celery) | Use `pico-boot` |
| Want zero-config plugin discovery | Use `pico-boot` |

---

## Installation

```bash
pip install pico-boot
```

This automatically installs `pico-ioc` as a dependency.

---

## Quick Start

### Basic Usage

```python
# app.py
from pico_ioc import component, provides
from pico_boot import init

@component
class Database:
    def query(self) -> str:
        return "data"

@component
class UserService:
    def __init__(self, db: Database):
        self.db = db

# pico-boot's init() replaces pico-ioc's init()
# It auto-discovers plugins and harvests custom scanners
container = init(modules=[__name__])

service = container.get(UserService)
print(service.db.query())
```

---

## Features

### 1. Plugin Auto-Discovery

When you install a pico-* integration package, it automatically registers itself:

```bash
pip install pico-fastapi pico-sqlalchemy pico-celery
```

```python
from pico_boot import init

# All installed pico-* plugins are automatically loaded!
container = init(modules=["myapp"])
```

No need to explicitly import or configure each integration.

### 2. Custom Scanner Harvesting

Modules can expose custom component scanners via `PICO_SCANNERS`:

```python
# my_plugin/__init__.py
from pico_ioc import CustomScanner

class MyScanner(CustomScanner):
    def scan(self, module):
        # Custom component discovery logic
        pass

PICO_SCANNERS = [MyScanner()]
```

Pico-Boot automatically collects and applies these scanners.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PICO_BOOT_AUTO_PLUGINS` | `true` | Enable/disable plugin auto-discovery |

### Disabling Auto-Discovery

```bash
export PICO_BOOT_AUTO_PLUGINS=false
```

Useful for testing or when you want explicit control.

---

## Creating a Pico-Boot Plugin

To make your library discoverable by pico-boot, add an entry point in `pyproject.toml`:

```toml
[project.entry-points."pico_boot.modules"]
my_library = "my_library"
```

### Example: Creating a Redis Integration

```python
# pico_redis/__init__.py
import redis
from pico_ioc import provides, configured
from dataclasses import dataclass

@configured(prefix="redis")
@dataclass
class RedisConfig:
    url: str = "redis://localhost:6379/0"

@provides(redis.Redis)
def build_redis(config: RedisConfig) -> redis.Redis:
    return redis.Redis.from_url(config.url)
```

```toml
# pyproject.toml
[project.entry-points."pico_boot.modules"]
pico_redis = "pico_redis"
```

Now any app using pico-boot will automatically have Redis available!

For a complete guide, see the [Creating Plugins](https://dperezcabrera.github.io/pico-boot/creating-plugins/) documentation.

---

## Complete Example

### Project Structure

```
myapp/
├── application.yaml
├── main.py
├── config.py
├── services.py
└── repositories.py
```

### application.yaml

```yaml
database:
  url: postgresql://localhost/myapp

redis:
  url: redis://localhost:6379/0

app:
  name: My Application
  debug: false
```

### config.py

```python
from dataclasses import dataclass
from pico_ioc import configured

@configured(prefix="database")
@dataclass
class DatabaseConfig:
    url: str

@configured(prefix="redis")
@dataclass
class RedisConfig:
    url: str

@configured(prefix="app")
@dataclass
class AppConfig:
    name: str
    debug: bool = False
```

### services.py

```python
from pico_ioc import component
from .config import AppConfig

@component
class GreetingService:
    def __init__(self, config: AppConfig):
        self.app_name = config.name

    def greet(self, user: str) -> str:
        return f"Welcome to {self.app_name}, {user}!"
```

### main.py

```python
from pico_ioc import configuration, YamlSource, EnvSource
from pico_boot import init
from .services import GreetingService

def main():
    # Load configuration via pico-ioc, let pico-boot discover plugins
    config = configuration(
        YamlSource("application.yaml"),
        EnvSource()
    )
    container = init(modules=["myapp.config", "myapp.services"], config=config)

    service = container.get(GreetingService)
    print(service.greet("Alice"))

    container.shutdown()

if __name__ == "__main__":
    main()
```

### Running

```bash
$ python -m myapp.main
Welcome to My Application, Alice!
```

### Override with Environment Variables

```bash
$ APP_NAME="Production App" python -m myapp.main
Welcome to Production App, Alice!
```

---

## API Reference

### `init(*args, **kwargs) -> PicoContainer`

Drop-in replacement for `pico_ioc.init()` with additional features:

- Auto-discovers plugins from `pico_boot.modules` entry points
- Harvests custom scanners (`PICO_SCANNERS`) from loaded modules

All parameters from `pico_ioc.init()` are supported:

```python
container = init(
    modules=["myapp"],           # Modules to scan
    config=my_config,            # Optional: custom ContextConfig
    profiles=["prod"],           # Optional: active profiles
    overrides={Service: Mock()}, # Optional: test overrides
    observers=[MyObserver()],    # Optional: container observers
    custom_scanners=[],          # Optional: additional scanners
)
```

---

## Documentation

Full documentation is available at [dperezcabrera.github.io/pico-boot](https://dperezcabrera.github.io/pico-boot/).

- [Getting Started](https://dperezcabrera.github.io/pico-boot/getting-started/)
- [Configuration](https://dperezcabrera.github.io/pico-boot/configuration/)
- [Creating Plugins](https://dperezcabrera.github.io/pico-boot/creating-plugins/)
- [API Reference](https://dperezcabrera.github.io/pico-boot/api-reference/)
- [Ecosystem](https://dperezcabrera.github.io/pico-boot/ecosystem/)

---

## Ecosystem

Pico-Boot works with these integration packages:

| Package | Description |
|---------|-------------|
| [pico-ioc](https://github.com/dperezcabrera/pico-ioc) | Core DI container |
| [pico-fastapi](https://github.com/dperezcabrera/pico-fastapi) | FastAPI integration |
| [pico-sqlalchemy](https://github.com/dperezcabrera/pico-sqlalchemy) | SQLAlchemy integration |
| [pico-celery](https://github.com/dperezcabrera/pico-celery) | Celery integration |
| [pico-pydantic](https://github.com/dperezcabrera/pico-pydantic) | Pydantic validation |

---

## Development

```bash
# Run tests
pip install tox
tox

# Build documentation locally
pip install -r docs/requirements.txt
mkdocs serve
```

---

## License

MIT - [LICENSE](./LICENSE)
