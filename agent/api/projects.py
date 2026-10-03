import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

import aiohttp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent.config import BASE_DIR
from agent.models.project import Project, ProjectCreate, ProjectUpdate
from agent.models.character import Character
from agent.sdk.persistence.sqlite_repository import SQLiteRepository
from agent.services.flow_client import get_flow_client
from agent.utils.slugify import slugify

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


COMPOSITION_GUIDELINES = {
    "character": (
        "STRUCTURE: Divided into EXACTLY THREE EQUAL VERTICAL FRAMES separated by thin white lines. "
        "FRAME 1 (left): Full body front view — character standing straight, arms at sides, full costume visible from head to toe, facing camera. "
        "FRAME 2 (center): Full body back view (rear) — character facing away, identical proportions, textures and costume matching frame 1 exactly. "
        "FRAME 3 (right): Extreme close-up of face and upper chest — ultra-realistic skin texture, eyes, hair detail, expression neutral. "
        "Neutral solid white or light grey studio background. Strictly NO text, NO numbers, NO labels, NO titles, NO watermarks anywhere in the image."
    ),
    "location": (
        "COMPOSITION: Establishing shot showing the full environment. "
        "Pure scenery, landscape and architecture only. Strictly NO people, NO humans, NO figures, empty environment. "
        "Balanced level composition with straight horizon. Clear focal point. "
        "Atmospheric and richly detailed. Show depth and spatial layout."
    ),
    "creature": (
        "COMPOSITION: Full body shot showing the creature's complete form. "
        "Emphasize natural stance (quadrupedal on all fours, bipedal upright, etc.). "
        "Centered with clear view of distinctive features. Neutral background. "
        "Proper scale and proportions relative to body structure."
    ),
    "visual_asset": (
        "COMPOSITION: Isolated object centered on a seamless, pure solid white background. "
        "Clear detailed view showcasing the item's complete form, materials, and surface textures. "
        "Clean neutral studio lighting with subtle contact shadow underneath. "
        "Strictly NO people, NO hands, NO human figures, NO room background, NO text, NO labels."
    ),
    "generic_troop": (
        "COMPOSITION: Military/tactical pose showing readiness. "
        "Full or three-quarter body view. Centered composition. "
        "Neutral background. Proper perspective and proportions."
    ),
    "faction": (
        "COMPOSITION: Military/tactical pose showing readiness. "
        "Full or three-quarter body view. Centered composition. "
        "Neutral background. Proper perspective and proportions."
    ),
}


_STYLE_COMPAT_MAP = {
    "3d": "3d_pixar",
    "3D": "3d_pixar",
    "photorealistic": "realistic",
}


def _resolve_material_id(value: str) -> str:
    """Map legacy style strings to material IDs. Returns value unchanged if no mapping."""
    return _STYLE_COMPAT_MAP.get(value, value)


