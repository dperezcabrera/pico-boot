# Troubleshooting

This is the unified troubleshooting guide for the Pico ecosystem.
Start from the symptom, follow the decision tree, arrive at the fix.

It covers **pico-ioc**, **pico-boot**, **pico-fastapi**, and **pico-pydantic**.

---

## "My component is not found"

```
pico_ioc.exceptions.ProviderNotFoundError: No provider registered for type 'MyService'
```

Follow this checklist **in order** — stop at the first match:

### 1. Is the class decorated?

Every class the container manages needs a decorator.

```python
from pico_ioc import component

@component          # <-- required
class MyService:
    pass
```

If the class is a third-party type you cannot decorate, use `@provides`:

```python
from pico_ioc import provides
import redis

@provides(redis.Redis)
def create_redis(config: RedisConfig) -> redis.Redis:
    return redis.Redis(host=config.host)
```

### 2. Is the module in the `modules` list?

pico-boot only scans modules you tell it about. If `MyService` lives in
`myapp/services/user.py`, that module must be reachable:

```python
from pico_boot import init

container = init(modules=[
    "myapp.services.user",   # exact module
    # or
    "myapp.services",        # package __init__.py that re-exports
])
```

> **Tip:** `init(modules=["myapp.services"])` scans `myapp/services/__init__.py`,
> not every file in the directory. Either re-export from `__init__.py` or list
> each submodule explicitly.

### 3. Can Python import the module?

```bash
python -c "import myapp.services.user"
```

If this fails, the container never sees your components. Common causes:

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError` | `pip install -e .` or fix `PYTHONPATH` |
| `SyntaxError` | Fix the syntax error in the module |
| `ImportError` (circular) | Use `TYPE_CHECKING` guard (see below) |

### 4. Is a profile required?

```python
@component(profiles=["production"])
class MyService:
    pass
```

This component only exists when the profile is active:

```python
container = init(modules=["myapp"], profiles=["production"])
```

### 5. Is there a qualifier mismatch?

```python
from typing import Annotated
from pico_ioc import Qualifier

# Registered with qualifier
@component(qualifier="fast")
class FastCache: ...

# Consumer must use the same qualifier
@component
class MyService:
    def __init__(self, cache: Annotated[Cache, Qualifier("fast")]):
        self.cache = cache
```

If the consumer asks for `Cache` without the qualifier, the container won't
match `FastCache`.

### 6. Is auto-discovery disabled?

If you use pico-boot plugins (pico-fastapi, pico-pydantic, etc.) and they
are not loading:

```bash
echo $PICO_BOOT_AUTO_PLUGINS
# If "false", plugins are skipped
unset PICO_BOOT_AUTO_PLUGINS
```

### 7. Did the plugin entry point fail silently?

Enable debug logging to see warnings:

```python
import logging
logging.getLogger("pico_boot").setLevel(logging.DEBUG)

from pico_boot import init
container = init(modules=["myapp"])
```

Look for:

```
WARNING:pico_boot:Failed to load pico-boot plugin entry point 'my_plugin' ...
```

This means the plugin is registered but its module fails to import.
Fix the underlying `ModuleNotFoundError` or `SyntaxError`.

### 8. Is the entry point registered correctly?

For plugins that expose components via entry points:

```toml
# pyproject.toml — must be exactly this group name
[project.entry-points."pico_boot.modules"]
my_plugin = "my_plugin"
```

Verify the entry point exists:

```bash
python -c "
from importlib.metadata import entry_points
eps = entry_points(group='pico_boot.modules')
for ep in eps:
    print(f'{ep.name} -> {ep.value}')
"
```

If empty, reinstall the package:

```bash
pip install -e ./my-plugin
```

---

## "My controller is not registered" (pico-fastapi)

Routes exist but return 404 for all paths.

### 1. Is the class decorated with `@controller`?

```python
from pico_fastapi import controller, get

@controller(prefix="/api")    # <-- required
class UserController:
    @get("/users")
    async def list_users(self):
        ...
```

`@controller` registers the class as a `@component` and marks it for
route scanning. Without it, pico-fastapi ignores the class.

### 2. Is the controller module in the `modules` list?

```python
container = init(modules=[
    "myapp.controllers",   # must include the controller module
    "myapp.services",
])
```

### 3. Is pico-fastapi itself loaded?

If you use `pico-boot`, pico-fastapi is auto-discovered. If auto-discovery
is disabled, add the pico-fastapi modules explicitly:

```python
container = init(modules=[
    "myapp",
    "pico_fastapi.config",
    "pico_fastapi.factory",
])
```

### 4. Does the controller have unsatisfied dependencies?

If the controller's `__init__` requires a service that is not registered,
the entire controller fails to instantiate. Check the logs for
`ProviderNotFoundError`.

---

## "My `@validate` is not running" (pico-pydantic)

You pass invalid data but the method executes without raising
`ValidationFailedError`.

> **Key concept:** `@validate` is a marker, not a validator. The actual
> validation happens in `ValidationInterceptor`, which only runs when the
> component is resolved from the pico-ioc container.

### 1. Are you getting the service from the container?

```python
# Validation runs — interceptor is active
service = container.get(UserService)
await service.create_user({"bad": "data"})  # -> ValidationFailedError

