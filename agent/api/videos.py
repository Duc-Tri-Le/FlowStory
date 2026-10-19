from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import logging
import subprocess
import urllib.request
from pathlib import Path

from agent.config import OUTPUT_DIR
from agent.models.video import Video, VideoCreate, VideoUpdate
from agent.sdk.persistence.sqlite_repository import SQLiteRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["videos"])

_repo = SQLiteRepository()


class VideoConcatRequest(BaseModel):
    with_tts: bool = False
    orientation: Optional[str] = None


def _video_to_flat(sdk_video) -> dict:
    """Convert SDK Video domain model to flat dict matching API response shape."""
    return {
        "id": sdk_video.id,
        "project_id": sdk_video.project_id,
        "title": sdk_video.title,
        "description": sdk_video.description,
        "display_order": sdk_video.display_order,
        "status": sdk_video.status,
        "orientation": sdk_video.orientation,
        "vertical_url": sdk_video.vertical_url,
        "horizontal_url": sdk_video.horizontal_url,
        "thumbnail_url": sdk_video.thumbnail_url,
        "duration": sdk_video.duration,
        "resolution": sdk_video.resolution,
        "youtube_id": sdk_video.youtube_id,
        "privacy": sdk_video.privacy,
        "tags": sdk_video.tags,
        "created_at": sdk_video.created_at,
        "updated_at": sdk_video.updated_at,
    }


@router.post("", response_model=Video)
async def create(body: VideoCreate):
    sdk_video = await _repo.create_video(**body.model_dump(exclude_none=True))
    return _video_to_flat(sdk_video)


@router.get("", response_model=list[Video])
async def list_by_project(project_id: str):
    videos = await _repo.list_videos(project_id)
    return [_video_to_flat(v) for v in videos]


@router.get("/{vid}", response_model=Video)
async def get(vid: str):
    sdk_video = await _repo.get_video(vid)
    if not sdk_video:
        raise HTTPException(404, "Video not found")
    return _video_to_flat(sdk_video)


@router.patch("/{vid}", response_model=Video)
async def update(vid: str, body: VideoUpdate):
    row = await _repo.update("video", vid, **body.model_dump(exclude_unset=True))
    if not row:
        raise HTTPException(404, "Video not found")
    sdk_video = _repo._row_to_video(row)
    return _video_to_flat(sdk_video)


@router.delete("/{vid}")
async def delete(vid: str):
    if not await _repo.delete("video", vid):
        raise HTTPException(404, "Video not found")
    return {"ok": True}


@router.post("/{vid}/concat")
async def concat_video(vid: str, body: Optional[VideoConcatRequest] = None):
    """Concatenate all scene videos for a given video ID using ffmpeg."""
    sdk_video = await _repo.get_video(vid)
    if not sdk_video:
        raise HTTPException(404, "Video not found")

    scenes = await _repo.list_scenes(vid)
    if not scenes:
        raise HTTPException(400, "No scenes found for this video")

    scenes = sorted(scenes, key=lambda s: getattr(s, "display_order", 0))

    orientation = (body.orientation if body and body.orientation else None) or getattr(sdk_video, "orientation", "HORIZONTAL") or "HORIZONTAL"
    is_horiz = orientation.upper() == "HORIZONTAL"
    url_attr = "horizontal_video_url" if is_horiz else "vertical_video_url"
    upscale_attr = "horizontal_upscale_url" if is_horiz else "vertical_upscale_url"

    preview_dir = OUTPUT_DIR / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for s in scenes:
        video_url = None
        if hasattr(s, "horizontal"):
            slot = s.horizontal if is_horiz else s.vertical
            video_url = getattr(getattr(slot, "video", None), "url", None) or getattr(getattr(slot, "upscale", None), "url", None)
        if not video_url:
            try:
                flat_s = _repo._scene_to_updates(s)
                video_url = flat_s.get(url_attr) or flat_s.get(upscale_attr)
            except Exception:
                pass
        if not video_url and isinstance(s, dict):
            video_url = s.get(url_attr) or s.get(upscale_attr)

        if not video_url:
            raise HTTPException(400, f"Phân cảnh {s.display_order + 1} chưa có video để ghép.")

        scene_file = preview_dir / f"scene_{s.display_order:03d}_{s.id[:8]}.mp4"
        if not scene_file.exists() or scene_file.stat().st_size == 0:
            logger.info("Downloading scene %s from %s", s.display_order, video_url[:60])
            try:
                urllib.request.urlretrieve(video_url, str(scene_file))
            except Exception as e:
                logger.error("Failed to download scene video %s: %s", s.id, e)
                raise HTTPException(500, f"Không thể tải video phân cảnh {s.display_order + 1}: {e}")

        downloaded.append(scene_file)

    concat_file = preview_dir / f"{vid}_concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for p in downloaded:
            f.write(f"file '{p.resolve().as_posix()}'\n")

    final_video_path = preview_dir / f"{vid}_final.mp4"

    cmd_copy = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        "-movflags", "+faststart",
        str(final_video_path)
    ]
    res = subprocess.run(cmd_copy, capture_output=True, text=True)
    if res.returncode != 0:
        logger.warning("Stream copy concat failed, re-encoding: %s", res.stderr[-200:])
        cmd_encode = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(final_video_path)
        ]
        res2 = subprocess.run(cmd_encode, capture_output=True, text=True)
        if res2.returncode != 0:
            logger.error("Re-encode concat failed: %s", res2.stderr[-200:])
            raise HTTPException(500, f"Ghép video thất bại: {res2.stderr[-200:]}")

    concat_file.unlink(missing_ok=True)

    final_url = f"/api/storytime/preview-video/{vid}_final.mp4"
    if is_horiz:
        await _repo.update("video", vid, horizontal_url=final_url, status="COMPLETED")
    else:
        await _repo.update("video", vid, vertical_url=final_url, status="COMPLETED")

    return {
        "ok": True,
        "video_id": vid,
        "scenes_count": len(downloaded),
        "video_url": final_url,
        "filename": f"{vid}_final.mp4",
        "file_size": final_video_path.stat().st_size,
    }


@router.get("/{vid}/final-video")
async def get_final_video(vid: str):
    """Serve the final concatenated video file."""
    preview_dir = OUTPUT_DIR / "preview"
    target = preview_dir / f"{vid}_final.mp4"
    if not target.exists():
        raise HTTPException(404, "Final video not found. Hãy bấm 'Ghép Video' trước.")
    return FileResponse(str(target), media_type="video/mp4")

