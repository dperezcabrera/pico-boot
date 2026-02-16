# How to Selectively Enable or Disable Auto-Discovered Plugins

This guide shows how to control which plugins are loaded when using `pico_boot.init()`.

## Background

By default `pico_boot.init()` discovers every installed package that registers a
`pico_boot.modules` entry point and imports the corresponding module.  This is
convenient, but sometimes you need finer control -- for example, disabling a
plugin in a staging environment or only loading a subset during tests.

## Disable All Auto-Discovery

Set the `PICO_BOOT_AUTO_PLUGINS` environment variable to turn off discovery
entirely.  Accepted "off" values are `false`, `0`, and `no` (case-insensitive).

```bash
export PICO_BOOT_AUTO_PLUGINS=false
```

Or set it in Python before calling `init()`:

```python
import os
os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"

from pico_boot import init

container = init(modules=["myapp.services"])  # only your modules, no plugins
```

When auto-discovery is disabled you can still load specific plugins by adding
them to the *modules* list explicitly:

```python
container = init(modules=["myapp.services", "pico_sqlalchemy"])
```

## Enable Only Specific Plugins

The recommended pattern is:

1. Disable auto-discovery.
2. List only the plugins you want.

```python
import os
os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"

from pico_boot import init

container = init(modules=[
    "myapp.services",
    "myapp.repos",
    "pico_sqlalchemy",  # explicitly enabled
    # pico_fastapi is NOT listed, so it won't load
])
```

## Exclude a Single Plugin

If most plugins should load but one should be skipped, disable auto-discovery
and list everything except the unwanted plugin:

```python
import os
os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"

from pico_boot import init

PLUGINS = [
    "pico_sqlalchemy",
    "pico_pydantic",
    # "pico_celery",  # excluded
]

container = init(modules=["myapp"] + PLUGINS)
```

## Per-Environment Plugin Selection

Use environment-specific configuration to choose plugins at deploy time:

```python
import os

os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"

PLUGIN_MAP = {
    "production":  ["pico_sqlalchemy", "pico_celery", "pico_fastapi"],
    "staging":     ["pico_sqlalchemy", "pico_fastapi"],
    "development": ["pico_sqlalchemy"],
    "test":        [],
}

env = os.getenv("APP_ENV", "development")
plugins = PLUGIN_MAP.get(env, [])

from pico_boot import init

container = init(modules=["myapp"] + plugins)
```

## Verify Which Plugins Are Loaded

Enable debug-level logging to see exactly which entry points are processed:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("pico_boot").setLevel(logging.DEBUG)

from pico_boot import init

container = init(modules=["myapp"])
```

You can also inspect installed entry points directly:

```bash
python -c "from importlib.metadata import entry_points; print([ep for ep in entry_points(group='pico_boot.modules')])"
```
