"""Storytime Animation API Endpoints.

Provides endpoints for:
- AI Script Breakdown (10-25 words, camera, expression)
- Vietnamese Edge-TTS voice synthesis
- Whisper word-level alignment (Karaoke subtitle timestamps)
- Audio serving & Demo project loading
"""
import asyncio
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent.config import OUTPUT_DIR
from agent.services.voice_manager import (
    get_all_voices,
    generate_speech_unified,
    generate_batch_narration_unified,
)
from agent.services.whisper_align import align_audio, align_scenes
from agent.services.image_filter import apply_noir_filter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/storytime", tags=["storytime"])

STORYTIME_DIR = OUTPUT_DIR / "storytime"
STORYTIME_DIR.mkdir(parents=True, exist_ok=True)


class BreakdownRequest(BaseModel):
    story_text: str
    genre: str = "general"


class TTSRequest(BaseModel):
    text: str
    voice: str = "vi-VN-NamMinhNeural"
    rate: str = "-4%"


class AlignRequest(BaseModel):
    filename: str


class LocationInput(BaseModel):
    """A reusable location/set for multiple scenes."""
    id: str  # e.g. "loc_1"
    name: str  # e.g. "Phòng khách", "Rừng cây"
    background_prompt: str
    color: Optional[str] = None  # Badge color for UI, e.g. "#f59e0b"


class ActorInput(BaseModel):
    """An actor (character) present on screen in a scene with position, action, and facing direction."""
    id: str  # Character ID, e.g. "char_1"
    position: str = "center"  # "left" (~20%), "center" (~50%), "right" (~80%)
    action: str = "stand"  # "stand", "walk", "run", "flee", "pursue", "shiver", "gesture"
    facing: int = 1  # 1 = facing right, -1 = facing left


class SceneInput(BaseModel):
    display_order: int
    speaker: str = "narrator"
    text: str
    camera: str = "zoom_in"
    expression: str = "serious"
    background_prompt: Optional[str] = None
    voice: Optional[str] = None
    location_id: Optional[str] = None  # Reference to a LocationInput.id
    action_type: Optional[str] = "dialogue"  # "dialogue" | "chase" | "trio" | "solo"
    actors: Optional[List[ActorInput]] = None  # Multi-actor layout for the scene


class PackageRequest(BaseModel):
    title: str = "Câu Chuyện Mới"
    genre: str = "general"
    voice: str = "vi-VN-NamMinhNeural"
    scenes: List[SceneInput]
    locations: Optional[List[LocationInput]] = None
    characters: Optional[List[Dict[str, Any]]] = None
    story_text: Optional[str] = None


PALETTE = [
    "#1e293b", "#0284c7", "#7c3aed", "#b91c1c", "#059669",
    "#d97706", "#db2777", "#4b5563", "#0891b2", "#4f46e5",
]


