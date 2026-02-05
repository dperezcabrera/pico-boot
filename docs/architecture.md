# Architecture

This document describes the internal architecture of Pico-Boot, its design decisions, and how it integrates with pico-ioc.

## Overview

Pico-Boot is intentionally minimal. It's a thin wrapper around `pico_ioc.init()` that adds:

1. **Plugin discovery** via Python entry points
2. **Module normalization** to handle various input types
3. **Scanner harvesting** from loaded modules (`PICO_SCANNERS`)
4. **Environment-based control** via `PICO_BOOT_AUTO_PLUGINS`

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Application                          │
│                                                                  │
│  from pico_boot import init                                      │
│  container = init(modules=["myapp"])                             │
│                                                                  │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          pico-boot                               │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Module    │  │   Plugin    │  │      Scanner            │  │
│  │ Normalizer  │  │  Discovery  │  │     Harvesting          │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                     │                 │
│         └────────────────┼─────────────────────┘                 │
│                          │                                       │
│                          ▼                                       │
│            ┌──────────────────────────┐                          │
│            │  Merged Modules +        │                          │
│            │  Harvested Scanners      │                          │
│            └─────────────┬────────────┘                          │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                          pico-ioc                                │
│                                                                  │
│                     pico_ioc.init()                              │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ Scanner  │  │ Container│  │  Scopes  │  │   Configuration  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Module Normalizer

The module normalizer handles various input types and deduplicates them:

```python
# All these are valid inputs:
init(modules=["myapp"])                    # String
init(modules=[myapp_module])               # Module object
init(modules=["myapp", myapp_module])      # Mixed
init(modules="myapp")                      # Single string (converted to list)
```

**Implementation:**

```
_to_module_list(input)
       │
       ▼
_import_module_like(item) for each item
       │
       ▼
_normalize_modules(modules) - deduplicate by __name__
```

### 2. Plugin Discovery

Plugin discovery uses Python's `importlib.metadata.entry_points()`:

```
entry_points(group="pico_boot.modules")
       │
       ▼
Filter out: pico_ioc, pico_boot
       │
       ▼
import_module(ep.module) for each
       │
       ▼
Deduplicate by module name
       │
       ▼
List[ModuleType]
```

**Why filter pico_ioc and pico_boot?**

These are infrastructure packages, not application modules. They don't contain components to scan.

### 3. Environment Configuration

A single environment variable controls plugin auto-discovery:

```
PICO_BOOT_AUTO_PLUGINS
       │
       ▼
"true" (default) ──────► Enable discovery
       │
"false", "0", "no" ────► Disable discovery
```

## Code Flow

### init() Execution Path

```python
def init(*args, **kwargs):
    # 1. Bind arguments to pico_ioc.init signature
    bound = _IOC_INIT_SIG.bind(*args, **kwargs)
    bound.apply_defaults()

    # 2. Normalize user modules
    base_modules = _normalize_modules(_to_module_list(bound.arguments["modules"]))

    # 3. Check auto-discovery setting
    auto_flag = os.getenv("PICO_BOOT_AUTO_PLUGINS", "true").lower()
    auto_plugins = auto_flag not in ("0", "false", "no")

    # 4. Discover and merge plugins
    if auto_plugins:
        plugin_modules = _load_plugin_modules()
        all_modules = _normalize_modules(list(base_modules) + plugin_modules)
    else:
        all_modules = base_modules

    # 5. Update modules argument
    bound.arguments["modules"] = all_modules

    # 6. Harvest PICO_SCANNERS from all modules
    harvested = _harvest_scanners(all_modules)
    if harvested:
        existing = bound.arguments.get("custom_scanners") or []
        bound.arguments["custom_scanners"] = list(existing) + harvested

    # 7. Delegate to pico_ioc.init
    return _ioc_init(*bound.args, **bound.kwargs)
```

## Design Decisions

### Why Wrap pico_ioc.init()?

**Alternative considered:** Subclass PicoContainer

**Decision:** Wrap the init function

**Rationale:**
- Minimal coupling - pico-boot doesn't need to know PicoContainer internals
- Forward compatible - any new pico_ioc.init() parameters work automatically
- Single responsibility - pico-boot only handles discovery, not container logic

### Why Entry Points?

**Alternative considered:** Configuration file listing plugins

**Decision:** Use Python entry points

**Rationale:**
- Standard Python mechanism (PEP 621)
- Zero configuration for end users
- Plugins are discovered at install time, not runtime
- Works with pip, poetry, conda, etc.

### Why Deduplicate Modules?

**Problem:** User might specify a module that's also a plugin

```python
# User explicitly lists pico-fastapi
init(modules=["myapp", "pico_fastapi"])

# But pico-fastapi is also auto-discovered!
```

**Solution:** Deduplicate by module `__name__`

The first occurrence wins, preserving user intent while avoiding duplicate scanning.

### Why Allow Disabling Auto-Discovery?

**Use cases:**
1. **Testing:** Isolate tests from installed plugins
2. **Debugging:** Understand what modules are being loaded
3. **Performance:** Skip discovery in serverless cold starts
4. **Compatibility:** Gradual migration from pico-ioc

## Error Handling

### Plugin Import Failures

Plugins that fail to import are logged and skipped:

```python
try:
    m = import_module(ep.module)
except Exception as exc:
    logger.warning(
        "Failed to load pico-boot plugin entry point '%s' (%s): %s",
        ep.name, ep.module, exc
    )
    continue  # Skip this plugin, continue with others
```

**Rationale:** A broken optional plugin shouldn't crash the application.

### Module Import Failures

Module import failures from user-specified modules propagate:

```python
# This will raise if "nonexistent" doesn't exist
init(modules=["myapp", "nonexistent"])
```

**Rationale:** User-specified modules are required, not optional.

## Performance Considerations

### Entry Point Discovery

`entry_points()` is called once per `init()`. The result is not cached because:

1. Applications typically call `init()` once at startup
2. Caching would prevent seeing newly installed plugins
3. The operation is fast (reads package metadata)

### Module Import

Modules are imported via `import_module()`. Python caches imports in `sys.modules`, so repeated `init()` calls don't re-import.

## Extensibility

### Custom Entry Point Group

Advanced users can use a custom group:

```python
# In _load_plugin_modules
def _load_plugin_modules(group: str = "pico_boot.modules"):
    ...
```

This is an internal API but available for special cases.

### Adding New Features

To add features to pico-boot:

1. **Don't modify init() signature** - it must match pico_ioc.init()
2. **Use environment variables** for configuration
3. **Fail gracefully** - don't break apps on errors
4. **Stay minimal** - complex features belong in pico-ioc

## Testing Strategy

### Unit Tests

Test each internal function in isolation:
- `_to_module_list` - input normalization
- `_import_module_like` - import handling
- `_normalize_modules` - deduplication
- `_load_plugin_modules` - entry point discovery
- `_harvest_scanners` - PICO_SCANNERS collection

### Integration Tests

Test the full flow with real pico-ioc:
- Container creation
- Component resolution
- Lifecycle management

### Mock Strategy

Mock these for unit tests:
- `entry_points()` - avoid depending on installed packages
- `import_module()` - avoid importing real modules
- `logger` - verify warning messages

## Future Considerations

### Potential Enhancements

1. **Config file discovery** - auto-load `application.yaml`
2. **Profile support** - environment-based profile activation

### Non-Goals

1. **Container features** - belong in pico-ioc
2. **Framework features** - belong in specific integrations
3. **CLI tools** - separate package
