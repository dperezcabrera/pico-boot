# AI Coding Skills

[Claude Code](https://code.claude.com) and [OpenAI Codex](https://openai.com/index/introducing-codex/) skills for AI-assisted development with pico-boot and the pico-framework ecosystem.

## Installation

Install pico-boot skills only:

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- boot
```

Or install all pico-framework skills (ioc, boot, fastapi, sqlalchemy, celery, pydantic, agent):

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash
```

### Platform-specific

```bash
# Claude Code only
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- --claude boot

# OpenAI Codex only
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- --codex boot
```

## Available Commands

### `/add-app`

Scaffolds a new pico-boot application with a ready-to-run project structure.

**What it generates:**
- `main.py` with `pico_boot.init()` entry point
- `config.py` with `@configured` dataclass
- `services.py` with example `@component`
- `application.yaml` with default configuration
- `pyproject.toml` with dependencies and entry points

```
/add-app my-project
```

### `/add-component`

Adds a new pico-ioc component to the current project. Supports multiple component types.

**Component types:** service, factory, interceptor, event subscriber, configured settings.

```
/add-component UserService
/add-component RedisFactory --type factory
/add-component LogInterceptor --type interceptor
/add-component AppSettings --type settings
```

### `/add-tests`

Generates tests for existing pico-framework components. Creates unit tests with proper container setup, overrides, and assertions.

```
/add-tests UserService
/add-tests UserRepository --integration
```

## More Information

See [pico-skills](https://github.com/dperezcabrera/pico-skills) for the full list of skills, selective installation, and details.
