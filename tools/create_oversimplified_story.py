#!/usr/bin/env python3
"""Tạo dự án mẫu Hoạt hình 2D Người Que Tối Giản / Kinh Dị Dân Gian chuẩn hóa 100% bằng Google Flow.

Chuẩn hóa 4 tiêu chí cốt lõi:
1. Nhân vật người que tối giản (Stick figure / Minimalist Chibi)
2. Tương phản dị biệt với quái thú (Uncanny Contrast: Manga/Anime bán thực tế chi tiết ma quái tùy theo loài thú như chó, gà, mèo, lợn, dê... không bắt buộc có sừng)
3. Bối cảnh tranh thủy mặc / sơn dầu kỹ thuật số (Textured painterly background)
4. Màu sắc lạnh lẽo u ám (Cold & Murky) kết hợp chuyển động cắt dán 2D (Cutout Puppet Animation)
"""
import json
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

conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

proj_name = "Con Dê Già Trong Chuồng Củi (Hoạt Hình 2D Kinh Dị Dân Gian)"

# Kiểm tra nếu dự án đã tồn tại
existing = c.execute("SELECT id FROM project WHERE name = ?", (proj_name,)).fetchone()
if existing:
    print(f"[*] Dự án đã tồn tại với ID: {existing[0]}")
    proj_id = existing[0]
