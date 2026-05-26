from .static import StaticIngestor
# Importing register triggers all StaticIngestor.register() calls.
from . import register as _register

__all__ = ["StaticIngestor"]
