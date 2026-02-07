"""
Tests for the init() function in pico-boot.

Tests cover:
- Basic initialization with modules
- Auto-discovery integration
- Environment variable control
- Parameter forwarding to pico_ioc.init()
"""

import os
from types import ModuleType
from unittest.mock import MagicMock, call, patch

import pytest

import pico_boot


class TestInit:
    """Tests for the init() function."""

    def test_basic_init_with_string_module(self):
        """Should initialize container with a string module name."""
        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                mock_container = MagicMock()
                mock_ioc_init.return_value = mock_container

                result = pico_boot.init(modules=["os"])

                assert result is mock_container
                mock_ioc_init.assert_called_once()

    def test_init_with_multiple_modules(self):
        """Should initialize container with multiple modules."""
        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                mock_container = MagicMock()
                mock_ioc_init.return_value = mock_container

                pico_boot.init(modules=["os", "sys", "collections"])

                mock_ioc_init.assert_called_once()
                call_kwargs = mock_ioc_init.call_args
                modules = call_kwargs.kwargs.get("modules") or call_kwargs.args[0]
                # Should have 3 unique modules
                assert len(modules) == 3

    def test_init_merges_plugin_modules(self):
        """Should merge discovered plugins with user modules."""
        mock_plugin = ModuleType("test_plugin")
        mock_plugin.__name__ = "test_plugin"

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[mock_plugin]):
                mock_container = MagicMock()
                mock_ioc_init.return_value = mock_container

                pico_boot.init(modules=["os"])

                mock_ioc_init.assert_called_once()
                call_kwargs = mock_ioc_init.call_args
                modules = call_kwargs.kwargs.get("modules") or call_kwargs.args[0]
                module_names = [m.__name__ for m in modules]
                assert "os" in module_names
                assert "test_plugin" in module_names

    def test_init_deduplicates_modules(self):
        """Should deduplicate modules between user and plugins."""
        import os as os_module

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[os_module]):
                mock_container = MagicMock()
                mock_ioc_init.return_value = mock_container

                pico_boot.init(modules=["os"])

                call_kwargs = mock_ioc_init.call_args
                modules = call_kwargs.kwargs.get("modules") or call_kwargs.args[0]
                # Should only have os once
                os_count = sum(1 for m in modules if m.__name__ == "os")
                assert os_count == 1


class TestInitWithAutoPlugins:
    """Tests for auto-discovery control via environment variable."""

    def test_auto_plugins_enabled_by_default(self):
        """Auto-discovery should be enabled by default."""
        # Ensure env var is not set
        if "PICO_BOOT_AUTO_PLUGINS" in os.environ:
            del os.environ["PICO_BOOT_AUTO_PLUGINS"]

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules") as mock_load:
                mock_load.return_value = []
                mock_ioc_init.return_value = MagicMock()

                pico_boot.init(modules=["os"])

                mock_load.assert_called_once()

    def test_auto_plugins_disabled_with_false(self):
        """Auto-discovery should be disabled when PICO_BOOT_AUTO_PLUGINS=false."""
        os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"

        try:
            with patch("pico_boot._ioc_init") as mock_ioc_init:
                with patch("pico_boot._load_plugin_modules") as mock_load:
                    mock_ioc_init.return_value = MagicMock()

                    pico_boot.init(modules=["os"])

                    mock_load.assert_not_called()
        finally:
            del os.environ["PICO_BOOT_AUTO_PLUGINS"]

    def test_auto_plugins_disabled_with_zero(self):
        """Auto-discovery should be disabled when PICO_BOOT_AUTO_PLUGINS=0."""
        os.environ["PICO_BOOT_AUTO_PLUGINS"] = "0"

        try:
            with patch("pico_boot._ioc_init") as mock_ioc_init:
                with patch("pico_boot._load_plugin_modules") as mock_load:
                    mock_ioc_init.return_value = MagicMock()

                    pico_boot.init(modules=["os"])

                    mock_load.assert_not_called()
        finally:
            del os.environ["PICO_BOOT_AUTO_PLUGINS"]

    def test_auto_plugins_disabled_with_no(self):
        """Auto-discovery should be disabled when PICO_BOOT_AUTO_PLUGINS=no."""
        os.environ["PICO_BOOT_AUTO_PLUGINS"] = "no"

        try:
            with patch("pico_boot._ioc_init") as mock_ioc_init:
                with patch("pico_boot._load_plugin_modules") as mock_load:
                    mock_ioc_init.return_value = MagicMock()

                    pico_boot.init(modules=["os"])

                    mock_load.assert_not_called()
        finally:
            del os.environ["PICO_BOOT_AUTO_PLUGINS"]

    def test_auto_plugins_enabled_with_true(self):
        """Auto-discovery should be enabled when PICO_BOOT_AUTO_PLUGINS=true."""
        os.environ["PICO_BOOT_AUTO_PLUGINS"] = "true"

        try:
            with patch("pico_boot._ioc_init") as mock_ioc_init:
                with patch("pico_boot._load_plugin_modules") as mock_load:
                    mock_load.return_value = []
                    mock_ioc_init.return_value = MagicMock()

                    pico_boot.init(modules=["os"])

                    mock_load.assert_called_once()
        finally:
            del os.environ["PICO_BOOT_AUTO_PLUGINS"]

    def test_auto_plugins_case_insensitive(self):
        """Environment variable should be case insensitive."""
        os.environ["PICO_BOOT_AUTO_PLUGINS"] = "FALSE"

        try:
            with patch("pico_boot._ioc_init") as mock_ioc_init:
                with patch("pico_boot._load_plugin_modules") as mock_load:
                    mock_ioc_init.return_value = MagicMock()

                    pico_boot.init(modules=["os"])

                    mock_load.assert_not_called()
        finally:
            del os.environ["PICO_BOOT_AUTO_PLUGINS"]


