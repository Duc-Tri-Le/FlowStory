"""Material CRUD operations."""
from agent.db.schema import get_db, _db_lock
from agent.db.crud.base import _now, _delete, _get_with_db


async def create_material(id: str, name: str, style_instruction: str,
                          negative_prompt: str = None, scene_prefix: str = None,
                          lighting: str = None) -> dict:
    db = await get_db()
    now = _now()
    async with _db_lock:
        await db.execute(
            """INSERT INTO material (id,name,style_instruction,negative_prompt,scene_prefix,lighting,created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (id, name, style_instruction, negative_prompt, scene_prefix,
             lighting or "Studio lighting, highly detailed", now))
        await db.commit()
    return await _get_with_db(db, "material", "id", id)


async def get_material(mid: str):
    from agent.db.crud.base import _get
    return await _get("material", "id", mid)


async def delete_material(mid: str):
    return await _delete("material", "id", mid)


async def list_materials() -> list[dict]:
    db = await get_db()
    cur = await db.execute("SELECT * FROM material ORDER BY created_at")
    return [dict(r) for r in await cur.fetchall()]
