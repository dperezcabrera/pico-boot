# Configuration

Pico-Boot provides automatic configuration loading with sensible defaults.

## How It Works

When you call `init()` without a custom `config` parameter, Pico-Boot:

1. Searches for configuration files in the current directory
2. Loads matching files (YAML/JSON)
3. Overlays environment variables on top

## Configuration File Discovery

Pico-Boot looks for files in this order:

1. Path specified by `PICO_BOOT_CONFIG_FILE` environment variable
2. `application.yaml`
3. `application.yml`
4. `application.json`
5. `settings.yaml`
6. `settings.yml`
7. `settings.json`

The first matching file is loaded. Multiple files are **not** merged.

## File Formats

### YAML (Recommended)

```yaml
# application.yaml
database:
  host: localhost
  port: 5432
  name: myapp
  pool_size: 10

cache:
  enabled: true
  ttl: 3600

logging:
  level: INFO
```

### JSON

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "myapp"
  }
}
```

## Defining Configuration Classes

Use `@configured` from pico-ioc to bind configuration to dataclasses:

```python
from dataclasses import dataclass
from pico_ioc import configured

@configured(prefix="database")
@dataclass
class DatabaseConfig:
    host: str
    port: int = 5432
    name: str = "default"
    pool_size: int = 5
```

The `prefix` maps to the YAML structure:
- `prefix="database"` → reads from `database:` key
- `prefix="cache"` → reads from `cache:` key

## Environment Variable Overrides

Environment variables **always override** file values.

### Naming Convention

Variables are uppercase with underscores:

| YAML Path | Environment Variable |
|-----------|---------------------|
| `database.host` | `DATABASE_HOST` |
| `database.pool_size` | `DATABASE_POOL_SIZE` |
| `cache.enabled` | `CACHE_ENABLED` |

### Example

```yaml
# application.yaml
database:
  host: localhost
  port: 5432
```

```bash
# Override host for production
$ DATABASE_HOST=prod-db.example.com python app.py
```

The application sees `host = "prod-db.example.com"`.

## Custom Configuration Path

Use `PICO_BOOT_CONFIG_FILE` to specify a custom path:

```bash
$ PICO_BOOT_CONFIG_FILE=/etc/myapp/config.yaml python app.py
```

## Disabling Auto-Configuration

If you need full control, pass your own `config`:

```python
from pico_ioc import configuration, EnvSource
from pico_boot import init

# Custom configuration
my_config = configuration(
    EnvSource(prefix="MYAPP_")
)

container = init(modules=["myapp"], config=my_config)
```

When `config` is provided, Pico-Boot **does not** apply its defaults.

## Nested Configuration

Complex nested structures work naturally:

```yaml
# application.yaml
aws:
  s3:
    bucket: my-bucket
    region: us-east-1
  dynamodb:
    table: my-table
```

```python
from dataclasses import dataclass
from pico_ioc import configured

@configured(prefix="aws.s3")
@dataclass
class S3Config:
    bucket: str
    region: str = "us-east-1"

@configured(prefix="aws.dynamodb")
@dataclass
class DynamoDBConfig:
    table: str
```

## Profiles

Combine with pico-ioc profiles for environment-specific configuration:

```python
from pico_ioc import component

@component(profiles=["production"])
class ProductionCache:
    pass

@component(profiles=["development"])
class DevelopmentCache:
    pass

# Activate profile
container = init(modules=["myapp"], profiles=["production"])
```

## Best Practices

1. **Use YAML for readability** - Easier to maintain than JSON
2. **Keep secrets in environment variables** - Never commit passwords to files
3. **Provide sensible defaults** - Use dataclass defaults for optional values
4. **Use prefixes** - Organize configuration into logical groups
5. **Document your configuration** - Add comments to YAML files

## Example: Full Configuration Setup

```yaml
# application.yaml
app:
  name: My Service
  version: 1.0.0
  debug: false

database:
  host: localhost
  port: 5432
  name: myservice
  pool:
    min_size: 2
    max_size: 10

redis:
  url: redis://localhost:6379/0

logging:
  level: INFO
  format: json
```

```python
# config.py
from dataclasses import dataclass
from pico_ioc import configured

@configured(prefix="app")
@dataclass
class AppConfig:
    name: str
    version: str
    debug: bool = False

@configured(prefix="database")
@dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str

@configured(prefix="database.pool")
@dataclass
class PoolConfig:
    min_size: int = 2
    max_size: int = 10

@configured(prefix="redis")
@dataclass
class RedisConfig:
    url: str = "redis://localhost:6379/0"

@configured(prefix="logging")
@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "text"
```

```python
# main.py
from pico_boot import init

container = init(modules=["config", "services"])
app_config = container.get(AppConfig)
print(f"Starting {app_config.name} v{app_config.version}")
```
