from .registry import ExtractorRegistry
# Importing extractors triggers all @ExtractorRegistry.register decorators.
from . import extractors as _extractors

__all__ = ["ExtractorRegistry"]
