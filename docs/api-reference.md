# API Reference

Complete API documentation for Pico-Boot.

## Functions

### `init(*args, **kwargs) -> PicoContainer`

Main entry point. Drop-in replacement for `pico_ioc.init()` with auto-discovery.

```python
from pico_boot import init

container = init(
    modules=["myapp"],           # Required: modules to scan
    config=None,                 # Optional: ContextConfig (auto-detected if None)
    profiles=(),                 # Optional: active profiles
    overrides={},                # Optional: component overrides for testing
    observers=[],                # Optional: ContainerObserver instances
    custom_scanners=[],          # Optional: additional CustomScanner instances
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `modules` | `Iterable[str \| ModuleType]` | Required | Modules to scan for components |
| `config` | `ContextConfig \| None` | `None` | Configuration context. If `None`, auto-detected |
| `profiles` | `tuple[str, ...]` | `()` | Active profiles for conditional components |
| `overrides` | `dict[type, Any]` | `{}` | Replace components (useful for testing) |
| `observers` | `list[ContainerObserver]` | `[]` | Lifecycle observers |
| `custom_scanners` | `list[CustomScanner]` | `[]` | Additional component scanners |

#### Returns

`PicoContainer` - The initialized dependency injection container.

#### Behavior

1. Normalizes and deduplicates provided modules
2. Discovers plugins from `pico_boot.modules` entry points (if enabled)
3. Harvests `PICO_SCANNERS` from all loaded modules
4. If `config` is `None`, builds default configuration:
   - Searches for `application.yaml/yml/json` or `settings.yaml/yml/json`
   - Adds environment variable source
5. Delegates to `pico_ioc.init()` with enriched parameters

#### Example

```python
from pico_boot import init

# Basic usage
container = init(modules=["myapp.services", "myapp.repos"])

# With profiles
container = init(modules=["myapp"], profiles=["production"])

# With test overrides
container = init(
    modules=["myapp"],
    overrides={DatabaseService: MockDatabase()}
)

# With custom configuration
from pico_ioc import configuration, EnvSource
container = init(
    modules=["myapp"],
    config=configuration(EnvSource(prefix="MYAPP_"))
)
```

---

## Environment Variables

### `PICO_BOOT_AUTO_PLUGINS`

Controls automatic plugin discovery.

| Value | Effect |
|-------|--------|
| `true` (default) | Discover and load plugins |
| `false`, `0`, `no` | Disable plugin discovery |

```bash
# Disable auto-discovery
export PICO_BOOT_AUTO_PLUGINS=false
```

### `PICO_BOOT_CONFIG_FILE`

Specify a custom configuration file path.

```bash
export PICO_BOOT_CONFIG_FILE=/etc/myapp/config.yaml
```

Takes precedence over default file discovery.

---

## Re-exported from pico-ioc

Pico-Boot re-exports these commonly used symbols for convenience:

| Symbol | Description |
|--------|-------------|
| `PicoContainer` | The container class |
| `ContextConfig` | Configuration context type |
| `ContainerObserver` | Observer protocol for lifecycle events |

For all other symbols, import from `pico_ioc`:

```python
from pico_ioc import component, provides, factory, configured
from pico_ioc import Qualifier, configure, cleanup
from pico_ioc import intercepted_by, MethodInterceptor, health
from pico_ioc import EventBus, Event, subscribe
```

---

## Module Attributes

### `PICO_SCANNERS`

A module-level list that plugins can define to provide custom scanners.

```python
# my_plugin/__init__.py
from pico_ioc import CustomScanner

class MyScanner(CustomScanner):
    def scan(self, module):
        pass

PICO_SCANNERS = [MyScanner()]
```

Pico-Boot collects these from all loaded modules.

---

## Entry Points

### `pico_boot.modules`

The entry point group used for plugin discovery.

```toml
# pyproject.toml
[project.entry-points."pico_boot.modules"]
my_plugin = "my_plugin"
```

Format: `<name> = "<module_path>"`

---

## Internal Functions

These are implementation details and may change:

| Function | Description |
|----------|-------------|
| `_to_module_list()` | Normalizes modules input to list |
| `_import_module_like()` | Imports module from various input types |
| `_normalize_modules()` | Deduplicates modules by name |
| `_load_plugin_modules()` | Discovers entry point plugins |
| `_build_default_config()` | Creates default ContextConfig |
| `_harvest_scanners()` | Collects PICO_SCANNERS from modules |

---

## Configuration File Search Order

When `config=None`:

1. `$PICO_BOOT_CONFIG_FILE` (if set)
2. `application.yaml`
3. `application.yml`
4. `application.json`
5. `settings.yaml`
6. `settings.yml`
7. `settings.json`

First match wins. Environment variables are always added as final source.

---

## Logging

Pico-Boot uses the `pico_boot` logger:

```python
import logging

# See plugin discovery
logging.getLogger("pico_boot").setLevel(logging.DEBUG)

# See all pico activity
logging.getLogger("pico_ioc").setLevel(logging.DEBUG)
```

Log messages:

| Level | Message |
|-------|---------|
| INFO | Auto-configuration file loading |
| WARNING | Plugin load failures |
| DEBUG | No config provided, applying defaults |

---

## Type Hints

```python
from typing import Any, Iterable, List, Union
from types import ModuleType

KeyT = Union[str, type]

def init(
    modules: Union[Any, Iterable[Any]],
    config: ContextConfig | None = None,
    profiles: tuple[str, ...] = (),
    overrides: dict[type, Any] | None = None,
    observers: list[ContainerObserver] | None = None,
    custom_scanners: list[CustomScanner] | None = None,
) -> PicoContainer: ...
```

---

## Version

```python
from pico_boot import __version__
print(__version__)
```

Note: Version is managed by `setuptools-scm` from git tags.
