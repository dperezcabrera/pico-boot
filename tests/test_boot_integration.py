import pytest
from pico_ioc import DictSource, PicoContainer, configuration

from pico_boot import init

pico_fastapi = pytest.importorskip("pico_fastapi")
pico_pydantic = pytest.importorskip("pico_pydantic")

FastApiSettings = pico_fastapi.FastApiSettings
FastApiAppFactory = pico_fastapi.FastApiAppFactory
ValidationInterceptor = pico_pydantic.ValidationInterceptor


# Minimal controller so pico-fastapi doesn't raise NoControllersFoundError
@pico_fastapi.controller(prefix="/test", tags=["Test"])
class _DummyController:
    @pico_fastapi.get("/ping")
    async def ping(self):
        return {"ok": True}


def test_pico_boot_auto_discovery():
    # Config must cover all auto-discovered pico-* plugins that may be installed
    minimal_config = configuration(
        DictSource(
            {
                "fastapi": {"title": "Stack Integration Test", "version": "0.0.1", "debug": True},
                "database": {"url": "sqlite+aiosqlite:///test_boot.db", "echo": False},
                "auth_client": {"enabled": False, "issuer": "http://test", "audience": "test"},
                "celery": {"broker_url": "memory://", "backend_url": "memory://"},
            }
        )
    )

    container = init(modules=[__name__], config=minimal_config)

    assert isinstance(container, PicoContainer)

    settings = container.get(FastApiSettings)
    assert settings is not None
    assert settings.title == "Stack Integration Test"

    interceptor = container.get(ValidationInterceptor)
    assert interceptor is not None
