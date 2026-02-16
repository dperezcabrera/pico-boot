"""Pico-Boot: zero-configuration bootstrap layer for the Pico ecosystem.

Pico-Boot wraps ``pico_ioc.init()`` to add automatic plugin discovery via
Python entry points and custom-scanner harvesting from ``PICO_SCANNERS``
module-level lists.  It is a drop-in replacement for ``pico_ioc.init()``.

Typical usage::

    from pico_boot import init

    container = init(modules=["myapp.services", "myapp.repos"])

Plugins that register the ``pico_boot.modules`` entry-point group are
loaded automatically unless the ``PICO_BOOT_AUTO_PLUGINS`` environment
variable is set to ``"false"``, ``"0"``, or ``"no"``.
"""

import inspect
import os
from importlib import import_module
from importlib.metadata import entry_points
from types import ModuleType
from typing import TYPE_CHECKING, Any, Iterable, List, Union

if TYPE_CHECKING:
    from pico_ioc import ContainerObserver, ContextConfig, PicoContainer
    from pico_ioc import init as init
else:
    import logging

    from pico_ioc import ContainerObserver, ContextConfig, PicoContainer
    from pico_ioc import init as _ioc_init

    logger = logging.getLogger(__name__)

    def _to_module_list(modules: Union[Any, Iterable[Any]]) -> List[Any]:
        """Coerce *modules* into a flat list.

        Strings and bytes are treated as single items (not iterated
        character-by-character).  Every other iterable is expanded.

        Args:
            modules: A single module reference (string, ``ModuleType``,
                or any object) or an iterable of such references.

        Returns:
            A list containing the original items.  If *modules* was
            already a list the same object is **not** reused; a new
            list is always created.

        Example:
            >>> _to_module_list("myapp")
            ['myapp']
            >>> _to_module_list(["a", "b"])
            ['a', 'b']
        """
        if isinstance(modules, Iterable) and not isinstance(modules, (str, bytes)):
            return list(modules)
        return [modules]

    def _import_module_like(obj: Any) -> ModuleType:
        """Resolve *obj* to an imported ``ModuleType``.

        The following input types are supported:

        * ``ModuleType`` -- returned as-is.
        * ``str`` -- interpreted as a dotted module path and imported.
        * Any other object -- its ``__module__`` (or ``__name__``)
          attribute is used to determine which module to import.

        Args:
            obj: A module, a dotted module name, or any Python object
                whose owning module should be resolved.

        Returns:
            The imported ``ModuleType``.

        Raises:
            ImportError: If the module cannot be determined or imported.
            ModuleNotFoundError: If the named module does not exist.

        Example:
            >>> import os
            >>> _import_module_like("os") is os
            True
        """
        if isinstance(obj, ModuleType):
            return obj
        if isinstance(obj, str):
            return import_module(obj)
        module_name = getattr(obj, "__module__", None) or getattr(obj, "__name__", None)
        if not module_name:
            raise ImportError(f"Cannot determine module for object {obj!r}")
        return import_module(module_name)

    def _normalize_modules(raw: Iterable[Any]) -> List[ModuleType]:
        """Import and deduplicate a sequence of module-like references.

        Each element of *raw* is resolved via :func:`_import_module_like`.
        If two elements resolve to the same ``__name__``, only the first
        occurrence is kept.

        Args:
            raw: An iterable of module references (strings, module
                objects, classes, functions, etc.).

        Returns:
            A deduplicated list of ``ModuleType`` objects in the order
            they were first encountered.

        Raises:
            ImportError: If any element cannot be resolved.
        """
        seen: set[str] = set()
        result: List[ModuleType] = []
        for item in raw:
            m = _import_module_like(item)
            name = m.__name__
            if name not in seen:
                seen.add(name)
                result.append(m)
        return result

    def _harvest_scanners(modules: List[ModuleType]) -> list:
        """Collect ``PICO_SCANNERS`` lists from loaded modules.

        Each module in *modules* is inspected for a module-level
        ``PICO_SCANNERS`` attribute.  When present its contents are
        appended to the result list.

        Args:
            modules: Already-imported module objects to inspect.

        Returns:
            A flat list of scanner instances gathered from all modules.
            Returns an empty list when no module defines
            ``PICO_SCANNERS``.

        Example:
            If ``my_plugin`` defines::

                PICO_SCANNERS = [MyCustomScanner()]

            then ``_harvest_scanners([my_plugin])`` returns
            ``[MyCustomScanner()]``.
        """
        scanners: list = []
        for m in modules:
            module_scanners = getattr(m, "PICO_SCANNERS", None)
            if module_scanners:
                scanners.extend(module_scanners)
        return scanners

    def _load_plugin_modules(group: str = "pico_boot.modules") -> List[ModuleType]:
        """Discover and import plugin modules registered via entry points.

        Reads the entry-point group *group* (default
        ``"pico_boot.modules"``) from installed package metadata,
        imports each referenced module, and returns them as a
        deduplicated list.

        Entry points whose ``module`` is ``"pico_ioc"`` or
        ``"pico_boot"`` are silently skipped because they are
        infrastructure packages, not application plugins.

        Plugins that fail to import are logged at ``WARNING`` level and
        skipped so that one broken optional plugin does not crash the
        whole application.

        Args:
            group: The entry-point group name to query.  Defaults to
                ``"pico_boot.modules"``.

        Returns:
            A deduplicated list of successfully imported
            ``ModuleType`` objects.

        Example:
            Given a ``pyproject.toml`` entry::

                [project.entry-points."pico_boot.modules"]
                my_plugin = "my_plugin"

            calling ``_load_plugin_modules()`` will import and return
            the ``my_plugin`` module.
        """
        selected = entry_points().select(group=group)

        seen: set[str] = set()
        modules: List[ModuleType] = []

        for ep in selected:
            try:
                if ep.module in ("pico_ioc", "pico_boot"):
                    continue
                m = import_module(ep.module)
            except Exception as exc:
                logger.warning(
                    "Failed to load pico-boot plugin entry point '%s' (%s): %s",
                    ep.name,
                    ep.module,
                    exc,
                )
                continue

            name = m.__name__
            if name not in seen:
                seen.add(name)
                modules.append(m)

        return modules

    _IOC_INIT_SIG = inspect.signature(_ioc_init)

    def init(*args: Any, **kwargs: Any) -> PicoContainer:
        """Bootstrap a ``PicoContainer`` with automatic plugin discovery.

        This is a drop-in replacement for ``pico_ioc.init()``.  It
        accepts exactly the same parameters and returns the same
        ``PicoContainer`` type.  On top of what ``pico_ioc.init()``
        does, ``pico_boot.init()`` performs three additional steps
        before delegating:

        1. **Module normalisation** -- the *modules* argument is
           coerced to a list, each element is imported if necessary,
           and duplicates are removed.
        2. **Plugin auto-discovery** -- unless disabled via the
           ``PICO_BOOT_AUTO_PLUGINS`` environment variable, all
           packages that register a ``pico_boot.modules`` entry point
           are imported and merged into the module list.
        3. **Scanner harvesting** -- every loaded module is inspected
           for a ``PICO_SCANNERS`` attribute.  Any scanners found are
           appended to the *custom_scanners* parameter before the call
           to ``pico_ioc.init()``.

        Args:
            *args: Positional arguments forwarded to
                ``pico_ioc.init()``.  Typically just *modules*.
            **kwargs: Keyword arguments forwarded to
                ``pico_ioc.init()``.  Common keywords include:

                * **modules** (``Union[Any, Iterable[Any]]``) --
                  Modules to scan for components.
                * **config** (``ContextConfig | None``) --
                  Configuration context built via
                  ``pico_ioc.configuration()``.
                * **profiles** (``tuple[str, ...]``) -- Active profiles
                  for conditional component activation.
                * **overrides** (``dict[type, Any] | None``) --
                  Component overrides, useful for testing.
                * **observers** (``list[ContainerObserver] | None``) --
                  Lifecycle observers.
                * **custom_scanners** (``list | None``) -- Additional
                  component scanners.  Scanners harvested from
                  ``PICO_SCANNERS`` are appended to this list.

        Returns:
            PicoContainer: The fully initialised dependency-injection
            container.

        Raises:
            ImportError: If a user-specified module cannot be imported.
            TypeError: If required arguments are missing.

        Example:
            >>> from pico_boot import init
            >>> container = init(modules=["myapp.services"])
            >>> service = container.get(MyService)
        """
        bound = _IOC_INIT_SIG.bind(*args, **kwargs)
        bound.apply_defaults()

        base_modules = _normalize_modules(_to_module_list(bound.arguments["modules"]))

        auto_flag = os.getenv("PICO_BOOT_AUTO_PLUGINS", "true").lower()
        auto_plugins = auto_flag not in ("0", "false", "no")

        if auto_plugins:
            plugin_modules = _load_plugin_modules()
            all_modules = _normalize_modules(list(base_modules) + plugin_modules)
        else:
            all_modules = base_modules

        bound.arguments["modules"] = all_modules

        harvested = _harvest_scanners(all_modules)
        if harvested:
            existing = bound.arguments.get("custom_scanners") or []
            bound.arguments["custom_scanners"] = list(existing) + harvested

        return _ioc_init(*bound.args, **bound.kwargs)

    init.__signature__ = _IOC_INIT_SIG

__all__ = [
    "init",
    "PicoContainer",
    "ContextConfig",
    "ContainerObserver",
]
