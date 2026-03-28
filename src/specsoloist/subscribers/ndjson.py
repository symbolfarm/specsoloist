"""NDJSON (Newline Delimited JSON) event subscriber.

Writes one JSON object per line to a file or stdout, enabling post-hoc
analysis with jq, Datadog, Grafana, or any log aggregator.
"""

import json
from typing import IO

from ..events import BuildEvent


class NdjsonSubscriber:
    """Writes BuildEvents as NDJSON to a writable file object."""

    def __init__(self, file: IO[str]) -> None:
        """Initialize with a writable file object.

        Args:
            file: Writable text stream (e.g., open file, sys.stdout, StringIO).
        """
        self._file = file

    def __call__(self, event: BuildEvent) -> None:
        """Serialize and write a single event as a JSON line."""
        record = {
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "spec_name": event.spec_name,
            **event.data,
        }
        self._file.write(json.dumps(record, default=str) + "\n")
        self._file.flush()
