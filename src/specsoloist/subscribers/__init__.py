"""Event bus subscribers for build observability."""

from .ndjson import NdjsonSubscriber

__all__ = ["NdjsonSubscriber"]