def dynamic_fallback_breakdown(text: str, requested_genre: str = "general") -> dict:
    """Universal NLP fallback extractor: dynamically extracts any characters, locations, and dialogue from any text without hardcoding."""
    raw_lines = [line.strip() for line in text.split("\n") if line.strip()]
    sentences = []
    for line in raw_lines:
        sub = [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ỹ\"“'])", line) if s.strip()]
        sentences.extend(sub if sub else [line])
    if not sentences:
        sentences = [text.strip()]

    characters_map: Dict[str, Dict[str, Any]] = {}
    locations_map: Dict[str, Dict[str, Any]] = {}
    scenes = []

    def make_slug(name_str: str) -> str:
        s = re.sub(r"[^\w\s-]", "", name_str.lower()).strip()
        return re.sub(r"[-\s]+", "_", s)[:24]

    color_idx = 0

    def register_char(name_clean: str, custom_gender: str = None) -> str:
        nonlocal color_idx
        cid = make_slug(name_clean) or f"char_{len(characters_map) + 1}"
        if cid not in characters_map:
            lower = name_clean.lower()
            if custom_gender:
                gender = custom_gender
            else:
                is_female = any(w in lower for w in ["bà", "chị", "cô", "nàng", "nữ", "mai", "lan", "hoa", "công chúa", "mẹ", "bé gái"])
                is_male = any(w in lower for w in ["ông", "anh", "chú", "chàng", "nam", "thỏ", "cáo", "sói", "hổ", "gấu", "hoàng tử", "vua", "cha", "bố", "bé trai"])
                gender = "female" if is_female else "male" if is_male else "other"
            characters_map[cid] = {
                "id": cid,
                "name": name_clean.title(),
                "gender": gender,
                "color": PALETTE[color_idx % len(PALETTE)],
                "description": f"Nhân vật: {name_clean.title()}",
            }
            color_idx += 1
        return cid

    SPEECH_VERBS = r"(?:nói|hỏi|bảo|kêu|thì thầm|quát|thề|đáp|lên tiếng|chất vấn|hét lên|than thở|cãi lại|thông báo|lo lắng|hô to|nhắc nhở)"
    dialogue_pattern_1 = re.compile(rf'([A-ZÀ-Ỹa-zà-ỹ0-9\s]{{2,25}})\s+{SPEECH_VERBS}\s*[:,\-]?\s*["“\']([^"”\']+)["”\']', re.IGNORECASE)
    dialogue_pattern_2 = re.compile(rf'["“\']([^"”\']+)["”\']\s*[-–]\s*([A-ZÀ-Ỹa-zà-ỹ0-9\s]{{2,25}})\s+{SPEECH_VERBS}', re.IGNORECASE)
    dialogue_pattern_3 = re.compile(r'([A-ZÀ-Ỹa-zà-ỹ0-9\s]{2,25})\s*:\s*["“\']([^"”\']+)["”\']')

    # 1. PRE-SCAN DIALOGUE SPEAKERS ACROSS WHOLE STORY
    for s in sentences:
        m1 = dialogue_pattern_1.search(s)
        m2 = dialogue_pattern_2.search(s)
        m3 = dialogue_pattern_3.search(s)
        if m1:
            register_char(m1.group(1).strip())
        elif m2:
            register_char(m2.group(2).strip())
        elif m3:
            register_char(m3.group(1).strip())

    # 2. PRE-SCAN COMMON STORY ENTITIES (ANIMAL, FANTASY, ROLE, OCCUPATION)
    COMMON_ENTITIES = [
        "thỏ", "cáo", "sói", "hổ", "gấu", "rùa", "nhím", "hươu", "sư tử", "mèo", "chó", "chuột",
        "hoàng tử", "công chúa", "nhà vua", "hoàng hậu", "phù thủy", "bà lão", "ông lão",
        "cô bé", "cậu bé", "chàng trai", "cô gái", "bác thợ săn", "bác nông dân",
        "thám tử", "tiến sĩ", "phi hành gia", "cảnh sát", "bác sĩ", "học sinh", "thầy giáo", "hiệp sĩ"
    ]
    full_lower = text.lower()
    for ent in COMMON_ENTITIES:
        if re.search(rf'\b{ent}\b', full_lower):
            register_char(ent)

    # Fallback characters if none detected at all
    if not characters_map:
        characters_map["char_1"] = {
            "id": "char_1",
            "name": "Nhân vật chính",
            "gender": "male",
            "color": "#1e293b",
            "description": "Nhân vật chính trong câu chuyện",
        }
        characters_map["char_2"] = {
            "id": "char_2",
            "name": "Nhân vật phụ",
            "gender": "female",
            "color": "#7c3aed",
            "description": "Nhân vật đồng hành hoặc đối thoại",
        }

    # 3. PRE-SCAN LOCATIONS
    loc_pattern = re.compile(
        r'(?:tại|ở|trong|ngoài|bên trong|bên ngoài)\s+(?:một\s+)?(?:căn|ngôi|khu|viện|phòng|trạm|con|bãi|vườn|chiếc|thành|làng|đảo|hang|lâu đài|biệt thự|rừng|núi|sông|biển|phố)\s+([a-zA-ZÀ-Ỹà-ỹ0-9\s]{2,25})',
        re.IGNORECASE
    )
    for s in sentences:
        lm = loc_pattern.search(s)
        if lm:
            loc_name = lm.group(1).strip()
            loc_id = f"loc_{make_slug(loc_name)}"
            if loc_id not in locations_map:
                locations_map[loc_id] = {
                    "id": loc_id,
                    "name": loc_name.title(),
                    "background_prompt": f"Atmospheric illustration of {loc_name}, dramatic cinematic lighting. Pure scenery illustration, strictly NO people, NO characters.",
                    "color": PALETTE[(len(locations_map) + 2) % len(PALETTE)],
                }

    if not locations_map:
        loc_id = "loc_main"
        locations_map[loc_id] = {
            "id": loc_id,
            "name": "Bối cảnh chính",
            "background_prompt": "Atmospheric moody interior or landscape with cinematic lighting. Pure scenery illustration, strictly NO people, NO characters.",
            "color": "#64748b",
        }

    # 4. BUILD SCENES & MULTI-ACTOR POSITIONS
    char_ids = [c for c in characters_map.keys() if c != "narrator"]
    if not char_ids:
        char_ids = list(characters_map.keys())

    for i, s in enumerate(sentences):
        lower = s.lower()
        speaker = "narrator"
        action_type = "dialogue"

        # Check dialogue
        m1 = dialogue_pattern_1.search(s)
        m2 = dialogue_pattern_2.search(s)
        m3 = dialogue_pattern_3.search(s)
        if m1:
            speaker = register_char(m1.group(1).strip())
        elif m2:
            speaker = register_char(m2.group(2).strip())
        elif m3:
            speaker = register_char(m3.group(1).strip())
        else:
            # Check if any registered character mentioned directly
            found_mention = None
            for cid, cinfo in characters_map.items():
                if cid != "narrator" and (cid.replace("_", " ") in lower or cinfo["name"].lower() in lower):
                    found_mention = cid
                    break
            quote_match = re.search(r'["“\']([^"”\']+)["”\']', s)
            if quote_match and found_mention:
                speaker = found_mention
            elif quote_match and char_ids:
                speaker = char_ids[i % len(char_ids)]

        # Action type & camera
        if any(w in lower for w in ["đuổi theo", "bỏ chạy", "chạy trốn", "truy bắt", "vùng chạy", "lao theo", "chạy thục mạng"]):
            action_type = "chase"
            cam = "pan_right"
            exp = "fear" if speaker != "narrator" else "serious"
        elif any(w in lower for w in ["đánh nhau", "xô xát", "ẩu đả", "vật lộn", "chiến đấu", "tấn công", "đấm", "đá"]):
            action_type = "chase"  # fight uses chase layout (two moving actors)
            cam = "close"
            exp = "shocked"
        elif any(w in lower for w in ["mọi người", "toàn bộ", "tất cả", "cả hai", "cả ba", "cả nhóm", "cả bọn"]):
            action_type = "trio"
            cam = "zoom_in"
            exp = "shocked"
        elif any(w in lower for w in ["bất ngờ", "sốc", "kinh hoàng", "hoảng loạn", "hét lên", "nguy hiểm", "chết"]):
            cam = "close"
            exp = "shocked"
        elif any(w in lower for w in ["suy nghĩ", "nghi ngờ", "trầm ngâm", "tự hỏi", "phân vân"]):
            cam = "zoom_in"
            exp = "thinking"
        elif any(w in lower for w in ["đi", "bước", "tiến", "lại gần", "đến", "rời đi", "quay lưng"]):
            cam = "pan_right"
            exp = "serious"
        else:
            cam = "zoom_in"
            exp = "talking" if speaker != "narrator" else "serious"

        # Multi-actor placement
        actors = []
        if action_type == "chase":
            flee_char = speaker if speaker != "narrator" else char_ids[0]
            actors.append({"id": flee_char, "position": "left", "action": "flee", "facing": 1})
            pursuers = [c for c in char_ids if c != flee_char]
            if pursuers:
                actors.append({"id": pursuers[0], "position": "right", "action": "pursue", "facing": -1})
        elif action_type == "trio":
            positions = ["left", "center", "right"]
            for idx_a, cid in enumerate(char_ids[:3]):
                actors.append({"id": cid, "position": positions[idx_a], "action": "stand", "facing": 1 if idx_a % 2 == 0 else -1})
        else:
            if speaker != "narrator":
                actors.append({"id": speaker, "position": "left", "action": "stand", "facing": 1})
                listeners = [c for c in char_ids if c != speaker]
                if listeners:
                    actors.append({"id": listeners[0], "position": "right", "action": "stand", "facing": -1})
            else:
                # Narrator: show up to 2 characters on screen
                actors.append({"id": char_ids[0], "position": "center" if len(char_ids) == 1 else "left", "action": "stand", "facing": 1})
                if len(char_ids) > 1:
                    actors.append({"id": char_ids[1], "position": "right", "action": "stand", "facing": -1})

        # Match location for this scene
        lm = loc_pattern.search(s)
        if lm:
            cur_loc_id = f"loc_{make_slug(lm.group(1).strip())}"
            if cur_loc_id not in locations_map:
                cur_loc_id = list(locations_map.keys())[0]
        else:
            cur_loc_id = list(locations_map.keys())[0]

        scenes.append({
            "display_order": i,
            "speaker": speaker,
            "action_type": action_type,
            "text": s,
            "camera": cam,
            "expression": exp,
            "background_prompt": locations_map[cur_loc_id]["background_prompt"],
            "location_id": cur_loc_id,
            "actors": actors,
        })

    if any(sc["speaker"] == "narrator" for sc in scenes) and "narrator" not in characters_map:
        characters_map["narrator"] = {
            "id": "narrator",
            "name": "Người kể chuyện",
            "gender": "male",
            "color": "#475569",
            "description": "Giọng đọc thuyết minh",
        }

    first_line = sentences[0][:36]
    return {
        "title": first_line + ("..." if len(sentences[0]) > 36 else ""),
        "genre": requested_genre or "general",
        "characters": list(characters_map.values()),
        "locations": list(locations_map.values()),
        "scenes": scenes,
    }