class TestInitParameterForwarding:
    """Tests for parameter forwarding to pico_ioc.init()."""

    def test_forwards_config_parameter(self):
        """Should forward config parameter to pico_ioc.init()."""
        mock_config = MagicMock()

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                mock_ioc_init.return_value = MagicMock()

                pico_boot.init(modules=["os"], config=mock_config)

                call_kwargs = mock_ioc_init.call_args.kwargs
                assert call_kwargs.get("config") is mock_config

    def test_forwards_profiles_parameter(self):
        """Should forward profiles parameter to pico_ioc.init()."""
        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                mock_ioc_init.return_value = MagicMock()

                pico_boot.init(modules=["os"], profiles=["prod", "secure"])

                call_kwargs = mock_ioc_init.call_args.kwargs
                assert call_kwargs.get("profiles") == ["prod", "secure"]

    def test_forwards_overrides_parameter(self):
        """Should forward overrides parameter to pico_ioc.init()."""
        overrides = {str: "mock_string"}

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                mock_ioc_init.return_value = MagicMock()

                pico_boot.init(modules=["os"], overrides=overrides)

                call_kwargs = mock_ioc_init.call_args.kwargs
                assert call_kwargs.get("overrides") == overrides

    def test_forwards_observers_parameter(self):
        """Should forward observers parameter to pico_ioc.init()."""
        mock_observer = MagicMock()

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                mock_ioc_init.return_value = MagicMock()

                pico_boot.init(modules=["os"], observers=[mock_observer])

                call_kwargs = mock_ioc_init.call_args.kwargs
                assert mock_observer in call_kwargs.get("observers", [])


