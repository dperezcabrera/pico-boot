"""pico-boot registers the EventBus by default (core infra, not a plugin)."""

from pico_ioc import EventBus

from pico_boot import init


def test_eventbus_registered_by_default(monkeypatch):
    monkeypatch.setenv("PICO_BOOT_AUTO_PLUGINS", "false")
    container = init(modules=[])
    assert container.has(EventBus)


def test_resilience_boots_zero_config(monkeypatch):
    monkeypatch.setenv("PICO_BOOT_AUTO_PLUGINS", "false")
    container = init(modules=["pico_resilience"])
    from pico_resilience import ResilienceSettings

    assert container.get(ResilienceSettings).enabled is True
