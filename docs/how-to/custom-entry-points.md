# How to Create Custom Entry Points for Your Own Plugins

This guide explains how to create a Python package that is automatically
discovered and loaded by `pico_boot.init()`.

## How Entry Points Work

Python entry points are a standard packaging mechanism (PEP 621) that lets
installed packages advertise modules or objects under a named group.
Pico-Boot queries the group `pico_boot.modules` at runtime and imports every
module registered there.

## Step 1: Choose Your Package Layout

A typical plugin package looks like this:

```
my-pico-plugin/
    pyproject.toml
    src/
        my_plugin/
            __init__.py
```

## Step 2: Register the Entry Point

Add the entry-point section to your `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-pico-plugin"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = ["pico-ioc>=2.2.0"]

[project.entry-points."pico_boot.modules"]
my_plugin = "my_plugin"
```

The format is:

```
<name> = "<dotted.module.path>"
```

- **name** -- a unique identifier (by convention the package name with
  underscores).
- **module path** -- the Python module that Pico-Boot will import.

## Step 3: Define Components in Your Module

```python
# src/my_plugin/__init__.py
from pico_ioc import component, configured
from dataclasses import dataclass

@configured(prefix="my_plugin")
@dataclass
class MyPluginConfig:
    """Plugin configuration.

    YAML::

        my_plugin:
          api_key: your-key
          timeout: 30
    """
    api_key: str = ""
    timeout: int = 30

@component
class MyPluginService:
    def __init__(self, config: MyPluginConfig):
        self.config = config

    def greet(self) -> str:
        return "Hello from my plugin!"
```

## Step 4: Install in Development Mode

```bash
pip install -e ./my-pico-plugin
```

Editable installs ensure entry-point metadata is written so that Pico-Boot
can discover the module at runtime.

## Step 5: Verify Discovery

```bash
python -c "from importlib.metadata import entry_points; \
    print([ep for ep in entry_points(group='pico_boot.modules')])"
```

You should see your entry point in the output.

## Step 6: Use in an Application

No extra configuration is needed in the consuming application:

```python
from pico_boot import init

container = init(modules=["myapp"])
# my_plugin is loaded automatically!
service = container.get(MyPluginService)
print(service.greet())
```

## Adding Custom Scanners

If your plugin introduces a new decorator or discovery mechanism you can
export a `PICO_SCANNERS` list.  Pico-Boot harvests these lists from all
loaded modules and merges them into the `custom_scanners` parameter before
calling `pico_ioc.init()`.

```python
# src/my_plugin/__init__.py
from pico_ioc import CustomScanner
from types import ModuleType

class MyDecoScanner(CustomScanner):
    """Discovers classes annotated with @my_marker."""

    def scan(self, module: ModuleType) -> None:
        for name in dir(module):
            obj = getattr(module, name)
            if getattr(obj, "_my_marker", False):
                self.register_component(obj)

PICO_SCANNERS = [MyDecoScanner()]
```

## Registering Multiple Modules

A single package can register more than one module:

```toml
[project.entry-points."pico_boot.modules"]
my_plugin_core = "my_plugin.core"
my_plugin_ext  = "my_plugin.extensions"
```

Both modules will be imported and scanned.

## Entry Points That Are Skipped

Pico-Boot silently skips entry points whose `module` field is `"pico_ioc"` or
`"pico_boot"` because these are infrastructure packages.  You do not need to
worry about self-registration.

## Handling Import Errors Gracefully

If your plugin module raises an exception at import time, Pico-Boot logs a
warning and continues loading other plugins.  The exact log message is:

```
WARNING:pico_boot:Failed to load pico-boot plugin entry point '<name>' (<module>): <exception>
```

This means a broken optional plugin will not crash the host application.

## Testing Your Plugin

### Unit test without pico-boot

```python
from pico_ioc import init, configuration, DictSource

def test_plugin_standalone():
    config = configuration(DictSource({"my_plugin": {"api_key": "test"}}))
    container = init(modules=["my_plugin"], config=config)
    service = container.get(MyPluginService)
    assert service.greet() == "Hello from my plugin!"
    container.shutdown()
```

### Integration test with pico-boot

```python
import os
from pico_boot import init

def test_plugin_auto_discovered():
    os.environ["PICO_BOOT_AUTO_PLUGINS"] = "true"
    container = init(modules=[])
    service = container.get(MyPluginService)
    assert service is not None
    container.shutdown()
```
