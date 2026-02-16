"""
Integration tests for pico-boot.

Tests cover:
- Full initialization flow with real pico-ioc
- Real module scanning
- Container functionality
"""

import os
import sys
from types import ModuleType
from typing import Any, Callable, Optional, Tuple, Union

import pytest
from pico_ioc import PicoContainer, component, configured, provides
from pico_ioc.factory import DeferredProvider, ProviderMetadata

import pico_boot


@pytest.fixture(autouse=True)
def _disable_auto_plugins(monkeypatch):
    """Isolate integration tests from entry-point plugins installed in the environment."""
    monkeypatch.setenv("PICO_BOOT_AUTO_PLUGINS", "false")


# --- Test fixtures: Sample components ---


@component
class SampleService:
    """A sample service for testing."""

    def get_message(self) -> str:
        return "Hello from SampleService"


@component
class DependentService:
    """A service that depends on SampleService."""

    def __init__(self, sample: SampleService):
        self.sample = sample

    def get_full_message(self) -> str:
        return f"Dependent says: {self.sample.get_message()}"


class TestBasicIntegration:
    """Basic integration tests with real pico-ioc."""

    def test_init_returns_pico_container(self, pico_container):
        """init() should return a PicoContainer instance."""
        container = pico_container(modules=[__name__])
        assert isinstance(container, PicoContainer)

    def test_can_resolve_component(self, pico_container):
        """Should be able to resolve registered components."""
        container = pico_container(modules=[__name__])
        service = container.get(SampleService)
        assert service is not None
        assert isinstance(service, SampleService)
        assert service.get_message() == "Hello from SampleService"

    def test_can_resolve_dependent_component(self, pico_container):
        """Should be able to resolve components with dependencies."""
        container = pico_container(modules=[__name__])
        service = container.get(DependentService)
        assert service is not None
        assert isinstance(service, DependentService)
        assert service.sample is not None
        assert "Hello from SampleService" in service.get_full_message()

    def test_singleton_scope_by_default(self, pico_container):
        """Components should be singletons by default."""
        container = pico_container(modules=[__name__])
        service1 = container.get(SampleService)
        service2 = container.get(SampleService)
        assert service1 is service2


class TestMultipleModules:
    """Tests for initialization with multiple modules."""

    def test_init_with_multiple_string_modules(self, pico_container):
        """Should handle multiple module strings."""
        container = pico_container(modules=[__name__, "os"])
        assert isinstance(container, PicoContainer)

    def test_init_with_module_objects(self, pico_container):
        """Should handle module objects directly."""
        import os
        import sys

        container = pico_container(modules=[__name__, os, sys])
        assert isinstance(container, PicoContainer)

    def test_init_with_mixed_inputs(self, pico_container):
        """Should handle mixed string and module inputs."""
        import os

        container = pico_container(modules=[__name__, os, "sys"])
        assert isinstance(container, PicoContainer)


class TestContainerLifecycle:
    """Tests for container lifecycle management."""

    def test_shutdown_is_callable(self, pico_container):
        """Container should have shutdown method."""
        container = pico_container(modules=[__name__])
        assert hasattr(container, "shutdown")
        assert callable(container.shutdown)

    def test_multiple_init_creates_separate_containers(self, pico_container):
        """Each init() call should create a separate container."""
        container1 = pico_container(modules=[__name__])
        container2 = pico_container(modules=[__name__])

        assert container1 is not container2

        service1 = container1.get(SampleService)
        service2 = container2.get(SampleService)

        # Different containers, different instances
        assert service1 is not service2


class TestProfiles:
    """Tests for profile support."""

    def test_init_with_empty_profiles(self, pico_container):
        """Should work with empty profiles."""
        container = pico_container(modules=[__name__], profiles=[])
        assert isinstance(container, PicoContainer)

    def test_init_with_profiles(self, pico_container):
        """Should accept profiles parameter."""
        container = pico_container(modules=[__name__], profiles=["test", "dev"])
        assert isinstance(container, PicoContainer)


class TestOverrides:
    """Tests for component overrides (useful for testing)."""

    def test_init_with_overrides(self, pico_container):
        """Should accept overrides parameter."""

        class MockService:
            def get_message(self):
                return "Mocked!"

        mock = MockService()
        container = pico_container(modules=[__name__], overrides={SampleService: mock})
        service = container.get(SampleService)
        assert service is mock
        assert service.get_message() == "Mocked!"

    def test_overrides_affect_dependencies(self, pico_container):
        """Overrides should propagate to dependent components."""

        class MockService:
            def get_message(self):
                return "MOCK"

        mock = MockService()
        container = pico_container(modules=[__name__], overrides={SampleService: mock})
        dependent = container.get(DependentService)
        assert "MOCK" in dependent.get_full_message()


