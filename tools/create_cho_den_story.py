#!/usr/bin/env python3
"""Khởi tạo dự án Hoạt hình 2D Người Que Tối Giản & Kinh Dị Dân Gian:
'Lời Nguyền Con Chó Đen (Hoạt Hình 2D Dân Gian)'
Chuẩn hóa 100% UUID dự án = FLOW_PROJECT_ID từ Google Flow (8222c95b-a99b-4501-b52e-163420646b19)
để mọi ảnh và video tạo ra hiển thị trực tiếp trên tab web flow.google.com!
"""
import json
import os
import sqlite3
import uuid
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "flow_agent.db"
ENV_PATH = ROOT / ".env"

# Đọc FLOW_PROJECT_ID từ .env
flow_project_id = None
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("FLOW_PROJECT_ID="):
            flow_project_id = line.split("=", 1)[1].strip()

if not flow_project_id:
    flow_project_id = os.environ.get("FLOW_PROJECT_ID", "8222c95b-a99b-4501-b52e-163420646b19")

print(f"[*] Đồng bộ UUID dự án với Google Flow: {flow_project_id}")

conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

proj_name = "Lời Nguyền Con Chó Đen (Hoạt Hình 2D Dân Gian)"
proj_id = flow_project_id
vid_id = str(uuid.uuid4())
now = "2026-10-20T03:00:00Z"

# Xóa các bản ghi cũ của dự án này (nếu có UUID khác hoặc đã tồn tại) để đồng bộ chuẩn xác
c.execute("PRAGMA foreign_keys = OFF;")
old_pids = [r[0] for r in c.execute("SELECT id FROM project WHERE name = ? OR id = ?", (proj_name, proj_id)).fetchall()]
for op in old_pids:
    old_vids = [r[0] for r in c.execute("SELECT id FROM video WHERE project_id = ?", (op,)).fetchall()]
    for ov in old_vids:
        c.execute("DELETE FROM request WHERE video_id = ?", (ov,))
        c.execute("DELETE FROM scene WHERE video_id = ?", (ov,))
    c.execute("DELETE FROM request WHERE project_id = ?", (op,))
    c.execute("DELETE FROM video WHERE project_id = ?", (op,))
    c.execute("DELETE FROM project_character WHERE project_id = ?", (op,))
    c.execute("DELETE FROM project WHERE id = ?", (op,))

c.execute("DELETE FROM character WHERE id NOT IN (SELECT character_id FROM project_character)")
conn.commit()
c.execute("PRAGMA foreign_keys = ON;")

story_text = """Lời Nguyền Con Chó Đen Lúc Nửa Đêm — Truyện Kinh Dị Dân Gian
Người dân trong một ngôi làng cổ truyền tai nhau rằng, sau nửa đêm, tuyệt đối không được mở cổng cho bất kỳ con vật nào đứng bên ngoài.
Một đêm nọ, anh Tư đi làm về muộn. Trước cổng làng, anh nhìn thấy một con chó đen đứng bất động giữa màn sương. Nó không sủa, không gầm gừ, chỉ nhìn anh bằng đôi mắt đỏ như than hồng.
Anh Tư vội chạy về nhà, khóa cửa và trùm chăn ngủ. Nhưng đúng lúc ấy, anh nghe thấy tiếng mẹ gọi từ ngoài sân: "Con ơi, mở cửa cho mẹ!"
Anh định mở cửa thì chợt nhớ ra một điều đáng sợ: Mẹ anh đã mất từ ba năm trước."""

# 1. Tạo Project với ID = flow_project_id
c.execute("""
    INSERT INTO project (id, name, description, story, material, status, user_paygate_tier, allow_voice, allow_music, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, 'ACTIVE', 'PAYGATE_TIER_TWO', 1, 1, ?, ?)
""", (
    proj_id, 
    proj_name, 
    "Hoạt hình 2D Người que tối giản tương phản Quái thú dân gian qua Google Flow (Imagen 3 & Veo 3)", 
    story_text, 
    "oversimplified_2d", 
    now, 
    now
))

# 2. Tạo Thực thể (Entities)
char_anh_tu = str(uuid.uuid4())
char_cho_den = str(uuid.uuid4())
loc_cong_lang = str(uuid.uuid4())
loc_gian_nha = str(uuid.uuid4())

