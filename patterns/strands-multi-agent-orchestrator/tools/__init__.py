"""
Tools module for multi-agent orchestration pattern.

This module exports shared tools that agents can import and use:
- SpecialistInvocationTools: Class-based wrapper for specialist invocation (recommended)
- invoke_colorado: Invoke Colorado specialist agent (standalone, for backward compatibility)
- invoke_umich: Invoke UMich specialist agent (standalone, for backward compatibility)
- invoke_coder: Invoke Coder specialist agent (standalone, for backward compatibility)

Note: execute_python_securely is not exported here because the orchestrator
doesn't execute code directly - it routes to the Coder specialist agent instead.

Agents can import these tools using:
    from tools import SpecialistInvocationTools  # Recommended for Strands
    from tools import invoke_colorado, invoke_umich, invoke_coder  # Backward compatibility
"""

from tools.invoke_specialist import (
    SpecialistInvocationTools,
    invoke_colorado,
    invoke_umich,
    invoke_coder
)

__all__ = [
    "SpecialistInvocationTools",
    "invoke_colorado",
    "invoke_umich",
    "invoke_coder",
]
