# Getting Started

This guide walks you through creating your first application with Pico-Boot.

## Prerequisites

- **Python 3.11** or newer
- Basic understanding of dependency injection concepts

## Installation

```bash
pip install pico-boot
```

This installs both `pico-boot` and `pico-ioc` (the core DI container).

For YAML configuration support:

```bash
pip install pico-boot "pico-ioc[yaml]"
```

## Understanding the Basics

### Key Concepts

1. **Container**: Manages component lifecycle and dependencies
2. **Component**: A class registered with the container (`@component`)
3. **Provider**: A function that creates instances (`@provides`)
4. **Module**: A Python module containing components to scan

### Import Pattern

```python
# Decorators come from pico-ioc
from pico_ioc import component, provides, configured

# Only init() comes from pico-boot
from pico_boot import init
```

## Your First Application

### Step 1: Create Components

```python
# myapp/services.py
from pico_ioc import component

@component
class DatabaseService:
    """Simulates database operations."""

    def get_user(self, user_id: int) -> dict:
        # In a real app, this would query a database
        return {"id": user_id, "name": "Alice", "email": "alice@example.com"}

    def save_user(self, user: dict) -> bool:
        print(f"Saving user: {user}")
        return True


@component
class UserService:
    """Business logic for user operations."""

    def __init__(self, db: DatabaseService):
        # DatabaseService is injected automatically
        self.db = db

    def get_user_profile(self, user_id: int) -> dict:
        user = self.db.get_user(user_id)
        return {
            "id": user["id"],
            "display_name": user["name"],
            "contact": user["email"]
        }

    def update_email(self, user_id: int, new_email: str) -> bool:
        user = self.db.get_user(user_id)
        user["email"] = new_email
        return self.db.save_user(user)
```

### Step 2: Initialize and Use

```python
# myapp/main.py
from pico_boot import init
from myapp.services import UserService

def main():
    # Initialize the container
    # pico-boot scans the modules for @component decorated classes
    container = init(modules=["myapp.services"])

    # Get your service - dependencies are resolved automatically
    user_service = container.get(UserService)

    # Use the service
    profile = user_service.get_user_profile(1)
    print(f"User profile: {profile}")

    # Clean shutdown (calls cleanup methods, releases resources)
    container.shutdown()

if __name__ == "__main__":
    main()
```

### Step 3: Run

```bash
python -m myapp.main
```

Output:
```
User profile: {'id': 1, 'display_name': 'Alice', 'contact': 'alice@example.com'}
```

## Adding Configuration

### Step 1: Create Configuration File

```yaml
# application.yaml
database:
  host: localhost
  port: 5432
  name: myapp

app:
  debug: true
  log_level: INFO
```

### Step 2: Define Configuration Classes

```python
# myapp/config.py
from dataclasses import dataclass
from pico_ioc import configured

@configured(prefix="database")
@dataclass
class DatabaseConfig:
    host: str
    port: int = 5432
    name: str = "default"


@configured(prefix="app")
@dataclass
class AppConfig:
    debug: bool = False
    log_level: str = "WARNING"
```

### Step 3: Use Configuration in Components

```python
# myapp/services.py
from pico_ioc import component
from myapp.config import DatabaseConfig, AppConfig

@component
class DatabaseService:
    def __init__(self, config: DatabaseConfig):
        self.host = config.host
        self.port = config.port
        self.db_name = config.name
        print(f"Connecting to {self.host}:{self.port}/{self.db_name}")

    # ... rest of the class
```

### Step 4: Initialize with Configuration

```python
# myapp/main.py
from pico_ioc import configuration, YamlSource, EnvSource
from pico_boot import init

# Load configuration from YAML, then overlay environment variables
config = configuration(
    YamlSource("application.yaml"),
    EnvSource()  # DATABASE_HOST, DATABASE_PORT, etc.
)

container = init(
    modules=["myapp.config", "myapp.services"],
    config=config
)
```

## Using Providers

For third-party classes you can't decorate:

```python
# myapp/providers.py
from pico_ioc import provides
import redis

from myapp.config import RedisConfig

@provides(redis.Redis)
def create_redis_client(config: RedisConfig) -> redis.Redis:
    """Creates and configures a Redis client."""
    return redis.Redis(
        host=config.host,
        port=config.port,
        decode_responses=True
    )
```

Now any component can inject `redis.Redis`:

```python
@component
class CacheService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def get(self, key: str) -> str | None:
        return self.redis.get(key)
```

## Working with Multiple Modules

### Project Structure

```
myapp/
├── __init__.py
├── main.py
├── config.py
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   └── order_service.py
├── repositories/
│   ├── __init__.py
│   ├── user_repo.py
│   └── order_repo.py
└── providers/
    ├── __init__.py
    └── database.py
```

### Initialize All Modules

```python
# myapp/main.py
from pico_boot import init

container = init(modules=[
    "myapp.config",
    "myapp.services.user_service",
    "myapp.services.order_service",
    "myapp.repositories.user_repo",
    "myapp.repositories.order_repo",
    "myapp.providers.database",
])
```

Or use package-level imports:

```python
# myapp/services/__init__.py
from .user_service import UserService
from .order_service import OrderService

# myapp/main.py
container = init(modules=[
    "myapp.config",
    "myapp.services",      # Imports __init__.py
    "myapp.repositories",
    "myapp.providers",
])
```

