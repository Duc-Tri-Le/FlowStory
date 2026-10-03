"""Backward-compatibility shim — use agent.schemas.review in new code."""
from agent.schemas.review import VideoReview, SceneReview, DimensionScores, SegmentScore, VideoError

__all__ = ["VideoReview", "SceneReview", "DimensionScores", "SegmentScore", "VideoError"]
