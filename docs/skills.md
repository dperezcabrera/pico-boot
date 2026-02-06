# Claude Code Skills

Pico-Boot includes pre-designed skills for [Claude Code](https://claude.ai/claude-code) that enable AI-assisted development following pico-framework patterns and best practices.

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Pico Boot Application** | `/pico-boot-app` | Configures applications with pico-boot auto-discovery |
| **Pico Component Creator** | `/pico-component` | Creates components with DI, scopes, factories and interceptors |
| **Pico Test Generator** | `/pico-tests` | Generates tests for pico-framework components |

---

## Pico Boot Application

Sets up a complete pico-boot application with auto-discovery.

### Project Structure

```
my_app/
├── __init__.py
├── main.py
├── settings.py
├── components/
│   ├── __init__.py
│   ├── services.py
│   └── repositories.py
├── api/
│   ├── __init__.py
│   └── routes.py
└── tests/
    └── ...
```

### main.py

```python
from pico_ioc import configuration, YamlSource, EnvSource
from pico_boot import init

def main():
    config = configuration(
        YamlSource("application.yaml"),
        EnvSource()
    )
    container = init(modules=["myapp"], config=config)
    # All pico-* plugins are auto-discovered!

if __name__ == "__main__":
    main()
```

### settings.py

```python
from dataclasses import dataclass
from pico_ioc import configured

@configured(prefix="app")
@dataclass
class AppSettings:
    name: str = "My Application"
    debug: bool = False
```

---

## Pico Test Generator

Generates tests for any pico-framework component.

### Test Structure

```python
import pytest
from unittest.mock import MagicMock
from pico_ioc import PicoContainer

@pytest.fixture
def container():
    """Container with mocks for testing."""
    container = PicoContainer()
    return container

@pytest.fixture
def service(container):
    return container.get(MyService)

class TestMyService:
    def test_get_returns_item(self, service):
        result = service.get(1)
        assert result.id == 1
```

---

## Installation

```bash
# Project-level (recommended)
mkdir -p .claude/skills/pico-boot-app
# Copy the skill YAML+Markdown to .claude/skills/pico-boot-app/SKILL.md

mkdir -p .claude/skills/pico-tests
# Copy the skill YAML+Markdown to .claude/skills/pico-tests/SKILL.md

# Or user-level (available in all projects)
mkdir -p ~/.claude/skills/pico-boot-app
mkdir -p ~/.claude/skills/pico-tests
```

## Usage

```bash
# Invoke directly in Claude Code
/pico-boot-app
/pico-tests UserService
```

See the full skill templates in the [pico-framework skill catalog](https://github.com/dperezcabrera/pico-boot).
