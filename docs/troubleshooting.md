# Troubleshooting

This guide covers common issues and their solutions when using pico-boot.

## Plugin Discovery Issues

### Plugin Not Being Discovered

**Symptoms:**
- Plugin components are not available in the container
- No error messages, plugin is silently ignored

**Diagnosis:**

1. **Check entry point group name:**
   ```toml
   # Must be exactly this:
   [project.entry-points."pico_boot.modules"]
   my_plugin = "my_plugin"
   ```

2. **Verify entry point is registered:**
   ```bash
   python -c "from importlib.metadata import entry_points; print([ep for ep in entry_points(group='pico_boot.modules')])"
   ```

3. **Check if package is installed:**
   ```bash
   pip show my-plugin
   ```

4. **Check if editable install is needed:**
   ```bash
   pip install -e ./my-plugin
   ```

**Solutions:**

- Fix the entry point group name (must be `pico_boot.modules`)
- Reinstall the package after changing `pyproject.toml`
- Use editable install during development

---

### Plugin Import Fails Silently

**Symptoms:**
- Plugin is registered but components aren't available
- No visible error

**Diagnosis:**

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("pico_boot").setLevel(logging.DEBUG)

from pico_boot import init
container = init(modules=["myapp"])
```

Look for warnings like:
```
WARNING:pico_boot:Failed to load pico-boot plugin entry point 'my_plugin' (my_plugin): ...
```

**Common causes:**

1. **Missing dependency:**
   ```
   ModuleNotFoundError: No module named 'some_dependency'
   ```
   Solution: Add missing dependency to plugin's `pyproject.toml`

2. **Syntax error in plugin:**
   ```
   SyntaxError: invalid syntax
   ```
   Solution: Fix the syntax error in the plugin module

3. **Import-time exception:**
   ```
   Exception: Something failed during import
   ```
   Solution: Wrap problematic code in functions, not module-level

---

### Auto-Discovery Disabled Unexpectedly

**Symptoms:**
- Plugins not loaded even though they're installed

**Diagnosis:**

```bash
echo $PICO_BOOT_AUTO_PLUGINS
```

**Solution:**

Unset or set to "true":

```bash
unset PICO_BOOT_AUTO_PLUGINS
# or
export PICO_BOOT_AUTO_PLUGINS=true
```

---

## Container Issues

### "Component not found" Error

**Symptoms:**
```
pico_ioc.exceptions.ComponentNotFoundError: No component registered for type 'MyService'
```

**Diagnosis checklist:**

1. **Is the module in the modules list?**
   ```python
   container = init(modules=["myapp.services"])  # Include the right module
   ```

2. **Does the class have a decorator?**
   ```python
   @component  # Required!
   class MyService:
       pass
   ```

3. **Is the decorator imported from pico_ioc?**
   ```python
   from pico_ioc import component  # Correct
   # NOT: from pico_boot import component  # Wrong!
   ```

4. **Is there an import error in the module?**
   ```python
   # Test the import
   python -c "import myapp.services"
   ```

5. **Is a profile required?**
   ```python
   @component(profiles=["production"])  # Only active with profile
   class MyService:
       pass

   # Activate the profile
   container = init(modules=["myapp"], profiles=["production"])
   ```

---

### Getting Wrong Instance

**Symptoms:**
- Component returns unexpected values
- Singleton returns different instances

**Diagnosis:**

1. **Multiple containers?**
   ```python
   # Each init() creates a NEW container
   container1 = init(modules=["myapp"])
   container2 = init(modules=["myapp"])

   # These are DIFFERENT instances:
   service1 = container1.get(MyService)
   service2 = container2.get(MyService)
   ```

2. **Prototype scope?**
   ```python
   @component(scope="prototype")  # New instance each time
   class MyService:
       pass
   ```

3. **Override in effect?**
   ```python
   container = init(
       modules=["myapp"],
       overrides={MyService: mock_service}  # Check for overrides
   )
   ```

---

### Circular Dependency Error

**Symptoms:**
```
pico_ioc.exceptions.CircularDependencyError: Circular dependency detected: A -> B -> A
```

**Solutions:**

1. **Use lazy injection:**
   ```python
   from pico_ioc import Lazy

   @component
   class ServiceA:
       def __init__(self, b: Lazy[ServiceB]):
           self._b = b

       def use_b(self):
           return self._b().do_something()
   ```

2. **Restructure dependencies:**
   - Extract common functionality to a third service
   - Use events instead of direct dependencies

---

## Import Issues

### "Module not found" Error

**Symptoms:**
```
ModuleNotFoundError: No module named 'myapp'
```

**Diagnosis:**

```bash
# Check if module is in Python path
python -c "import myapp"

