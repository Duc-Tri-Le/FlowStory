"""Whisper Forced Alignment & Word-Level Timestamps Service.

Extracts precise start and end timestamps for every single word in an audio file,
enabling exact word-by-word subtitle highlighting in Remotion animations.
Uses faster-whisper (CTranslate2) for high-speed local inference on CPU.
"""
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Cached model instance
_WHISPER_MODEL = None
_DEFAULT_MODEL_SIZE = "tiny"  # 'tiny' or 'base' for fast and accurate CPU alignment


def get_whisper_model(model_size: str = _DEFAULT_MODEL_SIZE):
    """Lazy-load and cache the faster-whisper model."""
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        from faster_whisper import WhisperModel
        logger.info("Loading Whisper model '%s' on CPU (int8)...", model_size)
        _WHISPER_MODEL = WhisperModel(model_size, device="cpu", compute_type="int8")
        logger.info("Whisper model loaded successfully.")
    return _WHISPER_MODEL


def align_audio(
    audio_path: str,
    language: str = "vi",
    model_size: str = _DEFAULT_MODEL_SIZE,
) -> Dict[str, Any]:
    """Extract word-level timestamps from an audio file.

    Args:
        audio_path: Path to the input MP3/WAV file.
        language: Language code (default 'vi' for Vietnamese).
        model_size: Model size ('tiny', 'base', etc.).

    Returns:
        Dict containing:
            - full_text: string
            - words: list of dicts [{'word': str, 'start': float, 'end': float}]
    """
    audio_file = Path(audio_path)
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = get_whisper_model(model_size)

    # Transcribe with word timestamps enabled
    segments, info = model.transcribe(
        str(audio_file),
        word_timestamps=True,
        language=language,
        vad_filter=True,  # Filter out silence/noise
    )

    words_list: List[Dict[str, Any]] = []
    text_segments: List[str] = []

    for seg in segments:
        text_segments.append(seg.text.strip())
        if seg.words:
            for w in seg.words:
                clean_word = w.word.strip()
                if clean_word:
                    words_list.append({
                        "word": clean_word,
                        "start": round(w.start, 2),
                        "end": round(w.end, 2),
                    })

    full_text = " ".join(text_segments)
    logger.info("Aligned audio %s: %d words (%.2fs)", audio_file.name, len(words_list), info.duration)

    return {
        "audio_path": str(audio_file),
        "duration": round(info.duration, 2),
        "full_text": full_text,
        "words": words_list,
    }


def format_srt_timestamp(seconds: float) -> str:
    """Convert float seconds to SRT time string (HH:MM:SS,mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def export_word_srt(words: List[Dict[str, Any]], srt_path: str):
    """Export word-level list into an SRT subtitle file."""
    lines = []
    for idx, w in enumerate(words, start=1):
        start_ts = format_srt_timestamp(w["start"])
        end_ts = format_srt_timestamp(w["end"])
        lines.append(f"{idx}\n{start_ts} --> {end_ts}\n{w['word']}\n")

    Path(srt_path).write_text("\n".join(lines), encoding="utf-8")


def align_scenes(
    scenes_with_audio: List[Dict[str, Any]],
    language: str = "vi",
) -> List[Dict[str, Any]]:
    """Align audio for all scenes in a batch and attach word timestamps.

    Args:
        scenes_with_audio: List of scene objects with 'audio_path'.
        language: Target language.

    Returns:
        Enriched scene list with 'subtitles' field: [{'word', 'start', 'end'}].
    """
    results = []
    for scene in scenes_with_audio:
        audio_path = scene.get("audio_path")
        if not audio_path or not Path(audio_path).exists():
            results.append({**scene, "subtitles": []})
            continue

        try:
            align_data = align_audio(audio_path, language=language)
            results.append({
                **scene,
                "subtitles": align_data["words"],
                "audio_duration": align_data["duration"],
            })
        except Exception as e:
            logger.error("Failed to align audio for scene: %s", e)
            results.append({**scene, "subtitles": [], "align_error": str(e)})

    return results