# Anh Tư (Người que tối giản chibi OverSimplified)
c.execute("""
    INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    char_anh_tu, "Anh Tư", "anh_tu", "character",
    "Người nông dân trẻ tuổi dáng người que gầy gò, đầu tròn chibi to, mặc áo vải nâu sờn, quần đùi đen, tay chân que mảnh dẻ, nét mặt biến chuyển từ mệt mỏi sang hoảng loạn tột cùng.",
    "Minimalist chibi stick-figure character turnaround model sheet (front, 3/4, side view) on pure solid white background #FFFFFF. Large round white head with expressive round eyes, sweating nervously, flat elliptic bean-shaped torso wearing rustic brown patched tunic, simple black stick-figure line limbs. Pure 2D paper cutout style, thick bold black ink outlines, flat solid colors, shadowless. Strictly NO text, NO labels, NO borders.",
    now, now
))

# Chó Đen Ma Quái (Chỉ mình con quái vật và các chi tiết sinh học ma quái của nó, tuyệt đối không người, không cảnh)
c.execute("""
    INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    char_cho_den, "Chó Đen Ma Quái", "cho_den_ma_quai", "creature",
    "Con chó đen quái thú lớn bất thường với bộ lông xơ xác rậm rạp, đôi mắt đỏ rực như than hồng, hàm răng nanh nhọn hoắt lộ ra trong bóng tối. Độc lập một mình hình ảnh con quái vật và các chi tiết sinh học ma quái của nó, không có bất kỳ con người hay bối cảnh nào.",
    "ONE single isolated black demon dog creature centered on pure solid white background #FFFFFF. High-detail semi-realistic dark fantasy manga anime creature design. Full body profile showing complete grotesque canine anatomy, coarse layered messy matted black fur, razor-sharp white fangs dripping saliva, terrifying glowing crimson red ember eyes with horizontal slit pupils, sharp claws, ominous stance. Pure isolated creature subject only, showcasing fine biological details. Strictly NO people, NO humans, NO stick figures, NO man, NO woman, NO child, NO handlers, NO cage, NO leash, NO background scenery, NO trees, NO text, NO labels, NO borders.",
    now, now
))

# Cổng Làng Cổ Đêm Sương (Tranh thủy mặc / sơn dầu kỹ thuật số)
c.execute("""
    INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    loc_cong_lang, "Cổng Làng Cổ Đêm Sương", "cong_lang_co_dem_suong", "location",
    "Cổng làng cổ bằng gỗ mục ven rừng lúc nửa đêm. Màn sương dày đặc trườn sát mặt đất, một ngọn đèn dầu treo lắt lay chập chờn trên cột gỗ, không gian u tịch lạnh lẽo.",
    "Textured digital ink wash and matte painterly folklore environment of an ancient decaying wooden village gate at midnight. Dense fog creeping along the muddy ground, a solitary flickering oil lantern hung on a weathered wooden post, decaying mossy stone pillars. Cold murky folklore palette of ash gray, midnight cyan and murky brown. Subtle painterly depth. Pure landscape scenery, strictly NO people, NO characters.",
    now, now
))

# Gian Nhà Gỗ Của Anh Tư (Tranh thủy mặc / sơn dầu kỹ thuật số)
c.execute("""
    INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    loc_gian_nha, "Gian Nhà Gỗ Của Anh Tư", "gian_nha_go_anh_tu", "location",
    "Gian nhà gỗ cũ kỹ của Anh Tư trong đêm giông lạnh. Cửa gỗ then cài, vách nứa cũ kỹ in bóng đèn dầu leo lét, sàn đất ẩm ướt.",
    "Textured digital ink wash and matte painterly folklore environment of a rustic decaying Vietnamese wooden village hut interior at night. Weathered wooden door with heavy sliding latch, peeling timber walls, dim warm amber oil lamp casting long eerie shadows. Cold murky folklore tones. Pure interior scenery, strictly NO people, NO characters.",
    now, now
))

# Liên kết Entities vào Project
for eid in [char_anh_tu, char_cho_den, loc_cong_lang, loc_gian_nha]:
    c.execute("INSERT INTO project_character (project_id, character_id) VALUES (?, ?)", (proj_id, eid))

# 3. Tạo Video chính (16:9 Landscape)
c.execute("""
    INSERT INTO video (id, project_id, title, description, display_order, status, orientation, created_at, updated_at)
    VALUES (?, ?, ?, ?, 0, 'DRAFT', 'HORIZONTAL', ?, ?)
""", (vid_id, proj_id, proj_name, "Loạt 6 cảnh hoạt hình 2D Veo 3 chuẩn folklore cutout", now, now))

