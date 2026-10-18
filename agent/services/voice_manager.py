"""Unified Voice Manager for FlowStory.

Orchestrates multiple TTS providers:
1. Edge-TTS (Cloud, fast, 0 VRAM) - vi-VN-NamMinhNeural & vi-VN-HoaiMyNeural
2. GPT-SoVITS (Local GPU GTX 1650, high-emotion character voice cloning)
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from agent.services.edge_tts_service import (
    generate_speech as generate_edge_speech,
    get_audio_duration_seconds,
    DEFAULT_VOICE_MALE,
    DEFAULT_VOICE_FEMALE,
)
from agent.services.gpt_sovits_service import (
    is_gpt_sovits_online,
    get_local_gpt_voices,
    generate_speech_gpt_sovits,
)

logger = logging.getLogger(__name__)


async def get_all_voices() -> Dict[str, Any]:
    """Retrieve full catalog of available voices across all engines with live status."""
    gpt_online = await is_gpt_sovits_online()
    gpt_voices = get_local_gpt_voices()

    edge_catalog = [
        {
            "id": "vi-VN-NamMinhNeural",
            "name": "🎙️ Nam Minh (Trầm ấm - Kể chuyện Noir)",
            "engine": "edge",
            "status": "ready",
            "gender": "male",
            "description": "Microsoft Edge Cloud Neural - Chuẩn dẫn truyện trinh thám, không cần GPU",
        },
        {
            "id": "vi-VN-HoaiMyNeural",
            "name": "🎙️ Hoài My (Truyền cảm - Drama)",
            "engine": "edge",
            "status": "ready",
            "gender": "female",
            "description": "Microsoft Edge Cloud Neural - Rõ ràng, cảm xúc gia đình / drama",
        },
    ]

    gpt_catalog = []
    for gv in gpt_voices:
        status_label = "ready" if gpt_online else "offline"
        gpt_catalog.append({
            **gv,
            "status": status_label,
            "description": "GPT-SoVITS Local (GTX 1650) - Biểu cảm kịch tính, lồng tiếng nhân vật"
            + ("" if gpt_online else " [Server chưa bật: http://localhost:9880]"),
        })

    return {
        "ok": True,
        "gpt_sovits_online": gpt_online,
        "voices": edge_catalog + gpt_catalog,
        "groups": [
            {
                "label": "⚡ Edge-TTS (Cloud Sẵn Sàng)",
                "engine": "edge",
                "voices": edge_catalog,
            },
            {
                "label": f"🎭 GPT-SoVITS (Voice Clone Cục Bộ - {'🟢 Đang Chạy' if gpt_online else '⚪ Chưa Bật Server'})",
                "engine": "gpt_sovits",
                "online": gpt_online,
                "voices": gpt_catalog,
            },
        ],
    }


async def generate_speech_unified(
    text: str,
    output_path: str,
    voice: Optional[str] = None,
    rate: str = "-4%",
    speed: float = 1.0,
) -> Dict[str, Any]:
    """Generate speech using the selected engine, with fallback if local engine offline."""
    selected_voice = voice or DEFAULT_VOICE_MALE

    # Check if voice is GPT-SoVITS
    if selected_voice.startswith("gpt:"):
        is_online = await is_gpt_sovits_online()
        if is_online:
            try:
                return await generate_speech_gpt_sovits(text, output_path, voice_id=selected_voice, speed=speed)
            except Exception as e:
                logger.warning("GPT-SoVITS failed for '%s', falling back to Edge-TTS: %s", selected_voice, e)
        else:
            logger.warning("GPT-SoVITS server is offline. Falling back to Edge-TTS for: %s", selected_voice)

        # Fallback to Edge-TTS
        fallback_voice = DEFAULT_VOICE_MALE if "nam" in selected_voice or "tra" in selected_voice else DEFAULT_VOICE_FEMALE
        return await generate_edge_speech(text, output_path, voice=fallback_voice, rate=rate)

    # Default: Edge-TTS
    return await generate_edge_speech(text, output_path, voice=selected_voice, rate=rate)


async def generate_batch_narration_unified(
    scenes: List[Dict[str, Any]],
    output_dir: str,
    default_voice: str = DEFAULT_VOICE_MALE,
    rate: str = "-4%",
) -> List[Dict[str, Any]]:
    """Batch generate narration for all scenes across mixed voices/engines."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for idx, scene in enumerate(scenes):
        order = scene.get("display_order", idx)
        text = scene.get("narrator_text") or scene.get("text") or ""
        scene_voice = scene.get("voice") or default_voice

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
            res = await generate_speech_unified(text, target_path, voice=scene_voice, rate=rate)
            results.append({
                **scene,
                "audio_path": res["path"],
                "audio_duration": res["duration"],
                "voice_used": res.get("voice", scene_voice),
                "status": "COMPLETED",
            })
        except Exception as e:
            logger.error("Failed TTS for scene %d (%s): %s", order, scene_voice, e)
            results.append({
                **scene,
                "audio_path": None,
                "audio_duration": 0.0,
                "error": str(e),
                "status": "FAILED",
            })

    return results
