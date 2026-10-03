"""Backward-compatibility shim — use agent.schemas.tts in new code."""
from agent.schemas.tts import (
    TTSGenerateRequest, TTSGenerateResponse,
    NarrateVideoRequest, NarrateVideoResponse,
    SceneNarrationResult, VoiceTemplateRequest, VoiceTemplateResponse,
    VoiceTemplateListItem,
)

__all__ = [
    "TTSGenerateRequest", "TTSGenerateResponse",
    "NarrateVideoRequest", "NarrateVideoResponse",
    "SceneNarrationResult", "VoiceTemplateRequest", "VoiceTemplateResponse",
    "VoiceTemplateListItem",
]