class TestHarvestScannersUnit:
    """Unit tests for the _harvest_scanners function directly."""

    def test_empty_module_list(self):
        """Should return empty list for no modules."""
        assert pico_boot._harvest_scanners([]) == []

    def test_module_without_pico_scanners(self):
        """Should return empty list when module has no PICO_SCANNERS."""
        mod = ModuleType("plain")
        assert pico_boot._harvest_scanners([mod]) == []

    def test_module_with_pico_scanners_none(self):
        """Should return empty list when PICO_SCANNERS is None."""
        mod = ModuleType("none_scanners")
        mod.PICO_SCANNERS = None
        assert pico_boot._harvest_scanners([mod]) == []

    def test_module_with_empty_pico_scanners(self):
        """Should return empty list when PICO_SCANNERS is empty."""
        mod = ModuleType("empty_scanners")
        mod.PICO_SCANNERS = []
        assert pico_boot._harvest_scanners([mod]) == []

    def test_single_module_single_scanner(self):
        """Should collect one scanner from one module."""
        scanner = MagicMock()
        mod = ModuleType("one_scanner")
        mod.PICO_SCANNERS = [scanner]
        assert pico_boot._harvest_scanners([mod]) == [scanner]

    def test_single_module_multiple_scanners(self):
        """Should collect all scanners from a single module."""
        s1, s2, s3 = MagicMock(), MagicMock(), MagicMock()
        mod = ModuleType("multi_scanner")
        mod.PICO_SCANNERS = [s1, s2, s3]
        assert pico_boot._harvest_scanners([mod]) == [s1, s2, s3]

    def test_multiple_modules_preserves_order(self):
        """Should preserve module order and scanner order within modules."""
        s1, s2, s3, s4 = MagicMock(), MagicMock(), MagicMock(), MagicMock()
        mod_a = ModuleType("mod_a")
        mod_a.PICO_SCANNERS = [s1, s2]
        mod_b = ModuleType("mod_b")
        mod_b.PICO_SCANNERS = [s3, s4]
        assert pico_boot._harvest_scanners([mod_a, mod_b]) == [s1, s2, s3, s4]

    def test_mixed_modules_with_and_without_scanners(self):
        """Should skip modules without PICO_SCANNERS and collect from the rest."""
        scanner = MagicMock()
        mod_with = ModuleType("with_scanners")
        mod_with.PICO_SCANNERS = [scanner]
        mod_without = ModuleType("without")
        mod_none = ModuleType("none_val")
        mod_none.PICO_SCANNERS = None
        mod_empty = ModuleType("empty_val")
        mod_empty.PICO_SCANNERS = []

        result = pico_boot._harvest_scanners([mod_without, mod_with, mod_none, mod_empty])
        assert result == [scanner]

    def test_pico_scanners_as_tuple(self):
        """Should work with PICO_SCANNERS as a tuple (any iterable)."""
        s1, s2 = MagicMock(), MagicMock()
        mod = ModuleType("tuple_scanners")
        mod.PICO_SCANNERS = (s1, s2)
        assert pico_boot._harvest_scanners([mod]) == [s1, s2]


