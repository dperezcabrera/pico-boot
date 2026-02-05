"""
Tests for module utility functions in pico-boot.

Tests cover:
- _to_module_list: Converting various inputs to module lists
- _import_module_like: Importing modules from different input types
- _normalize_modules: Deduplicating and normalizing module lists
"""

import pytest
from types import ModuleType
from unittest.mock import MagicMock, patch
import pico_boot


class TestToModuleList:
    """Tests for _to_module_list function."""

    def test_single_string_becomes_list(self):
        """A single string module name should become a one-element list."""
        result = pico_boot._to_module_list("myapp")
        assert result == ["myapp"]

    def test_single_module_becomes_list(self):
        """A single module object should become a one-element list."""
        import sys
        result = pico_boot._to_module_list(sys)
        assert result == [sys]

    def test_list_stays_list(self):
        """A list of modules should stay as a list."""
        input_list = ["app1", "app2", "app3"]
        result = pico_boot._to_module_list(input_list)
        assert result == input_list

    def test_tuple_becomes_list(self):
        """A tuple of modules should become a list."""
        input_tuple = ("app1", "app2")
        result = pico_boot._to_module_list(input_tuple)
        assert result == ["app1", "app2"]

    def test_generator_becomes_list(self):
        """A generator should become a list."""
        def gen():
            yield "app1"
            yield "app2"

        result = pico_boot._to_module_list(gen())
        assert result == ["app1", "app2"]

    def test_bytes_treated_as_single_item(self):
        """Bytes should be treated as a single item, not iterated."""
        result = pico_boot._to_module_list(b"myapp")
        assert result == [b"myapp"]

    def test_empty_list_stays_empty(self):
        """An empty list should stay empty."""
        result = pico_boot._to_module_list([])
        assert result == []


class TestImportModuleLike:
    """Tests for _import_module_like function."""

    def test_module_returns_itself(self):
        """A module object should return itself."""
        import sys
        result = pico_boot._import_module_like(sys)
        assert result is sys

    def test_string_imports_module(self):
        """A string module name should import the module."""
        result = pico_boot._import_module_like("os")
        import os
        assert result is os

    def test_string_imports_submodule(self):
        """A dotted string should import the submodule."""
        result = pico_boot._import_module_like("os.path")
        import os.path
        assert result is os.path

    def test_class_imports_its_module(self):
        """A class should import its containing module."""
        from collections import OrderedDict
        result = pico_boot._import_module_like(OrderedDict)
        import collections
        assert result is collections

    def test_function_imports_its_module(self):
        """A function should import its containing module."""
        from os.path import join
        result = pico_boot._import_module_like(join)
        import os.path
        # Note: posixpath or ntpath depending on OS
        assert result.__name__ in ("posixpath", "ntpath", "os.path")

    def test_invalid_module_raises_import_error(self):
        """An invalid module name should raise ImportError."""
        with pytest.raises(ModuleNotFoundError):
            pico_boot._import_module_like("nonexistent_module_xyz")

    def test_object_without_module_raises_import_error(self):
        """An object without __module__ or __name__ should raise ImportError."""
        obj = object()
        with pytest.raises(ImportError, match="Cannot determine module"):
            pico_boot._import_module_like(obj)


class TestNormalizeModules:
    """Tests for _normalize_modules function."""

    def test_deduplicates_same_module_string(self):
        """Duplicate module strings should be deduplicated."""
        result = pico_boot._normalize_modules(["os", "os", "os"])
        assert len(result) == 1
        import os
        assert result[0] is os

    def test_deduplicates_mixed_inputs(self):
        """Same module from different input types should be deduplicated."""
        import sys
        result = pico_boot._normalize_modules(["sys", sys, "sys"])
        assert len(result) == 1
        assert result[0] is sys

    def test_preserves_order(self):
        """Module order should be preserved (first occurrence wins)."""
        result = pico_boot._normalize_modules(["os", "sys", "collections"])
        assert len(result) == 3
        assert result[0].__name__ == "os"
        assert result[1].__name__ == "sys"
        assert result[2].__name__ == "collections"

    def test_empty_input_returns_empty(self):
        """Empty input should return empty list."""
        result = pico_boot._normalize_modules([])
        assert result == []

    def test_handles_submodules(self):
        """Submodules should be handled correctly."""
        result = pico_boot._normalize_modules(["os", "os.path"])
        assert len(result) == 2
        # os and os.path are different modules
        names = [m.__name__ for m in result]
        assert "os" in names
