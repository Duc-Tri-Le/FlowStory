"""Backward-compatibility shim — use agent.schemas.material in new code."""
from agent.schemas.material import MaterialCreateRequest, MaterialResponse

__all__ = ["MaterialCreateRequest", "MaterialResponse"]
