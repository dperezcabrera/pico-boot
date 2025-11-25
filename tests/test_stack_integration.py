import sys
import traceback
from pico_stack import init
from pico_ioc import PicoContainer, configuration, DictSource

try:
    from pico_fastapi import FastApiSettings, FastApiAppFactory
    from pico_pydantic import ValidationInterceptor
except ImportError:
    print("❌ CRITICAL ERROR: Could not import plugin modules directly.")
    sys.exit(1)

def test_pico_stack_auto_discovery():
    print("🚀 Starting pico-stack init()...")

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

    print("✅ Container initialized.")

    assert isinstance(container, PicoContainer), "Instance is not a PicoContainer"

    settings = container.get(FastApiSettings)
    assert settings is not None, "FastApiSettings component not found"
    assert settings.title == "Stack Integration Test", "FastAPI configuration not applied"
    print(f"✅ FastAPI Plugin detected and configured: {settings.title}")

    interceptor = container.get(ValidationInterceptor)
    assert interceptor is not None, "ValidationInterceptor component not found"
    print("✅ Pydantic Plugin detected and loaded.")

if __name__ == "__main__":
    try:
        test_pico_stack_auto_discovery()
        print("\n✨ SUCCESS: System integration works correctly.")
    except Exception as e:
        print(f"\n❌ FAILURE: {e}")
        traceback.print_exc()
        sys.exit(1)
