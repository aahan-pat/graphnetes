"""Registry mapping Kubernetes resource kind strings to extractor functions."""

from __future__ import annotations

from typing import Any, Callable


class ExtractorRegistry:
    """Maps Kubernetes resource kind names to extractor functions.

    Extractors are registered with the @ExtractorRegistry.register decorator
    and keyed by kind string (e.g. "Pod", "Deployment").
    """

    extractors: dict[str, Callable[..., Any]] = {}

    @staticmethod
    def register(kind: str) -> Callable:
        """Return a decorator that registers the wrapped function under kind."""
        def decorator(fn: Callable) -> Callable:
            ExtractorRegistry.extractors[kind] = fn
            return fn
        return decorator