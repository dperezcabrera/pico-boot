import inspect
import os
from importlib import import_module
from importlib.metadata import entry_points
from types import ModuleType
from typing import Any, Iterable, List, TYPE_CHECKING, Union

KeyT = Union[str, type]

if TYPE_CHECKING:
    from pico_ioc import PicoContainer, ContextConfig
    from pico_ioc import init as init, ContainerObserver
else:
    from typing import Dict, Optional, Tuple, Union
    import logging
    from pico_ioc import PicoContainer, ContextConfig
    from pico_ioc import init as _ioc_init, ContainerObserver

    def _to_module_list(modules: Union[Any, Iterable[Any]]) -> List[Any]:
        if isinstance(modules, Iterable) and not isinstance(modules, (str, bytes)):
            return list(modules)
        return [modules]

    def _import_module_like(obj: Any) -> ModuleType:
        if isinstance(obj, ModuleType):
            return obj
        if isinstance(obj, str):
            return import_module(obj)
        return import_module(obj.__name__)

    def _normalize_modules(raw: Iterable[Any]) -> List[ModuleType]:
        seen: set[str] = set()
        result: List[ModuleType] = []
        for item in raw:
            m = _import_module_like(item)
            name = m.__name__
            if name not in seen:
                seen.add(name)
                result.append(m)
        return result

    def _load_plugin_modules(group: str = "pico_stack.modules") -> List[ModuleType]:
        eps = entry_points()
        if hasattr(eps, "select"):
            selected = eps.select(group=group)
        else:
            selected = [ep for ep in eps if ep.group == group]

        seen: set[str] = set()
        modules: List[ModuleType] = []

        for ep in selected:
            try:
                # opcional: saltar cosas del core
                if ep.module in ("pico_ioc", "pico_stack"):
                    continue
                m = import_module(ep.module)
            except Exception:
                continue
            name = m.__name__
            if name not in seen:
                seen.add(name)
                modules.append(m)

        return modules


    _IOC_INIT_SIG = inspect.signature(_ioc_init)

    def init(
        modules: Union[Any, Iterable[Any]],
        *,
        profiles: Tuple[str, ...] = (),
        allowed_profiles: Optional[Iterable[str]] = None,
        environ: Optional[Dict[str, str]] = None,
        overrides: Optional[Dict[KeyT, Any]] = None,
        logger: Optional[logging.Logger] = None,
        config: Optional[ContextConfig] = None,
        custom_scopes: Optional[Iterable[str]] = None,
        validate_only: bool = False,
        container_id: Optional[str] = None,
        observers: Optional[List["ContainerObserver"]] = None,
    ) -> PicoContainer:
        bound = _IOC_INIT_SIG.bind(
            modules,
            profiles=profiles,
            allowed_profiles=allowed_profiles,
            environ=environ,
            overrides=overrides,
            logger=logger,
            config=config,
            custom_scopes=custom_scopes,
            validate_only=validate_only,
            container_id=container_id,
            observers=observers,
        )
        bound.apply_defaults()

        base_modules = _normalize_modules(_to_module_list(bound.arguments["modules"]))

        auto_flag = os.getenv("PICO_STACK_AUTO_PLUGINS", "true").lower()
        auto_plugins = auto_flag not in ("0", "false", "no")

        if auto_plugins:
            plugin_modules = _load_plugin_modules()
            all_modules = _normalize_modules(list(base_modules) + plugin_modules)
        else:
            all_modules = base_modules

        bound.arguments["modules"] = all_modules

        return _ioc_init(*bound.args, **bound.kwargs)

    init.__signature__ = _IOC_INIT_SIG
