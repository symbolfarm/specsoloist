"""
SpecSoloist: Spec-as-Source AI Coding Framework

SpecSoloist treats rigorous SRS-style Markdown specifications as the
single source of truth, using LLMs to compile them into code.
"""

from .core import SpecSoloistCore, BuildResult
from .config import SpecSoloistConfig

__all__ = [
    "SpecSoloistCore",
    "SpecSoloistConfig",
    "BuildResult",
]
