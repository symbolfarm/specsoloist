from typing import Any, Dict, List, Optional
import os

from .parser import ParsedSpec, SpecParser
from .agent import Agent
from .state import Blackboard

class Orchestrator:
    """
    Executes a multi-agent workflow based on an orchestrator spec.
    """
    def __init__(self, parser: SpecParser, build_dir: str, checkpoint_callback=None):
        self.parser = parser
        self.build_dir = build_dir
        self.blackboard = Blackboard(os.path.join(build_dir, ".spechestra_state.json"))
        self.checkpoint_callback = checkpoint_callback

    def run(self, spec_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the specified orchestration workflow.
        """
        import time
        from datetime import datetime
        
        spec = self.parser.parse_spec(spec_name)
        if spec.metadata.type != "orchestrator":
            raise ValueError(f"Spec '{spec_name}' is not an orchestrator")
            
        if not spec.schema or not spec.schema.steps:
            raise ValueError(f"Orchestrator spec '{spec_name}' has no defined steps in its schema")

        # Initial state
        self.blackboard.clear()
        self.blackboard.set("inputs", inputs, scope="system")
        
        step_results = {}
        trace = {
            "orchestrator": spec_name,
            "start_time": datetime.now().isoformat(),
            "inputs": inputs,
            "steps": []
        }
        
        for step in spec.schema.steps:
            # Checkpoint check
            if step.checkpoint and self.checkpoint_callback:
                print(f"--- Checkpoint reached at step: {step.name} ---")
                if not self.checkpoint_callback(step.name):
                    print("Orchestration aborted by user.")
                    break

            print(f"Executing step: {step.name} ({step.spec})...")
            
            # 1. Resolve inputs for this step
            step_inputs = self._resolve_inputs(step.inputs, step_results, inputs)
            
            step_trace = {
                "name": step.name,
                "spec": step.spec,
                "inputs": step_inputs,
                "start_time": time.time()
            }
            
            # 2. Execute agent
            try:
                agent = Agent(step.spec, self.build_dir)
                result = agent.execute(step_inputs)
                step_trace["success"] = True
                step_trace["output"] = result
            except Exception as e:
                step_trace["success"] = False
                step_trace["error"] = str(e)
                trace["steps"].append(step_trace)
                self._save_trace(trace)
                raise
            
            step_trace["end_time"] = time.time()
            step_trace["duration"] = step_trace["end_time"] - step_trace["start_time"]
            
            # 3. Store result
            step_results[step.name] = result
            self.blackboard.set(step.name, result, scope="steps")
            trace["steps"].append(step_trace)
            
        trace["end_time"] = datetime.now().isoformat()
        self._save_trace(trace)
        return step_results

    def _save_trace(self, trace: Dict[str, Any]):
        """Saves execution trace to disk."""
        import json
        from datetime import datetime
        
        trace_dir = os.path.join(self.build_dir, ".spechestra", "traces")
        os.makedirs(trace_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trace_{trace['orchestrator']}_{timestamp}.json"
        
        with open(os.path.join(trace_dir, filename), 'w') as f:
            json.dump(trace, f, indent=2)

    def _resolve_inputs(
        self, 
        mappings: Dict[str, str], 
        step_results: Dict[str, Any],
        initial_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolves input mappings to actual values."""
        resolved = {}
        for target, source in mappings.items():
            if source.startswith("inputs."):
                param = source.split(".", 1)[1]
                resolved[target] = initial_inputs.get(param)
            elif ".outputs." in source:
                parts = source.split(".")
                step_name = parts[0]
                param = parts[2]
                
                step_out = step_results.get(step_name, {})
                # If the agent returned a dict, we look up the param.
                # If it returned a single value and we expect 'result' or similar?
                if isinstance(step_out, dict):
                    resolved[target] = step_out.get(param)
                else:
                    # Fallback for single-return functions
                    resolved[target] = step_out
            else:
                # Literal or unsupported format
                resolved[target] = source
                
        return resolved