def _build_character_profile(char_name: str, char_desc: str | None, story: str | None,
                              entity_type: str = "character", material_id: str = "3d_pixar") -> dict:
    """Build a rich profile (description + image_prompt) for any reference entity.

    The image_prompt generates a reference image used as mediaId for all
    scene generations. Visual appearance is defined HERE, not in scene prompts.
    Scene prompts should only describe actions/environment/composition.

    story may be None — in that case the description omits story context and
    the image_prompt uses a simpler prefix.
    """
    from agent.services.materials import get_material
    material = get_material(material_id)
    if not material:
        raise ValueError(f"Unknown material: {material_id}")

    base_desc = char_desc or char_name
    composition = COMPOSITION_GUIDELINES.get(entity_type, COMPOSITION_GUIDELINES["character"])

    if entity_type == "character":
        single_image_note = (
            "THREE EQUAL VERTICAL FRAMES with thin white dividers: "
            "[FRAME 1] Full body FRONT view standing straight. "
            "[FRAME 2] Full body BACK/REAR view same proportions. "
            "[FRAME 3] Extreme CLOSE-UP face and chest with ultra-realistic skin detail. "
            "Absolutely NO text, NO numbers, NO labels anywhere. "
        )
    elif entity_type == "location":
        single_image_note = "Pure scenery and environment only. Strictly NO people, NO characters, NO human silhouettes. "
    elif entity_type == "visual_asset":
        single_image_note = (
            "ONE single clean isolated object centered on a pure solid white background only, NOT a multi-panel grid. "
            "Strictly NO people, NO hands holding it, NO background elements, NO text, NO labels. "
        )
    else:
        single_image_note = "ONE single clean reference image only, NOT a multi-panel grid. "

    if story:
        description = f"{char_name}: {base_desc}. Story context: {story}"
        image_prefix = f"Reference entity {char_name}: {base_desc}. "
    else:
        description = base_desc
        image_prefix = f"Reference entity {char_name}: {base_desc}. "

    style_instruction = material["style_instruction"]
    if material.get("negative_prompt"):
        style_instruction += f" {material['negative_prompt']}"
    lighting = material.get("lighting", "Studio lighting, highly detailed")

    image_prompt = (
        f"{image_prefix}"
        f"{style_instruction} "
        f"{composition} "
        f"{single_image_note}"
        f"{lighting}"
    )

    return {"description": description, "image_prompt": image_prompt}


async def _detect_user_tier(client) -> str:
    """Auto-detect user paygate tier from Flow credits API."""
    try:
        result = await client.get_credits()
        data = result.get("data", result)
        tier = data.get("userPaygateTier", "PAYGATE_TIER_ONE")
        logger.info("Auto-detected user tier: %s", tier)
        return tier
    except Exception as e:
        logger.warning("Failed to detect tier, defaulting to TIER_ONE: %s", e)
        return "PAYGATE_TIER_ONE"


def _read_flow_project_id(flow_result: dict) -> str:
    """Pull the project uuid out of whichever transport answered.

    The batch path answers `{"projectId": …}`; the legacy tRPC path buries it
    under result/data/json/result.
    """
    data = flow_result.get("data") or {}
    if isinstance(data, dict):
        if isinstance(data.get("projectId"), str):
            return data["projectId"]
        try:
            return data["result"]["data"]["json"]["result"]["projectId"]
        except (KeyError, TypeError):
            pass
    logger.error("Unexpected Flow response: %s", flow_result)
    raise HTTPException(502, "Could not read a Flow project id from the response")


def _get_repo() -> SQLiteRepository:
    return SQLiteRepository()


