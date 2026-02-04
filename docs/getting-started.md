# Getting Started with Pico-Stack

This guide walks you through setting up your first application with Pico-Stack.

## Prerequisites

- Python 3.10 or newer
- Basic understanding of dependency injection concepts

## Installation

```bash
pip install pico-stack
```

This installs both `pico-stack` and `pico-ioc` (the core DI container).

For YAML configuration support:

```bash
pip install pico-stack pico-ioc[yaml]
```

## Your First Application

### Step 1: Create Your Components

```python
# myapp/services.py
from pico_ioc import component

@component
class DatabaseService:
    """Handles database operations."""

    def get_user(self, user_id: int) -> dict:
        return {"id": user_id, "name": "Alice"}

@component
class UserService:
    """Business logic for users."""

    def __init__(self, db: DatabaseService):
        self.db = db

    def greet_user(self, user_id: int) -> str:
        user = self.db.get_user(user_id)
        return f"Hello, {user['name']}!"
```

### Step 2: Initialize the Container

```python
# myapp/main.py
from pico_stack import init
from myapp.services import UserService

def main():
    # Initialize with auto-discovery
    container = init(modules=["myapp.services"])

    # Get your service
    user_service = container.get(UserService)

    # Use it
    print(user_service.greet_user(1))

    # Clean shutdown
    container.shutdown()

if __name__ == "__main__":
    main()
```

### Step 3: Run

```bash
$ python -m myapp.main
Hello, Alice!
```

## Adding Configuration

### Step 1: Create a Configuration File

```yaml
# application.yaml
app:
  name: My Application
  debug: false

database:
  host: localhost
  port: 5432
```

### Step 2: Define Configuration Classes

```python
# myapp/config.py
from dataclasses import dataclass
from pico_ioc import configured

@configured(prefix="app")
@dataclass
class AppConfig:
    name: str
    debug: bool = False

@configured(prefix="database")
@dataclass
class DatabaseConfig:
    host: str
    port: int = 5432
```

### Step 3: Use Configuration in Components

```python
# myapp/services.py
from pico_ioc import component
from myapp.config import DatabaseConfig

@component
class DatabaseService:
    def __init__(self, config: DatabaseConfig):
        self.host = config.host
        self.port = config.port

    def connect(self):
        print(f"Connecting to {self.host}:{self.port}")
```

### Step 4: Update Initialization

```python
# myapp/main.py
from pico_stack import init

container = init(modules=["myapp.config", "myapp.services"])
```

Pico-Stack automatically finds `application.yaml` and loads it!

## Environment Variable Overrides

Environment variables always take precedence:

```bash
# Override database host
$ DATABASE_HOST=prod-db.example.com python -m myapp.main
Connecting to prod-db.example.com:5432
```

## Adding Integrations

Install integration packages and they're automatically discovered:

```bash
pip install pico-fastapi pico-sqlalchemy
```

No code changes needed - Pico-Stack finds and loads them automatically!

## Next Steps

- [Configuration Guide](./configuration.md) - Deep dive into configuration
- [Plugins Guide](./plugins.md) - Create your own plugins
- [API Reference](./api-reference.md) - Complete API documentation