# 4. Tạo 6 Phân cảnh chuẩn hóa 2D Veo 3 Cutout Puppet Animation
scenes = [
    {
        "order": 0,
        "prompt": "2D minimalist cutout folk animation style, flat chibi stick-figure characters with thick bold black outlines, textured painterly background. Ancient decaying wooden village gate at foggy midnight, thick mist crawling on the ground. A weathered elderly stick-figure villager in gray tunic slowly closes the heavy wooden gate, while a single oil lantern flickers in the eerie cold midnight blue breeze.",
        "video_prompt": (
            "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation, layered puppet joint rotation.\n"
            "0-3s: Wide 2D shot of the ancient wooden gate in thick rolling ground mist, oil lantern swaying gently.\n"
            "3-6s: The camera slowly glides forward in 2D parallax as the elderly stick-figure villager pushes the wooden gate shut with stiff paper-cutout arms.\n"
            "6-8s: The lantern flickers erratically, casting long jagged shadows into the thick ominous fog beyond the gate.\n\n"
            "Audio: eerie night wind howling, creaking wooden gate hinges.\n"
            "SFX: metallic lantern squeak, distant eerie crow call.\n"
            "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
        ),
        "narrator": "Ở ngôi làng này, có một điều cấm kỵ mà không ai dám phá vỡ. Sau nửa đêm, nếu thấy một con chó đen đứng trước cổng… tuyệt đối không được nhìn vào mắt nó.",
        "chars": json.dumps(["Cổng Làng Cổ Đêm Sương"], ensure_ascii=False)
    },
    {
        "order": 1,
        "prompt": "2D minimalist cutout folk animation style. Stark contrast: on the muddy village path covered in creeping fog, flat stick-figure Anh Tư in brown tunic holding a swaying wooden lantern freezes in shock. Directly ahead stands a huge detailed uncanny black dog with coarse matted fur and two glowing crimson ember eyes, staring silently without moving.",
        "video_prompt": (
            "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation.\n"
            "0-3s: Anh Tư walks forward on the muddy path, paper-cutout legs stepping cautiously as his lantern light wobbles.\n"
            "3-6s: He suddenly stops dead in his tracks; in the murky fog ahead, two unblinking crimson eyes ignite in the darkness.\n"
            "6-8s: The massive detailed demon dog slowly tilts its head with unnerving slowness while its four legs remain completely frozen like a statue.\n\n"
            "Audio: dead midnight silence, cold wind whistle, solitary breathing.\n"
            "SFX: squelch of footsteps stopping in mud, low ominous ambient drone.\n"
            "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
        ),
        "narrator": "Đêm ấy, anh Tư trở về muộn. Và nó đang ở đó. Một con chó đen lớn bất thường… đứng ngay giữa đường.",
        "chars": json.dumps(["Anh Tư", "Chó Đen Ma Quái", "Cổng Làng Cổ Đêm Sương"], ensure_ascii=False)
    },
    {
        "order": 2,
        "prompt": "2D minimalist cutout folk animation style. Panic and unnatural pursuit: stick-figure Anh Tư frantically runs through the muddy lane in wild terror. Far behind him, the detailed black dog remains motionless in the fog, but its pitch-black shadow stretches unnaturally long across the ground, creeping rapidly toward him like dark tendrils.",
        "video_prompt": (
            "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation.\n"
            "0-3s: Anh Tư turns around abruptly and sprints away with frantic stick-leg movement, arms pumping in panic.\n"
            "3-6s: Behind him, the stationary demon dog stands still in the mist, but its grotesque black shadow elongates rapidly along the muddy road.\n"
            "6-8s: The jagged ink-black shadow slithers across the puddles, closing the distance toward Anh Tư's heels at unnatural speed.\n\n"
            "Audio: frantic splashing footsteps in mud, ragged gasping breath.\n"
            "SFX: rapid squelch of running in mud, sinister slithering shadow hum.\n"
            "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
        ),
        "narrator": "Anh Tư nhớ lời người già trong làng. Anh quay đầu bỏ chạy. Nhưng có một điều anh không biết… con chó ấy chưa từng di chuyển. Thứ đang đuổi theo anh chỉ là cái bóng của nó.",
        "chars": json.dumps(["Anh Tư", "Chó Đen Ma Quái", "Cổng Làng Cổ Đêm Sương"], ensure_ascii=False)
    },
    {
        "order": 3,
        "prompt": "2D minimalist cutout folk animation style. Claustrophobic dread: inside the dim wooden hut, stick-figure Anh Tư huddles trembling on the wooden floor with wide hollow eyes. Outside the locked wooden door, illuminated through cracks in the wood, a motionless tall dark silhouette stands in the cold mist. Weak yellow lantern light on timber wall.",
        "video_prompt": (
            "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation.\n"
            "0-3s: Inside the dim hut, Anh Tư frantically shoves the wooden crossbar latch shut and backs away, chest heaving in relief.\n"
            "3-6s: Three slow, heavy knocks rap on the outside door: 'Knock... knock... knock'. Anh Tư freezes, trembling stick-figure body stiffening.\n"
            "6-8s: A chillingly gentle woman voice whispers through the wood: 'Tư ơi... mở cửa cho mẹ.' Anh Tư's paper jaw drops in paralyzed horror.\n\n"
            "Audio: tense silent horror atmosphere, muffled rainfall outside.\n"
            "SFX: three hollow wooden knocks, soft eerie whisper, sudden heavy heartbeat.\n"
            "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
        ),
        "narrator": "Anh Tư chết lặng. Giọng nói ấy dịu dàng đến mức anh suýt quên mất… người đang gọi mình không thể còn sống.",
        "chars": json.dumps(["Anh Tư", "Gian Nhà Gỗ Của Anh Tư"], ensure_ascii=False)
    },
    {
        "order": 4,
        "prompt": "2D minimalist cutout folk animation style. Terrifying realization: stick-figure Anh Tư's trembling black stick hand reaches toward the wooden latch then halts in mid-air. Underneath the bottom door gap, two pale barefoot human feet stand on the muddy ground, but the giant shadow cast onto the interior wall has the distinct monstrous shape of a wolf-dog with sharp bared fangs.",
        "video_prompt": (
            "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation.\n"
            "0-3s: Anh Tư's hand hovers an inch from the latch, sweat beads bursting from his forehead as realization dawns.\n"
            "3-6s: Camera tilts down to the door slit: two human feet stand outside, but the lantern shadow cast on the timber planks is a vicious demonic dog silhouette.\n"
            "6-8s: The lantern suddenly blows out into blackness; through the cracks in the door, two fierce glowing crimson eyes ignite, staring straight at the viewer.\n\n"
            "Audio: sudden dissonant violin screech, deep folklore horror bass drop.\n"
            "SFX: lantern flame snuffed out whoosh, low menacing beast growl.\n"
            "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
        ),
        "narrator": "Mẹ anh đã mất ba năm trước. Và ngay lúc ấy, anh Tư nhận ra… thứ ngoài cửa không muốn vào nhà. Nó muốn anh tự bước ra ngoài.",
        "chars": json.dumps(["Anh Tư", "Chó Đen Ma Quái", "Gian Nhà Gỗ Của Anh Tư"], ensure_ascii=False)
    },
    {
        "order": 5,
        "prompt": "2D minimalist cutout folk animation style. Eerie aftermath: daylight breaks over the ancient village in pale misty gray tones. Outside the empty hut, the wooden door remains locked from inside. On the muddy road leading toward the foggy village gate, a single line of human footprints abruptly turns into canine paw prints, where two motionless black dogs with glowing red eyes now stand side-by-side in the mist.",
        "video_prompt": (
            "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation.\n"
            "0-3s: Pale cold morning light reveals the intact locked hut door, camera pans down to muddy footprints leading away into the sylvan fog.\n"
            "3-6s: The camera follows the tracks to the village gate where two identical uncanny black dogs now sit side by side in absolute stillness.\n"
            "6-8s: Slow 2D push-in on the second dog's face as its crimson eyes flash brightly in the thick fog, before a sudden hard cut to black.\n\n"
            "Audio: mournful morning fog wind, distant temple bell chiming softly.\n"
            "SFX: wind rustle through dead leaves, sudden sharp cut to silence.\n"
            "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
        ),
        "narrator": "Sáng hôm sau, không ai tìm thấy anh Tư. Chỉ có một điều khiến dân làng khiếp sợ… Từ đêm đó, trước cổng làng xuất hiện thêm một con chó đen.",
        "chars": json.dumps(["Chó Đen Ma Quái", "Cổng Làng Cổ Đêm Sương"], ensure_ascii=False)
    }
]

