"""Backward-compatibility shim — imports now live in agent.schemas.

This package is kept so existing consumers don't break during migration.
Prefer importing directly from agent.schemas in new code.
"""
# Re-export everything from the canonical location
from agent.schemas.character import Character, CharacterCreate, CharacterUpdate
from agent.schemas.project import Project, ProjectCreate, ProjectUpdate
from agent.schemas.video import Video, VideoCreate, VideoUpdate
from agent.schemas.scene import Scene, SceneCreate, SceneUpdate
from agent.schemas.request import Request, RequestCreate
from agent.schemas.enums import RequestType, Orientation, StatusType, ChainType

__all__ = [
    "Character", "CharacterCreate", "CharacterUpdate",
    "Project", "ProjectCreate", "ProjectUpdate",
    "Video", "VideoCreate", "VideoUpdate",
    "Scene", "SceneCreate", "SceneUpdate",
    "Request", "RequestCreate",
    "RequestType", "Orientation", "StatusType", "ChainType",
]

