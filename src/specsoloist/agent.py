import importlib.util
import os
import sys
from typing import Any, Dict

class Agent:
    """
    Wraps a compiled SpecSoloist module to provide a standard interface.
    """
    def __init__(self, name: str, build_dir: str):
        self.name = name
        self.build_dir = build_dir
        self.module = self._load_module()

    def _load_module(self):
        """Dynamically loads the compiled python module."""
        module_path = os.path.join(self.build_dir, f"{self.name}.py")
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"Compiled module for agent '{self.name}' not found at {module_path}")
            
        spec = importlib.util.spec_from_file_location(self.name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module {self.name}")
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[self.name] = module
        spec.loader.exec_module(module)
        return module

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent with the given inputs.
        Tries to find a 'run', 'main', or 'execute' function, 
        or falls back to calling the module if it's callable.
        """
        # Try common entry points
        for entry in ["run", "main", "execute", "handler"]:
            if hasattr(self.module, entry):
                func = getattr(self.module, entry)
                return func(**inputs)
        
        # If no standard entry point, this might be a class-based agent 
        # (needs more sophisticated discovery)
        raise AttributeError(f"Agent '{self.name}' has no standard entry point (run, main, execute)")