# Validation does NOT run — no interceptor
service = UserService()
await service.create_user({"bad": "data"})  # -> executes normally
```

If you instantiate the class directly (with `UserService()` or in a unit
test), the interceptor never fires. This is by design — see the
[pico-pydantic testing guide](https://github.com/dperezcabrera/pico-pydantic)
for patterns that work with and without the container.

### 2. Is pico-pydantic loaded?

If you use `pico-boot`, it is auto-discovered. If auto-discovery is
disabled:

```python
container = init(modules=[
    "myapp",
    "pico_pydantic",      # registers ValidationInterceptor
])
```

### 3. Does the parameter have a `BaseModel` type hint?

Only parameters annotated with a Pydantic `BaseModel` subclass (or generics
like `List[Model]`, `Optional[Model]`, `Union[Model, ...]`) are validated.
Plain types are passed through:

```python
@validate
async def process(self, data: UserModel, count: int):
    # data  -> validated (BaseModel)
    # count -> passed through (int)
```

### 4. Is the method decorated with `@validate`?

```python
from pico_pydantic import validate

@component
class UserService:
    @validate                # <-- required on the method
    async def create_user(self, data: UserCreate):
        ...
```

Without the marker, the interceptor skips the method entirely.

---

## Circular dependencies

```
pico_ioc.exceptions.CircularDependencyError: Circular dependency detected: A -> B -> A
```

### Option 1: Use `lazy=True`

Break the cycle by deferring one of the components:

```python
@component(lazy=True)
class ServiceA:
    def __init__(self, b: ServiceB):
        self.b = b
```

The container creates a proxy for `ServiceA`. The real instance is created
on first access, by which time `ServiceB` already exists.

### Option 2: Use `@configure` for post-init wiring

```python
@component
class ServiceA:
    @configure
    def setup(self, b: ServiceB):
        self.b = b
```

`@configure` runs after all components are instantiated, so the cycle
doesn't exist at construction time.

### Option 3: Restructure

If A and B both depend on each other, they might belong in the same class,
or the shared logic should be extracted to a third service.

---

## Circular imports (Python-level)

```
ImportError: cannot import name 'ServiceB' from partially initialized module
```

This is a Python import cycle, not a pico-ioc dependency cycle.

**Fix:** Use `TYPE_CHECKING` guard:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myapp.other import ServiceB

@component
class ServiceA:
    def __init__(self, other: "ServiceB"):
        self.other = other
```

pico-ioc resolves string annotations at container init time, after all
modules are imported.

---

## Configuration not loading

### Precedence

Later sources override earlier ones. Environment variables always win:

```python
config = configuration(
    YamlTreeSource("defaults.yaml"),   # lowest priority
    YamlTreeSource("override.yaml"),   # overrides defaults
    EnvSource(),                       # highest priority
)
```

### `@configured` mapping mode

The `@configured` decorator auto-detects flat vs tree mode:

| Field types | Mode | ENV format |
|---|---|---|
| All primitives (`str`, `int`, `bool`) | flat | `PREFIX_FIELD` |
| Any nested dataclass, list, or dict | tree | `PREFIX__NESTED__FIELD` (double underscore) |

If auto-detection picks the wrong mode, force it:

```python
@configured(prefix="db", mapping="flat")
@dataclass
class DbConfig:
    host: str
    port: int
```

---

## Container returns the wrong instance

### Multiple containers

Each `init()` call creates a new, independent container:

```python
c1 = init(modules=["myapp"])
c2 = init(modules=["myapp"])

c1.get(MyService) is not c2.get(MyService)  # True — different instances
```

### Prototype scope

```python
@component(scope="prototype")    # new instance every time
class MyService: ...

s1 = container.get(MyService)
s2 = container.get(MyService)
assert s1 is not s2
```

### Active overrides

```python
container = init(
    modules=["myapp"],
    overrides={MyService: mock_service},   # check for this
)
```

---

## Slow startup

### Profile the imports

```bash
python -X importtime -c "from pico_boot import init; init(modules=['myapp'])" 2>&1 | head -50
```

### Reduce plugin scanning

```bash
export PICO_BOOT_AUTO_PLUGINS=false
```

Then list only the modules you need:

```python
container = init(modules=["myapp"])
```

### Defer heavy imports

```python
@component
class HeavyService:
    def process(self):
        import pandas as pd          # import when needed, not at module level
        return pd.DataFrame(...)
```

---

## Tests pollute each other

Create a fresh container per test and shut it down after:

```python
@pytest.fixture
def container(tmp_path):
    c = init(modules=["myapp"])
    yield c
    c.shutdown()
```

For integration tests that include pico-fastapi, also create a fresh
`FastAPI` app per test (see the pico-fastapi testing guide).

---

## Getting help

If this guide doesn't cover your issue:

1. Enable debug logging:
   ```python
   import logging
   logging.getLogger("pico_boot").setLevel(logging.DEBUG)
   logging.getLogger("pico_ioc").setLevel(logging.DEBUG)
   ```

2. Create a minimal reproduction script.

3. Open an issue at [pico-boot](https://github.com/dperezcabrera/pico-boot/issues) or the relevant package repo with:
   - Python version
   - Package versions (`pip list | grep pico`)
   - Full traceback
   - Minimal reproduction code
