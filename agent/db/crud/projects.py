"""Project CRUD operations."""
import logging
from agent.db.schema import get_db, _db_lock
from agent.db.crud.base import _uuid, _now, _get, _update, _delete, _get_with_db

logger = logging.getLogger(__name__)


async def create_project(name: str, description: str = None, story: str = None, language: str = "en",
                         user_paygate_tier: str = "PAYGATE_TIER_ONE", id: str = None,
                         material: str = None, allow_music: bool = False, allow_voice: bool = False) -> dict:
    db = await get_db()
    pid, now = id or _uuid(), _now()
    async with _db_lock:
        await db.execute(
            "INSERT INTO project (id,name,description,story,language,user_paygate_tier,material,allow_music,allow_voice,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (pid, name, description, story, language, user_paygate_tier, material, int(allow_music), int(allow_voice), now, now))
        await db.commit()
    return await _get_with_db(db, "project", "id", pid)


async def get_project(pid: str): return await _get("project", "id", pid)
async def update_project(pid: str, **kw): return await _update("project", "id", pid, **kw)
async def delete_project(pid: str) -> bool:
    """Cascade delete a project and all its related videos, scenes, requests, orphaned characters, and disk files."""
    db = await get_db()
    vids = []
    async with _db_lock:
        # Check if project exists
        cur = await db.execute("SELECT id FROM project WHERE id=?", (pid,))
        if not await cur.fetchone():
            return False

        # 1. Find all videos for this project
        cur_v = await db.execute("SELECT id FROM video WHERE project_id=?", (pid,))
        vids = [r[0] for r in await cur_v.fetchall()]

        # 2. Delete all scenes and requests for these videos
        for vid in vids:
            await db.execute("DELETE FROM request WHERE video_id=?", (vid,))
            await db.execute("DELETE FROM scene WHERE video_id=?", (vid,))

        # 3. Delete requests linked directly to project
        await db.execute("DELETE FROM request WHERE project_id=?", (pid,))

        # 4. Delete videos
        await db.execute("DELETE FROM video WHERE project_id=?", (pid,))

        # 5. Delete project_character links
        await db.execute("DELETE FROM project_character WHERE project_id=?", (pid,))

        # 6. Delete orphaned characters (not linked to any project anymore)
        await db.execute("""
            DELETE FROM character WHERE id NOT IN (
                SELECT character_id FROM project_character
            )
        """)

        # 7. Delete project itself
        await db.execute("DELETE FROM project WHERE id=?", (pid,))
        await db.commit()

    # 8. Clean disk files & active project state
    try:
        from agent.config import OUTPUT_DIR
        import shutil
        # Delete storytime package folder
        pkg_dir = OUTPUT_DIR / "storytime" / f"pkg_{pid}"
        if pkg_dir.exists():
            shutil.rmtree(pkg_dir, ignore_errors=True)

        # Delete any preview/concat files for this project or its videos
        preview_dir = OUTPUT_DIR / "preview"
        if preview_dir.exists():
            for vid in vids:
                for f in preview_dir.glob(f"*{vid}*"):
                    try:
                        f.unlink(missing_ok=True)
                    except Exception:
                        pass
            for f in preview_dir.glob(f"*{pid}*"):
                try:
                    f.unlink(missing_ok=True)
                except Exception:
                    pass

        # Clear active_project state if it matches this project
        from agent.api.active_project import _read_state, _clear_state
        state = _read_state()
        if state and state.get("project_id") == pid:
            _clear_state()
    except Exception as e:
        logger.warning("Error cleaning project files/state for %s: %s", pid, e)

    return True


async def list_projects(status: str = None) -> list[dict]:
    db = await get_db()
    if status:
        cur = await db.execute("SELECT * FROM project WHERE status=? ORDER BY created_at DESC", (status,))
    else:
        cur = await db.execute("SELECT * FROM project ORDER BY created_at DESC")
    return [dict(r) for r in await cur.fetchall()]


async def link_character_to_project(project_id: str, character_id: str) -> bool:
    db = await get_db()
    try:
        async with _db_lock:
            await db.execute("INSERT OR IGNORE INTO project_character VALUES (?,?)", (project_id, character_id))
            await db.commit()
        return True
    except Exception as e:
        logger.warning("link_character_to_project failed: %s", e)
        return False


async def unlink_character_from_project(project_id: str, character_id: str) -> bool:
    db = await get_db()
    async with _db_lock:
        cur = await db.execute("DELETE FROM project_character WHERE project_id=? AND character_id=?", (project_id, character_id))
        await db.commit()
    return cur.rowcount > 0


async def get_project_characters(project_id: str) -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        "SELECT c.* FROM character c JOIN project_character pc ON c.id=pc.character_id WHERE pc.project_id=?",
        (project_id,))
    return [dict(r) for r in await cur.fetchall()]
