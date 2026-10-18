"""Storytime Animation API Endpoints.

Provides endpoints for:
- AI Script Breakdown (10-25 words, camera, expression)
- Vietnamese Edge-TTS voice synthesis
- Whisper word-level alignment (Karaoke subtitle timestamps)
- Audio serving & Demo project loading
"""
import asyncio
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent.config import OUTPUT_DIR
from agent.services.voice_manager import (
    get_all_voices,
    generate_speech_unified,
    generate_batch_narration_unified,
)
from agent.services.whisper_align import align_audio, align_scenes
from agent.services.image_filter import apply_noir_filter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/storytime", tags=["storytime"])

STORYTIME_DIR = OUTPUT_DIR / "storytime"
STORYTIME_DIR.mkdir(parents=True, exist_ok=True)


class BreakdownRequest(BaseModel):
    story_text: str
    genre: str = "trinh_tham"


class TTSRequest(BaseModel):
    text: str
    voice: str = "vi-VN-NamMinhNeural"
    rate: str = "-4%"


class AlignRequest(BaseModel):
    filename: str


class SceneInput(BaseModel):
    display_order: int
    speaker: str = "thanh_tra"
    text: str
    camera: str = "zoom_in"
    expression: str = "serious"
    background_prompt: Optional[str] = None
    voice: Optional[str] = None


class PackageRequest(BaseModel):
    title: str = "Vụ Án Mới"
    genre: str = "trinh_tham"
    voice: str = "vi-VN-NamMinhNeural"
    scenes: List[SceneInput]


@router.post("/breakdown")
async def api_breakdown(req: BreakdownRequest):
    """Breakdown raw story text into structured scenes."""
    text = req.story_text.strip()
    if not text:
        raise HTTPException(400, "Vui lòng nhập nội dung câu chuyện.")

    # Try calling AI CLI
    from scripts.breakdown_storytime import call_ai, extract_json, validate_storytime_spec
    try:
        raw_ai = await asyncio.to_thread(call_ai, text)
        spec = extract_json(raw_ai)
        warnings = validate_storytime_spec(spec)
        return {"ok": True, "spec": spec, "warnings": warnings}
    except Exception as e:
        logger.warning("AI CLI breakdown failed (%s), using smart sentence splitting fallback", e)
        # Smart fallback: split story into 15-word chunks
        sentences = re.split(r"(?<=[.!?])\s+", text)
        scenes = []
        for i, s in enumerate(sentences):
            clean = s.strip()
            if not clean:
                continue
            cam = "close" if any(w in clean.lower() for w in ["chết", "máu", "án mạng", "bất ngờ", "sốc", "hung thủ", "biến mất"]) else "zoom_in"
            exp = "shocked" if cam == "close" else "serious"
            scenes.append({
                "display_order": i,
                "speaker": "thanh_tra",
                "text": clean,
                "camera": cam,
                "expression": exp,
                "background_prompt": "Dark detective room, rainy window. Pure scenery illustration, dark noir moody background, strictly NO people, NO characters."
            })
        fallback_spec = {
            "title": "Vụ Án Trinh Thám",
            "genre": req.genre,
            "characters": [
                {
                    "id": "thanh_tra",
                    "name": "Thanh tra Minh",
                    "description": "Nhân vật người que 2D đầu tròn trắng, áo măng tô than chì"
                }
            ],
            "scenes": scenes,
        }
        return {"ok": True, "spec": fallback_spec, "is_fallback": True}


@router.get("/voices")
async def api_get_voices():
    """Retrieve full list of available voices across Edge-TTS and GPT-SoVITS engines."""
    return await get_all_voices()


@router.post("/tts")
async def api_single_tts(req: TTSRequest):
    """Generate audio for a single sentence."""
    filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
    target_path = STORYTIME_DIR / "audio" / filename
    res = await generate_speech_unified(req.text, str(target_path), voice=req.voice, rate=req.rate)
    if not res.get("ok"):
        raise HTTPException(500, res.get("error", "TTS generation failed"))
    return {
        "ok": True,
        "filename": filename,
        "audio_url": f"/api/storytime/audio/{filename}",
        "duration": res["duration"],
    }


@router.post("/align")
async def api_align(req: AlignRequest):
    """Align word timestamps for an audio file."""
    audio_path = STORYTIME_DIR / "audio" / req.filename
    if not audio_path.exists():
        raise HTTPException(404, "Audio file not found")
    try:
        aligned = await asyncio.to_thread(align_audio, str(audio_path), language="vi")
        return {"ok": True, "words": aligned["words"], "duration": aligned["duration"]}
    except Exception as e:
        logger.error("Alignment failed: %s", e)
        raise HTTPException(500, f"Whisper alignment error: {e}")