@router.post("/breakdown")
async def api_breakdown(req: BreakdownRequest):
    """Breakdown raw story text into structured scenes."""
    text = req.story_text.strip()
    if not text:
        raise HTTPException(400, "Vui lòng nhập nội dung câu chuyện.")

    # Try calling AI CLI
    from scripts.breakdown_storytime import call_ai, extract_json, validate_storytime_spec
    try:
        raw_ai = await asyncio.to_thread(call_ai, text)
        spec = extract_json(raw_ai)
        warnings = validate_storytime_spec(spec)
        return {"ok": True, "spec": spec, "warnings": warnings}
    except Exception as e:
        logger.warning("AI CLI breakdown failed (%s), using smart sentence splitting fallback", e)
        # Smart universal NLP fallback: extracts any characters, locations, and dialogues dynamically
        fallback_spec = dynamic_fallback_breakdown(text, req.genre)
        return {"ok": True, "spec": fallback_spec, "is_fallback": True}


@router.get("/voices")
async def api_get_voices():
    """Retrieve full list of available voices across Edge-TTS and GPT-SoVITS engines."""
    return await get_all_voices()


@router.post("/tts")
async def api_single_tts(req: TTSRequest):
    """Generate audio for a single sentence."""
    filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
    target_path = STORYTIME_DIR / "audio" / filename
    res = await generate_speech_unified(req.text, str(target_path), voice=req.voice, rate=req.rate)
    if not res.get("ok"):
        raise HTTPException(500, res.get("error", "TTS generation failed"))
    return {
        "ok": True,
        "filename": filename,
        "audio_url": f"/api/storytime/audio/{filename}",
        "duration": res["duration"],
    }


