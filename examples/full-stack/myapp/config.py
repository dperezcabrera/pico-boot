from dataclasses import dataclass

from pico_ioc import configured


@configured(prefix="database")
@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "default"


@configured(prefix="app")
@dataclass
class AppConfig:
    debug: bool = False
    log_level: str = "WARNING"
