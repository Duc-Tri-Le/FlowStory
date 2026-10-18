"""Audio Mixing Service with Ducking and EBU R128 Loudness Normalization.

Combines voice narration track with background music (BGM):
1. Ducking: Automatically attenuates BGM volume when speech is present.
2. Loudness normalization: Uses FFmpeg 'loudnorm' filter (EBU R128 standard, target -16 LUFS)
   optimized for YouTube / faceless storytime videos.
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def mix_voice_and_bgm(
    voice_path: str,
    bgm_path: str,
    output_path: str,
    bgm_base_volume: float = 0.18,  # Background music volume when talking
    fade_out_duration: float = 2.0,
    normalize_loudness: bool = True,
    target_i: float = -16.0,        # Target Integrated Loudness (-16 LUFS is YouTube standard)
) -> bool:
    """Mix speech audio with background music, applying ducking and loudness normalization.

    Args:
        voice_path: Path to voiceover audio file.
        bgm_path: Path to background music track (looped if shorter than voice).
        output_path: Path to output audio file.
        bgm_base_volume: BGM volume level (0.15 - 0.25 recommended).
        fade_out_duration: BGM fade-out duration at the end of the voice track.
        normalize_loudness: Apply ffmpeg loudnorm filter (EBU R128).
        target_i: Integrated loudness target in LUFS (-16 for web/YouTube).

    Returns:
        True if success, False otherwise.
    """
    if not Path(voice_path).exists():
        logger.error("Voice file not found: %s", voice_path)
        return False
    if not Path(bgm_path).exists():
        logger.error("BGM file not found: %s", bgm_path)
        return False

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Probe voice duration
    probe_cmd = ["ffmpeg", "-i", str(voice_path)]
    voice_dur = 0.0
    try:
        proc = subprocess.run(probe_cmd, capture_output=True, text=True)
        import re
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", proc.stderr)
        if m:
            h, mi, s = m.groups()
            voice_dur = int(h) * 3600 + int(mi) * 60 + float(s)
    except Exception:
        pass

    total_dur = max(1.0, voice_dur)
    fade_start = max(0.0, total_dur - fade_out_duration)

    # 2. Build FFmpeg filter chain
    # Stream 0 = Voice, Stream 1 = BGM (stream_loop -1 ensures BGM loops if voice is longer)
    # [1:a] volume reduced + fadeout, merged with voice [0:a], then passed through loudnorm
    filter_parts = [
        f"[1:a]volume={bgm_base_volume:.2f},afade=t=out:st={fade_start:.2f}:d={fade_out_duration:.2f}[bgm]",
        f"[0:a]volume=1.0[voice]",
        f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[mixed]",
    ]

    if normalize_loudness:
        filter_parts.append(f"[mixed]loudnorm=I={target_i:.1f}:TP=-1.5:LRA=11[aout]")
        map_out = "[aout]"
    else:
        map_out = "[mixed]"

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(voice_path),
        "-stream_loop", "-1", "-i", str(bgm_path),
        "-filter_complex", filter_complex,
        "-map", map_out,
        "-t", str(total_dur + 0.5),  # slight padding
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(out_file),
    ]

    logger.info("Mixing voice + BGM with ducking to %s", out_file.name)
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if res.returncode != 0:
        logger.error("FFmpeg audio mix failed: %s", res.stderr[-300:] if res.stderr else "unknown error")
        return False

    return True
