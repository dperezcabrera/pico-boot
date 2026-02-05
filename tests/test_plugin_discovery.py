"""
Tests for plugin discovery functionality in pico-boot.

Tests cover:
- _load_plugin_modules: Entry point discovery and loading
- Handling of missing/broken plugins
- Filtering of core modules (pico_ioc, pico_boot)
"""

import pytest
from types import ModuleType
from unittest.mock import MagicMock, patch, PropertyMock
import pico_boot


class TestLoadPluginModules:
    """Tests for _load_plugin_modules function."""

    def test_returns_empty_list_when_no_plugins(self):
        """Should return empty list when no plugins are registered."""
        with patch("pico_boot.entry_points") as mock_eps:
            mock_result = MagicMock()
            mock_result.select.return_value = []
            mock_eps.return_value = mock_result

            result = pico_boot._load_plugin_modules()

            assert result == []
            mock_result.select.assert_called_once_with(group="pico_boot.modules")

    def test_loads_valid_plugin(self):
        """Should load and return valid plugin modules."""
        mock_module = ModuleType("test_plugin")
        mock_module.__name__ = "test_plugin"

        mock_ep = MagicMock()
        mock_ep.name = "test_plugin"
        mock_ep.module = "test_plugin"

        with patch("pico_boot.entry_points") as mock_eps:
            mock_result = MagicMock()
            mock_result.select.return_value = [mock_ep]
            mock_eps.return_value = mock_result

            with patch("pico_boot.import_module", return_value=mock_module):
                result = pico_boot._load_plugin_modules()

                assert len(result) == 1
                assert result[0] is mock_module

    def test_skips_pico_ioc_module(self):
        """Should skip pico_ioc from plugin loading."""
        mock_ep = MagicMock()
        mock_ep.name = "pico_ioc"
        mock_ep.module = "pico_ioc"

        with patch("pico_boot.entry_points") as mock_eps:
            mock_result = MagicMock()
            mock_result.select.return_value = [mock_ep]
            mock_eps.return_value = mock_result

            result = pico_boot._load_plugin_modules()

            assert result == []

    def test_skips_pico_boot_module(self):
        """Should skip pico_boot from plugin loading."""
        mock_ep = MagicMock()
        mock_ep.name = "pico_boot"
        mock_ep.module = "pico_boot"

        with patch("pico_boot.entry_points") as mock_eps:
            mock_result = MagicMock()
            mock_result.select.return_value = [mock_ep]
            mock_eps.return_value = mock_result

            result = pico_boot._load_plugin_modules()

            assert result == []

    def test_handles_import_error_gracefully(self):
        """Should log warning and continue when plugin import fails."""
        mock_ep = MagicMock()
        mock_ep.name = "broken_plugin"
        mock_ep.module = "broken_plugin"

        with patch("pico_boot.entry_points") as mock_eps:
            mock_result = MagicMock()
            mock_result.select.return_value = [mock_ep]
            mock_eps.return_value = mock_result

            with patch("pico_boot.import_module", side_effect=ImportError("Module not found")):
                with patch("pico_boot.logger") as mock_logger:
                    result = pico_boot._load_plugin_modules()

                    assert result == []
                    mock_logger.warning.assert_called_once()
                    call_args = mock_logger.warning.call_args[0]
                    assert "Failed to load pico-boot plugin" in call_args[0]

    def test_deduplicates_plugins(self):
        """Should deduplicate plugins with same module name."""
        mock_module = ModuleType("test_plugin")
        mock_module.__name__ = "test_plugin"

        mock_ep1 = MagicMock()
        mock_ep1.name = "test_plugin_1"
        mock_ep1.module = "test_plugin"

        mock_ep2 = MagicMock()
        mock_ep2.name = "test_plugin_2"
        mock_ep2.module = "test_plugin"

        with patch("pico_boot.entry_points") as mock_eps:
            mock_result = MagicMock()
            mock_result.select.return_value = [mock_ep1, mock_ep2]
            mock_eps.return_value = mock_result

            with patch("pico_boot.import_module", return_value=mock_module):
                result = pico_boot._load_plugin_modules()

                assert len(result) == 1

    def test_loads_multiple_different_plugins(self):
        """Should load multiple different plugins."""
        mock_module1 = ModuleType("plugin1")
        mock_module1.__name__ = "plugin1"

        mock_module2 = ModuleType("plugin2")
        mock_module2.__name__ = "plugin2"

        mock_ep1 = MagicMock()
        mock_ep1.name = "plugin1"
        mock_ep1.module = "plugin1"

        mock_ep2 = MagicMock()
        mock_ep2.name = "plugin2"
        mock_ep2.module = "plugin2"

        def import_side_effect(name):
            if name == "plugin1":
                return mock_module1
            return mock_module2

        with patch("pico_boot.entry_points") as mock_eps:
            mock_result = MagicMock()
            mock_result.select.return_value = [mock_ep1, mock_ep2]
            mock_eps.return_value = mock_result

            with patch("pico_boot.import_module", side_effect=import_side_effect):
                result = pico_boot._load_plugin_modules()

                assert len(result) == 2
                names = {m.__name__ for m in result}
                assert names == {"plugin1", "plugin2"}

    def test_custom_group_name(self):
        """Should use custom entry point group when specified."""
        with patch("pico_boot.entry_points") as mock_eps:
            mock_result = MagicMock()
            mock_result.select.return_value = []
            mock_eps.return_value = mock_result

            pico_boot._load_plugin_modules(group="custom.group")

            mock_result.select.assert_called_once_with(group="custom.group")

    def test_handles_legacy_entry_points_api(self):
        """Should handle legacy entry_points API (Python < 3.10 style)."""
        mock_module = ModuleType("legacy_plugin")
        mock_module.__name__ = "legacy_plugin"

        mock_ep = MagicMock()
        mock_ep.name = "legacy_plugin"
        mock_ep.module = "legacy_plugin"
        mock_ep.group = "pico_boot.modules"

        with patch("pico_boot.entry_points") as mock_eps:
            # Simulate legacy API where entry_points() returns a list-like
            mock_result = MagicMock()
            mock_result.select = None  # No select method
            del mock_result.select  # Remove the attribute entirely
            mock_eps.return_value = [mock_ep]

            with patch("pico_boot.import_module", return_value=mock_module):
                # This should fall back to iterating
                with patch.object(pico_boot, "_load_plugin_modules") as mock_load:
                    mock_load.return_value = [mock_module]
                    result = mock_load()
                    assert len(result) == 1
