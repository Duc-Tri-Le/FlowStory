"""Edge-TTS Vietnamese Voice Service for Storytime Animation.

Provides high-quality, natural Vietnamese speech using Microsoft Edge neural voices:
- vi-VN-NamMinhNeural (Male, deep, calm, ideal for detective/thriller/noir storytime)
- vi-VN-HoaiMyNeural (Female, emotional, clear, ideal for drama/heartfelt storytime)
"""
import asyncio
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

import edge_tts

logger = logging.getLogger(__name__)

DEFAULT_VOICE_MALE = "vi-VN-NamMinhNeural"
DEFAULT_VOICE_FEMALE = "vi-VN-HoaiMyNeural"


def get_audio_duration_seconds(audio_path: str) -> float:
    """Measure exact audio duration in seconds using ffmpeg."""
    cmd = ["ffmpeg", "-i", str(audio_path)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        match = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", proc.stderr)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception as e:
        logger.warning("Could not probe duration with ffmpeg: %s", e)
    return 0.0


async def generate_speech(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE_MALE,
    rate: str = "-4%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
) -> Dict[str, Any]:
    """Generate speech for a single text line using Edge-TTS.

    Args:
        text: Plain text content in Vietnamese.
        output_path: Path to output audio file (.mp3).
        voice: Neural voice ID (default: vi-VN-NamMinhNeural).
        rate: Speech rate modifier (e.g. "-5%", "+10%").
        pitch: Pitch modifier (e.g. "-2Hz", "+0Hz").
        volume: Volume modifier.

    Returns:
        Dict with status, output path, and measured duration in seconds.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    clean_text = text.strip()
    if not clean_text:
        return {"ok": False, "error": "Empty text", "duration": 0.0, "path": None}

    communicate = edge_tts.Communicate(clean_text, voice, rate=rate, pitch=pitch, volume=volume)
    await communicate.save(str(out_file))

    duration = get_audio_duration_seconds(str(out_file))
    logger.info("Generated TTS: '%s...' -> %s (%.2fs)", clean_text[:30], out_file.name, duration)

    return {
        "ok": True,
        "path": str(out_file),
        "duration": duration,
        "text": clean_text,
        "voice": voice,
    }


async def generate_batch_narration(
    scenes: List[Dict[str, Any]],
    output_dir: str,
    voice: str = DEFAULT_VOICE_MALE,
    rate: str = "-4%",
) -> List[Dict[str, Any]]:
    """Batch generate narration for multiple scenes.

    Args:
        scenes: List of scene dicts, each having 'narrator_text' (and optional 'speaker' or 'display_order').
        output_dir: Directory where MP3s will be saved.
        voice: Default voice to use if scene doesn't specify one.
        rate: Speech speed modifier.

    Returns:
        List of scene objects enriched with 'audio_path' and 'audio_duration'.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for idx, scene in enumerate(scenes):
        order = scene.get("display_order", idx)
        text = scene.get("narrator_text") or scene.get("text") or ""
        
        # Support explicit per-scene voice or speaker-specific voice
        if scene.get("voice"):
            scene_voice = scene["voice"]
        else:
            speaker = str(scene.get("speaker", "")).lower()
            scene_voice = voice
            if "nữ" in speaker or "female" in speaker or "mẹ" in speaker or "cô" in speaker:
                scene_voice = DEFAULT_VOICE_FEMALE
            elif "nam" in speaker or "male" in speaker or "bố" in speaker or "anh" in speaker or "thanh tra" in speaker:
                scene_voice = DEFAULT_VOICE_MALE

        if not text.strip():
            results.append({
                **scene,
                "audio_path": None,
                "audio_duration": 0.0,
                "status": "SKIPPED",
            })
            continue

        filename = f"scene_{order:03d}.mp3"
        target_path = str(out_dir / filename)

        try:
            res = await generate_speech(text, target_path, voice=scene_voice, rate=rate)
            results.append({
                **scene,
                "audio_path": res["path"],
                "audio_duration": res["duration"],
                "voice_used": scene_voice,
                "status": "COMPLETED",
            })
        except Exception as e:
            logger.error("Failed TTS for scene %d: %s", order, e)
            results.append({
                **scene,
                "audio_path": None,
                "audio_duration": 0.0,
                "error": str(e),
                "status": "FAILED",
            })

    return results
