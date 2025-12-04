# Lazy import to avoid breaking FastAPI imports
# Only import Flask blueprint when actually needed (Flask context)
# When FastAPI imports fastapi_security.py, we don't want to trigger the Flask blueprint import
# Simply catch any import errors and continue without the blueprint
try:
    from .security import security_bp
    __all__ = ['security_bp']
except (ImportError, ModuleNotFoundError):
    # If import fails (e.g., in FastAPI context where dependencies might not be available),
    # just define __all__ without the blueprint - this allows FastAPI to import fastapi_security.py
    __all__ = []

