#!/usr/bin/env python3
import sqlite3
import uuid
import json
import shutil
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "flow_agent.db"
BAK_PATH = ROOT / "flow_agent.db.bak"

conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

# Check if Mộc Tinh already exists
existing = c.execute("SELECT id FROM project WHERE name LIKE '%Mộc Tinh%'").fetchone()
if existing:
    print(f"Project Mộc Tinh already exists with ID: {existing[0]}")
    proj_id = existing[0]
else:
    proj_id = str(uuid.uuid4())
    vid_id = str(uuid.uuid4())
    now = "2026-10-19T08:00:00Z"

    story_text = """Mộc Tinh — Cây Biết Gọi Tên
Đêm hôm đó, trong cánh rừng già Tây Bắc, gió rít qua những tán cây cổ thụ như tiếng ai oán than.
Dân làng đồn rằng cây đa ngàn năm ở đầu khe suối có thể cất tiếng gọi tên người đi đêm.
Bất kỳ ai lỡ miệng trả lời đều sẽ biến mất không dấu vết vào sáng hôm sau.
Thanh tra Minh cầm đèn pin soi vào vết tích cào xới kỳ dị trên thân cây, linh cảm vụ án này vượt xa logic thông thường."""

    c.execute("""
        INSERT INTO project (id, name, description, story, material, status, user_paygate_tier, allow_voice, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'ACTIVE', 'PAYGATE_TIER_TWO', 1, ?, ?)
    """, (proj_id, "Mộc Tinh — Cây Biết Gọi Tên", "Kịch bản Noir bí ẩn dân gian 16:9 (4 phân cảnh)", story_text, "cinematic_drama", now, now))

    # Entities
    char_minh = str(uuid.uuid4())
    loc_cayda = str(uuid.uuid4())
    loc_rung = str(uuid.uuid4())

    c.execute("""
        INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (char_minh, "Thanh tra Minh", "thanh_tra_minh", "character", 
          "35-year-old Vietnamese detective, sharp intense observant eyes, wearing a dark weathered trench coat over simple shirt, rugged handsome look, natural skin texture.",
          "Portrait of 35-year-old Vietnamese male detective in dark trench coat, holding flashlight, dark forest background, cinematic lighting, 16:9 aspect ratio.",
          now, now))

    c.execute("""
        INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (loc_cayda, "Cây đa ngàn năm", "cay_da_ngan_nam", "location", 
          "Ancient colossal twisted banyan tree by a misty mountain stream at night, massive hanging aerial roots, moss-covered sinister bark, faint cold moonlight filtering through thick fog. Pure scenery illustration, strictly NO people, NO characters.",
          "Colossal ancient banyan tree by misty mountain stream at night, deep eerie shadows, moonlight, pure empty scenery, 16:9 cinema wide shot.",
          now, now))

    c.execute("""
        INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (loc_rung, "Rừng già Tây Bắc", "rung_gia_tay_bac", "location", 
          "Dense primeval misty pine forest in northwest Vietnam at midnight, winding dirt path, cold fog drifting between towering trees, eerie silence. Pure scenery illustration, strictly NO people, NO characters.",
          "Atmospheric misty dark forest path at night, deep shadows, cinematic noir landscape, 16:9 wide shot, pure scenery.",
          now, now))

    for cid in [char_minh, loc_cayda, loc_rung]:
        c.execute("INSERT INTO project_character (project_id, character_id) VALUES (?, ?)", (proj_id, cid))

    # Video with 16:9 HORIZONTAL
    c.execute("""
        INSERT INTO video (id, project_id, title, display_order, orientation, status, created_at, updated_at)
        VALUES (?, ?, ?, 0, 'HORIZONTAL', 'DRAFT', ?, ?)
    """, (vid_id, proj_id, "Mộc Tinh — Cây Biết Gọi Tên (16:9)", now, now))

    # Scenes (All 16:9 standard prompts)
    scenes_data = [
        (
            0,
            "Gió rít qua những tán cây cổ thụ trong cánh rừng già Tây Bắc ban đêm, sương mù mờ ảo cuộn tròn theo từng cơn gió lạnh.",
            "Wide shot 16:9, primeval dark mountain forest in northwest Vietnam at midnight, thick fog rolling through ancient giant trees, cold moonlight casting long eerie shadows. Pure moody atmosphere.",
            "0-3s: Wide static shot looking deep into the dark mountain forest, dense cold mist drifts slowly between mossy tree trunks. 3-6s: Strong wind violently sways the upper branches, rustling dead leaves as moonlight breaks through drifting fog.\n\nAudio: howling mountain wind, distant creaking tree branches.\nSFX: rustling dry leaves, eerie whistling breeze.\nNegative: subtitles, watermark, text overlay.",
            "Đêm hôm đó, trong cánh rừng già Tây Bắc, gió rít qua những tán cây cổ thụ như tiếng ai oán than.",
            5.0,
            ["Rừng già Tây Bắc"]
        ),
        (
            1,
            "Cây đa khổng lồ ngàn năm tuổi đứng sừng sững bên khe suối cạn, những chùm rễ phụ rủ xuống như những cánh tay ma quái trong màn đêm.",
            "Establishing wide shot 16:9, ancient colossal banyan tree looming over rocky stream bank at night, twisted roots hanging like eerie tentacles, soft cold blue mist hovering over dark water.",
            "0-3s: The camera performs a slow creeping pan across the dark water toward the monumental banyan tree. 3-6s: The camera tilts slowly upward revealing the immense twisted crown shrouded in nocturnal fog.\n\nAudio: slow dripping water, low haunting drone.\nSFX: gentle stream trickle, distant night owl call.\nNegative: subtitles, watermark, text overlay.",
            "Dân làng đồn rằng cây đa ngàn năm ở đầu khe suối có thể cất tiếng gọi tên người đi đêm.",
            5.5,
            ["Cây đa ngàn năm"]
        ),
        (
            2,
            "Một bóng người đi đêm bước đi đơn độc trong màn sương mờ ảo bên bờ suối rồi bỗng khựng lại như nghe thấy tiếng thì thầm gọi tên mình.",
            "Medium wide shot 16:9, shadowy silhouette of a lonely traveler walking along the misty forest trail near the ancient tree, suddenly stopping and turning head toward the dark woods.",
            "0-3s: Medium wide shot, the solitary silhouette walks slowly along the foggy trail, breath visible in cold night air. 3-6s: The traveler stops dead in their tracks, slowly turning head toward the dark root hollow as an eerie muffled whisper echoes.\n\nAudio: soft whispering wind, sudden tense heartbeat sound.\nSFX: crunching gravel footsteps stopping abruptly.\nNegative: subtitles, watermark, text overlay.",
            "Bất kỳ ai lỡ miệng trả lời đều sẽ biến mất không dấu vết vào sáng hôm sau.",
            6.0,
            ["Cây đa ngàn năm", "Rừng già Tây Bắc"]
        ),
        (
            3,
            "Thanh tra Minh cầm đèn pin rọi luồng sáng vàng sắc bén vào những vết cào xới sâu hoắm kỳ lạ trên thân vỏ cây đa xù xì, đôi mắt tập trung căng thẳng.",
            "Medium close-up shot 16:9, Thanh tra Minh in dark trench coat shining bright flashlight beam onto the scarred tree bark, illuminating deep jagged claw marks, his face tense and resolute.",
            "0-3s: Medium close-up on Thanh tra Minh from side angle, his flashlight beam cuts through mist illuminating fresh bizarre claw marks carved deep into the bark. 3-6s: Minh leans in closer, brow furrowed in grim realization as camera slowly pushes in on his focused eyes.\n\nAudio: tense low-frequency cello drone, steady heavy breathing.\nSFX: flashlight click, fabric rustle of coat.\nNegative: subtitles, watermark, text overlay.",
            "Thanh tra Minh cầm đèn pin soi vào vết tích cào xới kỳ dị trên thân cây, linh cảm vụ án này vượt xa logic thông thường.",
            6.0,
            ["Thanh tra Minh", "Cây đa ngàn năm"]
        ),
    ]

    for order, pmt, img_pmt, vid_pmt, narr, dur, chars in scenes_data:
        sid = str(uuid.uuid4())
        c.execute("""
            INSERT INTO scene (id, video_id, display_order, prompt, image_prompt, video_prompt, narrator_text, duration, character_names, chain_type, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ROOT', 'user', ?, ?)
        """, (sid, vid_id, order, pmt, img_pmt, vid_pmt, narr, dur, json.dumps(chars, ensure_ascii=False), now, now))

    conn.commit()
    print(f"SUCCESS: Created Mộc Tinh project: {proj_id} with Video 16:9 HORIZONTAL: {vid_id}")

conn.close()

# Update flow_agent.db.bak
shutil.copyfile(str(DB_PATH), str(BAK_PATH))
print("Updated flow_agent.db.bak")