@router.post("", response_model=Project)
async def create(body: ProjectCreate):
    from agent.services.materials import get_material

    # Step 1: Create project on Google Flow to get the real projectId
    client = get_flow_client()
    if not client.connected:
        raise HTTPException(503, "Extension not connected — cannot create project on Google Flow")

    # Resolve material (support legacy style field + material field)
    material_id = _resolve_material_id(body.material)
    material = get_material(material_id)
    if not material:
        raise HTTPException(400, f"Unknown material: '{material_id}'. Use GET /api/materials to list available materials.")

    # Validate characters before any API calls to avoid orphan projects
    characters_input_raw = body.model_dump(exclude_none=True).get("characters")
    if characters_input_raw:
        slugs = [slugify(c["name"]) for c in characters_input_raw]
        if len(slugs) != len(set(slugs)):
            dupes = [s for s in slugs if slugs.count(s) > 1]
            raise HTTPException(400, f"Duplicate character slugs: {list(set(dupes))}")

    detected_tier = await _detect_user_tier(client)

    # Explicit flow_project_id means intentional reuse. Otherwise create a
    # fresh real Flow project through the current batchexecute endpoint.
    flow_project_id = client.flow_project_id(body.flow_project_id)
    if flow_project_id:
        logger.info("Flow project reused: %s", flow_project_id)
    else:
        flow_result = await client.create_project(body.name, body.tool_name)
        if flow_result.get("error"):
            raise HTTPException(502, f"Flow API error: {flow_result['error']}")
        flow_project_id = _read_flow_project_id(flow_result)
        logger.info("Flow project created: %s", flow_project_id)

    repo = _get_repo()

    # Step 2: Create local project with the Flow-assigned ID and detected tier
    create_data = body.model_dump(exclude_none=True)
    create_data.pop("tool_name", None)
    create_data.pop("flow_project_id", None)
    create_data.pop("style", None)
    characters_input = create_data.pop("characters", None)

    project = await repo.create_project(
        id=flow_project_id,
        name=create_data["name"],
        description=create_data.get("description"),
        story=create_data.get("story"),
        language=create_data.get("language", "en"),
        user_paygate_tier=detected_tier,
        material=material_id,
        allow_music=create_data.get("allow_music", False),
        allow_voice=create_data.get("allow_voice", False),
    )

    # Step 3: Create reference entities (characters, locations, assets) with profiles
    if characters_input:
        for char_input in characters_input:
            etype = char_input.get("entity_type", "character")
            profile = _build_character_profile(
                char_input["name"],
                char_input.get("description"),
                body.story,
                entity_type=etype,
                material_id=material_id,
            )
            description = profile["description"]
            image_prompt = profile["image_prompt"]
            char = await repo.create_character(
                name=char_input["name"],
                slug=slugify(char_input["name"]),
                entity_type=etype,
                description=description,
                image_prompt=image_prompt,
                voice_description=char_input.get("voice_description"),
            )
            await repo.link_character_to_project(flow_project_id, char.id)
            logger.info("%s '%s' created and linked: %s", etype, char_input["name"], char.id)

    return project


@router.get("", response_model=list[Project])
async def list_all(status: Optional[str] = None):
    repo = _get_repo()
    rows = await repo.list("project", **({} if status is None else {"status": status}))
    return [repo._row_to_project(r) for r in rows]


@router.get("/{pid}", response_model=Project)
async def get(pid: str):
    repo = _get_repo()
    p = await repo.get_project(pid)
    if not p:
        raise HTTPException(404, "Project not found")
    return p


@router.patch("/{pid}", response_model=Project)
async def update(pid: str, body: ProjectUpdate):
    repo = _get_repo()
    row = await repo.update("project", pid, **body.model_dump(exclude_unset=True))
    if not row:
        raise HTTPException(404, "Project not found")
    return repo._row_to_project(row)


@router.delete("/{pid}")
async def delete(pid: str):
    repo = _get_repo()
    if not await repo.delete_project(pid):
        raise HTTPException(404, "Project not found")
    return {"ok": True}


@router.post("/{pid}/characters/{cid}")
async def link_character(pid: str, cid: str):
    repo = _get_repo()
    if not await repo.link_character_to_project(pid, cid):
        raise HTTPException(400, "Failed to link character")
    return {"ok": True}


@router.delete("/{pid}/characters/{cid}")
async def unlink_character(pid: str, cid: str):
    repo = _get_repo()
    if not await repo.unlink_character_from_project(pid, cid):
        raise HTTPException(404, "Link not found")
    return {"ok": True}


@router.get("/{pid}/characters", response_model=list[Character])
async def get_characters(pid: str):
    repo = _get_repo()
    return await repo.get_project_characters(pid)


