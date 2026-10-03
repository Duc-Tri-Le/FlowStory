import urllib.request
import json

vid = "5dd13489-bde7-4856-a65c-ff87b0da775a"
scenes = [
    {
        "display_order": 0,
        "duration": 4.0,
        "character_names": ["Husband", "Wife", "Living Room", "DNA Test Paper"],
        "chain_type": "ROOT",
        "prompt": "Vertical 9:16, cinematic realistic drama, cold moody color grade. Extreme close-up, top-down angle tilted 15 degrees, on the DNA test paper in the center of the glass coffee table. The husband's right hand slams down on the paper from the right side of frame, the cold teacup on the table rattles. Wife's blurred shape sits on the sofa at the far left edge.",
        "video_prompt": """Extreme close-up, top-down angle tilted 15 degrees, on the DNA test paper in the center of the glass table. The husband's right hand slams down firmly on the paper from the right side of frame, causing the teacup on the table to rattle. Wife's blurred shape sits motionless on the sofa at the far left edge. Camera holds still. Husband off-screen says in an angry, gritted voice: "Kết quả xét nghiệm đã có rồi. Cả hai đứa trẻ đều không phải con tôi." (no subtitles) Half a second of tense silence follows. Cold moody lighting.

Audio: off-screen male voice, natural room silence.
SFX: loud hand slam on table, teacup rattling on glass.
Negative: subtitles, watermark, text overlay."""
    },
    {
        "display_order": 1,
        "duration": 4.0,
        "character_names": ["Husband", "Wife", "Living Room"],
        "chain_type": "ROOT",
        "prompt": "Vertical 9:16, cinematic realistic drama, cold moody color grade. Low angle shot looking up at the husband standing behind the coffee table on the RIGHT side of frame, facing left toward his wife. The wife's shoulder is blurred at the left edge of frame in over-the-shoulder view. Dramatic lamp shadows across his face, red eyes and stubble visible.",
        "video_prompt": """Low angle shot looking up at the husband standing behind the glass coffee table on the right side of frame, facing left toward his wife. The wife's shoulder is blurred at the left edge of frame in an over-the-shoulder composition. The camera slowly pushes in toward his furious eyes. Dramatic lamp shadows fall across his face. Husband growls in a low tone: "Cô còn gì để nói nữa không?" (no subtitles) The camera holds on his trembling expression.

Audio: low male growling voice.
SFX: subtle tense room tone.
Negative: subtitles, watermark, text overlay."""
    },
    {
        "display_order": 2,
        "duration": 4.0,
        "character_names": ["Wife", "Living Room"],
        "chain_type": "ROOT",
        "prompt": "Vertical 9:16, cinematic realistic drama, cold moody color grade. Medium close-up of the wife seated in the middle of the gray leather sofa on the LEFT side of frame, back straight, hands folded on her lap, face turned slightly right toward the husband. Camera completely static. Dark window blurred behind her. Expression totally calm, blank.",
        "video_prompt": """Medium close-up of the wife seated on the gray leather sofa on the left side of frame, back straight, hands neatly folded on her lap, face turned slightly right toward the husband. The camera is completely static. Dark window blurred behind her. Her expression is completely calm and blank; she blinks once slowly, lips barely parting. Wife says in a flat, soft voice: "Tôi không còn gì để nói." (no subtitles) She holds her steady, neutral gaze across the room.

Audio: calm soft female voice, distant quiet ambience.
SFX: none, heavy silence.
Negative: subtitles, watermark, text overlay."""
    },
    {
        "display_order": 3,
        "duration": 5.0,
        "character_names": ["Husband", "Wife", "Living Room"],
        "chain_type": "ROOT",
        "prompt": "Vertical 9:16, cinematic realistic drama, cold moody color grade. Two-shot: husband prominent in the RIGHT of frame stepping to the edge of the coffee table, pointing his right arm toward the front door on the right wall behind him; wife sitting motionless on the sofa at the LEFT of frame. Coffee table in the center.",
        "video_prompt": """Two-shot in the upscale living room: husband on the right side of frame steps to the edge of the coffee table, pointing his right arm toward the closed front door on the right wall; wife sits motionless on the sofa at the left. The camera pans right following his arm to the closed front door, then quick cut back to the two-shot. Husband shouting, voice cracking at the end: "Ngày mai chúng ta đi ly hôn. Cô dẫn bọn trẻ rời đi ngay. Biến khỏi cuộc đời tôi luôn." (no subtitles) Heavy breathing fills the room.

Audio: loud strained male shouting voice, echoing slightly in the room.
SFX: footsteps stepping forward on hardwood, heavy cloth rustle.
Negative: subtitles, watermark, text overlay."""
    },
    {
        "display_order": 4,
        "duration": 4.0,
        "character_names": ["Wife", "Living Room"],
        "chain_type": "ROOT",
        "prompt": "Vertical 9:16, cinematic realistic drama, cold moody color grade. Close-up of the wife seated on the LEFT side of frame, head slightly tilted, face turned right toward the husband off-screen. Eyebrows knit slightly in genuine, sincere confusion. Soft natural indoor lighting.",
        "video_prompt": """Close-up of the wife still seated on the left side of frame, head slightly tilted, face turned right. The camera performs a slow gentle push-in. Her eyebrows knit slightly, sincerely confused, not acting. The husband is off-screen on the right. Wife asks in a nonchalant, puzzled voice: "Tại sao là tôi phải dẫn con đi?" (no subtitles) The camera holds on her questioning eyes.

Audio: calm puzzled female voice.
SFX: quiet room atmosphere.
Negative: subtitles, watermark, text overlay."""
    },
    {
        "display_order": 5,
        "duration": 5.0,
        "character_names": ["Husband", "Two Children", "Living Room"],
        "chain_type": "ROOT",
        "prompt": "Vertical 9:16, cinematic realistic drama, cold moody color grade. Close-up profile shot of the husband on the RIGHT side of frame, facing left, standing one step back with the framed family photo of four on the wall blurred behind him in shallow depth of field. Eyes full of pain mixed with hatred.",
        "video_prompt": """Close-up profile shot of the husband on the right side of frame, facing left, standing one step back with the family photo of four on the wall blurred behind him in shallow depth of field. Quick insert cut to the framed family photo showing the two children and parents, then back to his face: eyes full of pain mixed with hatred. Wife is off-screen on the left. Husband says, angry and choked with emotion: "Chứ cô còn định để lại cho tôi à? Nhìn thấy chúng là tôi nhớ đến sự phản bội của cô." (no subtitles) His jaw clenches tightly.

Audio: strained emotional male voice, choked with anger.
SFX: subtle ambient room hum.
Negative: subtitles, watermark, text overlay."""
    },
    {
        "display_order": 6,
        "duration": 5.0,
        "character_names": ["Wife", "Husband", "Living Room"],
        "chain_type": "ROOT",
        "prompt": "Vertical 9:16, cinematic realistic drama, cold moody color grade. Medium shot of the wife standing on the LEFT side of frame beside the left edge of the coffee table, facing right toward the husband who stands on the RIGHT side of the table, about 2 meters apart. Her expression turns impatient and incredulous.",
        "video_prompt": """Start on a close-up of the wife seated on the left, then camera tilts up as she stands, ending on her face at eye level, still on the left side of frame, standing beside the left edge of the coffee table, facing right toward the husband on the right side about 2 meters apart. Background music cuts to total silence; only a clock ticking. Her expression turns impatient and incredulous. Wife says with clear, cutting disbelief: "Anh có bị điên không vậy? Bọn trẻ là con của vợ phụ anh mà. Liên quan gì đến tôi chứ?" (no subtitles) The camera holds steady.

Audio: clear sharp female dialogue, rhythmic clock ticking in background.
SFX: soft rustle of knit dress as she stands up.
Negative: subtitles, watermark, text overlay."""
    },
    {
        "display_order": 7,
        "duration": 4.0,
        "character_names": ["Husband", "DNA Test Paper", "Living Room"],
        "chain_type": "ROOT",
        "prompt": "Vertical 9:16, cinematic realistic drama, cold moody color grade. Extreme close-up of the husband's eyes on the RIGHT side of frame, pupils dilating, anger collapsing into shock. Background stretches away in dolly zoom distortion, face stays same size.",
        "video_prompt": """Extreme close-up of the husband's eyes on the right side of frame, pupils dilating, anger collapsing into shock. Dolly zoom effect causes background to stretch away while his face stays the same size. Quick cut to the DNA paper slipping from his hand and falling to the floor at his feet, right of the coffee table. Faint ringing in the ears, then the sound of paper touching the floor. No dialogue; he opens his mouth but no words come out.

Audio: faint ringing in the ears, fading into absolute silence.
SFX: light flutter and soft tap of paper landing on the floor.
Negative: subtitles, watermark, text overlay."""
    },
    {
        "display_order": 8,
        "duration": 3.0,
        "character_names": ["Wife", "Husband", "Two Children", "Living Room", "DNA Test Paper"],
        "chain_type": "ROOT",
        "prompt": "Vertical 9:16, cinematic realistic drama, cold moody color grade. Static wide shot from main camera position showing the whole room: wife standing on the LEFT with arms crossed looking right, husband frozen stiff on the RIGHT, coffee table in the center, DNA paper on the floor near husband's feet, family photo and front door visible on the right wall.",
        "video_prompt": """Static wide shot from the main camera position showing the whole room: wife standing on the left with arms crossed, looking right; husband frozen stiff on the right; coffee table in the center; DNA paper on the floor near the husband's feet; family photo and front door visible on the right wall. The camera holds completely still. Slow fade to black.

Audio: dead interior silence.
SFX: none.
Negative: subtitles, watermark, text overlay."""
    }
]

created = []
for sc in scenes:
    sc["video_id"] = vid
    req = urllib.request.Request(
        "http://127.0.0.1:8100/api/scenes",
        data=json.dumps(sc).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode("utf-8"))
    created.append((data["display_order"], data["id"]))

print(f"Created {len(created)} scenes successfully:")
for order, sid in created:
    print(f"  Scene #{order}: {sid}")