else:
    proj_id = str(uuid.uuid4())
    vid_id = str(uuid.uuid4())
    now = "2026-10-19T22:00:00Z"

    story_text = """Con Dê Già Trong Chuồng Củi — Truyện Kinh Dị Dân Gian
Đêm hôm đó, giữa cơn mưa bão xối xả, Lão Tam bước vào chuồng củi và nhận ra con dê già đang nhìn mình với ánh mắt của loài quỷ dữ.
Từng bước chân của con quái thú nặng nề giẫm lên bùn đất, bóp nghẹt mọi hy vọng trốn chạy của người nông dân tội nghiệp.
Ngọn lửa bốc cháy dữ dội thiêu rụi cả gian chuồng củi, nhưng bóng đen quỷ dị của con quái vật vẫn sừng sững giữa biển lửa."""

    # 1. Tạo Project
    c.execute("""
        INSERT INTO project (id, name, description, story, material, status, user_paygate_tier, allow_voice, allow_music, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'ACTIVE', 'PAYGATE_TIER_TWO', 1, 1, ?, ?)
    """, (proj_id, proj_name, "Hoạt hình 2D Người que tối giản tương phản Quái thú dân gian qua Google Flow (Imagen 3 & Veo 3)", story_text, "oversimplified_2d", now, now))

    # 2. Tạo Thực thể (Entities): Nhân vật người que & Quái thú tương phản
    char_lao_tam = str(uuid.uuid4())
    char_de_gia = str(uuid.uuid4())
    loc_chuong_cui = str(uuid.uuid4())

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

    # Con Dê Già (Quái thú chi tiết sắc lạnh - Uncanny Contrast)
    c.execute("""
        INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        char_de_gia, "Con Dê Già", "con_de_gia", "creature",
        "Quái vật con dê già ma quái trong chuồng củi. Trái ngược hoàn toàn với người que, con dê được vẽ theo phong cách bán thực tế manga chi tiết rùng rợn: bộ lông xơ xác vương bùn đất, đôi sừng dài nhọn vân xoắn đen kịt, ánh mắt đỏ quỷ dị với đồng tử nằm ngang ghê rợn.",
        "Dark uncanny demon goat creature model sheet on pure solid white background #FFFFFF. High-detail semi-realistic dark fantasy manga anime style, coarse layered dirty matted gray fur, long sharp ridged black twisted horns, terrifying horizontal-slit demonic pupils glowing sinister crimson red. Extreme uncanny contrast against minimalist characters. Strictly NO text, NO labels, NO borders.",
        now, now
    ))

    # Chuồng Củi Đêm Lạnh (Tranh thủy mặc / sơn dầu kỹ thuật số)
    c.execute("""
        INSERT INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        loc_chuong_cui, "Chuồng Củi Đêm Mưa", "chuong_cui_dem_mua", "location",
        "Bối cảnh chuồng củi cũ kỹ ven rừng trong đêm mưa lạnh lẽo. Tranh thủy mặc kết hợp sơn dầu kỹ thuật số: vách gỗ mọt nứt nẻ, mái rơm dột ướt, sàn đất bùn nhão, tông màu u ám xám tro và xanh lam đêm huyền bí. Pure scenery only, strictly NO people, NO characters.",
        "Textured digital ink wash and matte painterly folklore environment of a decaying rustic wooden firewood shed at stormy night. Weathered rotten wood textures, cracked timber walls, mud floor, cold murky folklore palette of ash gray, midnight cyan and earthy brown. Subtle painterly depth. Strictly pure scenery, landscape only, strictly NO people, NO characters.",
        now, now
    ))

    # Liên kết Entities vào Project
    for eid in [char_lao_tam, char_de_gia, loc_chuong_cui]:
        c.execute("INSERT INTO project_character (project_id, character_id) VALUES (?, ?)", (proj_id, eid))

    # 3. Tạo Video chính (16:9 Landscape)
    c.execute("""
        INSERT INTO video (id, project_id, title, description, display_order, status, orientation, created_at, updated_at)
        VALUES (?, ?, ?, ?, 0, 'DRAFT', 'HORIZONTAL', ?, ?)
    """, (vid_id, proj_id, proj_name, "Loạt cảnh hoạt hình 2D Veo 3 chuẩn folklore cutout", now, now))

    # 4. Tạo các Scene chuẩn 2D Veo 3 Cutout Puppet Animation
    scenes = [
        {
            "order": 0,
            "prompt": "2D minimalist cutout folk animation style, flat chibi stick-figure characters with thick bold black outlines, textured painterly background. In the decaying wooden firewood shed, Lão Tam holding a wooden oil lantern trembles in terror, staring at the dark corner where two eerie crimson goat eyes glow in the shadows. Cold murky folklore tones.",
            "video_prompt": (
                "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation, layered puppet joint rotation, intentional slightly rigid folk paper puppet movement, eerie folklore mystery pacing.\n"
                "0-3s: The 2D cutout scene opens in the decaying shed, Lão Tam holds up an oil lantern with trembling stick arms, rain pounding against rotting wooden planks.\n"
                "3-6s: In the murky darkness, two horizontal-slit crimson eyes suddenly open, gleaming with sinister malice.\n"
                "6-8s: Lão Tam's paper cutout jaw drops in sheer terror, cartoon sweat droplets bursting from his round white head.\n\n"
                "Audio: rainstorm howling outside, creaking wooden planks.\n"
                "SFX: cold wind howling, sudden terrifying low goat growl.\n"
                "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
            ),
            "narrator": "Đêm hôm đó, giữa cơn mưa bão xối xả, Lão Tam bước vào chuồng củi và nhận ra con dê già đang nhìn mình với ánh mắt của loài quỷ dữ.",
            "chars": json.dumps(["Lão Tam", "Con Dê Già", "Chuồng Củi Đêm Mưa"], ensure_ascii=False)
        },
        {
            "order": 1,
            "prompt": "2D minimalist cutout folk animation style. Close-up contrast: the detailed demonic goat with razor-sharp ridged horns and eerie red slit pupils steps forward from the shadows, looming over the terrified flat stick-figure Lão Tam who stumbles backward onto the muddy ground.",
            "video_prompt": (
                "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation, layered puppet joint rotation, intentional slightly rigid folk paper puppet movement.\n"
                "0-3s: The terrifying detailed demon goat steps slowly forward into the dim lantern light, coarse fur rustling, long ridged horns casting a jagged silhouette.\n"
                "3-6s: Lão Tam trips backward with rigid cutout leg movement, stick arms flailing in desperate panic.\n"
                "6-8s: The beast lowers its head, mouth opening slightly as dark breath steams into the cold night air.\n\n"
                "Audio: tense folklore horror drone, heavy rhythmic hoof beats on mud.\n"
                "SFX: mud splash, deep guttural breathing.\n"
                "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
            ),
            "narrator": "Từng bước chân của con quái thú nặng nề giẫm lên bùn đất, bóp nghẹt mọi hy vọng trốn chạy của người nông dân tội nghiệp.",
            "chars": json.dumps(["Lão Tam", "Con Dê Già", "Chuồng Củi Đêm Mưa"], ensure_ascii=False)
        },
        {
            "order": 2,
            "prompt": "2D minimalist cutout folk animation style. High-contrast climax: harsh fiery amber-orange flames suddenly erupt across the wooden firewood shed, blazing violently against the cold midnight blue shadows as Lão Tam flees frantically into the rain.",
            "video_prompt": (
                "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows. 2D cutout puppet animation, layered puppet joint rotation.\n"
                "0-3s: Harsh fiery amber-orange flames burst across the dry wood stacks, casting sharp flickering illumination against the midnight blue walls.\n"
                "3-6s: Lão Tam scrambles out the door with frantic paper puppet running motion, disappearing into the torrential downpour.\n"
                "6-8s: In the heart of the blazing fire, the dark silhouette of the goat stands motionless, unharmed, glowing with red demonic eyes.\n\n"
                "Audio: roaring crackle of intense fire contrasting with driving rain.\n"
                "SFX: fire whoosh, torrential thunder strike.\n"
                "Negative: 3D render, photorealistic, realistic human skin, CGI depth, subtitles, watermark, text overlay."
            ),
            "narrator": "Ngọn lửa bốc cháy dữ dội thiêu rụi cả gian chuồng củi, nhưng bóng đen quỷ dị của con quái vật vẫn sừng sững giữa biển lửa.",
            "chars": json.dumps(["Lão Tam", "Con Dê Già", "Chuồng Củi Đêm Mưa"], ensure_ascii=False)
        }
    ]

    for sc in scenes:
        sid = str(uuid.uuid4())
        c.execute("""
            INSERT INTO scene (id, video_id, display_order, prompt, image_prompt, video_prompt, narrator_text, character_names, chain_type, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ROOT', 'user', ?, ?)
        """, (sid, vid_id, sc["order"], sc["prompt"], sc["prompt"], sc["video_prompt"], sc["narrator"], sc["chars"], now, now))

    conn.commit()
    print(f"✅ Đã tạo thành công dự án Hoạt hình 2D Người que & Quái thú dân gian!")
    print(f"  - Project ID: {proj_id}")
    print(f"  - Video ID:   {vid_id}")
    print(f"  - Thực thể:   Lão Tam (Người que), Con Dê Già (Manga chi tiết), Chuồng Củi Đêm Mưa (Sơn dầu thủy mặc)")
    print(f"  - Phân cảnh:  3 cảnh chuẩn Veo 3 2D Cutout Puppet Animation")

conn.close()