@router.get("/{pid}/output-dir")
async def get_output_dir(pid: str):
    """Get or create project output directory with meta.json."""
    repo = _get_repo()
    project = await repo.get_project(pid)
    if not project:
        raise HTTPException(404, "Project not found")

    project_name = project.name if hasattr(project, "name") else project["name"]
    slug = slugify(project_name)
    output_dir = BASE_DIR / "output" / slug

    for subdir in ["scenes", "4k", "tts", "narrated", "trimmed", "norm", "thumbnails", "subclips", "review"]:
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)

    videos = await repo.list_videos(pid)
    video = videos[0] if videos else None
    video_id = video.id if video else None
    scene_count = 0
    if video_id:
        scenes = await repo.list_scenes(video_id)
        scene_count = len(scenes) if scenes else 0

    # Orientation lives on the video table, not project
    video_orientation = (getattr(video, "orientation", None) if video else None) or "VERTICAL"

    now = datetime.now(timezone.utc).isoformat()
    meta = {
        "project_id": pid,
        "project_name": project_name,
        "slug": slug,
        "video_id": video_id,
        "orientation": video_orientation,
        "material": getattr(project, "material", None) or (project.get("material") if isinstance(project, dict) else None) or "",
        "scene_count": scene_count,
        "created_at": now,
    }
    meta_path = output_dir / "meta.json"
    if meta_path.exists():
        existing = json.loads(meta_path.read_text())
        meta["created_at"] = existing.get("created_at", now)
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    return {"slug": slug, "path": f"output/{slug}", "meta": meta}


_ASPECT_RATIO_MAP = {
    "LANDSCAPE": "IMAGE_ASPECT_RATIO_LANDSCAPE",
    "PORTRAIT": "IMAGE_ASPECT_RATIO_PORTRAIT",
}


class ThumbnailRequest(BaseModel):
    prompt: str
    character_names: list[str] = []
    aspect_ratio: str = "LANDSCAPE"
    output_filename: str = "thumbnail.png"


class ThumbnailResponse(BaseModel):
    success: bool
    media_id: str | None = None
    image_url: str | None = None
    output_path: str | None = None
    prompt: str | None = None
    error: str | None = None


@router.post("/{pid}/generate-thumbnail", response_model=ThumbnailResponse)
async def generate_thumbnail(pid: str, body: ThumbnailRequest):
    """Generate a thumbnail image for a project via Google Flow API (synchronous, no queue)."""
    import logging
    logger = logging.getLogger(__name__)
    from agent.services.materials import get_material
    from agent.sdk.services.result_handler import parse_result

    logger.info("generate_thumbnail: started for project %s", pid)

    client = get_flow_client()
    if not client.connected:
        raise HTTPException(503, "Extension not connected")

    repo = _get_repo()
    project = await repo.get_project(pid)
    if not project:
        raise HTTPException(404, "Project not found")

    # Build full prompt: prepend material scene_prefix for style consistency
    material_id = getattr(project, "material", None) or "realistic"
    material = get_material(material_id)
    scene_prefix = material["scene_prefix"] if material and material.get("scene_prefix") else ""
    full_prompt = f"{scene_prefix} {body.prompt}".strip() if scene_prefix else body.prompt

    # Resolve character reference media_ids (error if any named entity is missing media_id)
    character_media_ids = None
    if body.character_names:
        entities = await repo.get_project_characters(pid)
        valid_ids = []
        missing = []
        for entity in entities:
            name = entity["name"] if isinstance(entity, dict) else entity.name
            mid = entity.get("media_id") if isinstance(entity, dict) else getattr(entity, "media_id", None)
            char_slug = (entity.get("slug") if isinstance(entity, dict) else getattr(entity, "slug", None)) or ""
            if not ((char_slug and char_slug in body.character_names) or (name and name in body.character_names)):
                continue
            if mid:
                valid_ids.append(mid)
            else:
                missing.append(name)
        if missing:
            raise HTTPException(400, f"Missing reference images for: {', '.join(missing)}. Generate ref images first.")
        character_media_ids = valid_ids if valid_ids else None

    aspect_ratio = _ASPECT_RATIO_MAP.get(body.aspect_ratio.upper(), "IMAGE_ASPECT_RATIO_LANDSCAPE")
    tier = getattr(project, "user_paygate_tier", "PAYGATE_TIER_TWO") or "PAYGATE_TIER_TWO"

    logger.info("generate_thumbnail: calling generate_images prompt=%s refs=%s", full_prompt[:60], character_media_ids)
    raw = await client.generate_images(
        prompt=full_prompt,
        project_id=pid,
        aspect_ratio=aspect_ratio,
        user_paygate_tier=tier,
        character_media_ids=character_media_ids,
    )
    logger.info("generate_thumbnail: generate_images returned, error=%s", raw.get("error") if isinstance(raw, dict) else "n/a")

    gen_result = parse_result(raw, "GENERATE_IMAGE")
    if not gen_result.success:
        raise HTTPException(502, gen_result.error or "Image generation failed")

    # Download and save to output/{project_name}/thumbnails/{filename}
    project_name = slugify(getattr(project, "name", "project"))
    out_dir = BASE_DIR / "output" / project_name / "thumbnails"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / body.output_filename

    if gen_result.url and gen_result.url.startswith("http"):
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(gen_result.url) as resp:
                    if resp.status == 200:
                        output_path.write_bytes(await resp.read())
                    else:
                        raise HTTPException(502, f"Failed to download image: HTTP {resp.status}")
        except aiohttp.ClientError as e:
            raise HTTPException(502, f"Failed to download image: {e}") from e

    return ThumbnailResponse(
        success=True,
        media_id=gen_result.media_id,
        image_url=gen_result.url,
        output_path=str(output_path),
        prompt=full_prompt,
    )


