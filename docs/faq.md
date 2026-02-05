# Frequently Asked Questions

## General

### What's the difference between pico-ioc and pico-boot?

**pico-ioc** is the core dependency injection container. It provides:
- Component registration (`@component`, `@provides`, `@factory`)
- Configuration binding (`@configured`)
- Scopes, AOP, event bus, and more

**pico-boot** is an orchestration layer that wraps pico-ioc to provide:
- Automatic plugin discovery via entry points
- Custom scanner harvesting (`PICO_SCANNERS`)

Think of it like Spring Framework (pico-ioc) vs Spring Boot (pico-boot).

### Should I use pico-boot or pico-ioc?

| Use Case | Recommendation |
|----------|----------------|
| Building a library/package | pico-ioc |
| Building an application | pico-boot |
| Need auto-discovery of plugins | pico-boot |
| Want minimal dependencies | pico-ioc |
| Multiple pico-* packages installed | pico-boot |

### Is pico-boot a replacement for pico-ioc?

No. pico-boot **wraps** pico-ioc. You still use pico-ioc decorators (`@component`, `@provides`, etc.) in your code. pico-boot only changes how you initialize the container.

---

## Usage

### How do I import decorators?

Always import decorators from `pico_ioc`:

```python
from pico_ioc import component, provides, factory, configured
from pico_boot import init  # Only init from pico-boot
```

### Can I use pico-ioc features with pico-boot?

Yes, all pico-ioc features work with pico-boot:

```python
from pico_ioc import component, provides, intercepted_by, MethodInterceptor
from pico_boot import init

# AOP works
@component
class MyService:
    @intercepted_by(LoggingInterceptor)
    def do_work(self):
        pass

# Profiles work
container = init(modules=["myapp"], profiles=["production"])

# Overrides work (great for testing)
container = init(modules=["myapp"], overrides={Service: MockService()})
```

### How do I disable plugin auto-discovery?

Set the environment variable:

```bash
export PICO_BOOT_AUTO_PLUGINS=false
```

Or in Python:

```python
import os
os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"

from pico_boot import init
container = init(modules=["myapp"])
```

### How do I see which plugins are loaded?

Enable debug logging:

```python
import logging
logging.getLogger("pico_boot").setLevel(logging.DEBUG)

from pico_boot import init
container = init(modules=["myapp"])
```

---

## Plugins

### How do I create a pico-boot plugin?

Add an entry point to your `pyproject.toml`:

```toml
[project.entry-points."pico_boot.modules"]
my_plugin = "my_plugin"
```

See [Creating Plugins](./creating-plugins.md) for a complete guide.

### Why isn't my plugin being discovered?

Check these common issues:

1. **Entry point group is wrong:**
   ```toml
   # Wrong
   [project.entry-points."pico_stack.modules"]

   # Correct
   [project.entry-points."pico_boot.modules"]
   ```

2. **Package not installed in editable mode:**
   ```bash
   pip install -e ./my-plugin
   ```

3. **Auto-discovery is disabled:**
   ```bash
   echo $PICO_BOOT_AUTO_PLUGINS  # Should not be "false"
   ```

4. **Module import fails:**
   ```python
   import logging
   logging.getLogger("pico_boot").setLevel(logging.DEBUG)
   ```

### Can I have a plugin without any components?

Yes, but it's unusual. A plugin module can contain:
- Components (`@component`)
- Providers (`@provides`)
- Factories (`@factory`)
- Configuration classes (`@configured`)
- Custom scanners (`PICO_SCANNERS`)

If your plugin has none of these, it won't contribute anything to the container.

### How do I depend on another plugin?

Just declare it as a Python dependency:

```toml
# my-plugin/pyproject.toml
[project]
dependencies = [
    "pico-ioc>=2.2.0",
    "pico-sqlalchemy>=0.1.0",  # Depend on another plugin
]
```

pico-boot will load both plugins. Dependencies are resolved by pip, not pico-boot.

---

## Configuration

### Does pico-boot load configuration files?

No. Pico-boot focuses on plugin discovery and scanner harvesting. Configuration file loading (YAML, JSON) is handled by pico-ioc's configuration system.

You combine them like this:

```python
from pico_ioc import configuration, YamlSource, EnvSource
from pico_boot import init

config = configuration(
    YamlSource("application.yaml"),
    EnvSource()
)

container = init(modules=["myapp"], config=config)
```

### How do I use environment variables for configuration?

Use pico-ioc's `@configured` decorator with `EnvSource`:

```python
from dataclasses import dataclass
from pico_ioc import configured, configuration, EnvSource
from pico_boot import init

@configured(prefix="database")
@dataclass
class DatabaseConfig:
    host: str
    port: int = 5432

config = configuration(EnvSource())
container = init(modules=[__name__], config=config)

# Set DATABASE_HOST=localhost, DATABASE_PORT=5433
```

---

## Testing

### How do I test code that uses pico-boot?

Use component overrides:

```python
def test_my_service():
    from pico_boot import init

    mock_repo = MockRepository()
    container = init(
        modules=["myapp"],
        overrides={Repository: mock_repo}
    )

    try:
        service = container.get(MyService)
        result = service.do_something()
        assert result == expected
    finally:
        container.shutdown()
```

### Should I disable auto-discovery in tests?

It depends:

- **Disable** if you want isolated unit tests
- **Enable** if you want integration tests with real plugins

```python
import os

# For unit tests
os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"

# For integration tests
os.environ["PICO_BOOT_AUTO_PLUGINS"] = "true"
```

### How do I mock a plugin in tests?

Use overrides to replace plugin-provided components:

```python
container = init(
    modules=["myapp"],
    overrides={
        # Replace plugin's real database with mock
        AsyncSession: mock_session,
    }
)
```

---

## Troubleshooting

### "Module not found" errors

Make sure modules are installed and importable:

```bash
# Check if module is importable
python -c "import mymodule"
```

### "Component not found" errors

1. Check that the module with the component is in the modules list
2. Check that the component has a decorator (`@component`, `@provides`, etc.)
3. Check that auto-discovery didn't fail (enable debug logging)

### Container returns wrong instance

Check for:
1. Multiple containers (each `init()` creates a new container)
2. Scope issues (prototype vs singleton)
3. Overrides that you forgot about

### Performance is slow at startup

Plugin discovery reads package metadata. For faster cold starts:

```bash
export PICO_BOOT_AUTO_PLUGINS=false
```

Then explicitly list required modules.

---

## Migration

### How do I migrate from pico-ioc to pico-boot?

1. Change the import:
   ```python
   # Before
   from pico_ioc import init

   # After
   from pico_boot import init
   ```

2. That's it! The API is identical.

### How do I migrate from another DI framework?

See pico-ioc's documentation for migration guides. pico-boot doesn't change how you define components, only how you initialize the container.

---

## Advanced

### Can I use multiple containers?

Yes, each `init()` call creates a separate container:

```python
container1 = init(modules=["app1"])
container2 = init(modules=["app2"])

# These are different instances
service1 = container1.get(MyService)
service2 = container2.get(MyService)
assert service1 is not service2
```

### Can I customize the entry point group?

Not currently exposed as public API. If you need this, open an issue.

### How does pico-boot handle circular imports?

pico-boot imports modules lazily during `init()`. Circular imports are handled the same as in pico-ioc - use forward references or restructure your code.

### Is pico-boot thread-safe?

Yes, as thread-safe as pico-ioc. The container itself is thread-safe. Your components should be designed for thread safety if used in multi-threaded contexts.
