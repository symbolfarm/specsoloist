from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, ValidationError

class ParameterDefinition(BaseModel):
    """Definition of a single input or output parameter."""
    type: str
    description: Optional[str] = None
    default: Optional[Any] = None
    required: bool = True
    # Basic constraints for validation
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    enum: Optional[List[Any]] = None

    def compatible_with(self, other: 'ParameterDefinition') -> bool:
        """Checks if this definition (as an output) is compatible with other (as an input)."""
        # Basic type check
        if self.type != other.type:
            return False
            
        # Basic constraint check (if we have a range, it must be within their range)
        if other.minimum is not None and (self.minimum is None or self.minimum < other.minimum):
            return False
        if other.maximum is not None and (self.maximum is None or self.maximum > other.maximum):
            return False
            
        return True

class WorkflowStep(BaseModel):
    """A single step in an orchestration workflow."""
    name: str
    spec: str
    checkpoint: bool = False
    inputs: Dict[str, str] = Field(
        default_factory=dict, 
        description="Mapping of input name to source (e.g., 'step1.outputs.result')"
    )

class InterfaceSchema(BaseModel):
    """
    Represents the strict schema interface for a function or component.
    """
    inputs: Dict[str, ParameterDefinition] = Field(default_factory=dict)
    outputs: Dict[str, ParameterDefinition] = Field(default_factory=dict)
    
    # New: for orchestration
    steps: Optional[List[WorkflowStep]] = None
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Runtime validation of input dictionary against schema."""
        # This is a placeholder for runtime validation logic
        pass

def parse_schema_block(raw_yaml: Dict[str, Any]) -> InterfaceSchema:
    """Parses a raw YAML dictionary into an InterfaceSchema."""
    try:
        return InterfaceSchema(**raw_yaml)
    except ValidationError as e:
        raise ValueError(f"Invalid schema definition: {e}")
