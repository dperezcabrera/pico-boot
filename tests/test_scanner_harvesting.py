"""End-to-end check of the two things pico-boot claims to do with real metadata.

The rest of the discovery suite mocks ``entry_points``. This one installs a
plugin the way a wheel does - a module plus a ``.dist-info`` directory holding
``entry_points.txt`` - and boots it in a subprocess, because ``entry_points()``
results and ``sys.modules`` are process-global and would leak into other tests.

Pins two documented claims:
  1. a package registering ``pico_boot.modules`` is imported and scanned;
  2. ``PICO_SCANNERS`` exposed by that package reach ``custom_scanners``, so a
     scanner can register components pico-ioc would not have found on its own.
"""

import json
import os
import pathlib
import subprocess
import sys
import textwrap

PLUGIN_SOURCE = '''
from pico_ioc import ProviderMetadata, component


@component
class Stamp:
    """Found by the normal scan, because the module was auto-discovered."""

    def text(self) -> str:
        return "stamped"


class Marker:
    """Not a component: only a custom scanner can turn this into one."""

    marker = True

    def text(self) -> str:
        return "marked"


class MarkerScanner:
    """CustomScanner is a Protocol: BOTH methods have to be implemented.

    Subclassing it and defining only scan() leaves the inherited should_scan()
    returning None, so the scanner is silently never applied.
    """

    seen = []

    def should_scan(self, obj):
        MarkerScanner.seen.append(getattr(obj, "__name__", type(obj).__name__))
        return isinstance(obj, type) and getattr(obj, "marker", False)

    def scan(self, obj):
        md = ProviderMetadata(
            key=obj,
            provided_type=obj,
            concrete_class=obj,
            factory_class=None,
            factory_method=None,
            qualifiers=set(),
            primary=False,
            lazy=False,
            infra=None,
            pico_name=None,
        )
        return obj, (lambda cls=obj: cls()), md


PICO_SCANNERS = [MarkerScanner()]
'''

# Auto-discovery boots every pico-* package installed next to the tests, so the
# config has to satisfy the ones that may be present (same approach as
# test_boot_integration.py).
BOOT_SCRIPT = textwrap.dedent(
    """
    import json
    from pico_ioc import DictSource, configuration
    from pico_boot import init

    import qa_plugin

    container = init(
        modules=[],
        config=configuration(DictSource({
            "resilience": {"enabled": False},
            "cache": {"enabled": False},
            "fastapi": {"title": "t", "version": "0.0.1"},
            "celery": {"broker_url": "memory://", "backend_url": "memory://"},
            "database": {"url": "sqlite+aiosqlite:///:memory:", "echo": False},
            "auth_client": {"enabled": False, "issuer": "http://t", "audience": "t"},
        })),
    )

    keys = {k.__name__ for k in container.keys() if isinstance(k, type)}
    print("__RESULT__" + json.dumps({
        "discovered": "Stamp" in keys,
        "scanner_ran": bool(qa_plugin.MarkerScanner.seen),
        "harvested": "Marker" in keys,
        "marker_text": container.get(qa_plugin.Marker).text() if "Marker" in keys else None,
    }))
    """
)


def _install_plugin(root: pathlib.Path) -> None:
    """Lay out a plugin exactly as a wheel would, entry point included."""
    (root / "qa_plugin.py").write_text(PLUGIN_SOURCE, encoding="utf-8")
    dist = root / "qa_plugin-0.1.0.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text("Metadata-Version: 2.1\nName: qa-plugin\nVersion: 0.1.0\n", encoding="utf-8")
    (dist / "entry_points.txt").write_text("[pico_boot.modules]\nqa_plugin = qa_plugin\n", encoding="utf-8")


def _boot(tmp_path: pathlib.Path) -> dict:
    _install_plugin(tmp_path)
    script = tmp_path / "boot.py"
    script.write_text(BOOT_SCRIPT, encoding="utf-8")

    # pico-testing sets PICO_BOOT_AUTO_PLUGINS=false for every test and the
    # subprocess inherits it - which would switch off the very thing under test.
    env = {**os.environ, "PICO_BOOT_AUTO_PLUGINS": "true"}

    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    assert proc.returncode == 0, f"boot failed:\n{proc.stdout}\n{proc.stderr}"
    line = next(out for out in proc.stdout.splitlines() if out.startswith("__RESULT__"))
    return json.loads(line.removeprefix("__RESULT__"))


def test_entry_point_module_is_discovered_and_scanned(tmp_path):
    """A package registering pico_boot.modules is booted without being listed."""
    assert _boot(tmp_path)["discovered"] is True


def test_pico_scanners_are_harvested_into_custom_scanners(tmp_path):
    """PICO_SCANNERS from a discovered module register their own components."""
    result = _boot(tmp_path)
    assert result["scanner_ran"] is True, "the scanner was never offered any object"
    assert result["harvested"] is True, "PICO_SCANNERS did not reach custom_scanners"
    assert result["marker_text"] == "marked"