def generate_script_subtitles(text: str, duration: float) -> list:
    """Generate word-level timestamps directly from script text and audio duration without needing STT."""
    words = text.strip().split()
    if not words:
        return []
    total_chars = sum(max(1, len(w)) for w in words)
    cursor = 0.12
    avail = max(0.5, duration - 0.28)
    subs = []
    for w in words:
        w_dur = max(0.12, (max(1, len(w)) / total_chars) * avail)
        subs.append({
            "word": w,
            "start": round(cursor, 3),
            "end": round(cursor + w_dur, 3),
        })
        cursor += w_dur
    return subs


@router.post("/build-package")
async def api_build_package(req: PackageRequest):
    """Generate TTS and clean subtitles directly from script text for an entire scene list."""
    package_id = uuid.uuid4().hex[:8]
    pkg_dir = STORYTIME_DIR / f"pkg_{package_id}"
    audio_dir = pkg_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # 1. Edge-TTS Batch
    tts_items = [
        {
            "display_order": s.display_order,
            "text": s.text,
            "speaker": s.speaker,
            "camera": s.camera,
            "expression": s.expression,
            "background_prompt": s.background_prompt,
            "voice": s.voice or req.voice,
        }
        for s in req.scenes
    ]
    scenes_with_audio = await generate_batch_narration_unified(tts_items, str(audio_dir), default_voice=req.voice)

    # 2. Subtitles derived directly from script text (no Whisper STT / voice-to-text required!)
    for sc in scenes_with_audio:
        sc["subtitles"] = generate_script_subtitles(sc.get("text", ""), sc.get("audio_duration", 4.0))
    scenes_with_subtitles = scenes_with_audio

    # 3. Assemble package
    total_frames = 0
    total_duration = 0.0
    fps = 30
    final_scenes = []

    for sc in scenes_with_subtitles:
        dur = sc.get("audio_duration", 4.0)
        padded_dur = round(dur + 0.35, 2)
        frame_count = int(padded_dur * fps)
        audio_name = Path(sc["audio_path"]).name if sc.get("audio_path") else None

        final_scenes.append({
            "id": sc["display_order"],
            "speaker": sc.get("speaker", "thanh_tra"),
            "text": sc.get("text", ""),
            "camera": sc.get("camera", "zoom_in"),
            "expression": sc.get("expression", "serious"),
            "voice": sc.get("voice_used") or sc.get("voice") or req.voice,
            "audio_url": f"/api/storytime/pkg-audio/{package_id}/{audio_name}" if audio_name else None,
            "duration_seconds": padded_dur,
            "duration_frames": frame_count,
            "start_frame": total_frames,
            "end_frame": total_frames + frame_count,
            "subtitles": sc.get("subtitles", []),
            "background_prompt": sc.get("background_prompt", ""),
        })
        total_frames += frame_count
        total_duration += padded_dur

    package_data = {
        "package_id": package_id,
        "title": req.title,
        "genre": req.genre,
        "fps": fps,
        "width": 1920,
        "height": 1080,
        "total_duration_seconds": round(total_duration, 2),
        "total_frames": total_frames,
        "scenes": final_scenes,
    }

    # Save manifest
    (pkg_dir / "package.json").write_text(json.dumps(package_data, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"ok": True, "package": package_data}


@router.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve single audio file."""
    path = STORYTIME_DIR / "audio" / filename
    if not path.exists():
        raise HTTPException(404, "Audio not found")
    return FileResponse(str(path), media_type="audio/mpeg")


@router.get("/pkg-audio/{package_id}/{filename}")
async def serve_pkg_audio(package_id: str, filename: str):
    """Serve package audio file."""
    path = STORYTIME_DIR / f"pkg_{package_id}" / "audio" / filename
    if not path.exists():
        raise HTTPException(404, "Package audio not found")
    return FileResponse(str(path), media_type="audio/mpeg")


@router.get("/packages")
async def list_packages():
    """List all created storytime packages for batch dashboard."""
    packages = []
    
    # 1. Include sample package if exists
    sample_file = OUTPUT_DIR / "sample_remotion_dist" / "remotion_input.json"
    if sample_file.exists():
        try:
            sdata = json.loads(sample_file.read_text(encoding="utf-8"))
            packages.append({
                "package_id": "sample",
                "title": sdata.get("title", "Bí Ẩn Vụ Án Căn Phòng Kín"),
                "genre": sdata.get("genre", "trinh_tham"),
                "scenes_count": len(sdata.get("scenes", [])),
                "total_duration": sdata.get("total_duration_seconds", 12.0),
                "status": "COMPLETED",
                "is_sample": True,
            })
        except Exception:
            pass

    # 2. Scan STORYTIME_DIR for pkg_*
    for pkg_folder in sorted(STORYTIME_DIR.glob("pkg_*"), reverse=True):
        manifest_file = pkg_folder / "package.json"
        if manifest_file.exists():
            try:
                pdata = json.loads(manifest_file.read_text(encoding="utf-8"))
                packages.append({
                    "package_id": pdata.get("package_id", pkg_folder.name.replace("pkg_", "")),
                    "title": pdata.get("title", "Vụ Án Không Tên"),
                    "genre": pdata.get("genre", "trinh_tham"),
                    "scenes_count": len(pdata.get("scenes", [])),
                    "total_duration": pdata.get("total_duration_seconds", 0.0),
                    "status": "COMPLETED",
                    "is_sample": False,
                })
            except Exception:
                continue

    return {"ok": True, "packages": packages}


@router.get("/packages/{package_id}")
async def get_package(package_id: str):
    """Get full package data by ID."""
    if package_id == "sample":
        return await get_sample_package()
    
    pkg_file = STORYTIME_DIR / f"pkg_{package_id}" / "package.json"
    if not pkg_file.exists():
        raise HTTPException(404, "Package not found")
    
    try:
        pdata = json.loads(pkg_file.read_text(encoding="utf-8"))
        return {"ok": True, "package": pdata}
    except Exception as e:
        raise HTTPException(500, f"Error reading package: {e}")


@router.delete("/packages/{package_id}")
async def delete_package(package_id: str):
    """Delete a package and its audio files."""
    if package_id == "sample":
        raise HTTPException(400, "Cannot delete sample package")
    
    import shutil
    target_dir = STORYTIME_DIR / f"pkg_{package_id}"
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
    return {"ok": True}


class BatchStoryItem(BaseModel):
    title: str
    story_text: str
    voice: Optional[str] = "vi-VN-NamMinhNeural"


class BatchStoriesRequest(BaseModel):
    stories: List[BatchStoryItem]


@router.post("/batch-create")
async def api_batch_create(req: BatchStoriesRequest):
    """Batch generate multiple video packages from a list of raw story scripts."""
    results = []
    for s in req.stories:
        title = s.title.strip() or "Vụ Án Mới"
        text = s.story_text.strip()
        if not text:
            continue
        
        # 1. Breakdown text into scenes
        sentences = re.split(r"(?<=[.!?])\s+", text)
        scenes = []
        for i, sentence in enumerate(sentences):
            clean = sentence.strip()
            if not clean:
                continue
            cam = "close" if any(w in clean.lower() for w in ["chết", "máu", "án mạng", "bất ngờ", "sốc", "hung thủ", "biến mất"]) else "zoom_in"
            exp = "shocked" if cam == "close" else "serious"
            scenes.append(SceneInput(
                display_order=i,
                speaker="thanh_tra",
                text=clean,
                camera=cam,
                expression=exp,
                background_prompt="Dark detective room. Pure scenery illustration, dark noir moody background, strictly NO people, NO characters."
            ))
        
        # 2. Build package
        pkg_req = PackageRequest(
            title=title,
            genre="trinh_tham",
            voice=s.voice or "vi-VN-NamMinhNeural",
            scenes=scenes
        )
        try:
            pkg_res = await api_build_package(pkg_req)
            if pkg_res.get("ok"):
                results.append({
                    "title": title,
                    "package_id": pkg_res["package"]["package_id"],
                    "scenes_count": len(pkg_res["package"]["scenes"]),
                    "total_duration": pkg_res["package"]["total_duration_seconds"],
                    "status": "COMPLETED",
                })
        except Exception as e:
            logger.error("Failed batch item '%s': %s", title, e)
            results.append({
                "title": title,
                "status": "FAILED",
                "error": str(e)
            })

    return {"ok": True, "created": results}


@router.get("/sample-package")
async def get_sample_package():
    """Return pre-generated sample detective mystery package for instant preview."""
    sample_file = OUTPUT_DIR / "sample_remotion_dist" / "remotion_input.json"
    if sample_file.exists():
        try:
            data = json.loads(sample_file.read_text(encoding="utf-8"))
            # Convert relative audio paths to API URLs
            for sc in data.get("scenes", []):
                if sc.get("audio_file"):
                    fname = Path(sc["audio_file"]).name
                    sc["audio_url"] = f"/api/storytime/sample-audio/{fname}"
            return {"ok": True, "package": data}
        except Exception:
            pass
    return {"ok": False, "reason": "No sample found"}


@router.get("/sample-audio/{filename}")
async def serve_sample_audio(filename: str):
    """Serve sample audio file."""
    path = OUTPUT_DIR / "sample_remotion_dist" / "audio" / filename
    if not path.exists():
        raise HTTPException(404, "Sample audio not found")
    return FileResponse(str(path), media_type="audio/mpeg")
