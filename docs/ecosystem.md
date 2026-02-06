# Pico Ecosystem

The Pico framework consists of multiple packages that work together seamlessly.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Application                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         pico-boot                              │
│              Zero-configuration bootstrap layer                  │
│         (auto-discovery, scanner harvesting)                    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          pico-ioc                               │
│                   Core DI Container Engine                       │
│    (components, factories, scopes, AOP, event bus, config)      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   pico-fastapi  │ │ pico-sqlalchemy │ │   pico-celery   │
│                 │ │                 │ │                 │
│  FastAPI routes │ │  SQLAlchemy ORM │ │  Celery tasks   │
│  & middleware   │ │  & sessions     │ │  & workers      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │                                       │
          ▼                                       ▼
┌─────────────────┐                     ┌─────────────────┐
│  pico-pydantic  │                     │   pico-agent    │
│                 │                     │                 │
│   Validation    │                     │   LLM agents    │
│  interceptors   │                     │   & tools       │
└─────────────────┘                     └─────────────────┘
```

## Core Packages

### pico-ioc

The foundation of the ecosystem. A lightweight, async-native dependency injection container.

| | |
|---|---|
| **PyPI** | [pico-ioc](https://pypi.org/project/pico-ioc/) |
| **Repository** | [github.com/dperezcabrera/pico-ioc](https://github.com/dperezcabrera/pico-ioc) |
| **Documentation** | [dperezcabrera.github.io/pico-ioc](https://dperezcabrera.github.io/pico-ioc/) |

**Features:**
- Decorator-based component registration (`@component`, `@provides`, `@factory`)
- Unified configuration binding (`@configured`)
- Multiple scopes (singleton, prototype, request, session)
- AOP interceptors (`@intercepted_by`)
- Async-native (`__ainit__`, `aget()`, `ashutdown()`)
- Event bus for decoupled communication
- Health checks and observability

**Installation:**
```bash
pip install pico-ioc
pip install pico-ioc[yaml]  # For YAML config support
```

### pico-boot

Zero-configuration bootstrap layer. Recommended for applications.

| | |
|---|---|
| **PyPI** | [pico-boot](https://pypi.org/project/pico-boot/) |
| **Repository** | [github.com/dperezcabrera/pico-boot](https://github.com/dperezcabrera/pico-boot) |
| **Documentation** | [dperezcabrera.github.io/pico-boot](https://dperezcabrera.github.io/pico-boot/) |

**Features:**
- Auto-discovery of plugins via entry points
- Custom scanner harvesting
- Drop-in replacement for `pico_ioc.init()`

**Installation:**
```bash
pip install pico-boot
```

---

## Integration Packages

### pico-fastapi

FastAPI integration with automatic dependency injection in routes.

| | |
|---|---|
| **PyPI** | [pico-fastapi](https://pypi.org/project/pico-fastapi/) |
| **Repository** | [github.com/dperezcabrera/pico-fastapi](https://github.com/dperezcabrera/pico-fastapi) |

**Features:**
- Automatic injection in route handlers
- Request-scoped dependencies
- Middleware integration
- Lifespan management

**Usage:**
```python
from fastapi import FastAPI
from pico_boot import init
from pico_fastapi import PicoFastAPI

app = FastAPI()
container = init(modules=["myapp"])
pico = PicoFastAPI(container)
pico.install(app)

@app.get("/")
def index(service: MyService):  # Injected automatically
    return service.get_data()
```

### pico-sqlalchemy

SQLAlchemy integration with session management.

| | |
|---|---|
| **PyPI** | [pico-sqlalchemy](https://pypi.org/project/pico-sqlalchemy/) |
| **Repository** | [github.com/dperezcabrera/pico-sqlalchemy](https://github.com/dperezcabrera/pico-sqlalchemy) |

**Features:**
- Engine and session factory providers
- Request-scoped sessions
- Transaction management
- Async engine support

**Configuration:**
```yaml
database:
  url: postgresql://user:pass@localhost/db
  pool_size: 5
  echo: false
