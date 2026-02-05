# Creating Pico-Boot Plugins

This guide explains how to create libraries that integrate automatically with Pico-Boot.

## How Plugin Discovery Works

Pico-Boot uses Python's [entry points](https://packaging.python.org/en/latest/specifications/entry-points/) mechanism to discover plugins at runtime.

```
┌─────────────────────────────────────────────────────────────┐
│                      Application                            │
│                                                             │
│  from pico_boot import init                                │
│  container = init(modules=["myapp"])                        │
│                                                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     Pico-Boot                              │
│                                                             │
│  1. Scan entry_points(group="pico_boot.modules")           │
│  2. Import each discovered module                           │
│  3. Collect PICO_SCANNERS from modules                      │
│  4. Merge with user modules                                 │
│  5. Delegate to pico_ioc.init()                             │
│                                                             │
└───────────┬─────────────────┬─────────────────┬─────────────┘
            │                 │                 │
            ▼                 ▼                 ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │  pico-fastapi │ │ pico-sqlalch. │ │  your-plugin  │
    │               │ │               │ │               │
    │ entry_point:  │ │ entry_point:  │ │ entry_point:  │
    │ pico_fastapi  │ │ pico_sqlalch. │ │ your_plugin   │
    └───────────────┘ └───────────────┘ └───────────────┘
```

## Step-by-Step Guide

### 1. Create Your Package Structure

```
my-pico-plugin/
├── pyproject.toml
├── README.md
├── LICENSE
└── src/
    └── my_plugin/
        ├── __init__.py
        ├── config.py
        ├── components.py
        └── providers.py
```

### 2. Define Your pyproject.toml

The key is the `[project.entry-points."pico_boot.modules"]` section:

```toml
[build-system]
requires = ["setuptools>=69.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-pico-plugin"
version = "1.0.0"
description = "My awesome Pico-Boot plugin"
requires-python = ">=3.11"
dependencies = [
    "pico-ioc>=2.2.0",
]

# This is the magic line that makes auto-discovery work!
[project.entry-points."pico_boot.modules"]
my_plugin = "my_plugin"
```

**Entry Point Format:**

```toml
[project.entry-points."pico_boot.modules"]
<name> = "<module_path>"
```

- `<name>`: A unique identifier (typically your package name)
- `<module_path>`: The Python module path to import

### 3. Create Your Main Module

```python
# src/my_plugin/__init__.py
"""
My Pico-Boot Plugin

Provides integration with SomeService.
"""

# Re-export main components for easy access
from .config import MyPluginConfig
from .components import MyPluginService
from .providers import build_some_client

__all__ = [
    "MyPluginConfig",
    "MyPluginService",
    "build_some_client",
]
```

### 4. Define Configuration

```python
# src/my_plugin/config.py
from dataclasses import dataclass
from pico_ioc import configured

@configured(prefix="my_plugin")
@dataclass
class MyPluginConfig:
    """
    Configuration for my-plugin.

    Add to your application.yaml:

        my_plugin:
          api_key: your-api-key
          timeout: 30
          enabled: true

    Or use environment variables:
        MY_PLUGIN_API_KEY=your-api-key
        MY_PLUGIN_TIMEOUT=30
        MY_PLUGIN_ENABLED=true
    """
    api_key: str
    timeout: int = 30
    enabled: bool = True
```

### 5. Create Components

```python
# src/my_plugin/components.py
from pico_ioc import component, health, cleanup
from .config import MyPluginConfig

@component
class MyPluginService:
    """Main service provided by the plugin."""

    def __init__(self, config: MyPluginConfig):
        self.config = config
        self._connected = False

    def connect(self) -> None:
        if self.config.enabled:
            # Connection logic
            self._connected = True

    def do_something(self) -> str:
        if not self.config.enabled:
            return "Plugin disabled"
        return "Plugin working!"

    @health
    def is_healthy(self) -> bool:
        """Health check for observability."""
        return self._connected or not self.config.enabled

    @cleanup
    def close(self) -> None:
        """Cleanup when container shuts down."""
        self._connected = False
```

### 6. Create Providers for Third-Party Types

```python
# src/my_plugin/providers.py
from pico_ioc import provides
from .config import MyPluginConfig

# Example: providing a third-party client
from some_external_library import SomeClient

@provides(SomeClient)
def build_some_client(config: MyPluginConfig) -> SomeClient:
    """
    Provides a configured SomeClient instance.

    This allows applications to inject SomeClient directly
    without knowing how to configure it.
    """
    return SomeClient(
        api_key=config.api_key,
        timeout=config.timeout
    )
```

### 7. (Optional) Add Custom Scanners

If your plugin needs custom component discovery:

```python
# src/my_plugin/__init__.py
from pico_ioc import CustomScanner
from types import ModuleType

class MyCustomScanner(CustomScanner):
    """Discovers components with @my_decorator."""

    def scan(self, module: ModuleType) -> None:
        for name in dir(module):
            obj = getattr(module, name)
            if hasattr(obj, "_my_plugin_marker"):
                # Register with container
                self.register_component(obj)

# Export for Pico-Boot to discover
PICO_SCANNERS = [MyCustomScanner()]
```

## Complete Example: Redis Plugin

Here's a complete, production-ready example:

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=69.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pico-redis"
version = "1.0.0"
description = "Redis integration for Pico-Boot"
requires-python = ">=3.11"
license = {text = "MIT"}
dependencies = [
    "pico-ioc>=2.2.0",
    "redis>=5.0.0",
]