# ──────────────────────────────────────────────────────────────
# Generate scenes from a scenario prompt (AI expansion)
# ──────────────────────────────────────────────────────────────

def _extract_entities_from_script(script: str, project_name: str) -> list[dict]:
    """Extract characters, locations (pure scenery, no people), and visual assets from the script text."""
    import re

    entities: list[dict] = []
    seen_slugs: set[str] = set()

    def add_entity(name: str, entity_type: str, description: str):
        slug = slugify(name)
        if slug and slug not in seen_slugs:
            seen_slugs.add(slug)
            entities.append({
                "name": name,
                "entity_type": entity_type,
                "description": description,
            })

    lower_text = (script + " " + project_name).lower()

    # 1. Detect locations (bối cảnh thuần, không có người)
    location_patterns = [
        (r"(?:làng quê|nông thôn|village)", "Làng Quê", "Rustic peaceful countryside village with green trees, brick paths, and natural environment. Pure scenery, strictly NO people, NO humans, empty landscape."),
        (r"(?:sa mạc|desert)", "Sa Mạc", "Vast expansive desert with golden sand dunes under dramatic open sky. Pure scenery, strictly NO people, NO humans, empty landscape."),
        (r"(?:khu vườn|garden|courtyard)", "Khu Vườn", "Lush tranquil garden courtyard with vibrant tropical foliage, rustic brick walls and soft sunlight. Pure scenery, strictly NO people, NO humans, empty landscape."),
        (r"(?:rừng|forest|woods)", "Khu Rừng", "Dense atmospheric forest with tall ancient trees, mist filtering through canopy. Pure scenery, strictly NO people, NO humans, empty landscape."),
        (r"(?:thành phố|city|urban)", "Thành Phố", "Cinematic urban cityscape with detailed architecture, streets and buildings. Pure scenery, strictly NO people, NO humans, empty landscape."),
        (r"(?:lâu đài|castle|palace|cung điện)", "Lâu Đài", "Grand majestic ancient stone castle with towering battlements and courtyard. Pure scenery, strictly NO people, NO humans, empty landscape."),
        (r"(?:phòng chỉ huy|situation room|command center)", "Phòng Chỉ Huy", "High-tech command center with monitor displays, tactical maps and atmospheric lighting. Pure scenery, strictly NO people, NO humans, empty landscape."),
        (r"(?:bờ biển|bãi biển|seashore|beach)", "Bờ Biển", "Scenic ocean coastline with rolling waves and sandy shore. Pure scenery, strictly NO people, NO humans, empty landscape."),
        (r"(?:vũ trụ|space|cosmos)", "Vũ Trụ", "Deep cosmic outer space with glowing nebulae and distant stars. Pure scenery, strictly NO people, NO humans, empty landscape."),
    ]

    # Explicit bối cảnh: ... pattern
    explicit_loc_match = re.search(r"(?:bối cảnh|location|setting)[:\s]+([^,\.\n\)]+)", script, re.IGNORECASE)
    if explicit_loc_match:
        loc_raw = explicit_loc_match.group(1).strip()
        add_entity(loc_raw.title(), "location", f"Detailed establishing environment of {loc_raw}. Pure scenery, landscape and architecture only. Strictly NO people, NO humans, empty environment.")

    for pat, name, desc in location_patterns:
        if re.search(pat, lower_text):
            add_entity(name, "location", desc)

    # Default fallback location if none detected
    if not any(e["entity_type"] == "location" for e in entities):
        add_entity("Bối Cảnh Khung Cảnh", "location", f"Atmospheric environment for {project_name}. Pure scenery and architecture only, strictly NO people, NO humans, empty environment.")

    # 2. Detect characters (3-frame turnaround: front, back, face)
    char_patterns = [
        (r"(?:cậu bé|boy)", "Cậu Bé", "Young Vietnamese boy in comfortable rustic casual clothes. Base default look. 3 frames turnaround reference."),
        (r"(?:cô bé|girl)", "Cô Bé", "Sweet young Vietnamese girl with neat hair in casual dress. Base default look. 3 frames turnaround reference."),
        (r"(?:chiến binh|warrior)", "Chiến Binh", "Heroic resolute warrior in detailed functional combat attire and dark cloak. Base default look. 3 frames turnaround reference."),
        (r"(?:người chỉ huy|commander)", "Người Chỉ Huy", "Authoritative commander in formal military uniform with focused expression. Base default look. 3 frames turnaround reference."),
        (r"(?:hoàng tử|prince)", "Hoàng Tử", "Noble young prince in regal tunic. Base default look. 3 frames turnaround reference."),
        (r"(?:công chúa|princess)", "Công Chúa", "Graceful young princess in elegant gown. Base default look. 3 frames turnaround reference."),
        (r"(?:phi hành gia|astronaut)", "Phi Hành Gia", "Futuristic astronaut in detailed space exploration suit. Base default look. 3 frames turnaround reference."),
        (r"(?:thám tử|detective)", "Thám Tử", "Astute detective in classic trench coat. Base default look. 3 frames turnaround reference."),
        (r"(?:chú chó|dog)", "Chú Chó", "Loyal friendly dog. Base default look. Turnaround reference."),
        (r"(?:mèo|cat)", "Mèo", "Agile expressive domestic cat. Base default look. Turnaround reference."),
    ]

    for pat, name, desc in char_patterns:
        if re.search(pat, lower_text):
            add_entity(name, "character", desc)

    # If no character detected, look for capitalized word tokens in script
    if not any(e["entity_type"] == "character" for e in entities):
        name_words = re.findall(r"\b[A-ZÀ-Ỹ][a-zà-ỹ]+\b", project_name)
        if name_words:
            char_title = " ".join(name_words[:2])
            add_entity(char_title, "character", f"Main character {char_title}. 3 frames turnaround reference: front view, back view, and face close-up, no text.")

    # 3. Detect visual assets (đạo cụ, đồ vật chính)
    asset_patterns = [
        (r"(?:quả bóng|bóng đá|soccer ball|ball)", "Quả Bóng", "Classic soccer ball with recognizable hexagonal pattern and authentic texture."),
        (r"(?:thanh kiếm|sword|blade)", "Thanh Kiếm", "Ornate forged steel sword with leather-wrapped hilt and gleaming edge."),
        (r"(?:lá cờ|flag|banner)", "Lá Cờ", "Fabric standard flag blowing gently in wind."),
        (r"(?:chiếc xe|car|vehicle)", "Chiếc Xe", "Detailed vehicle model with authentic metallic finish."),
        (r"(?:bảo vật|artifact|relic)", "Bảo Vật", "Ancient glowing artifact with intricate etched runes."),
    ]

    for pat, name, desc in asset_patterns:
        if re.search(pat, lower_text):
            add_entity(name, "visual_asset", desc)

    return entities


