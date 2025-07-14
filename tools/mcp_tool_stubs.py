
"""
MCP Tool Stubs (Modular)
=======================

This file now delegates to submodules by operation class:
- filesystem.py: Filesystem & code-editing tools
- exec_debug.py: Code execution & debugging
- analysis.py: Static & dynamic analysis

Import from these modules directly for new code.
"""

from .filesystem import *
from .exec_debug import *
from .analysis import *
