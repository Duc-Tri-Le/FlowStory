"""Backward-compatibility shim — use agent.schemas.character in new code."""
from agent.schemas.character import Character, CharacterCreate, CharacterUpdate

__all__ = ["Character", "CharacterCreate", "CharacterUpdate"]

