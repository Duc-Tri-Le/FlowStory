"""Set up project entities and scenes for 'cậu bé và cô bé' (id: 662aacf3-af1f-4dd1-a40f-7efff09b2211)."""

import json
import sqlite3

PROJECT_ID = "662aacf3-af1f-4dd1-a40f-7efff09b2211"
VIDEO_ID = "b389e02d-84ea-487e-85a7-6ac966f8f8eb"

db_path = "/home/ductri/flowkit/flow_agent.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Update project story and description
print("1. Updating project description and story...")
cur.execute("""
    UPDATE project 
    SET description = ?, language = 'vi', material = 'realistic', updated_at = datetime('now')
    WHERE id = ?
""", ("Câu chuyện làng quê Việt Nam: Cậu bé sút bóng vô tình trúng đầu cô bé và chạy sang đỡ bạn dậy xin lỗi.", PROJECT_ID))
conn.commit()

entities = [
    {
        "id": "char-caube-01",
        "name": "Cậu Bé",
        "slug": "cau-be",
        "entity_type": "character",
        "description": "8-year-old Vietnamese rural boy, short messy dark hair, tanned skin, wearing faded blue t-shirt and dark shorts, barefoot or slippers, energetic and playful expression.",
        "image_prompt": "Real RAW photograph, shot on Canon EOS R5, 35mm lens, natural available light. Full body portrait of an 8-year-old Vietnamese rural boy, short messy dark hair, tanned skin, wearing faded blue t-shirt and dark shorts, standing on dirt ground in a rustic Vietnamese village path. Centered, front-facing view, looking directly at camera, neutral simple background, natural proportions. ONE single image only.",
    },
    {
        "id": "char-cobe-01",
        "name": "Cô Bé",
        "slug": "co-be",
        "entity_type": "character",
        "description": "7-year-old Vietnamese rural girl, hair in two neat low pigtails, round innocent face, wearing a floral cotton short-sleeve shirt and dark cotton shorts, sweet gentle appearance.",
        "image_prompt": "Real RAW photograph, shot on Canon EOS R5, 35mm lens, natural available light. Full body portrait of a 7-year-old Vietnamese rural girl, hair in two neat low pigtails, round innocent face, wearing a floral cotton short-sleeve shirt and dark cotton shorts, standing in a rustic garden path. Centered, front-facing view, looking directly at camera, neutral simple background. ONE single image only.",
    },
    {
        "id": "loc-langque-01",
        "name": "Làng Quê Việt Nam",
        "slug": "lang-que-viet-nam",
        "entity_type": "location",
        "description": "Peaceful Vietnamese countryside path with weathered red brick wall, banana plants, lush green bamboo groves, warm golden sunlight. PURE SCENERY, EMPTY ENVIRONMENT, NO PEOPLE, NO CHARACTERS.",
        "image_prompt": "Real RAW photograph, shot on Canon EOS R5, 35mm lens, natural available light. Establishing wide shot showing a peaceful Vietnamese countryside lane with a weathered red brick garden wall, banana trees, dirt path, and lush green bamboo grove under warm golden afternoon sunlight. Atmospheric and richly detailed, show depth. Pure scenery, empty environment, absolutely NO people, NO characters.",
    },
    {
        "id": "asset-quabong-01",
        "name": "Quả Bóng",
        "slug": "qua-bong",
        "entity_type": "visual_asset",
        "description": "A slightly worn classic black and white patterned soccer ball resting on rural dirt ground.",
        "image_prompt": "Real RAW photograph, shot on Canon EOS R5, 35mm lens, natural available light. Clear detailed shot of a slightly worn classic black and white patterned soccer ball resting on dry rural dirt ground. Appropriate angle showing complete form and surface texture. Neutral simple background, no people.",
    },
]

for e in entities:
    # Insert or replace character
    cur.execute(
        """
        INSERT OR REPLACE INTO character (id, name, slug, entity_type, description, image_prompt, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """,
        (
            e["id"],
            e["name"],
            e["slug"],
            e["entity_type"],
            e["description"],
            e["image_prompt"],
        ),
    )
    # Link to project
    cur.execute(
        """
        INSERT OR IGNORE INTO project_character (project_id, character_id)
        VALUES (?, ?)
    """,
        (PROJECT_ID, e["id"]),
    )
    print(f"  + Entity created & linked: {e['name']} ({e['entity_type']})")