def _parse_script_scenes(text: str) -> list[str]:
    """Parse scenes from user's script text based on 'Cảnh 1', 'Scene 1', paragraphs, or lines."""
    import re
    # Check for scene headings like "Cảnh 1:", "Scene 1:", "Phân cảnh 1:", "1.", "- Cảnh"
    pattern = r"(?:^|\n)(?:Cảnh\s*\d+|Scene\s*\d+|Phân cảnh\s*\d+|\d+[\.\)])[:\s-]*"
    splits = re.split(pattern, text, flags=re.IGNORECASE)
    parts = [p.strip() for p in splits if p.strip()]
    if len(parts) >= 2:
        return parts
    # Split by double newlines (paragraphs)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) >= 2:
        return paragraphs
    # Split by single newlines if distinct
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 8]
    if len(lines) >= 2:
        return lines
    return [text.strip()] if text.strip() else ["Bối cảnh khởi đầu câu chuyện"]


class GenerateScenesRequest(BaseModel):
    video_id: str
    prompt: str
    scene_count: int | None = None


class GeneratedScene(BaseModel):
    order: int
    prompt: str
    image_prompt: str
    video_prompt: str
    narrator_text: str


class GenerateScenesResponse(BaseModel):
    scenes: list[GeneratedScene]
    created: int


