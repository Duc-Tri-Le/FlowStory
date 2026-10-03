"""Video CRUD operations."""
from agent.db.schema import get_db, _db_lock
from agent.db.crud.base import _uuid, _now, _get, _update, _delete, _get_with_db


async def create_video(project_id: str, title: str, description: str = None,
                       display_order: int = 0, orientation: str = None) -> dict:
    db = await get_db()
    vid, now = _uuid(), _now()
    async with _db_lock:
        await db.execute(
            "INSERT INTO video (id,project_id,title,description,display_order,orientation,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (vid, project_id, title, description, display_order, orientation, now, now))
        await db.commit()
    return await _get_with_db(db, "video", "id", vid)


async def get_video(vid: str): return await _get("video", "id", vid)
async def update_video(vid: str, **kw): return await _update("video", "id", vid, **kw)
async def delete_video(vid: str): return await _delete("video", "id", vid)


async def list_videos(project_id: str) -> list[dict]:
    db = await get_db()
    cur = await db.execute("SELECT * FROM video WHERE project_id=? ORDER BY display_order", (project_id,))
    return [dict(r) for r in await cur.fetchall()]