@router.post("/align")
async def api_align(req: AlignRequest):
    """Align word timestamps for an audio file."""
    audio_path = STORYTIME_DIR / "audio" / req.filename
    if not audio_path.exists():
        raise HTTPException(404, "Audio file not found")
    try:
        aligned = await asyncio.to_thread(align_audio, str(audio_path), language="vi")
        return {"ok": True, "words": aligned["words"], "duration": aligned["duration"]}
    except Exception as e:
        logger.error("Alignment failed: %s", e)
        raise HTTPException(500, f"Whisper alignment error: {e}")


def generate_script_subtitles(text: str, duration: float) -> list:
    """Generate word-level timestamps directly from script text and audio duration without needing STT."""
    words = text.strip().split()
    if not words:
        return []
    total_chars = sum(max(1, len(w)) for w in words)
    cursor = 0.12
    avail = max(0.5, duration - 0.28)
    subs = []
    for w in words:
        w_dur = max(0.12, (max(1, len(w)) / total_chars) * avail)
        subs.append({
            "word": w,
            "start": round(cursor, 3),
            "end": round(cursor + w_dur, 3),
        })
        cursor += w_dur
    return subs


async def save_storytime_package_to_sqlite(package_data: dict, story_text: str = "") -> Optional[str]:
    """Save a Storytime package (scenes, locations, narrator) directly into SQLite tables (project, video, scene, character)."""
    try:
        from agent.db import crud
        from agent.api.active_project import _write_state

        title = package_data.get("title") or "Câu Chuyện Mới"
        scenes = package_data.get("scenes", [])
        locations = package_data.get("locations", [])

        # Build full story text if not provided
        if not story_text:
            story_text = "\n\n".join(s.get("text", "") for s in scenes if s.get("text"))

        total_sec = package_data.get("total_duration_seconds", 0)
        dur_min = round(total_sec / 60, 1) if total_sec else 0.0

        # 1. Create Project
        proj = await crud.create_project(
            name=title,
            story=story_text[:3000],
            description=f"Gói kịch bản Storytime ({len(scenes)} cảnh, ~{dur_min} phút)",
            material="realistic",
            allow_voice=True,
        )
        project_id = proj["id"]

        # 2. Create Location entities and link to project
        loc_id_map = {}
        for loc in locations:
            loc_name = loc.get("name") or "Bối cảnh"
            bg_prompt = loc.get("background_prompt") or ""
            try:
                char_rec = await crud.create_character(
                    name=loc_name,
                    entity_type="location",
                    description=f"Bối cảnh Storytime: {loc_name}",
                    image_prompt=bg_prompt,
                )
                await crud.link_character_to_project(project_id, char_rec["id"])
                if loc.get("id"):
                    loc_id_map[loc["id"]] = loc_name
            except Exception as loc_err:
                logger.warning("Could not link location entity %s: %s", loc_name, loc_err)

        # 3. Create Video (16:9 Standard)
        video = await crud.create_video(
            project_id=project_id,
            title=title,
            display_order=0,
            orientation="HORIZONTAL",
        )
        video_id = video["id"]

        # 4. Create Scenes
        for sc_idx, sc_item in enumerate(scenes):
            txt = sc_item.get("text", "")
            bg = sc_item.get("background_prompt", "")
            dur = sc_item.get("duration_seconds", 4.0)
            cam = sc_item.get("camera", "zoom_in")
            exp = sc_item.get("expression", "serious")
            lid = sc_item.get("location_id")

            char_names = []
            if lid and lid in loc_id_map:
                char_names.append(loc_id_map[lid])

            s_rec = await crud.create_scene(
                video_id=video_id,
                display_order=sc_idx,
                prompt=txt,
                image_prompt=bg,
                video_prompt=f"{txt}. Camera: {cam}. Expression: {exp}.",
                duration=dur,
                character_names=char_names if char_names else None,
            )
            # Save narrator text and actors layout
            update_kw = {}
            if txt:
                update_kw["narrator_text"] = txt
            actors_data = sc_item.get("actors")
            if actors_data:
                update_kw["actors"] = json.dumps(actors_data, ensure_ascii=False)
            if update_kw:
                await crud.update_scene(s_rec["id"], **update_kw)

        # 5. Set active project
        _write_state({"project_id": project_id})
        logger.info("Successfully saved Storytime package to SQLite project %s (%s)", project_id, title)
        return project_id
    except Exception as e:
        logger.error("Failed to save storytime package to SQLite: %s", e)
        return None