## Plugin Auto-Discovery

When you install pico ecosystem packages, they're discovered automatically:

```bash
pip install pico-fastapi pico-sqlalchemy
```

```python
from pico_boot import init

# pico-fastapi and pico-sqlalchemy components are loaded automatically!
container = init(modules=["myapp"])
```

### Disabling Auto-Discovery

For testing or explicit control:

```bash
export PICO_BOOT_AUTO_PLUGINS=false
```

```python
from pico_boot import init

# Only myapp is loaded, no plugins
container = init(modules=["myapp"])
```

## Testing Your Application

### Using Overrides

```python
# tests/test_user_service.py
import pytest
from pico_boot import init
from myapp.services import UserService, DatabaseService

class MockDatabase:
    def get_user(self, user_id: int) -> dict:
        return {"id": user_id, "name": "Test User", "email": "test@test.com"}

    def save_user(self, user: dict) -> bool:
        return True

@pytest.fixture
def container():
    c = init(
        modules=["myapp.services"],
        overrides={DatabaseService: MockDatabase()}
    )
    yield c
    c.shutdown()

def test_get_user_profile(container):
    service = container.get(UserService)
    profile = service.get_user_profile(1)

    assert profile["display_name"] == "Test User"
    assert profile["contact"] == "test@test.com"
```

### Isolating Tests

Disable plugin auto-discovery in tests:

```python
# conftest.py
import os

def pytest_configure(config):
    os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"
```

## Complete Example Application

Here's a complete, runnable example:

### Project Structure

```
todo_app/
├── application.yaml
├── main.py
├── config.py
├── models.py
├── repositories.py
└── services.py
```

### application.yaml

```yaml
app:
  name: Todo Application
  version: 1.0.0

storage:
  type: memory
```

### config.py

```python
from dataclasses import dataclass
from pico_ioc import configured

@configured(prefix="app")
@dataclass
class AppConfig:
    name: str
    version: str = "0.0.0"

@configured(prefix="storage")
@dataclass
class StorageConfig:
    type: str = "memory"
```

### models.py

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Todo:
    id: int
    title: str
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
```

### repositories.py

```python
from pico_ioc import component
from models import Todo

@component
class TodoRepository:
    def __init__(self):
        self._todos: dict[int, Todo] = {}
        self._next_id = 1

    def create(self, title: str) -> Todo:
        todo = Todo(id=self._next_id, title=title)
        self._todos[todo.id] = todo
        self._next_id += 1
        return todo

    def get(self, todo_id: int) -> Todo | None:
        return self._todos.get(todo_id)

    def get_all(self) -> list[Todo]:
        return list(self._todos.values())

    def update(self, todo: Todo) -> bool:
        if todo.id in self._todos:
            self._todos[todo.id] = todo
            return True
        return False

    def delete(self, todo_id: int) -> bool:
        if todo_id in self._todos:
            del self._todos[todo_id]
            return True
        return False
```

### services.py

```python
from pico_ioc import component
from config import AppConfig
from models import Todo
from repositories import TodoRepository

@component
class TodoService:
    def __init__(self, repo: TodoRepository, config: AppConfig):
        self.repo = repo
        self.app_name = config.name

    def add_todo(self, title: str) -> Todo:
        return self.repo.create(title)

    def complete_todo(self, todo_id: int) -> bool:
        todo = self.repo.get(todo_id)
        if todo:
            todo.completed = True
            return self.repo.update(todo)
        return False

    def list_todos(self) -> list[Todo]:
        return self.repo.get_all()

    def get_app_info(self) -> str:
        return f"Running {self.app_name}"
```

### main.py

```python
from pico_ioc import configuration, YamlSource, EnvSource
from pico_boot import init
from services import TodoService

def main():
    # Load configuration
    config = configuration(
        YamlSource("application.yaml"),
        EnvSource()
    )

    # Initialize container
    container = init(
        modules=["config", "repositories", "services"],
        config=config
    )

    # Get service
    todo_service = container.get(TodoService)

    # Use the application
    print(todo_service.get_app_info())

    # Add some todos
    todo1 = todo_service.add_todo("Learn pico-boot")
    todo2 = todo_service.add_todo("Build an application")
    todo3 = todo_service.add_todo("Deploy to production")

    print(f"\nCreated todos:")
    for todo in todo_service.list_todos():
        print(f"  [{todo.id}] {todo.title}")

    # Complete a todo
    todo_service.complete_todo(1)

    print(f"\nAfter completing todo 1:")
    for todo in todo_service.list_todos():
        status = "✓" if todo.completed else " "
        print(f"  [{status}] {todo.title}")

    # Cleanup
    container.shutdown()

if __name__ == "__main__":
    main()
```

### Run It

```bash
python main.py
```

Output:
```
Running Todo Application

Created todos:
  [1] Learn pico-boot
  [2] Build an application
  [3] Deploy to production

After completing todo 1:
  [✓] Learn pico-boot
  [ ] Build an application
  [ ] Deploy to production
```

## Next Steps

- [Configuration Guide](./configuration.md) - Deep dive into configuration
- [Plugins Guide](./plugins.md) - Understanding plugin discovery
- [Creating Plugins](./creating-plugins.md) - Build your own plugins
- [API Reference](./api-reference.md) - Complete API documentation
- [FAQ](./faq.md) - Common questions answered
