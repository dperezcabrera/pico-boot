# How to Test With and Without Auto-Discovery

This guide covers testing strategies for applications that use `pico_boot.init()`, focusing on the `PICO_BOOT_AUTO_PLUGINS` environment variable.

## Why Auto-Discovery Matters in Tests

When auto-discovery is enabled (the default), every installed pico plugin is
imported during `init()`.  In a test environment this can cause:

- Slow test startup due to importing heavy plugin modules.
- Unexpected failures when a plugin requires a running database, message
  broker, or other external service.
- Non-deterministic behaviour depending on which packages happen to be
  installed in the test environment.

Disabling auto-discovery gives tests full control over which modules are
loaded.

## Disable Auto-Discovery Globally for Tests

The simplest approach is to disable auto-discovery for the whole test suite
using a `conftest.py` at the project root:

```python
# conftest.py
import os

def pytest_configure(config):
    os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"
```

Every test that calls `init()` will now only load the modules passed
explicitly.

## Per-Test Control With a Fixture

When some tests need auto-discovery and others do not, use a pytest fixture:

```python
# conftest.py
import os
import pytest

@pytest.fixture()
def no_auto_plugins(monkeypatch):
    """Disable pico-boot auto-discovery for a single test."""
    monkeypatch.setenv("PICO_BOOT_AUTO_PLUGINS", "false")

@pytest.fixture()
def with_auto_plugins(monkeypatch):
    """Ensure pico-boot auto-discovery is enabled for a single test."""
    monkeypatch.setenv("PICO_BOOT_AUTO_PLUGINS", "true")
```

Usage:

```python
from pico_boot import init

def test_unit_isolated(no_auto_plugins):
    container = init(modules=["myapp.services"])
    # only myapp.services is loaded

def test_integration_full(with_auto_plugins):
    container = init(modules=["myapp.services"])
    # all installed plugins are also loaded
```

## Fresh Container Per Test

Always create a new container in each test and shut it down afterwards to
avoid leaked state:

```python
import pytest
from pico_boot import init

@pytest.fixture()
def container(no_auto_plugins):
    c = init(modules=["myapp.services"])
    yield c
    c.shutdown()

def test_service(container):
    service = container.get(MyService)
    assert service.do_work() == "expected"
```

## Testing With Overrides

Use the *overrides* parameter to replace real implementations with mocks:

```python
from unittest.mock import Mock
from pico_boot import init

def test_with_mock(no_auto_plugins):
    mock_repo = Mock(spec=Repository)
    mock_repo.find_all.return_value = []

    container = init(
        modules=["myapp.services"],
        overrides={Repository: mock_repo},
    )

    service = container.get(MyService)
    assert service.list_items() == []
    mock_repo.find_all.assert_called_once()
    container.shutdown()
```

## Integration Tests With Real Plugins

For integration tests that verify plugin wiring, enable auto-discovery and
provide the required configuration:

```python
import os
import pytest
from pico_ioc import DictSource, configuration
from pico_boot import init

pico_fastapi = pytest.importorskip("pico_fastapi")

def test_fastapi_plugin_loads():
    os.environ["PICO_BOOT_AUTO_PLUGINS"] = "true"

    config = configuration(
        DictSource({"fastapi": {"title": "Test App", "version": "0.0.1"}})
    )
    container = init(modules=[__name__], config=config)

    settings = container.get(pico_fastapi.FastApiSettings)
    assert settings.title == "Test App"
    container.shutdown()
```

## Mocking Entry Points

For unit tests that should not depend on which packages are installed, mock
the entry-point machinery directly:

```python
from types import ModuleType
from unittest.mock import MagicMock, patch
from pico_boot import init

def test_with_mocked_plugins():
    fake_module = ModuleType("fake_plugin")
    fake_module.__name__ = "fake_plugin"

    ep = MagicMock()
    ep.name = "fake_plugin"
    ep.module = "fake_plugin"

    with patch("pico_boot.entry_points") as mock_eps:
        mock_result = MagicMock()
        mock_result.select.return_value = [ep]
        mock_eps.return_value = mock_result

        with patch("pico_boot.import_module", return_value=fake_module):
            container = init(modules=[])
            container.shutdown()
```
