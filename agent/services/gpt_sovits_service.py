"""GPT-SoVITS Voice Cloning Service for Storytime Animation.

Connects to local GPT-SoVITS API server (default http://127.0.0.1:9880)
to provide high-emotion zero-shot voice cloning for characters.
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

from agent.services.edge_tts_service import get_audio_duration_seconds

logger = logging.getLogger(__name__)

GPT_SOVITS_URL = os.environ.get("GPT_SOVITS_URL", "http://127.0.0.1:9880")
VOICES_DIR = Path("voices/gpt_sovits")


async def is_gpt_sovits_online(url: str = GPT_SOVITS_URL) -> bool:
    """Check if local GPT-SoVITS API server is online and responding."""
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(f"{url}/")
            return resp.status_code in [200, 404, 405]
    except Exception:
        return False


def get_local_gpt_voices() -> List[Dict[str, Any]]:
    """Scan voices/gpt_sovits directory for reference audio clips."""
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    voices = []

    for audio_file in sorted(VOICES_DIR.glob("*.*")):
        if audio_file.suffix.lower() not in [".wav", ".mp3", ".flac", ".ogg"]:
            continue

        voice_key = audio_file.stem
        # Check for companion transcript file (.txt)
        txt_file = audio_file.with_suffix(".txt")
        prompt_text = ""
        if txt_file.exists():
            try:
                prompt_text = txt_file.read_text(encoding="utf-8").strip()
            except Exception as e:
                logger.warning("Could not read prompt text %s: %s", txt_file, e)

        # Create human-readable title
        clean_title = voice_key.replace("_", " ").replace("-", " ").title()

        voices.append({
            "id": f"gpt:{voice_key}",
            "name": f"🎭 {clean_title} (Clone)",
            "key": voice_key,
            "engine": "gpt_sovits",
            "audio_path": str(audio_file.resolve()),
            "prompt_text": prompt_text,
            "gender": "male" if ("nam" in voice_key or "minh" in voice_key or "tra" in voice_key) else "female",
        })

    # If no local files yet, provide preset placeholder suggestions
    if not voices:
        voices = [
            {
                "id": "gpt:thanh_tra_minh",
                "name": "🎭 Thanh Tra Minh (Mẫu)",
                "key": "thanh_tra_minh",
                "engine": "gpt_sovits",
                "audio_path": None,
                "prompt_text": "Màn đêm buông xuống, tôi linh cảm điều bất thường sắp xảy ra.",
                "gender": "male",
            },
            {
                "id": "gpt:sat_nhan_giau_mat",
                "name": "🎭 Kẻ Giấu Mặt (Mẫu)",
                "key": "sat_nhan_giau_mat",
                "engine": "gpt_sovits",
                "audio_path": None,
                "prompt_text": "Ngươi tưởng có thể thoát khỏi nơi này sao?",
                "gender": "male",
            }
        ]

    return voices


async def generate_speech_gpt_sovits(
    text: str,
    output_path: str,
    voice_id: str,
    speed: float = 1.0,
    url: str = GPT_SOVITS_URL,
) -> Dict[str, Any]:
    """Generate speech using GPT-SoVITS local API server.

    Args:
        text: Vietnamese text to speak.
        output_path: Target audio file path (.mp3 or .wav).
        voice_id: Voice identifier (e.g. 'gpt:thanh_tra_minh').
        speed: Speed factor (1.0 = normal).
        url: GPT-SoVITS API base URL.

    Returns:
        Dict with status, output path, duration.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    voice_key = voice_id.replace("gpt:", "")
    voices = {v["key"]: v for v in get_local_gpt_voices()}
    voice_info = voices.get(voice_key, {})

    ref_audio_path = voice_info.get("audio_path")
    prompt_text = voice_info.get("prompt_text", "")

    # Payload for GPT-SoVITS API (compatible with api.py and api_v2.py)
    payload = {
        "text": text.strip(),
        "text_lang": "vi",
        "ref_audio_path": ref_audio_path or "",
        "prompt_text": prompt_text,
        "prompt_lang": "vi",
        "speed_factor": speed,
        "streaming_mode": False,
    }

    temp_wav = out_file.with_suffix(".temp.wav")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{url}/tts", json=payload)
            if resp.status_code != 200:
                # Try GET endpoint fallback
                params = {
                    "text": text.strip(),
                    "text_lang": "vi",
                    "ref_audio_path": ref_audio_path or "",
                    "prompt_text": prompt_text,
                    "prompt_lang": "vi",
                }
                resp = await client.get(f"{url}/tts", params=params)

            if resp.status_code != 200:
                raise RuntimeError(f"GPT-SoVITS API error HTTP {resp.status_code}: {resp.text[:120]}")

            temp_wav.write_bytes(resp.content)

        # Convert to target mp3 or move to final path
        if out_file.suffix.lower() == ".mp3":
            cmd = ["ffmpeg", "-y", "-i", str(temp_wav), "-b:a", "192k", str(out_file)]
            subprocess.run(cmd, capture_output=True, check=True)
            if temp_wav.exists():
                temp_wav.unlink()
        else:
            if temp_wav.exists():
                if out_file.exists():
                    out_file.unlink()
                temp_wav.rename(out_file)

        duration = get_audio_duration_seconds(str(out_file))
        logger.info("Generated GPT-SoVITS: '%s...' -> %s (%.2fs)", text[:25], out_file.name, duration)

        return {
            "ok": True,
            "path": str(out_file),
            "duration": duration,
            "text": text,
            "voice": voice_id,
        }

    except Exception as e:
        logger.error("GPT-SoVITS generation failed: %s", e)
        if temp_wav.exists():
            temp_wav.unlink()
        raise e
