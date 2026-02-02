import json
import os
from typing import Any, Dict, Optional

class Blackboard:
    """
    A persistent state store for orchestration context.
    Allows agents to share data without direct coupling.
    """
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Loads state from disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def save(self):
        """Saves state to disk."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def set(self, key: str, value: Any, scope: str = "shared"):
        """Sets a value in the blackboard."""
        if scope not in self.data:
            self.data[scope] = {}
        self.data[scope][key] = value
        self.save()

    def get(self, key: str, scope: str = "shared") -> Optional[Any]:
        """Gets a value from the blackboard."""
        return self.data.get(scope, {}).get(key)

    def get_all(self, scope: str = "shared") -> Dict[str, Any]:
        """Returns all data in a given scope."""
        return self.data.get(scope, {}).copy()

    def clear(self):
        """Clears all data."""
        self.data = {}
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