# --- Fixtures for scanner harvesting integration ---


class PlainService:
    """Not decorated — only discoverable via custom scanner."""

    def value(self) -> str:
        return "found by scanner"


KeyT = Union[str, type]


class _TestScanner:
    """A real CustomScanner that discovers PlainService."""

    def should_scan(self, obj: Any) -> bool:
        return isinstance(obj, type) and getattr(obj, "__name__", "") == "PlainService"

    def scan(self, obj: Any) -> Optional[Tuple[KeyT, Callable[..., Any], ProviderMetadata]]:
        if not self.should_scan(obj):
            return None
        provider = DeferredProvider(lambda pico, loc, c=obj: c())
        md = ProviderMetadata(
            key=obj,
            provided_type=obj,
            concrete_class=obj,
            factory_class=None,
            factory_method=None,
            qualifiers=set(),
            primary=True,
            lazy=False,
            infra="custom",
            pico_name=None,
            scope="singleton",
            dependencies=(),
        )
        return (obj, provider, md)


# Module that exposes PICO_SCANNERS for harvesting
_scanner_module = ModuleType("_test_scanner_mod")
_scanner_module.__name__ = "_test_scanner_mod"
_scanner_module.PICO_SCANNERS = [_TestScanner()]
_scanner_module.PlainService = PlainService
sys.modules[_scanner_module.__name__] = _scanner_module


class TestScannerHarvestingIntegration:
    """End-to-end tests: PICO_SCANNERS harvested by pico-boot work with real pico-ioc."""

    def test_harvested_scanner_discovers_component(self, pico_container):
        """A scanner exposed via PICO_SCANNERS should discover and register its component."""
        container = pico_container(modules=[__name__, "_test_scanner_mod"])
        assert container.has(PlainService)
        svc = container.get(PlainService)
        assert isinstance(svc, PlainService)
        assert svc.value() == "found by scanner"

    def test_harvested_scanner_singleton_scope(self, pico_container):
        """Component registered by harvested scanner should be singleton by default."""
        container = pico_container(modules=[__name__, "_test_scanner_mod"])
        svc1 = container.get(PlainService)
        svc2 = container.get(PlainService)
        assert svc1 is svc2

    def test_without_scanner_module_component_not_found(self, pico_container):
        """Without the scanner module, PlainService should NOT be in the container."""
        container = pico_container(modules=[__name__])
        assert not container.has(PlainService)

    def test_harvested_scanner_coexists_with_decorated_components(self, pico_container):
        """Harvested scanners should work alongside normal @component classes."""
        container = pico_container(modules=[__name__, "_test_scanner_mod"])

        # Normal decorated component
        sample = container.get(SampleService)
        assert sample.get_message() == "Hello from SampleService"

        # Scanner-discovered component
        plain = container.get(PlainService)
        assert plain.value() == "found by scanner"

    def test_user_scanner_and_harvested_scanner_both_work(self, pico_container):
        """Explicitly passed custom_scanners and harvested ones should both register components."""

        class AnotherPlain:
            def val(self):
                return "from user scanner"

        class UserScanner:
            def should_scan(self, obj):
                return isinstance(obj, type) and getattr(obj, "__name__", "") == "AnotherPlain"

            def scan(self, obj):
                if not self.should_scan(obj):
                    return None
                provider = DeferredProvider(lambda pico, loc, c=obj: c())
                md = ProviderMetadata(
                    key=obj,
                    provided_type=obj,
                    concrete_class=obj,
                    factory_class=None,
                    factory_method=None,
                    qualifiers=set(),
                    primary=True,
                    lazy=False,
                    infra="custom",
                    pico_name=None,
                    scope="singleton",
                    dependencies=(),
                )
                return (obj, provider, md)

        # Module containing AnotherPlain for scanning
        user_mod = ModuleType("_user_scanner_mod")
        user_mod.__name__ = "_user_scanner_mod"
        user_mod.AnotherPlain = AnotherPlain
        sys.modules[user_mod.__name__] = user_mod

        try:
            container = pico_container(
                modules=[__name__, "_test_scanner_mod", "_user_scanner_mod"],
                custom_scanners=[UserScanner()],
            )

            # Harvested scanner found PlainService
            assert container.has(PlainService)
            # User scanner found AnotherPlain
            assert container.has(AnotherPlain)
            assert container.get(AnotherPlain).val() == "from user scanner"
        finally:
            del sys.modules["_user_scanner_mod"]