conn.commit()

# 3. Create Scenes
scenes = [
    {
        "id": "scene-cb-01",
        "video_id": VIDEO_ID,
        "display_order": 0,
        "prompt": "Real RAW photograph, shot on Canon EOS R5, 35mm lens. In Làng Quê Việt Nam village path, Cậu Bé kicks the Quả Bóng with full power, launching the ball soaring over a weathered red brick wall into an adjoining yard. Action shot, dynamic motion blur, sunny afternoon.",
        "image_prompt": "A young Vietnamese boy kicking a soccer ball over a weathered brick wall in a rustic Vietnamese village path with banana trees and warm sunlight.",
        "video_prompt": "0-3s: Cậu Bé winds up his foot and forcefully kicks the Quả Bóng. The camera tracks the ball rising high, arching gracefully over the rustic brick wall and disappearing into the garden beyond. Warm natural afternoon lighting, dust kicking up from the dirt ground.",
        "narrator_text": "Buổi chiều êm đềm ở làng quê, cậu bé đang mải mê chơi bóng thì lỡ chân sút một cú cực mạnh bay qua bờ tường.",
        "duration": 3,
        "character_names": json.dumps(
            ["Cậu Bé", "Quả Bóng", "Làng Quê Việt Nam"]
        ),
        "chain_type": "ROOT",
    },
    {
        "id": "scene-cb-02",
        "video_id": VIDEO_ID,
        "display_order": 1,
        "prompt": "Real RAW photograph, shot on Canon EOS R5, 35mm lens. In the rustic garden courtyard on the other side of the brick wall, the soccer ball hits Cô Bé, causing her to tumble onto the grass, tearful and crying holding her forehead. Làng Quê Việt Nam garden setting.",
        "image_prompt": "A sweet young Vietnamese girl in a floral shirt falling onto grassy ground in a village garden, rubbing her head and starting to cry as a soccer ball bounces nearby.",
        "video_prompt": "0-3s: The soccer ball drops from above and bumps Cô Bé gently on the head. She loses balance and sits down on the soft grass, rubbing her forehead with tears welling in her eyes, crying in surprise. Golden sunlight filtering through tree leaves.",
        "narrator_text": "Không may, quả bóng rơi trúng đầu cô bé hàng xóm khiến cô bé ngã xuống và bật khóc nức nở.",
        "duration": 3,
        "character_names": json.dumps(
            ["Cô Bé", "Quả Bóng", "Làng Quê Việt Nam"]
        ),
        "chain_type": "ROOT",
    },
    {
        "id": "scene-cb-03",
        "video_id": VIDEO_ID,
        "display_order": 2,
        "prompt": "Real RAW photograph, shot on Canon EOS R5, 35mm lens. Cậu Bé rushes through the wooden gate into the garden, kneeling down beside Cô Bé, gently offering a hand to help her up, with a remorseful, apologetic and caring expression. Làng Quê Việt Nam garden.",
        "image_prompt": "A young Vietnamese boy kneeling beside a crying little girl in a rural garden, gently helping her up with an apologetic expression.",
        "video_prompt": "0-3s: Cậu Bé dashes in through the wooden gate, panic on his face. He quickly kneels down next to Cô Bé, gently dusting off her shoulder and offering his hand to help her stand, speaking comforting apologies. Her crying softens into a sniffle.",
        "narrator_text": "Biết mình gây họa, cậu bé hốt hoảng chạy ngay sang đỡ cô bé dậy và liên tục cúi đầu xin lỗi.",
        "duration": 3,
        "character_names": json.dumps(["Cậu Bé", "Cô Bé", "Làng Quê Việt Nam"]),
        "chain_type": "CONTINUATION",
    },
]

for s in scenes:
    cur.execute(
        """
        INSERT OR REPLACE INTO scene (
            id, video_id, display_order, prompt, image_prompt, video_prompt,
            narrator_text, duration, character_names, chain_type, source,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'user', datetime('now'), datetime('now'))
    """,
        (
            s["id"],
            s["video_id"],
            s["display_order"],
            s["prompt"],
            s["image_prompt"],
            s["video_prompt"],
            s["narrator_text"],
            s["duration"],
            s["character_names"],
            s["chain_type"],
        ),
    )
    print(f"  + Scene {s['display_order'] + 1} created: {s['narrator_text'][:50]}...")

conn.commit()
conn.close()
print("Setup complete!")