# Check Python path
python -c "import sys; print(sys.path)"
```

**Solutions:**

1. **Install the package:**
   ```bash
   pip install -e .
   ```

2. **Add to PYTHONPATH:**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/myapp"
   ```

3. **Check module name:**
   ```python
   # File: myapp/services.py
   # Module name: myapp.services (not myapp/services)

   container = init(modules=["myapp.services"])
   ```

---

### Import Order Issues

**Symptoms:**
- Works sometimes, fails other times
- Depends on which module is imported first

**Cause:** Circular imports at module level

**Solution:**

Move imports inside functions or use `TYPE_CHECKING`:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myapp.other import OtherService

@component
class MyService:
    def __init__(self, other: "OtherService"):
        self.other = other
```

---

## Performance Issues

### Slow Startup

**Symptoms:**
- Application takes long to start
- Delay at `init()` call

**Diagnosis:**

1. **Many plugins installed:**
   ```bash
   python -c "from importlib.metadata import entry_points; print(len(list(entry_points(group='pico_boot.modules'))))"
   ```

2. **Heavy module imports:**
   Profile the imports:
   ```bash
   python -X importtime -c "from pico_boot import init; init(modules=['myapp'])" 2>&1 | head -50
   ```

**Solutions:**

1. **Disable auto-discovery:**
   ```bash
   export PICO_BOOT_AUTO_PLUGINS=false
   ```

2. **Explicitly list modules:**
   ```python
   container = init(modules=[
       "myapp.services",
       "myapp.repos",
       # Only what you need
   ])
   ```

3. **Lazy imports in modules:**
   ```python
   # Don't import heavy libraries at module level
   @component
   class MyService:
       def heavy_operation(self):
           import heavy_library  # Import when needed
           return heavy_library.process()
   ```

---

## Testing Issues

### Tests Pollute Each Other

**Symptoms:**
- Tests pass individually, fail together
- Order-dependent test failures

**Cause:** Shared container state between tests

**Solution:**

Create fresh container per test:

```python
import pytest
from pico_boot import init

@pytest.fixture
def container():
    c = init(modules=["myapp"])
    yield c
    c.shutdown()

def test_one(container):
    service = container.get(MyService)
    # ...

def test_two(container):
    service = container.get(MyService)  # Fresh instance
    # ...
```

---

### Mocking Doesn't Work

**Symptoms:**
- Mock objects not used
- Real implementations called

**Cause:** Container created before mock applied

**Solution:**

Use container overrides:

```python
def test_with_mock():
    mock_repo = Mock(spec=Repository)
    mock_repo.get_all.return_value = []

    container = init(
        modules=["myapp"],
        overrides={Repository: mock_repo}
    )

    service = container.get(MyService)
    service.process()

    mock_repo.get_all.assert_called_once()
```

---

## Environment Issues

### Different Behavior in Production

**Symptoms:**
- Works in development, fails in production
- Missing plugins in Docker

**Diagnosis:**

1. **Check installed packages:**
   ```bash
   pip list | grep pico
   ```

2. **Check environment variables:**
   ```bash
   env | grep PICO
   ```

3. **Check Python version:**
   ```bash
   python --version  # Must be 3.11+
   ```

**Solutions:**

1. **Pin dependencies:**
   ```
   pico-boot==0.1.0
   pico-ioc==2.2.0
   pico-fastapi==0.2.0
   ```

2. **Verify Docker installs all packages:**
   ```dockerfile
   RUN pip install -r requirements.txt
   ```

3. **Log plugin discovery:**
   ```python
   import logging
   logging.getLogger("pico_boot").setLevel(logging.INFO)
   ```

---

## Getting Help

If you can't resolve your issue:

1. **Search existing issues:** [GitHub Issues](https://github.com/dperezcabrera/pico-boot/issues)

2. **Create a minimal reproduction:**
   ```python
   # minimal_repro.py
   from pico_ioc import component
   from pico_boot import init

   @component
   class MyService:
       pass

   container = init(modules=[__name__])
   service = container.get(MyService)  # Error here
   ```

3. **Open an issue** with:
   - Python version
   - pico-boot version
   - pico-ioc version
   - Minimal reproduction code
   - Full error traceback
