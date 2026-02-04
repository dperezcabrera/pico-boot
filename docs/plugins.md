# Plugins

Pico-Boot uses Python entry points for zero-configuration plugin discovery.

## How Plugin Discovery Works

1. When `init()` is called, Pico-Boot scans installed packages
2. Packages with `pico_boot.modules` entry points are discovered
3. The referenced modules are imported and added to the container
4. Any `PICO_SCANNERS` defined in those modules are collected

## Using Existing Plugins

### Installation

Simply install the plugin package:

```bash
pip install pico-fastapi pico-sqlalchemy pico-celery
```

### Usage

No additional configuration needed:

```python
from pico_boot import init

# Plugins are automatically discovered and loaded!
container = init(modules=["myapp"])
```

### Verifying Loaded Plugins

Enable debug logging to see what's loaded:

```python
import logging
logging.getLogger("pico_boot").setLevel(logging.DEBUG)

container = init(modules=["myapp"])
```

## Creating Your Own Plugin

### Step 1: Create Your Package

```
my_plugin/
├── pyproject.toml
└── src/
    └── my_plugin/
        └── __init__.py
```

### Step 2: Define Components

```python
# src/my_plugin/__init__.py
from pico_ioc import component, provides, configured
from dataclasses import dataclass

# Configuration
@configured(prefix="my_plugin")
@dataclass
class MyPluginConfig:
    enabled: bool = True
    timeout: int = 30

# Components
@component
class MyPluginService:
    def __init__(self, config: MyPluginConfig):
        self.config = config

    def do_something(self):
        if self.config.enabled:
            return "Plugin is working!"
        return "Plugin is disabled"

# Provider for third-party types
@provides(SomeExternalClient)
def build_client(config: MyPluginConfig) -> SomeExternalClient:
    return SomeExternalClient(timeout=config.timeout)
```

### Step 3: Register Entry Point

```toml
# pyproject.toml
[project]
name = "my-plugin"
version = "1.0.0"
dependencies = ["pico-ioc>=2.2.0"]

[project.entry-points."pico_boot.modules"]
my_plugin = "my_plugin"
```

The format is:
```
[project.entry-points."pico_boot.modules"]
<entry_name> = "<module_path>"
```

### Step 4: Install and Use

```bash
pip install -e ./my-plugin
```

Now any application using Pico-Boot will automatically have your plugin!

## Custom Component Scanners

Plugins can provide custom scanners for specialized component discovery.

### Defining a Scanner

```python
# src/my_plugin/__init__.py
from pico_ioc import CustomScanner
from types import ModuleType

class MyCustomScanner(CustomScanner):
    """Discovers components with a custom decorator."""

    def scan(self, module: ModuleType) -> None:
        for name in dir(module):
            obj = getattr(module, name)
            if hasattr(obj, "_my_custom_marker"):
                # Register with container
                self.register_component(obj)

# Export scanners for Pico-Boot to discover
PICO_SCANNERS = [MyCustomScanner()]
```

### Using the Scanner

Pico-Boot automatically collects `PICO_SCANNERS` from all loaded modules:

```python
# Application code - no changes needed!
from pico_boot import init

container = init(modules=["myapp"])  # Scanner is applied automatically
```

## Disabling Auto-Discovery

For testing or explicit control:

```bash
export PICO_BOOT_AUTO_PLUGINS=false
```

Or programmatically:

```python
import os
os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"

from pico_boot import init
container = init(modules=["myapp"])  # Only myapp is loaded
```

## Plugin Best Practices

### 1. Use Configuration Prefixes

Avoid conflicts with a unique prefix:

```python
@configured(prefix="my_plugin")  # Good
@configured(prefix="database")   # Bad - too generic
```

### 2. Make Components Optional

Use profiles or conditional binding:

```python
@component(profiles=["my_plugin"])
class MyPluginFeature:
    pass
```

### 3. Handle Missing Dependencies Gracefully

```python
try:
    import optional_dependency
    HAS_OPTIONAL = True
except ImportError:
    HAS_OPTIONAL = False

if HAS_OPTIONAL:
    @component
    class OptionalFeature:
        pass
```

### 4. Document Required Configuration

```python
@configured(prefix="my_plugin")
@dataclass
class MyPluginConfig:
    """
    Configuration for my-plugin.

    Required in application.yaml:
        my_plugin:
          api_key: your-api-key  # Required
          timeout: 30            # Optional, default 30
    """
    api_key: str
    timeout: int = 30
```

### 5. Provide Health Checks

```python
from pico_ioc import component, health

@component
class MyPluginService:
    @health
    def is_healthy(self) -> bool:
        return self._connection.is_alive()
```

## Ecosystem Plugins

| Plugin | Entry Point | Description |
|--------|-------------|-------------|
| pico-fastapi | `pico_fastapi` | FastAPI integration |
| pico-sqlalchemy | `pico_sqlalchemy` | SQLAlchemy ORM integration |
| pico-celery | `pico_celery` | Celery task queue integration |
| pico-pydantic | `pico_pydantic` | Pydantic validation interceptor |

## Troubleshooting

### Plugin Not Loading

1. Verify entry point is correct:
   ```bash
   python -c "from importlib.metadata import entry_points; print([ep for ep in entry_points(group='pico_boot.modules')])"
   ```

2. Check for import errors:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   from pico_boot import init
   container = init(modules=["myapp"])
   ```

### Conflicting Components

If two plugins provide the same type, use qualifiers:

```python
from pico_ioc import component, Qualifier
from typing import Annotated

@component(qualifiers={"my_plugin"})
class MyCache:
    pass

# Consumer specifies which one
@component
class MyService:
    def __init__(self, cache: Annotated[MyCache, Qualifier("my_plugin")]):
        self.cache = cache
```
