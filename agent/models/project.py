"""Backward-compatibility shim — use agent.schemas.project in new code."""
from agent.schemas.project import Project, ProjectCreate, ProjectUpdate, CharacterInput

__all__ = ["Project", "ProjectCreate", "ProjectUpdate", "CharacterInput"]
