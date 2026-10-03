"""Backward-compatibility shim — use agent.schemas.scene in new code."""
from agent.schemas.scene import Scene, SceneCreate, SceneUpdate

__all__ = ["Scene", "SceneCreate", "SceneUpdate"]
