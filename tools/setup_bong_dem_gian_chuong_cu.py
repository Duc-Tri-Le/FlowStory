#!/usr/bin/env python3
"""Xóa toàn bộ các dự án cũ và chỉ giữ lại / tạo mới duy nhất dự án:
'Bóng Đêm Gian Chuồng Cũ (Hoạt Hình 2D Dân Gian)'
chuẩn 4 tiêu chí OverSimplified 2D & Uncanny Contrast.
"""
import json
import sqlite3
import uuid
import sys
import shutil
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "flow_agent.db"
OUTPUT_DIR = ROOT / "output"

def clean_database():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    tables = ["request", "scene", "video", "project_character", "project", "character"]
    print("--- Đang xóa toàn bộ dữ liệu dự án cũ ---")
    conn.execute("PRAGMA foreign_keys = OFF;")
    for t in tables:
        c.execute(f"DELETE FROM {t};")
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.execute("VACUUM;")
    except Exception as e:
        print(f"Vacuum note: {e}")

    conn.close()
    print("✅ Đã dọn sạch database.")

def create_target_project():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    proj_name = "Bóng Đêm Gian Chuồng Cũ (Hoạt Hình 2D Dân Gian)"
    proj_id = str(uuid.uuid4())
    vid_id = str(uuid.uuid4())
    now = "2026-10-20T02:00:00Z"

    story_text = """Bóng Đêm Gian Chuồng Cũ — Truyện Kinh Dị Dân Gian
Đêm hôm đó, giữa cơn mưa bão xối xả, Lão Tam nghe thấy tiếng cào xé kỳ lạ phát ra sau gian chuồng cũ.
Cầm ngọn đèn dầu rọi vào bóng tối, ông bàng hoàng nhận ra đôi mắt đỏ quỷ dị của con quái thú đang nhìn mình trừng trừng!
Con quái thú nhe hàm nanh sắc nhọn gầm lên một tiếng rùng rợn, xé toạc màn mưa đêm giông bão!
Lão Tam hốt hoảng vứt cả chiếc đèn dầu, cuống cuồng tháo chạy trong nỗi kinh hoàng tột độ!"""

    # 1. Tạo Project
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

    # 2. Tạo Thực thể (Entities): Lão Tam, Quái Thú Gian Chuồng, Gian Chuồng Cũ
    char_lao_tam = str(uuid.uuid4())
    char_quai_thu = str(uuid.uuid4())
    loc_chuong_cu = str(uuid.uuid4())

    # Lão Tam (Người que tối giản chibi)
    c.execute("""
        INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        char_lao_tam, "Lão Tam", "lao_tam", "character",
        "Người nông dân trung niên dáng người que gầy gò, đầu tròn chibi to, mặc áo nâu sờn vá vai, quần đùi đen, tay chân que, nét mặt hốc hác đầy vẻ kinh hoàng bất an.",
        "Minimalist chibi stick-figure character turnaround model sheet (front, 3/4, side view) on pure solid white background #FFFFFF. Large round white head, anxious hollow dark circle eyes, sweating nervously, flat elliptic bean torso wearing patched dark brown rustic tunic, simple black stick-figure line limbs. Pure 2D paper cutout style, thick bold black outlines, flat solid colors, shadowless. Strictly NO text, NO labels, NO borders.",
        now, now
    ))

    # Quái Thú Gian Chuồng Cũ (Manga bán thực tế chi tiết sắc lạnh - Uncanny Contrast)
    c.execute("""
        INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        char_quai_thu, "Quái Thú Gian Chuồng Cũ", "quai_thu_gian_chuong_cu", "creature",
        "Quái thú bóng đêm ẩn náu sau gian chuồng cũ. Trái ngược hoàn toàn với người que, con quái thú được vẽ theo phong cách bán thực tế manga chi tiết rùng rợn: bộ lông bết dính bùn đất, đôi nanh nhọn hoắt rỉ nước dãi, hàm răng lởm chởm và đôi mắt đỏ quỷ dị phát sáng trong bóng tối.",
        "Dark uncanny shadow beast creature model sheet on pure solid white background #FFFFFF. High-detail semi-realistic dark fantasy manga anime style, coarse layered dirty matted black fur, sharp dripping fangs, terrifying unearthly glowing crimson eyes. Extreme uncanny contrast against minimalist stick-figure characters. Strictly NO text, NO labels, NO borders.",
        now, now
    ))

    # Gian Chuồng Cũ Đêm Mưa (Tranh thủy mặc / sơn dầu kỹ thuật số u ám)
    c.execute("""
        INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        loc_chuong_cu, "Gian Chuồng Cũ Đêm Mưa", "gian_chuong_cu_dem_mua", "location",
        "Bối cảnh gian chuồng củi cũ kỹ ven rừng trong đêm mưa lạnh lẽo. Tranh thủy mặc kết hợp sơn dầu kỹ thuật số: vách gỗ mọt nứt nẻ, mái rơm dột ướt, sàn đất bùn nhão, tông màu u ám xám tro và xanh lam đêm huyền bí. Pure scenery only, strictly NO people, NO characters.",
        "Textured digital ink wash and matte painterly folklore environment of a decaying rustic wooden barn shed at stormy night. Weathered rotten wood textures, cracked timber walls, mud floor, cold murky folklore palette of ash gray, midnight cyan and earthy brown. Subtle painterly depth. Strictly pure scenery, landscape only, strictly NO people, NO characters.",
        now, now
    ))

    # Liên kết Entities vào Project
    for eid in [char_lao_tam, char_quai_thu, loc_chuong_cu]:
        c.execute("INSERT INTO project_character (project_id, character_id) VALUES (?, ?)", (proj_id, eid))

    # 3. Tạo Video chính (16:9 Landscape)
    c.execute("""
        INSERT INTO video (id, project_id, title, description, display_order, status, orientation, created_at, updated_at)
        VALUES (?, ?, ?, ?, 0, 'DRAFT', 'HORIZONTAL', ?, ?)
    """, (vid_id, proj_id, proj_name, "Loạt cảnh hoạt hình 2D Veo 3 chuẩn folklore cutout", now, now))

    # 4. Tạo các Phân cảnh (Scenes)
    scenes = [
        {
            "order": 0,
            "prompt": "2D minimalist cutout folk animation style, flat chibi stick-figure characters with thick bold black outlines, textured painterly background. In the decaying wooden barn shed, Lão Tam holding a wooden oil lantern trembles in terror, staring at the dark corner where two eerie crimson beast eyes glow in the shadows. Cold murky folklore tones.",
            "video_prompt": (
                "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation, layered puppet joint rotation, intentional slightly rigid folk paper puppet movement, eerie folklore mystery pacing.\n"
                "0-3s: The 2D cutout scene opens in the decaying shed, Lão Tam holds up an oil lantern with trembling stick arms, rain pounding against rotting wooden planks.\n"
                "3-6s: In the murky darkness, two crimson eyes suddenly open, gleaming with sinister malice.\n"
                "6-8s: Lão Tam's paper cutout jaw drops in sheer terror, cartoon sweat droplets bursting from his round white head.\n\n"
                "Audio: rainstorm howling outside, creaking wooden planks.\n"
                "SFX: cold wind howling, sudden terrifying low growl.\n"
                "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
            ),
            "narrator": "Đêm hôm đó, giữa cơn mưa bão xối xả, Lão Tam nghe thấy tiếng cào xé kỳ lạ phát ra sau gian chuồng cũ.",
            "chars": json.dumps(["Lão Tam", "Quái Thú Gian Chuồng Cũ", "Gian Chuồng Cũ Đêm Mưa"], ensure_ascii=False)
        },
        {
            "order": 1,
            "prompt": "2D minimalist cutout folk animation style. Close-up contrast: the detailed shadow beast with razor-sharp fangs and eerie red glowing eyes steps forward from the shadows, looming over the terrified flat stick-figure Lão Tam who stumbles backward onto the muddy ground.",
            "video_prompt": (
                "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation, layered puppet joint rotation, intentional slightly rigid folk paper puppet movement.\n"
                "0-3s: The terrifying detailed shadow beast steps slowly forward into the dim lantern light, coarse fur rustling, dripping fangs gleaming in the gloom.\n"
                "3-6s: Lão Tam trips backward with rigid cutout leg movement, stick arms flailing in desperate panic.\n"
                "6-8s: The beast snarls, red eyes blazing with predatory hunger.\n\n"
                "Audio: tense folklore horror drone, heavy rhythmic paw steps on mud.\n"
                "SFX: mud splash, deep guttural snarl.\n"
                "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
            ),
            "narrator": "Cầm ngọn đèn dầu rọi vào bóng tối, ông bàng hoàng nhận ra đôi mắt đỏ quỷ dị của con quái thú đang nhìn mình trừng trừng!",
            "chars": json.dumps(["Lão Tam", "Quái Thú Gian Chuồng Cũ", "Gian Chuồng Cũ Đêm Mưa"], ensure_ascii=False)
        },
        {
            "order": 2,
            "prompt": "2D minimalist cutout folk animation style. Intense confrontation: the grotesque beast roars violently into the storm, sharp fangs bared, saliva spraying, while lightning strikes outside illuminating the wooden shed in cold cyan flashes.",
            "video_prompt": (
                "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation, layered puppet joint rotation.\n"
                "0-3s: Lightning flashes through cracks in the wooden wall, lighting up the horrifying detailed maw of the beast.\n"
                "3-6s: The beast lets out an earth-shattering roar, soundwaves vibrating the dim lantern light.\n"
                "6-8s: Thunder roars outside, rain pouring violently through the roof.\n\n"
                "Audio: deafening thunderclap, visceral monstrous roar.\n"
                "SFX: thunder strike, roaring beast, rain deluge.\n"
                "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
            ),
            "narrator": "Con quái thú nhe hàm nanh sắc nhọn gầm lên một tiếng rùng rợn, xé toạc màn mưa đêm giông bão!",
            "chars": json.dumps(["Lão Tam", "Quái Thú Gian Chuồng Cũ", "Gian Chuồng Cũ Đêm Mưa"], ensure_ascii=False)
        },
        {
            "order": 3,
            "prompt": "2D minimalist cutout folk animation style. Climax escape: Lão Tam drops his wooden lantern to the ground, turning and frantically sprinting out of the barn door into the dark stormy rain as the beast leaps forward from the shadows.",
            "video_prompt": (
                "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation, layered puppet joint rotation.\n"
                "0-3s: The lantern smashes on the mud floor, fire flickering briefly before dying.\n"
                "3-6s: Lão Tam scrambles out the door with frantic paper puppet running motion, disappearing into the torrential downpour.\n"
                "6-8s: The beast lunges into the doorway, staring into the dark stormy night with glowing crimson eyes.\n\n"
                "Audio: frantic running footsteps splashing in mud, heavy rain.\n"
                "SFX: glass smash, wind rush, distant screams.\n"
                "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
            ),
            "narrator": "Lão Tam hốt hoảng vứt cả chiếc đèn dầu, cuống cuồng tháo chạy trong nỗi kinh hoàng tột độ!",
            "chars": json.dumps(["Lão Tam", "Quái Thú Gian Chuồng Cũ", "Gian Chuồng Cũ Đêm Mưa"], ensure_ascii=False)
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

    # 5. Cập nhật active_project.json
    active_data = {
        "project_id": proj_id,
        "video_id": vid_id,
        "project_name": proj_name
    }
    for p in [ROOT / "agent" / "active_project.json", ROOT / "active_project.json"]:
        p.write_text(json.dumps(active_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n🎉 ĐÃ THIẾT LẬP THÀNH CÔNG DỰ ÁN DUY NHẤT:")
    print(f"  - Tên dự án: {proj_name}")
    print(f"  - Project ID: {proj_id}")
    print(f"  - Video ID:   {vid_id}")
    print(f"  - Thực thể (3): Lão Tam, Quái Thú Gian Chuồng Cũ, Gian Chuồng Cũ Đêm Mưa")
    print(f"  - Phân cảnh: 4 phân cảnh hoàn chỉnh chuẩn OverSimplified 2D & Veo 3")

if __name__ == "__main__":
    clean_database()
    create_target_project()
