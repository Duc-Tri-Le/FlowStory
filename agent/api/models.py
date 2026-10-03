"""Model configuration API — view and update video/image/upscale model keys."""
import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from agent import config

router = APIRouter(prefix="/api/models", tags=["models"])
logger = logging.getLogger(__name__)

_MODELS_FILE = Path(__file__).parent.parent / "models.json"


def _read_models() -> dict:
    with open(_MODELS_FILE) as f:
        return json.load(f)


def _write_models(data: dict):
    tmp = _MODELS_FILE.with_suffix(".json.tmp")
    try:
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, _MODELS_FILE)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _reload_config(data: dict):
    """Hot-reload model keys into the running config module.

    Omni Flash is resolved directly from models.json at submit time, so no
    config-module mirror is required for that section.
    """
    config.VIDEO_MODELS.clear()
    config.VIDEO_MODELS.update(data["video_models"])
    config.UPSCALE_MODELS.clear()
    config.UPSCALE_MODELS.update(data["upscale_models"])
    config.IMAGE_MODELS.clear()
    config.IMAGE_MODELS.update(data["image_models"])
    config.DEFAULT_IMAGE_MODEL = data.get("default_image_model", "NANO_BANANA_PRO")
    config.DEFAULT_VIDEO_MODEL_FAMILY = data.get("default_video_model_family", "omni_flash")
    config.DEFAULT_VEO_MODEL = data.get(
        "default_veo_model",
        data.get("batch_video_models", {}).get("default", "veo_3_1_i2v_lite_low_priority"),
    )
    config.DEFAULT_OMNI_DURATION = int(data.get("default_omni_duration", 6))
    config.DEFAULT_OMNI_RESOLUTION = data.get("default_omni_resolution", "720p")


@router.get("")
async def get_models():
    """Return current model configuration."""
    return _read_models()


@router.patch("")
async def patch_models(body: dict):
    """Update model keys. Merges provided keys into existing config.

    Example body to change video model for TIER_TWO i2v portrait:
    {
      "video_models": {
        "PAYGATE_TIER_TWO": {
          "frame_2_video": {
            "VIDEO_ASPECT_RATIO_PORTRAIT": "veo_3_1_i2v_s_fast_portrait_ultra"
          }
        }
      }
    }

    Omni Flash duration keys are configurable too:
    {
      "omni_flash_models": {
        "reference_to_video": {"10": "abra_r2v_10s"}
      }
    }
    """
    current = _read_models()

    if "default_omni_duration" in body:
        try:
            body["default_omni_duration"] = int(body["default_omni_duration"])
        except (TypeError, ValueError):
            raise HTTPException(422, "default_omni_duration must be an integer")

    for scalar_key in (
        "default_image_model",
        "default_video_model_family",
        "default_veo_model",
        "default_omni_duration",
        "default_omni_resolution",
    ):
        if scalar_key in body:
            current[scalar_key] = body[scalar_key]

    if "default_veo_model" in body:
        veo_key = body["default_veo_model"]
        current.setdefault("batch_video_models", {})["default"] = veo_key
        # Sync to video_models for backward compatibility with legacy lookups
        for tier in ("PAYGATE_TIER_TWO", "PAYGATE_TIER_ONE"):
            if tier in current.get("video_models", {}):
                for gen_type in ("frame_2_video", "start_end_frame_2_video"):
                    if gen_type in current["video_models"][tier]:
                        for aspect in ("VIDEO_ASPECT_RATIO_LANDSCAPE", "VIDEO_ASPECT_RATIO_PORTRAIT"):
                            current["video_models"][tier][gen_type][aspect] = veo_key

    # Deep merge: only update keys that are provided.
    for section in (
        "video_models",
        "omni_flash_models",
        "image_models",
        "upscale_models",
    ):
        if section not in body:
            continue
        if section in ("upscale_models", "image_models"):
            # Flat dict — direct merge.
            current.setdefault(section, {}).update(body[section])
        elif section == "omni_flash_models":
            # Nested by generation mode -> duration -> model key.
            target = current.setdefault(section, {})
            for mode, durations in body[section].items():
                target.setdefault(mode, {}).update(durations)
        else:
            # Nested dict — merge per tier, per gen_type.
            for tier, gen_types in body[section].items():
                if tier not in current[section]:
                    current[section][tier] = {}
                for gen_type, ratios in gen_types.items():
                    if gen_type not in current[section][tier]:
                        current[section][tier][gen_type] = {}
                    current[section][tier][gen_type].update(ratios)

    _write_models(current)
    _reload_config(current)
    logger.info("Models updated and hot-reloaded: %s", list(body.keys()))

    return {"status": "updated", "models": current}