for sc in scenes:
    sid = str(uuid.uuid4())
    c.execute("""
        INSERT INTO scene (id, video_id, display_order, prompt, image_prompt, video_prompt, narrator_text, character_names, chain_type, source, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ROOT', 'user', ?, ?)
    """, (sid, vid_id, sc["order"], sc["prompt"], sc["prompt"], sc["video_prompt"], sc["narrator"], sc["chars"], now, now))

conn.commit()
conn.close()

# 5. Cập nhật active_project.json với đúng UUID của Google Flow
active_data = {
    "project_id": proj_id,
    "video_id": vid_id,
    "project_name": proj_name
}
for p in [ROOT / "agent" / "active_project.json", ROOT / "active_project.json"]:
    p.write_text(json.dumps(active_data, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n🎉 ĐÃ ĐỒNG BỘ HOÀN TOÀN UUID DỰ ÁN VỚI GOOGLE FLOW:")
print(f"  - Tên dự án:    {proj_name}")
print(f"  - Project UUID: {proj_id} (Trùng khớp 100% với FLOW_PROJECT_ID trên Google Flow)")
print(f"  - Video ID:     {vid_id}")
print(f"  - Thực thể (4): Anh Tư, Chó Đen Ma Quái (Chỉ mình quái vật), Cổng Làng Cổ, Gian Nhà Gỗ")
print(f"  - Phân cảnh:    6 cảnh chuẩn OverSimplified 2D & Veo 3")
