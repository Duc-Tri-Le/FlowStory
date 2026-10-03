"""Backward-compatibility shim — use agent.schemas.request in new code."""
from agent.schemas.request import Request, RequestCreate

__all__ = ["Request", "RequestCreate"]
