"""Backward-compatibility shim — use agent.schemas.video in new code."""
from agent.schemas.video import Video, VideoCreate, VideoUpdate

__all__ = ["Video", "VideoCreate", "VideoUpdate"]
