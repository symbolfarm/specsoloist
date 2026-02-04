"""
Spechestra - Orchestration layer for spec-driven development.

Provides high-level workflows for turning plain English requests into working software.

Components:
- SpecComposer: Drafts architecture and specs from natural language
- SpecConductor: Manages parallel builds and workflow execution
"""

from .composer import SpecComposer
from .conductor import SpecConductor

__all__ = ["SpecComposer", "SpecConductor"]
