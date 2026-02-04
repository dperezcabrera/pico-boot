# Pico-Stack Documentation

Welcome to the Pico-Stack documentation.

## Contents

| Document | Description |
|----------|-------------|
| [Getting Started](./getting-started.md) | Quick start guide |
| [Configuration](./configuration.md) | Auto-configuration features |
| [Plugins](./plugins.md) | Creating and using plugins |
| [API Reference](./api-reference.md) | Complete API documentation |

## Overview

Pico-Stack is the recommended way to bootstrap applications in the Pico ecosystem. It wraps `pico-ioc` with:

1. **Zero-config plugin discovery** - Install a package, it's automatically available
2. **Automatic configuration** - Drop a YAML file, it's loaded automatically
3. **Scanner harvesting** - Plugins can extend component discovery

## Quick Example

```python
from pico_ioc import component
from pico_stack import init

@component
class MyService:
    pass

container = init(modules=[__name__])
service = container.get(MyService)
```

## When to Use Pico-Stack

Use Pico-Stack when:
- You're building an application (not a library)
- You want automatic plugin discovery
- You want convention-over-configuration

Use `pico-ioc` directly when:
- You're building a reusable library
- You need fine-grained control over initialization
- You want minimal dependencies