[project.optional-dependencies]
test = ["pytest>=8", "pytest-asyncio>=0.23"]

[project.entry-points."pico_boot.modules"]
pico_redis = "pico_redis"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

### src/pico_redis/__init__.py

```python
"""
Pico-Redis: Redis integration for Pico-Boot

Usage:
    1. Install: pip install pico-redis
    2. Add to application.yaml:
        redis:
          url: redis://localhost:6379/0
    3. Inject redis.Redis in your components:
        @component
        class MyService:
            def __init__(self, redis: redis.Redis):
                self.redis = redis
"""

from .config import RedisConfig
from .providers import build_redis_client

__all__ = ["RedisConfig", "build_redis_client"]
```

### src/pico_redis/config.py

```python
from dataclasses import dataclass
from pico_ioc import configured

@configured(prefix="redis")
@dataclass
class RedisConfig:
    """Redis connection configuration."""
    url: str = "redis://localhost:6379/0"
    max_connections: int = 10
    decode_responses: bool = True
    socket_timeout: float = 5.0
```

### src/pico_redis/providers.py

```python
import redis
from pico_ioc import provides, cleanup
from .config import RedisConfig

_pool: redis.ConnectionPool | None = None

@provides(redis.Redis)
def build_redis_client(config: RedisConfig) -> redis.Redis:
    """Provides a configured Redis client with connection pooling."""
    global _pool

    if _pool is None:
        _pool = redis.ConnectionPool.from_url(
            config.url,
            max_connections=config.max_connections,
            decode_responses=config.decode_responses,
            socket_timeout=config.socket_timeout,
        )

    return redis.Redis(connection_pool=_pool)

@cleanup
def close_redis_pool() -> None:
    """Cleanup connection pool on shutdown."""
    global _pool
    if _pool is not None:
        _pool.disconnect()
        _pool = None
```

## Testing Your Plugin

### Unit Tests

```python
# tests/test_plugin.py
import pytest
from pico_ioc import init, configuration, DictSource

def test_plugin_loads():
    """Verify plugin components are discoverable."""
    from my_plugin import MyPluginConfig, MyPluginService

    config = configuration(
        DictSource({"my_plugin": {"api_key": "test-key"}})
    )

    container = init(
        modules=["my_plugin"],
        config=config
    )

    service = container.get(MyPluginService)
    assert service.config.api_key == "test-key"
    container.shutdown()
```

### Integration Test with Pico-Boot

```python
# tests/test_integration.py
import os
import pytest

def test_auto_discovery():
    """Verify plugin is discovered by pico-boot."""
    os.environ["MY_PLUGIN_API_KEY"] = "test-key"

    from pico_boot import init
    from my_plugin import MyPluginService

    container = init(modules=[])  # Empty - relies on auto-discovery

    # Plugin should be loaded automatically
    service = container.get(MyPluginService)
    assert service is not None

    container.shutdown()
    del os.environ["MY_PLUGIN_API_KEY"]
```

## Best Practices

### 1. Use Unique Prefixes

Avoid configuration conflicts:

```python
# Good - unique prefix
@configured(prefix="my_plugin")

# Bad - too generic, may conflict
@configured(prefix="database")
```

### 2. Provide Sensible Defaults

```python
@dataclass
class MyPluginConfig:
    required_field: str          # No default = required
    optional_field: int = 30     # With default = optional
```

### 3. Document Configuration

```python
@configured(prefix="my_plugin")
@dataclass
class MyPluginConfig:
    """
    My Plugin Configuration.

    YAML:
        my_plugin:
          api_key: your-key
          timeout: 30

    Environment:
        MY_PLUGIN_API_KEY=your-key
        MY_PLUGIN_TIMEOUT=30
    """
```

### 4. Add Health Checks

```python
@component
class MyService:
    @health
    def is_healthy(self) -> bool:
        return self._connection.is_alive()
```

### 5. Implement Cleanup

```python
@component
class MyService:
    @cleanup
    async def close(self) -> None:
        await self._connection.close()
```

### 6. Handle Optional Dependencies

```python
try:
    import optional_lib
    HAS_OPTIONAL = True
except ImportError:
    HAS_OPTIONAL = False

if HAS_OPTIONAL:
    @provides(optional_lib.Client)
    def build_client() -> optional_lib.Client:
        return optional_lib.Client()
```

### 7. Support Profiles

```python
@component(profiles=["production"])
class ProductionCache:
    pass

@component(profiles=["development", "test"])
class MockCache:
    pass
```

## Publishing Your Plugin

1. **Test thoroughly** with multiple Python versions
2. **Document** configuration options clearly
3. **Add badges** to your README
4. **Publish to PyPI**:
   ```bash
   pip install build twine
   python -m build
   twine upload dist/*
   ```

## Troubleshooting

### Plugin Not Loading

1. Verify entry point is correct:
   ```bash
   python -c "from importlib.metadata import entry_points; print([ep for ep in entry_points(group='pico_boot.modules')])"
   ```

2. Check for import errors:
   ```python
   import logging
   logging.getLogger("pico_boot").setLevel(logging.DEBUG)
   from pico_boot import init
   container = init(modules=[])
   ```

### Configuration Not Found

Ensure prefix matches YAML structure:

```yaml
# application.yaml
my_plugin:        # <-- This must match prefix
  api_key: xxx
```

```python
@configured(prefix="my_plugin")  # <-- Same prefix
```