@router.post("/{pid}/generate-scenes", response_model=GenerateScenesResponse)
async def generate_scenes(pid: str, body: GenerateScenesRequest):
    """Generate or parse scenes directly from the script into rich scene records."""
    repo = _get_repo()
    project = await repo.get_project(pid)
    if not project:
        raise HTTPException(404, "Project not found")

    video = await repo.get_video(body.video_id)
    if not video:
        raise HTTPException(404, "Video not found")

    chars = await repo.get_project_characters(pid)
    char_names = [c["name"] if isinstance(c, dict) else c.name for c in chars]

    material_id = (project.material if hasattr(project, "material") else project.get("material")) or "realistic"
    from agent.services.materials import get_material
    material = get_material(material_id)
    scene_prefix = material["scene_prefix"] if material and material.get("scene_prefix") else "Real RAW photograph, shot on Canon EOS R5, 35mm lens."

    detected_scenes = _parse_script_scenes(body.prompt)
    limit = body.scene_count if body.scene_count and body.scene_count > 0 else len(detected_scenes)

    existing = await repo.list_scenes(body.video_id)
    start_order = max((s.display_order for s in existing), default=-1) + 1

    created_scenes = []
    for i, raw_scene in enumerate(detected_scenes[:limit]):
        # Match entity names present in this scene
        scene_lower = raw_scene.lower()
        matched_chars = [cname for cname in char_names if cname.lower() in scene_lower]
        if not matched_chars and char_names:
            matched_chars = char_names[:2]

        clean_text = raw_scene.replace("\n", " ").strip()
        prompt = f"{scene_prefix} In the scene, {clean_text}. Dynamic cinematic composition, natural lighting."
        video_prompt = (
            f"0-3s: The scene opens with {clean_text}. The camera smoothly tracks the motion. "
            f"3-6s: Action continues with steady cinematic movement. "
            f"6-8s: The camera settles into a stable composition with natural atmospheric depth.\n\n"
            f"Audio: natural environmental ambiance.\n"
            f"SFX: subtle Foley movement sounds.\n"
            f"Negative: subtitles, watermark, text overlay."
        )

        sdk_scene = await repo.create_scene(
            video_id=body.video_id,
            display_order=start_order + i,
            prompt=prompt,
            image_prompt=clean_text,
            video_prompt=video_prompt,
            character_names=matched_chars,
            chain_type="ROOT" if i == 0 else "CONTINUATION",
            source="user",
        )
        if clean_text:
            from agent.db import crud
            await crud.update_scene(sdk_scene.id, narrator_text=clean_text)
        created_scenes.append(GeneratedScene(
            order=start_order + i,
            prompt=prompt,
            image_prompt=clean_text,
            video_prompt=video_prompt,
            narrator_text=clean_text,
        ))

    return GenerateScenesResponse(scenes=created_scenes, created=len(created_scenes))


