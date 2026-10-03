"""Character CRUD operations."""
from agent.db.schema import get_db, _db_lock
from agent.db.crud.base import _uuid, _now, _get, _update, _delete, _get_with_db


async def create_character(name: str, entity_type: str = "character", description: str = None,
                           image_prompt: str = None, voice_description: str = None,
                           reference_image_url: str = None, media_id: str = None, slug: str = None) -> dict:
    from agent.utils.slugify import slugify
    db = await get_db()
    cid, now = _uuid(), _now()
    _slug = slug or slugify(name)
    async with _db_lock:
        await db.execute(
            "INSERT INTO character (id,name,slug,entity_type,description,image_prompt,voice_description,reference_image_url,media_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (cid, name, _slug, entity_type, description, image_prompt, voice_description, reference_image_url, media_id, now, now))
        await db.commit()
    return await _get_with_db(db, "character", "id", cid)


async def get_character(cid: str): return await _get("character", "id", cid)
async def update_character(cid: str, **kw): return await _update("character", "id", cid, **kw)
async def delete_character(cid: str): return await _delete("character", "id", cid)


async def list_characters() -> list[dict]:
    db = await get_db()
    cur = await db.execute("SELECT * FROM character ORDER BY created_at DESC")
    return [dict(r) for r in await cur.fetchall()]


async def list_characters_by_media_id(media_id: str) -> list[dict]:
    """Find characters where media_id matches."""
    db = await get_db()
    cur = await db.execute("SELECT * FROM character WHERE media_id=?", (media_id,))
    return [dict(r) for r in await cur.fetchall()]