```

### pico-celery

Celery integration for background tasks.

| | |
|---|---|
| **PyPI** | [pico-celery](https://pypi.org/project/pico-celery/) |
| **Repository** | [github.com/dperezcabrera/pico-celery](https://github.com/dperezcabrera/pico-celery) |

**Features:**
- Task registration with DI
- Worker container management
- Result backend configuration

**Configuration:**
```yaml
celery:
  broker_url: redis://localhost:6379/0
  result_backend: redis://localhost:6379/1
```

### pico-pydantic

Pydantic validation via AOP interceptors.

| | |
|---|---|
| **PyPI** | [pico-pydantic](https://pypi.org/project/pico-pydantic/) |
| **Repository** | [github.com/dperezcabrera/pico-pydantic](https://github.com/dperezcabrera/pico-pydantic) |

**Features:**
- Automatic input validation
- Output serialization
- Error formatting

**Usage:**
```python
from pico_ioc import component, intercepted_by
from pico_pydantic import ValidationInterceptor

@component
class UserService:
    @intercepted_by(ValidationInterceptor)
    def create_user(self, data: CreateUserRequest) -> UserResponse:
        # data is validated automatically
        pass
```

### pico-agent

LLM agent framework with dependency injection.

| | |
|---|---|
| **PyPI** | [pico-agent](https://pypi.org/project/pico-agent/) |
| **Repository** | [github.com/dperezcabrera/pico-agent](https://github.com/dperezcabrera/pico-agent) |

**Features:**
- Declarative agent definitions with `@agent` and `@tool`
- Multiple LLM backends (OpenAI, Gemini, LangChain)
- Agent capabilities (memory, structured output, streaming)
- Virtual and proxy agent patterns

**Usage:**
```python
from pico_agent import agent, tool, AgentType

@agent(type=AgentType.OPENAI)
class AssistantAgent:
    system_prompt = "You are a helpful assistant."

@tool
def search(query: str) -> str:
    return f"Results for {query}"
```

---

## Version Compatibility

| Package | pico-ioc Version | Python |
|---------|------------------|--------|
| pico-boot | >= 2.1.0 | 3.11+ |
| pico-fastapi | >= 2.0.0 | 3.11+ |
| pico-sqlalchemy | >= 2.0.0 | 3.11+ |
| pico-celery | >= 2.0.0 | 3.11+ |
| pico-pydantic | >= 2.0.0 | 3.11+ |
| pico-agent | >= 2.0.0 | 3.11+ |

---

## Quick Start: Full Stack

Install everything:

```bash
pip install pico-boot pico-fastapi pico-sqlalchemy pico-pydantic
```

Create `application.yaml`:

```yaml
app:
  name: My Application
  debug: false

database:
  url: postgresql://localhost/myapp
  pool_size: 10
```

Create your application:

```python
# main.py
from fastapi import FastAPI
from pico_boot import init
from pico_fastapi import PicoFastAPI
from pico_ioc import component
from sqlalchemy.orm import Session

@component
class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self):
        return self.session.query(User).all()

app = FastAPI()
container = init(modules=[__name__])
PicoFastAPI(container).install(app)

@app.get("/users")
def list_users(repo: UserRepository):
    return repo.get_all()
```

Run:

```bash
uvicorn main:app --reload
```

All integrations are loaded automatically!

---

## Creating Your Own Integration

See [Creating Plugins](./creating-plugins.md) for a complete guide on building your own Pico-Boot integration.

Key steps:

1. Add entry point to `pyproject.toml`:
   ```toml
   [project.entry-points."pico_boot.modules"]
   my_integration = "my_integration"
   ```

2. Define configuration with `@configured`
3. Create components with `@component`
4. Provide third-party types with `@provides`
5. Publish to PyPI