class TestScannerHarvestingInInit:
    """Tests for scanner harvesting integration within init()."""

    def _make_module(self, name, scanners=None):
        mod = ModuleType(name)
        mod.__name__ = name
        if scanners is not None:
            mod.PICO_SCANNERS = scanners
        return mod

    def test_harvested_scanners_forwarded_to_ioc(self):
        """Harvested scanners should be passed as custom_scanners to pico_ioc.init."""
        scanner = MagicMock()
        mod = self._make_module("sc_mod", [scanner])

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                with patch("pico_boot._normalize_modules", return_value=[mod]):
                    mock_ioc_init.return_value = MagicMock()
                    pico_boot.init(modules=[mod])
                    call_kwargs = mock_ioc_init.call_args.kwargs
                    assert call_kwargs["custom_scanners"] == [scanner]

    def test_no_custom_scanners_key_when_nothing_harvested(self):
        """Should not inject custom_scanners when no PICO_SCANNERS found."""
        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                mock_ioc_init.return_value = MagicMock()
                pico_boot.init(modules=["os"])
                call_kwargs = mock_ioc_init.call_args.kwargs
                assert not call_kwargs.get("custom_scanners")

    def test_user_scanners_come_before_harvested(self):
        """User-provided custom_scanners should appear before harvested ones."""
        user_sc = MagicMock(name="user")
        harvested_sc = MagicMock(name="harvested")
        mod = self._make_module("sc_mod", [harvested_sc])

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                with patch("pico_boot._normalize_modules", return_value=[mod]):
                    mock_ioc_init.return_value = MagicMock()
                    pico_boot.init(modules=[mod], custom_scanners=[user_sc])
                    scanners = mock_ioc_init.call_args.kwargs["custom_scanners"]
                    assert scanners == [user_sc, harvested_sc]

    def test_harvests_from_plugin_modules_too(self):
        """Scanners from auto-discovered plugins should be harvested."""
        scanner = MagicMock()
        plugin_mod = self._make_module("plugin_with_sc", [scanner])

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[plugin_mod]):
                mock_ioc_init.return_value = MagicMock()
                pico_boot.init(modules=["os"])
                scanners = mock_ioc_init.call_args.kwargs.get("custom_scanners", [])
                assert scanner in scanners

    def test_harvests_from_multiple_modules(self):
        """Should collect scanners from all modules."""
        sc_a, sc_b = MagicMock(), MagicMock()
        mod_a = self._make_module("mod_a", [sc_a])
        mod_b = self._make_module("mod_b", [sc_b])

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                with patch("pico_boot._normalize_modules", return_value=[mod_a, mod_b]):
                    mock_ioc_init.return_value = MagicMock()
                    pico_boot.init(modules=[mod_a, mod_b])
                    scanners = mock_ioc_init.call_args.kwargs["custom_scanners"]
                    assert sc_a in scanners
                    assert sc_b in scanners

    def test_skips_modules_without_scanners(self):
        """Should only collect from modules that define PICO_SCANNERS."""
        scanner = MagicMock()
        mod_with = self._make_module("with_sc", [scanner])
        mod_without = self._make_module("without_sc")

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                with patch("pico_boot._normalize_modules", return_value=[mod_with, mod_without]):
                    mock_ioc_init.return_value = MagicMock()
                    pico_boot.init(modules=[mod_with, mod_without])
                    scanners = mock_ioc_init.call_args.kwargs["custom_scanners"]
                    assert scanners == [scanner]

    def test_empty_pico_scanners_not_forwarded(self):
        """Modules with empty PICO_SCANNERS should not cause custom_scanners to be set."""
        mod = self._make_module("empty_sc", [])

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                with patch("pico_boot._normalize_modules", return_value=[mod]):
                    mock_ioc_init.return_value = MagicMock()
                    pico_boot.init(modules=[mod])
                    call_kwargs = mock_ioc_init.call_args.kwargs
                    assert not call_kwargs.get("custom_scanners")

    def test_multiple_scanners_per_module_all_forwarded(self):
        """All scanners in a module's PICO_SCANNERS should be forwarded."""
        s1, s2, s3 = MagicMock(), MagicMock(), MagicMock()
        mod = self._make_module("multi", [s1, s2, s3])

        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                with patch("pico_boot._normalize_modules", return_value=[mod]):
                    mock_ioc_init.return_value = MagicMock()
                    pico_boot.init(modules=[mod])
                    scanners = mock_ioc_init.call_args.kwargs["custom_scanners"]
                    assert scanners == [s1, s2, s3]

    def test_harvesting_disabled_plugins_still_harvests_user_modules(self):
        """With auto-discovery off, user module scanners should still be harvested."""
        scanner = MagicMock()
        mod = self._make_module("user_mod", [scanner])
        os.environ["PICO_BOOT_AUTO_PLUGINS"] = "false"

        try:
            with patch("pico_boot._ioc_init") as mock_ioc_init:
                with patch("pico_boot._normalize_modules", return_value=[mod]):
                    mock_ioc_init.return_value = MagicMock()
                    pico_boot.init(modules=[mod])
                    scanners = mock_ioc_init.call_args.kwargs["custom_scanners"]
                    assert scanner in scanners
        finally:
            del os.environ["PICO_BOOT_AUTO_PLUGINS"]


class TestInitSignature:
    """Tests for init() function signature compatibility."""

    def test_has_same_signature_as_pico_ioc_init(self):
        """init() should have the same signature as pico_ioc.init()."""
        import inspect

        from pico_ioc import init as ioc_init

        pico_boot_sig = inspect.signature(pico_boot.init)
        ioc_sig = inspect.signature(ioc_init)

        # Parameter names should match
        boot_params = list(pico_boot_sig.parameters.keys())
        ioc_params = list(ioc_sig.parameters.keys())

        assert boot_params == ioc_params

    def test_accepts_positional_modules(self):
        """Should accept modules as positional argument."""
        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                mock_ioc_init.return_value = MagicMock()

                # This should not raise
                pico_boot.init(["os"])

    def test_accepts_keyword_modules(self):
        """Should accept modules as keyword argument."""
        with patch("pico_boot._ioc_init") as mock_ioc_init:
            with patch("pico_boot._load_plugin_modules", return_value=[]):
                mock_ioc_init.return_value = MagicMock()

                # This should not raise
                pico_boot.init(modules=["os"])
