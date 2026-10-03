"""Async CRUD operations with column whitelisting."""
from agent.db.crud.base import (
    _VALID_TABLES,
    _COLUMNS,
    _validate_table,
    _now,
    _uuid,
    _safe_kwargs,
    _update,
    _get,
    _get_with_db,
    _delete,
)
from agent.db.crud.characters import (
    create_character,
    get_character,
    update_character,
    delete_character,
    list_characters,
    list_characters_by_media_id,
)
from agent.db.crud.projects import (
    create_project,
    get_project,
    update_project,
    delete_project,
    list_projects,
    link_character_to_project,
    unlink_character_from_project,
    get_project_characters,
)
from agent.db.crud.videos import (
    create_video,
    get_video,
    update_video,
    delete_video,
    list_videos,
)
from agent.db.crud.scenes import (
    create_scene,
    get_scene,
    update_scene,
    delete_scene,
    list_scenes,
    list_scenes_by_media_id,
)
from agent.db.crud.requests import (
    create_request,
    get_request,
    update_request,
    list_requests,
    list_pending_requests,
    list_actionable_requests,
    reset_stale_processing,
)
from agent.db.crud.materials import (
    create_material,
    get_material,
    delete_material,
    list_materials,
)

__all__ = [
    "_VALID_TABLES", "_COLUMNS", "_validate_table", "_now", "_uuid", "_safe_kwargs",
    "_update", "_get", "_get_with_db", "_delete",
    "create_character", "get_character", "update_character", "delete_character",
    "list_characters", "list_characters_by_media_id",
    "create_project", "get_project", "update_project", "delete_project", "list_projects",
    "link_character_to_project", "unlink_character_from_project", "get_project_characters",
    "create_video", "get_video", "update_video", "delete_video", "list_videos",
    "create_scene", "get_scene", "update_scene", "delete_scene", "list_scenes",
    "list_scenes_by_media_id",
    "create_request", "get_request", "update_request", "list_requests",
    "list_pending_requests", "list_actionable_requests", "reset_stale_processing",
    "create_material", "get_material", "delete_material", "list_materials",
]
