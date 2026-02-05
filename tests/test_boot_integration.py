import pytest
from pico_boot import init
from pico_ioc import PicoContainer, configuration, DictSource

pico_fastapi = pytest.importorskip("pico_fastapi")
pico_pydantic = pytest.importorskip("pico_pydantic")

FastApiSettings = pico_fastapi.FastApiSettings
FastApiAppFactory = pico_fastapi.FastApiAppFactory
ValidationInterceptor = pico_pydantic.ValidationInterceptor


def test_pico_boot_auto_discovery():
    minimal_config = configuration(
        DictSource({
            "fastapi": {
                "title": "Stack Integration Test",
                "version": "0.0.1",
                "debug": True
            }
        })
    )

    container = init(modules=[__name__], config=minimal_config)

    assert isinstance(container, PicoContainer)

    settings = container.get(FastApiSettings)
    assert settings is not None
    assert settings.title == "Stack Integration Test"

    interceptor = container.get(ValidationInterceptor)
    assert interceptor is not None
