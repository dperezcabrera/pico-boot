
# Pico Stack Demo

This demo shows how Pico Stack automatically loads integration modules via Python entry points.

## How it works

- Libraries that want to participate in the dependency-injection stack declare an entry point under the group `pico_stack.modules`.
- When a project calls `pico_stack.init()`, Pico Stack:
  1. Loads the modules explicitly passed by the application.
  2. Scans all installed packages for `pico_stack.modules` entry points.
  3. Imports the associated modules and adds them to the DI environment.
  4. Delegates to `pico_ioc.init()` with the complete module list.

This makes integrations zero‑configuration for the application: simply installing the package is enough.

## Example Entry Point

```toml
[project.entry-points."pico_stack.modules"]
pico_sqlalchemy = "pico_sqlalchemy"
```

## Usage in an Application

```python
from pico_stack import init
import my_app

container = init(my_app)
```

No need to explicitly mention `pico_sqlalchemy` or other integration libraries.
