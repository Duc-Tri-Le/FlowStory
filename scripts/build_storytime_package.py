#!/usr/bin/env python3
"""Storytime Package Builder for Remotion.

End-to-end pipeline:
1. Load scenes from Story Spec JSON.
2. Generate Vietnamese TTS for each scene via Edge-TTS (Nam Minh / Hoai My).
3. Align audio with Faster-Whisper to extract word-level timestamps for Remotion karaoke subtitles.
4. Calculate exact duration in frames (fps=30) for Remotion timeline.
5. (Optional) Post-process background images with noir filter (B&W + darken).
6. Export final 'remotion_input.json' ready to plug directly into Remotion React components.

Usage:
    python scripts/build_storytime_package.py --spec story_spec.json --output-dir ./storytime_dist/
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from agent.services.edge_tts_service import generate_batch_narration
from agent.services.whisper_align import align_scenes
from agent.services.image_filter import apply_noir_filter


async def run_pipeline(spec_path: str, output_dir: str, voice: str = "vi-VN-NamMinhNeural", fps: int = 30):
    spec_file = Path(spec_path)
    if not spec_file.exists():
        print(f"[!] Lỗi: Không tìm thấy file spec: {spec_path}")
        sys.exit(1)

    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    scenes = spec.get("scenes", [])
    if not scenes:
        print("[!] Lỗi: Không có scene nào trong spec.")
        sys.exit(1)

    dist_dir = Path(output_dir)
    audio_dir = dist_dir / "audio"
    bg_dir = dist_dir / "backgrounds"
    audio_dir.mkdir(parents=True, exist_ok=True)
    bg_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== BƯỚC 1: SINH GIỌNG ĐỌC EDGE-TTS ({voice}) ===")
    tts_scenes = []
    for sc in scenes:
        tts_scenes.append({
            **sc,
            "narrator_text": sc.get("text", "")
        })

    scenes_with_audio = await generate_batch_narration(tts_scenes, str(audio_dir), voice=voice)
    print(f"[+] Đã sinh xong {len(scenes_with_audio)} file audio giọng đọc.")

    print("\n=== BƯỚC 2: PHỤ ĐỀ CHÍNH XÁC (WHISPER WORD-LEVEL ALIGNMENT) ===")
    scenes_with_subtitles = align_scenes(scenes_with_audio, language="vi")
    print(f"[+] Đã phân tích mốc thời gian từng từ cho toàn bộ {len(scenes_with_subtitles)} scenes.")

    print("\n=== BƯỚC 3: ĐỒNG BỘ THỜI GIAN & KHUNG HÌNH (FPS=30) ===")
    final_scenes = []
    total_frames = 0
    total_duration = 0.0

    for sc in scenes_with_subtitles:
        dur = sc.get("audio_duration", 0.0)
        # Pad with 0.3s silence so speech doesn't cut off abruptly
        padded_dur = round(dur + 0.3, 2)
        frame_count = int(padded_dur * fps)

        # Relativize audio path for Remotion assets
        audio_rel_path = f"audio/{Path(sc['audio_path']).name}" if sc.get("audio_path") else None

        final_scenes.append({
            "id": sc.get("id", sc.get("display_order")),
            "speaker": sc.get("speaker", "narrator"),
            "text": sc.get("text", ""),
            "camera": sc.get("camera", "zoom_in"),
            "expression": sc.get("expression", "serious"),
            "audio_file": audio_rel_path,
            "duration_seconds": padded_dur,
            "duration_frames": frame_count,
            "start_frame": total_frames,
            "end_frame": total_frames + frame_count,
            "subtitles": sc.get("subtitles", []),
            "background_prompt": sc.get("background_prompt", ""),
            "sound_fx": sc.get("sound_fx", ""),
        })

        total_frames += frame_count
        total_duration += padded_dur

    remotion_package = {
        "title": spec.get("title", "Storytime Animation"),
        "genre": spec.get("genre", "trinh_tham"),
        "fps": fps,
        "width": 1920,
        "height": 1080,
        "total_duration_seconds": round(total_duration, 2),
        "total_frames": total_frames,
        "characters": spec.get("characters", []),
        "scenes": final_scenes,
    }

    out_json = dist_dir / "remotion_input.json"
    out_json.write_text(json.dumps(remotion_package, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[+] HOÀN TẤT GÓI DỮ LIỆU REMOTION:")
    print(f"    - Thư mục xuất bản: {dist_dir.resolve()}")
    print(f"    - File input Remotion: {out_json.resolve()}")
    print(f"    - Tổng thời lượng: {total_duration:.1f}s ({total_frames} frames)")
    print(f"    - Từng từ phụ đề đã có mốc start/end milliseconds!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", "-s", required=True, help="Path to story spec JSON")
    parser.add_argument("--output-dir", "-o", default="./storytime_dist", help="Output directory")
    parser.add_argument("--voice", default="vi-VN-NamMinhNeural", help="Edge-TTS voice")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second for Remotion")
    args = parser.parse_args()

    asyncio.run(run_pipeline(args.spec, args.output_dir, voice=args.voice, fps=args.fps))
