"""Backward-compatibility shim — use agent.services.materials in new code."""
from agent.services.materials import *  # noqa: F401, F403
from agent.services.materials import (
    MATERIALS,
    _BUILTIN_IDS,
    get_material,
    list_materials,
    register_material,
    unregister_material,
    load_custom_materials_from_db,
    build_scene_image_prompt,
    build_character_image_prompt,
    build_custom_style_instruction,
)
