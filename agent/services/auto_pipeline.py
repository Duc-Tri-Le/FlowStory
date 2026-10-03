"""Automated pipeline orchestrator for FlowKit projects.

Executes the full pipeline automatically:
1. Stage 0: Reference images for all entities (GENERATE_CHARACTER_IMAGE)
2. Stage 1: Scene images for all scenes (GENERATE_IMAGE)
3. Stage 2: Scene videos for all scenes (GENERATE_VIDEO)

Throttling, concurrency (max 5) and cool-downs are managed by the worker.
This orchestrator transitions from one stage to the next as items complete.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from agent.db import crud
from agent.services.event_bus import event_bus

logger = logging.getLogger(__name__)

# Active pipeline tasks tracked by project_id
_active_pipelines: dict[str, asyncio.Task] = {}


async def enqueue_reference_images_only(project_id: str):
    """Enqueue ONLY Stage 0: reference images for entities missing media_id.
    Does NOT auto-advance to scene images or videos.
    The user reviews reference images on the dashboard first, then manually clicks to generate scene images.
    """
    chars = await crud.get_project_characters(project_id)
    if not chars:
        return
    logger.info("Enqueuing reference images ONLY for %d entities in project %s (manual workflow)", len(chars), project_id[:8])
    for c in chars:
        if not c.get("media_id"):
            reqs = await crud.list_requests(project_id=project_id)
            exists = any(r.get("character_id") == c["id"] and r.get("status") in ("PENDING", "PROCESSING") for r in reqs)
            if not exists:
                await crud.create_request(
                    req_type="GENERATE_CHARACTER_IMAGE",
                    character_id=c["id"],
                    project_id=project_id,
                )


async def _wait_for_character_refs(project_id: str, max_wait_s: float = 600.0) -> bool:
    """Ensure all characters/entities have media_id before proceeding."""
    deadline = asyncio.get_event_loop().time() + max_wait_s
    while asyncio.get_event_loop().time() < deadline:
        chars = await crud.get_project_characters(project_id)
        if not chars:
            return True
        missing = [c for c in chars if not c.get("media_id")]
        if not missing:
            logger.info("All %d reference entities for project %s have media_id", len(chars), project_id[:8])
            return True

        # Check if any requests failed
        reqs = await crud.list_requests(project_id=project_id)
        ref_reqs = [r for r in reqs if r.get("type") in ("GENERATE_CHARACTER_IMAGE", "REGENERATE_CHARACTER_IMAGE")]
        active = [r for r in ref_reqs if r.get("status") in ("PENDING", "PROCESSING")]
        failed = [r for r in ref_reqs if r.get("status") == "FAILED"]

        # If no active requests but some characters still missing, submit for missing
        active_cids = {r.get("character_id") for r in active}
        for c in missing:
            if c["id"] not in active_cids:
                logger.info("Enqueuing missing ref image for '%s' (%s)", c["name"], c["id"][:8])
                await crud.create_request(
                    req_type="GENERATE_CHARACTER_IMAGE",
                    character_id=c["id"],
                    project_id=project_id,
                )

        await asyncio.sleep(6.0)

    logger.warning("Timed out waiting for reference images for project %s", project_id[:8])
    return False


async def _run_pipeline_loop(project_id: str, video_id: str, orientation: str = "VERTICAL"):
    prefix = "vertical" if orientation == "VERTICAL" else "horizontal"
    logger.info("Starting auto-pipeline for project %s, video %s [%s]", project_id[:8], video_id[:8], orientation)

    try:
        # ── STAGE 0: Reference Images ──
        chars = await crud.get_project_characters(project_id)
        if chars:
            logger.info("Pipeline Stage 0: Enqueuing reference images for %d entities...", len(chars))
            for c in chars:
                if not c.get("media_id"):
                    # Check if request already pending
                    reqs = await crud.list_requests(project_id=project_id)
                    exists = any(r.get("character_id") == c["id"] and r.get("status") in ("PENDING", "PROCESSING") for r in reqs)
                    if not exists:
                        await crud.create_request(
                            req_type="GENERATE_CHARACTER_IMAGE",
                            character_id=c["id"],
                            project_id=project_id,
                        )

            await _wait_for_character_refs(project_id)

        # ── STAGE 1: Scene Images ──
        logger.info("Pipeline Stage 1: Enqueuing scene images for video %s...", video_id[:8])
        scenes = await crud.list_scenes(video_id)
        if not scenes:
            logger.warning("No scenes found for video %s, stopping pipeline", video_id[:8])
            return

        for s in scenes:
            status = s.get(f"{prefix}_image_status")
            if status != "COMPLETED":
                # Check if request already pending
                s_reqs = await crud.list_requests(scene_id=s["id"])
                exists = any(r.get("type") in ("GENERATE_IMAGE", "REGENERATE_IMAGE") and r.get("status") in ("PENDING", "PROCESSING") for r in s_reqs)
                if not exists:
                    await crud.create_request(
                        req_type="GENERATE_IMAGE",
                        scene_id=s["id"],
                        video_id=video_id,
                        project_id=project_id,
                        orientation=orientation,
                    )

        # Wait for all scene images
        max_img_wait = 1800.0  # 30 mins
        deadline = asyncio.get_event_loop().time() + max_img_wait
        while asyncio.get_event_loop().time() < deadline:
            scenes = await crud.list_scenes(video_id)
            incomplete = [s for s in scenes if s.get(f"{prefix}_image_status") != "COMPLETED"]
            if not incomplete:
                logger.info("All %d scene images for video %s COMPLETED!", len(scenes), video_id[:8])
                break

            # Resubmit any failed once
            for s in incomplete:
                if s.get(f"{prefix}_image_status") == "FAILED":
                    s_reqs = await crud.list_requests(scene_id=s["id"])
                    active = any(r.get("status") in ("PENDING", "PROCESSING") for r in s_reqs)
                    failed_cnt = sum(1 for r in s_reqs if r.get("status") == "FAILED")
                    if not active and failed_cnt < 3:
                        logger.info("Retrying scene image for %s...", s["id"][:8])
                        await crud.create_request(
                            req_type="REGENERATE_IMAGE",
                            scene_id=s["id"],
                            video_id=video_id,
                            project_id=project_id,
                            orientation=orientation,
                        )

            await asyncio.sleep(6.0)

        # ── STAGE 2: Scene Videos ──
        logger.info("Pipeline Stage 2: Enqueuing scene videos for video %s...", video_id[:8])
        scenes = await crud.list_scenes(video_id)
        ready_scenes = [s for s in scenes if s.get(f"{prefix}_image_status") == "COMPLETED"]

        for s in ready_scenes:
            v_status = s.get(f"{prefix}_video_status")
            if v_status != "COMPLETED":
                s_reqs = await crud.list_requests(scene_id=s["id"])
                exists = any(r.get("type") in ("GENERATE_VIDEO", "REGENERATE_VIDEO") and r.get("status") in ("PENDING", "PROCESSING") for r in s_reqs)
                if not exists:
                    await crud.create_request(
                        req_type="GENERATE_VIDEO",
                        scene_id=s["id"],
                        video_id=video_id,
                        project_id=project_id,
                        orientation=orientation,
                    )

        # Monitor videos
        max_vid_wait = 3600.0  # 1 hour
        deadline = asyncio.get_event_loop().time() + max_vid_wait
        while asyncio.get_event_loop().time() < deadline:
            scenes = await crud.list_scenes(video_id)
            incomplete_vids = [s for s in scenes if s.get(f"{prefix}_video_status") != "COMPLETED"]
            if not incomplete_vids:
                logger.info("All %d scene videos for video %s COMPLETED! Auto-pipeline finished!", len(scenes), video_id[:8])
                break
            await asyncio.sleep(10.0)

    except asyncio.CancelledError:
        logger.info("Auto-pipeline task cancelled for project %s", project_id[:8])
        raise
    except Exception as e:
        logger.error("Error in auto-pipeline for project %s: %s", project_id[:8], e, exc_info=True)
    finally:
        _active_pipelines.pop(project_id, None)


def start_auto_pipeline(project_id: str, video_id: str, orientation: str = "VERTICAL") -> asyncio.Task:
    """Start or resume the automated full pipeline for a project in the background."""
    if project_id in _active_pipelines and not _active_pipelines[project_id].done():
        logger.info("Pipeline already active for project %s", project_id[:8])
        return _active_pipelines[project_id]

    task = asyncio.create_task(_run_pipeline_loop(project_id, video_id, orientation))
    _active_pipelines[project_id] = task
    return task


def is_pipeline_active(project_id: str) -> bool:
    task = _active_pipelines.get(project_id)
    return task is not None and not task.done()