class CreateWithScriptRequest(BaseModel):
    name: str
    story: str
    material: str = "realistic"
    flow_project_id: str | None = None
    scene_count: int | None = None
    description: str | None = None
    characters: list[dict] | None = None
    orientation: str = "VERTICAL"


class CreateWithScriptResponse(BaseModel):
    project_id: str
    project_name: str
    video_id: str
    scenes_created: int
    characters_created: int
    pipeline_started: bool
    project: dict | None = None


@router.post("/create-with-script", response_model=CreateWithScriptResponse)
async def create_with_script(body: CreateWithScriptRequest):
    """Create a new project, extract all entities & scenes from script, switch active project, and trigger the full auto-pipeline."""
    from agent.api.active_project import _write_state
    from agent.services.auto_pipeline import enqueue_reference_images_only

    flow_id = body.flow_project_id.strip() if body.flow_project_id and body.flow_project_id.strip() else None

    # Step 1: Extract entities if not passed explicitly
    entities = body.characters or []
    if not entities:
        entities = _extract_entities_from_script(body.story, body.name)

    # Step 2: Create project with all entities linked
    proj_create = ProjectCreate(
        name=body.name,
        story=body.story,
        description=body.description or body.name,
        material=body.material,
        flow_project_id=flow_id,
        characters=entities,
    )
    project = await create(proj_create)

    # Step 3: Create default video
    repo = _get_repo()
    sdk_video = await repo.create_video(
        project_id=project.id,
        title=body.name,
        display_order=0,
        orientation=body.orientation,
    )

    # Step 4: Create all scenes from the script
    scenes_res = await generate_scenes(
        project.id,
        GenerateScenesRequest(
            video_id=sdk_video.id,
            prompt=body.story,
            scene_count=body.scene_count,
        ),
    )

    # Step 5: Switch active project so dashboard focuses on it
    try:
        _write_state({"project_id": project.id})
        logger.info("Active project switched to %s (%s)", project.name, project.id[:8])
    except Exception as e:
        logger.warning("Could not set active project: %s", e)

    # Step 6: Enqueue reference images ONLY (do NOT auto-generate scene images or videos).
    # The user will review reference images on the dashboard, then manually click "Tạo tất cả ảnh".
    await enqueue_reference_images_only(project.id)

    proj_dict = {
        "id": project.id if hasattr(project, "id") else project["id"],
        "name": project.name if hasattr(project, "name") else project["name"],
        "story": body.story,
        "material": body.material,
    }

    return CreateWithScriptResponse(
        project_id=proj_dict["id"],
        project_name=proj_dict["name"],
        video_id=sdk_video.id,
        scenes_created=scenes_res.created,
        characters_created=len(entities),
        pipeline_started=False,
        project=proj_dict,
    )


@router.post("/{pid}/auto-pipeline")
async def trigger_auto_pipeline(pid: str, orientation: str = "VERTICAL"):
    """Trigger or resume the automated full pipeline (refs -> scene images -> scene videos) for a project."""
    from agent.services.auto_pipeline import start_auto_pipeline, is_pipeline_active

    repo = _get_repo()
    project = await repo.get_project(pid)
    if not project:
        raise HTTPException(404, "Project not found")

    videos = await repo.list_videos(pid)
    if not videos:
        raise HTTPException(400, "Project has no video to run pipeline on")

    video = videos[0]
    orient = orientation or video.get("orientation") or "VERTICAL"
    task = start_auto_pipeline(pid, video["id"], orientation=orient)

    return {
        "status": "started",
        "project_id": pid,
        "video_id": video["id"],
        "orientation": orient,
        "active": is_pipeline_active(pid),
    }