@router.post("/build-package")
async def api_build_package(req: PackageRequest):
    """Generate TTS and clean subtitles directly from script text for an entire scene list."""
    package_id = uuid.uuid4().hex[:8]
    pkg_dir = STORYTIME_DIR / f"pkg_{package_id}"
    audio_dir = pkg_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Build locations lookup from request (if provided)
    locations_lookup: Dict[str, Dict] = {}
    if req.locations:
        for loc in req.locations:
            locations_lookup[loc.id] = {
                "id": loc.id,
                "name": loc.name,
                "background_prompt": loc.background_prompt,
                "color": loc.color or "#64748b",
            }

    # 1. Edge-TTS Batch
    tts_items = [
        {
            "display_order": s.display_order,
            "text": s.text,
            "speaker": s.speaker,
            "camera": s.camera,
            "expression": s.expression,
            "background_prompt": s.background_prompt,
            "voice": s.voice or req.voice,
            "location_id": s.location_id,
            "action_type": s.action_type or "dialogue",
            "actors": [a.model_dump() for a in s.actors] if s.actors else [],
        }
        for s in req.scenes
    ]
    scenes_with_audio = await generate_batch_narration_unified(tts_items, str(audio_dir), default_voice=req.voice)

    # 2. Subtitles derived directly from script text (no Whisper STT / voice-to-text required!)
    for sc in scenes_with_audio:
        sc["subtitles"] = generate_script_subtitles(sc.get("text", ""), sc.get("audio_duration", 4.0))
    scenes_with_subtitles = scenes_with_audio

    # 3. Assemble package
    total_frames = 0
    total_duration = 0.0
    fps = 30
    final_scenes = []

    for sc in scenes_with_subtitles:
        dur = sc.get("audio_duration", 4.0)
        padded_dur = round(dur + 0.35, 2)
        frame_count = int(padded_dur * fps)
        audio_name = Path(sc["audio_path"]).name if sc.get("audio_path") else None

        # Resolve background_prompt from location if scene has location_id
        loc_id = sc.get("location_id")
        bg_prompt = sc.get("background_prompt", "")
        if loc_id and loc_id in locations_lookup:
            bg_prompt = bg_prompt or locations_lookup[loc_id]["background_prompt"]

        final_scenes.append({
            "id": sc["display_order"],
            "speaker": sc.get("speaker", "narrator"),
            "action_type": sc.get("action_type", "dialogue"),
            "text": sc.get("text", ""),
            "camera": sc.get("camera", "zoom_in"),
            "expression": sc.get("expression", "serious"),
            "voice": sc.get("voice_used") or sc.get("voice") or req.voice,
            "audio_url": f"/api/storytime/pkg-audio/{package_id}/{audio_name}" if audio_name else None,
            "duration_seconds": padded_dur,
            "duration_frames": frame_count,
            "start_frame": total_frames,
            "end_frame": total_frames + frame_count,
            "subtitles": sc.get("subtitles", []),
            "background_prompt": bg_prompt,
            "location_id": loc_id,
            "actors": sc.get("actors", []),
        })
        total_frames += frame_count
        total_duration += padded_dur

    # 4. Build unique locations list for package
    # Auto-detect from scenes if no explicit locations provided
    if not locations_lookup:
        for sc in final_scenes:
            bg = sc.get("background_prompt", "")
            lid = sc.get("location_id")
            if bg and lid and lid not in locations_lookup:
                locations_lookup[lid] = {
                    "id": lid,
                    "name": lid.replace("loc_", "").replace("_", " ").title(),
                    "background_prompt": bg,
                    "color": "#64748b",
                }

    package_data = {
        "package_id": package_id,
        "title": req.title,
        "genre": req.genre,
        "fps": fps,
        "width": 1920,
        "height": 1080,
        "total_duration_seconds": round(total_duration, 2),
        "total_frames": total_frames,
        "characters": req.characters or [],
        "locations": list(locations_lookup.values()),
        "scenes": final_scenes,
    }

    # Save into SQLite database so it immediately appears in /projects & dashboard
    project_id = await save_storytime_package_to_sqlite(package_data, story_text=req.story_text or "")
    if project_id:
        package_data["project_id"] = project_id

    # Save manifest with project_id
    (pkg_dir / "package.json").write_text(json.dumps(package_data, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"ok": True, "package": package_data, "project_id": project_id}


@router.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve single audio file."""
    path = STORYTIME_DIR / "audio" / filename
    if not path.exists():
        raise HTTPException(404, "Audio not found")
    return FileResponse(str(path), media_type="audio/mpeg")


@router.get("/pkg-audio/{package_id}/{filename}")
async def serve_pkg_audio(package_id: str, filename: str):
    """Serve package audio file."""
    path = STORYTIME_DIR / f"pkg_{package_id}" / "audio" / filename
    if not path.exists():
        raise HTTPException(404, "Package audio not found")
    return FileResponse(str(path), media_type="audio/mpeg")


@router.get("/packages")
async def list_packages():
    """List all created storytime packages for batch dashboard."""
    packages = []
    
    # 1. Include sample package if exists
    sample_file = OUTPUT_DIR / "sample_remotion_dist" / "remotion_input.json"
    if sample_file.exists():
        try:
            sdata = json.loads(sample_file.read_text(encoding="utf-8"))
            packages.append({
                "package_id": "sample",
                "title": sdata.get("title", "Bí Ẩn Vụ Án Căn Phòng Kín"),
                "genre": sdata.get("genre", "trinh_tham"),
                "scenes_count": len(sdata.get("scenes", [])),
                "total_duration": sdata.get("total_duration_seconds", 12.0),
                "status": "COMPLETED",
                "is_sample": True,
            })
        except Exception:
            pass

    # 2. Scan STORYTIME_DIR for pkg_*
    for pkg_folder in sorted(STORYTIME_DIR.glob("pkg_*"), reverse=True):
        manifest_file = pkg_folder / "package.json"
        if manifest_file.exists():
            try:
                pdata = json.loads(manifest_file.read_text(encoding="utf-8"))
                packages.append({
                    "package_id": pdata.get("package_id", pkg_folder.name.replace("pkg_", "")),
                    "title": pdata.get("title", "Câu Chuyện Không Tên"),
                    "genre": pdata.get("genre", "general"),
                    "scenes_count": len(pdata.get("scenes", [])),
                    "total_duration": pdata.get("total_duration_seconds", 0.0),
                    "status": "COMPLETED",
                    "is_sample": False,
                })
            except Exception:
                continue

    return {"ok": True, "packages": packages}


@router.get("/packages/{package_id}")
async def get_package(package_id: str):
    """Get full package data by ID."""
    if package_id == "sample":
        return await get_sample_package()
    
    pkg_file = STORYTIME_DIR / f"pkg_{package_id}" / "package.json"
    if not pkg_file.exists():
        raise HTTPException(404, "Package not found")
    
    try:
        pdata = json.loads(pkg_file.read_text(encoding="utf-8"))
        return {"ok": True, "package": pdata}
    except Exception as e:
        raise HTTPException(500, f"Error reading package: {e}")


@router.delete("/packages/{package_id}")
async def delete_package(package_id: str):
    """Delete a package and its audio files."""
    if package_id == "sample":
        raise HTTPException(400, "Cannot delete sample package")
    
    import shutil
    target_dir = STORYTIME_DIR / f"pkg_{package_id}"
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
    return {"ok": True}


class BatchStoryItem(BaseModel):
    title: Optional[str] = None
    story_text: str
    voice: Optional[str] = "vi-VN-NamMinhNeural"
    genre: Optional[str] = "general"


class BatchStoriesRequest(BaseModel):
    stories: List[BatchStoryItem]


@router.post("/batch-create")
async def api_batch_create(req: BatchStoriesRequest):
    """Batch generate multiple video packages dynamically extracting characters, locations, and actors from any story genre."""
    results = []
    for s in req.stories:
        text = s.story_text.strip()
        if not text:
            continue
        genre = s.genre or "general"
        
        # 1. Dynamically extract characters, locations, dialogue and scenes from story text
        parsed = dynamic_fallback_breakdown(text, requested_genre=genre)
        title = (s.title or "").strip() or parsed.get("title") or "Câu Chuyện Mới"

        locations = [
            LocationInput(
                id=loc["id"],
                name=loc["name"],
                background_prompt=loc["background_prompt"],
                color=loc.get("color", "#64748b"),
            )
            for loc in parsed.get("locations", [])
        ]

        scenes = [
            SceneInput(
                display_order=sc["display_order"],
                speaker=sc.get("speaker", "narrator"),
                text=sc["text"],
                camera=sc.get("camera", "zoom_in"),
                expression=sc.get("expression", "serious"),
                background_prompt=sc.get("background_prompt"),
                location_id=sc.get("location_id"),
                action_type=sc.get("action_type", "dialogue"),
                actors=[
                    ActorInput(
                        id=act["id"],
                        position=act.get("position", "center"),
                        action=act.get("action", "stand"),
                        facing=act.get("facing", 1),
                    )
                    for act in sc.get("actors", [])
                ] if sc.get("actors") else None,
            )
            for sc in parsed.get("scenes", [])
        ]

        # 2. Build package
        pkg_req = PackageRequest(
            title=title,
            genre=genre,
            voice=s.voice or "vi-VN-NamMinhNeural",
            scenes=scenes,
            locations=locations,
            characters=parsed.get("characters", []),
            story_text=text,
        )
        try:
            pkg_res = await api_build_package(pkg_req)
            if pkg_res.get("ok"):
                pkg_data = pkg_res["package"]
                pkg_id = pkg_data["package_id"]
                project_id = pkg_res.get("project_id") or pkg_data.get("project_id")

                results.append({
                    "title": title,
                    "package_id": pkg_id,
                    "project_id": project_id,
                    "scenes_count": len(pkg_data["scenes"]),
                    "total_duration": pkg_data["total_duration_seconds"],
                    "status": "COMPLETED",
                })
        except Exception as e:
            logger.error("Failed batch item '%s': %s", title, e)
            results.append({
                "title": title,
                "status": "FAILED",
                "error": str(e)
            })

    return {"ok": True, "created": results}


@router.get("/sample-package")
async def get_sample_package():
    """Return pre-generated sample detective mystery package for instant preview."""
    sample_file = OUTPUT_DIR / "sample_remotion_dist" / "remotion_input.json"
    if sample_file.exists():
        try:
            data = json.loads(sample_file.read_text(encoding="utf-8"))
            # Convert relative audio paths to API URLs
            for sc in data.get("scenes", []):
                if sc.get("audio_file"):
                    fname = Path(sc["audio_file"]).name
                    sc["audio_url"] = f"/api/storytime/sample-audio/{fname}"
            return {"ok": True, "package": data}
        except Exception:
            pass
    return {"ok": False, "reason": "No sample found"}


@router.get("/sample-audio/{filename}")
async def serve_sample_audio(filename: str):
    """Serve sample audio file."""
    path = OUTPUT_DIR / "sample_remotion_dist" / "audio" / filename
    if not path.exists():
        raise HTTPException(404, "Sample audio not found")
    return FileResponse(str(path), media_type="audio/mpeg")
