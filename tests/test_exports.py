"""
Tests for pico-boot module exports.

Tests cover:
- __all__ exports
- Re-exported symbols from pico-ioc
- Module-level accessibility
"""

import pytest

import pico_boot


class TestModuleExports:
    """Tests for module-level exports."""

    def test_init_is_exported(self):
        """init function should be exported."""
        assert hasattr(pico_boot, "init")
        assert callable(pico_boot.init)

    def test_pico_container_is_exported(self):
        """PicoContainer should be re-exported."""
        assert hasattr(pico_boot, "PicoContainer")

    def test_context_config_is_exported(self):
        """ContextConfig should be re-exported."""
        assert hasattr(pico_boot, "ContextConfig")

    def test_container_observer_is_exported(self):
        """ContainerObserver should be re-exported."""
        assert hasattr(pico_boot, "ContainerObserver")

    def test_all_contains_expected_exports(self):
        """__all__ should contain all public exports."""
        expected = ["init", "PicoContainer", "ContextConfig", "ContainerObserver"]
        for name in expected:
            assert name in pico_boot.__all__, f"{name} not in __all__"

    def test_all_exports_are_accessible(self):
        """All items in __all__ should be accessible."""
        for name in pico_boot.__all__:
            assert hasattr(pico_boot, name), f"{name} in __all__ but not accessible"


class TestReexportedTypes:
    """Tests for re-exported types from pico-ioc."""

    def test_pico_container_is_same_as_ioc(self):
        """PicoContainer should be the same class as pico_ioc.PicoContainer."""
        from pico_ioc import PicoContainer as IocContainer

        assert pico_boot.PicoContainer is IocContainer

    def test_context_config_is_same_as_ioc(self):
        """ContextConfig should be the same as pico_ioc.ContextConfig."""
        from pico_ioc import ContextConfig as IocConfig

        assert pico_boot.ContextConfig is IocConfig

    def test_container_observer_is_same_as_ioc(self):
        """ContainerObserver should be the same as pico_ioc.ContainerObserver."""
        from pico_ioc import ContainerObserver as IocObserver

        assert pico_boot.ContainerObserver is IocObserver


class TestInternalFunctions:
    """Tests for internal function accessibility."""

    def test_internal_functions_exist(self):
        """Internal functions should exist (but not in __all__)."""
        # These are implementation details but should exist
        assert hasattr(pico_boot, "_to_module_list")
        assert hasattr(pico_boot, "_import_module_like")
        assert hasattr(pico_boot, "_normalize_modules")
        assert hasattr(pico_boot, "_load_plugin_modules")

    def test_internal_functions_not_in_all(self):
        """Internal functions should not be in __all__."""
        internal = ["_to_module_list", "_import_module_like", "_normalize_modules", "_load_plugin_modules"]
        for name in internal:
            assert name not in pico_boot.__all__
