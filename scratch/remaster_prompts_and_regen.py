"""Remaster all 21 scene prompts with dynamic camera angles, cinematic realism, and correct wardrobe, then regenerate."""
import urllib.request
import json
import sqlite3
import time
import sys
import io
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / "flow_agent.db"
PID = "a0558109-06ce-4df6-837a-73cbfe4376a2"
VID = "caf885ed-d8cc-41e6-9cdc-b3e38d387842"
BASE_URL = "http://127.0.0.1:8100"

STYLE_PREFIX = (
    "Photorealistic cinematic live-action drama, shot on 35mm lens, shallow depth of field, "
    "handheld camera with subtle shake, natural practical lighting, muted desaturated warm-gray color grade, "
    "fine film grain, realistic skin texture and natural imperfections, authentic Vietnamese setting, 16:9. "
    "No text, no subtitles, no logo, no watermark."
)

SCENES_CONFIG = [
    {
        "order": 0,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mẹ (Bà Hoa)", "Mai", "Nhà cha mẹ"],
        "prompt": (
            f"{STYLE_PREFIX} Intimate eye-level tight close-up on Mẹ (Bà Hoa), a 50-year-old Vietnamese mother with graying hair. "
            "Tears glisten on her cheeks, her lips trembling with heartbreak as she pleads. In the soft-focus foreground edge, "
            "the back of Mai's shoulder and dark ponytail are blurred. Warm afternoon sunlight streams through sheer white curtains in the family living room. "
            "Intense emotional portrait, fine 35mm film grain."
        ),
        "video_prompt": (
            "0-3s: Tight close-up on Mẹ with trembling lips and tears spilling down her weathered cheeks, pleading softly as the camera holds with subtle handheld shake. Mai's shoulder is blurred in the foreground edge. "
            "3-6s: The camera slowly drifts closer to the mother's anguished face as warm afternoon side light illuminates dust motes in the air.\n\n"
            "Audio: soft muffled weeping, maternal voice pleading: \"Con sẽ phải chịu khổ đấy.\"\n"
            "SFX: gentle fabric rustle, soft breathing.\n"
            "Negative: subtitles, watermark, text overlay, oversaturated colors."
        ),
        "narrator_text": "Mẹ: \"Con sẽ phải chịu khổ đấy.\""
    },
    {
        "order": 1,
        "chain_type": "CONTINUATION",
        "parent_order": 0,
        "character_names": ["Bố (Ông Quân)", "Mẹ (Bà Hoa)", "Mai", "Nhà cha mẹ"],
        "prompt": (
            f"{STYLE_PREFIX} Medium wide shot in the traditional Vietnamese living room with polished wooden furniture. "
            "In the mid-foreground, Bố (Ông Quân) in a teal polo shirt stands furious, pointing his finger with moral authority. "
            "Mẹ in a gray cardigan trembles behind him, clutching his arm in distress. On the opposite side of the frame, "
            "Mai in a clean white t-shirt and dark trousers stands defiantly with chin raised, clutching her bag. Warm domestic interior lighting."
        ),
        "video_prompt": (
            "0-3s: Medium wide shot in the family living room. Father stands stern and furious in the foreground, his voice booming with authority. Mother trembles behind him, clutching his arm in distress. "
            "3-6s: Mai stands motionless and defiant at the far edge of the frame, chin raised, refusing to back down as tension fills the warm room. Subtle handheld camera drift.\n\n"
            "Audio: Father shouting sternly: \"Nó là hạng người gì, con chưa nhìn ra sao?\", Mai replying firmly: \"Con yêu anh ấy!\"\n"
            "SFX: footsteps on wooden floor, heavy tense breathing.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Bố: \"Nó là hạng người gì, con chưa nhìn ra sao?\" Mai: \"Con yêu anh ấy!\""
    },
    {
        "order": 2,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Tuấn", "Đầu ngõ ban đêm"],
        "prompt": (
            f"{STYLE_PREFIX} Medium side-profile shot at night in a narrow quiet Vietnamese brick alley. "
            "Tuấn, a 25-year-old Vietnamese man with buzz cut and sharp jawline, wearing a black leather jacket, sits astride his dark parked motorbike under a dim amber incandescent streetlamp. "
            "He glances impatiently at his wristwatch, then turns his head toward the distant house gate. Moody deep shadows, cinematic night look."
        ),
        "video_prompt": (
            "0-3s: Medium shot of Tuấn sitting astride a parked motorbike in the quiet alleyway. A single dim yellow streetlight casts deep shadows across his sharp jawline. He raises his wrist to check his watch with an impatient sigh. "
            "3-5s: He turns his head sharply to gaze toward the house gate, engine idling quietly with subtle vibration. Handheld camera.\n\n"
            "Audio: low rumble of motorcycle engine idling, distant city hum.\n"
            "SFX: leather jacket creaking, metal keys clinking.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "(Tuấn sốt ruột chờ Mai ngoài đầu ngõ vắng giữa đêm khuya)"
    },
    {
        "order": 3,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Tuấn", "Đầu ngõ ban đêm"],
        "prompt": (
            f"{STYLE_PREFIX} Three-quarter rear-angle medium shot on the motorbike in the dark alleyway. "
            "Both Mai and Tuấn are mounted together on the motorbike. Mai sits closely behind Tuấn, both her hands tightly gripping the waist of his black leather jacket, a vintage brown suitcase strapped between them. "
            "Tuấn grips the handlebars ready to accelerate, while Mai turns her head back for one last guilty, lingering look at her family alley gate. Red taillight glow on wet asphalt."
        ),
        "video_prompt": (
            "0-3s: Tight medium shot of Mai seated behind Tuấn on the motorbike, hands firmly gripping his leather jacket, small suitcase securely between them. "
            "3-6s: Tuấn turns his head slightly, speaking with confidence: \"Đi thôi. Có anh rồi.\" The motorbike accelerates forward into the darkness, Mai looking back one last time.\n\n"
            "Audio: motorcycle throttle revving, Tuấn speaking confidently: \"Đi thôi. Có anh rồi.\"\n"
            "SFX: tires rolling on damp asphalt, wind rushing past.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Tuấn: \"Đi thôi. Có anh rồi.\""
    },
    {
        "order": 4,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Atmospheric still life, wide shot of an empty, depressing 12m² rental room in Hanoi at early dawn. "
            "Cold, pale gray morning light filters through a barred window with faded ripped curtains. Damp peeling plaster walls, a bare rusted iron bed frame without mattress, "
            "and a rickety wooden table littered with discarded styrofoam food boxes and empty green beer bottles. Bleak, quiet, melancholic atmosphere."
        ),
        "video_prompt": (
            "0-2s: The scene fades up from darkness into the cold, silent atmosphere of a tiny rental room. Faded curtains hang by a barred window, dust motes floating in pale gray light. "
            "2-4s: The camera slowly drifts across the damp peeling walls and an empty iron bed, as a baby's faint cry echoes in from off-screen.\n\n"
            "Audio: distant faint cry of a newborn infant, subtle city traffic.\n"
            "SFX: wind rattling old window panes.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Một năm sau... Những ảo mộng tan vỡ trong căn phòng trọ chật chội."
    },
    {
        "order": 5,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Bé", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Intimate medium shot inside the dingy rental room. "
            "Mai, 23 years old, visibly aged and exhausted, with loose messy uncombed black hair falling around her face, noticeable dark eye circles of severe sleep deprivation, and dry chapped lips. "
            "She wears an oversized worn faded gray sweatshirt and dark track pants, sitting slumped on the edge of the iron bed, tenderly cradling her newborn baby wrapped in a pale blue blanket. "
            "Cold gray window light illuminating her tired, gentle face."
        ),
        "video_prompt": (
            "0-3s: Medium shot of Mai sitting slumped on the edge of the rusty iron bed in her faded gray sweatshirt and messy hair. She cradles her newborn baby against her chest, rocking gently. "
            "3-6s: She looks down at the sleeping infant with tender love mixed with deep fatigue, softly whispering a lullaby as cold gray window light falls across them.\n\n"
            "Audio: soft gentle humming, baby's quiet breathing, distant motorbike horns.\n"
            "SFX: iron bed spring creaking softly.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "(Mai mệt mỏi nhưng dịu dàng ôm đứa con thơ trong căn phòng trọ xám lạnh)"
    },
    {
        "order": 6,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Tuấn", "Mai", "Bé", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Dynamic low-angle wide shot inside the cluttered rental room. "
            "In the foreground, an unwashed Tuấn with scruffy facial stubble and bloodshot lazy eyes lies sprawled across the mattress, staring into his glowing smartphone screen while shouting a harsh order. "
            "Empty beer bottles and litter cover the floor. In the background near the barred window, Mai in her worn gray sweatshirt clutches her baby protectively, recoiling with hurt eyes. Cold realistic lighting."
        ),
        "video_prompt": (
            "0-3s: Low angle shot focused on Tuấn lying sprawled on the rumpled bed with an unwashed look and stubble, scrolling his smartphone indifferently. Empty green beer bottles litter the floor beside discarded food cartons. "
            "3-6s: Without glancing up from his screen, Tuấn barks harshly: \"Mau ra ngoài kiếm tiền cho tôi!\" In the background, Mai clutches the baby tighter, stepping back in silent hurt.\n\n"
            "Audio: Tuấn snapping harshly: \"Mau ra ngoài kiếm tiền cho tôi!\", phone game sounds.\n"
            "SFX: beer bottle clinking on concrete, baby whimpering.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Tuấn: \"Mau ra ngoài kiếm tiền cho tôi!\""
    },
    {
        "order": 7,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Bé", "Vỉa hè ban đêm"],
        "prompt": (
            f"{STYLE_PREFIX} Ground-level wide shot of a wet night sidewalk in Hanoi with blurred rushing traffic. "
            "Mai, wearing her oversized faded gray sweatshirt, jeans, and sandals, sits on a tiny blue plastic stool on the cold damp pavement, cradling her newborn baby tightly against the freezing night wind. "
            "On a dark cloth laid on the ground in front of her are several bundled pairs of cheap socks for sale. Streaking motorcycle headlights in the background, bustling pedestrians rushing past without looking."
        ),
        "video_prompt": (
            "0-3s: Wide handheld tracking shot of the bustling night street. Mai sits on a tiny plastic stool on the cold sidewalk in her worn sweatshirt, holding her wrapped baby close. In front of her, cheap socks are laid out on a dark cloth. "
            "3-6s: Commuters on motorbikes speed past, headlights streaking. Mai timidly calls out with a strained, desperate voice: \"Tất ba đôi hai mươi nghìn đây, xem thử đi ạ!\" Nobody stops.\n\n"
            "Audio: Mai calling out timidly: \"Tất ba đôi hai mươi nghìn đây, xem thử đi ạ!\", roar of passing traffic.\n"
            "SFX: motorbike engines rushing by, wind rustling tree leaves.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Mai: \"Tất ba đôi hai mươi nghìn đây, xem thử đi ạ!\""
    },
    {
        "order": 8,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Bé", "Vỉa hè ban đêm"],
        "prompt": (
            f"{STYLE_PREFIX} Extreme close-up (ECU) on Mai's weary, sorrowful face on the night sidewalk. "
            "Her dark eyes are red-rimmed and filled with tears, her lips chapped and shivering. A heavy solitary tear rolls down her pale cheek, falling directly onto the corner of the knitted blanket sheltering her baby. "
            "Extreme shallow depth of field, warm blurry city bokeh in the dark background, raw emotional vulnerability."
        ),
        "video_prompt": (
            "0-3s: Extreme close-up of Mai's face as she bows her head down to protect her baby from a sudden chilly gust of wind. Her eyes glisten with tears, lips chapped and trembling. "
            "3-5s: A heavy teardrop rolls down her cheek and absorbs into the infant's blanket. The camera holds tight with subtle emotional shake as traffic sounds fade into a lonely hum.\n\n"
            "Audio: choked silent sob, cold wind blowing, muffled city rumble.\n"
            "SFX: fabric rustling as she pulls the blanket tighter.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "(Từng giọt nước mắt rơi xuống manh chăn mỏng của đứa con thơ)"
    },
    {
        "order": 9,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Tuấn", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} High-angle top-down shot inside the dim rental room at night under a harsh fluorescent tube. "
            "Mai in her gray sweatshirt sits kneeling on the cold stained concrete floor, her chapped hands carefully flattening and counting crumpled small-denomination Vietnamese banknotes (10k, 20k dong) beside a plastic bowl. "
            "In the far background, Tuấn lies slouched on the bed with his face illuminated only by his smartphone screen. Stained walls, heartbreaking poverty."
        ),
        "video_prompt": (
            "0-3s: High-angle shot of the dingy rental room under a buzzing fluorescent tube. Mai sits kneeling on the cold floor, flattening out crumpled small-denomination bills with trembling tired fingers. "
            "3-6s: She stacks the few bills together, looking down with a heavy sigh. In the background on the bed, Tuấn remains slouched in silence, scrolling his phone without caring.\n\n"
            "Audio: faint hum of an old electric fan, quiet rustling of paper money.\n"
            "SFX: paper bills smoothing out, beer bottle rolling slightly on floor.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "(Những đồng tiền lẻ nhàu nát gom góp cả đêm cũng chẳng đủ tiền sữa cho con)"
    },
    {
        "order": 10,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Tuấn", "Bé", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Over-the-shoulder (OTS) medium shot framed closely past Tuấn's indifferent turned back. "
            "The camera focuses directly on Mai sitting on the edge of the bed cradling her baby, her face pale with dark eye circles, looking at Tuấn with desperate pleading eyes filled with tears as she asks for milk money. "
            "Tuấn's dark silhouette shows no reaction, cold dismissive body language. Natural dim interior light."
        ),
        "video_prompt": (
            "0-4s: Over-the-shoulder shot framed past Tuấn's indifferent slouching shoulder. Mai sits on the edge of the bed holding the baby, speaking in a strained, cracking whisper: \"Hết tiền mua sữa cho con rồi. Tiền nhà còn đang nợ, tiền tiết kiệm cũng hết rồi.\" "
            "4-7s: Tuấn scoffs dismissively without turning his head, muttering coldly: \"Em lo mà xoay đi.\" Mai looks at him, heartbroken by his utter callousness.\n\n"
            "Audio: Mai pleading quietly: \"Hết tiền mua sữa cho con rồi...\", Tuấn muttering coldly: \"Em lo mà xoay đi.\"\n"
            "SFX: soft baby breathing, ceiling fan rattling.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Mai: \"Hết tiền mua sữa cho con rồi... Tiền nhà còn đang nợ.\" Tuấn: \"Em lo mà xoay đi.\""
    },
    {
        "order": 11,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Bé", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Eye-level medium close-up of Mai leaning against the barred window where natural daylight illuminates her face. "
            "She holds a cracked smartphone at arm's length for a video call while supporting her baby with her other arm. "
            "Despite her worn gray sweatshirt, messy hair, and deep eye circles, she forces a radiant, cheerful, brave smile toward the camera to reassure her parents. Natural window lighting."
        ),
        "video_prompt": (
            "0-3s: Mai leans against the window frame where daylight is strongest, holding her cracked phone up with one hand while supporting the baby with the other. She forces a cheerful, bright smile across her weary face. "
            "3-6s: She nods encouragingly into the camera, speaking cheerfully: \"Dạ, con vẫn ổn, bố mẹ đừng lo!\" Her voice sounds sweet, concealing all her hardship.\n\n"
            "Audio: Mai speaking cheerfully: \"Dạ, con vẫn ổn, bố mẹ đừng lo!\", faint mother voice from phone speaker.\n"
            "SFX: phone audio chirp, breeze through window bars.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Mai: \"Dạ, con vẫn ổn, bố mẹ đừng lo.\""
    },
    {
        "order": 12,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Bé", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Tight close-up on Mai's face against the blurred window bars immediately after the video call ends. "
            "Her forced smile has completely collapsed into raw emotional agony, her mouth open in a silent sob, heavy tears streaming down both cheeks. "
            "She buries her tear-soaked cheek tenderly against the baby's soft head, clutching the child tightly to her chest. Heartbreaking drama."
        ),
        "video_prompt": (
            "0-2s: Close-up on Mai's face. The cheerful smile vanishes the exact microsecond the phone screen turns black. Her expression crumbles into raw agony. "
            "2-6s: She lowers the phone, tears streaming freely down both cheeks. She presses her cheek against the soft top of her baby's head, whispering brokenly: \"Mẹ con mình... cố gắng sống cho tốt nhé.\"\n\n"
            "Audio: Mai whispering through tears: \"Mẹ con mình... cố gắng sống cho tốt nhé.\", muffled sob.\n"
            "SFX: phone screen locking click, soft baby coo.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Mai: \"Mẹ con mình... cố gắng sống cho tốt nhé.\""
    },
    {
        "order": 13,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Low-angle medium shot in the damp communal boarding house hallway. "
            "Mai squats on the wet concrete floor, the sleeves of her worn gray sweatshirt rolled up, scrubbing clothes by hand inside a blue plastic washbasin filled with sudsy water. "
            "Her posture is exhausted, back curved with fatigue. Behind her through the open door, the messy room is visible with empty beer bottles on the table. Gritty domestic realism."
        ),
        "video_prompt": (
            "0-3s: Mai squats by the doorway on the damp floor, scrubbing laundry rigorously with reddened, chapped hands inside a large blue plastic basin. Soapy water sloshes over the edge. "
            "3-6s: She pauses, breathless and exhausted, rubbing her aching lower back. Behind her inside the open doorway, the neglected room sits in messy disarray with trash and beer bottles.\n\n"
            "Audio: soapy water splashing, rhythmic scrubbing sounds.\n"
            "SFX: heavy tired sigh, drops of water dripping from laundry.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "(Bao nhọc nhằn dồn hết lên đôi vai gầy mòn mỏi)"
    },
    {
        "order": 14,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Bé", "Tuấn", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Nighttime medium shot in the dark rental room under a dim bedside lamp. "
            "Mai in panic presses the back of her hand against her baby's burning, feverish forehead, holding a glowing digital thermometer with terror in her eyes. "
            "With her other hand, she urgently shakes the shoulder of Tuấn, who lies sleeping face-down on the mattress, swatting her away with uncaring laziness. Tense dramatic atmosphere."
        ),
        "video_prompt": (
            "0-3s: Panic in the dark room. Mai feels the baby's burning forehead with the back of her hand, checking the digital thermometer in shock. The baby whimpers weakly with flushed cheeks. "
            "3-7s: Mai urgently shakes Tuấn's shoulder on the bed, pleading in panic: \"Anh ơi, con sốt rồi, đưa con đi viện đi.\" Tuấn merely swats her hand away, rolling over and mumbling: \"Cho nó uống thuốc là được rồi.\"\n\n"
            "Audio: Mai panicking: \"Anh ơi, con sốt rồi, đưa con đi viện đi.\", Tuấn grumbling: \"Cho nó uống thuốc là được rồi.\"\n"
            "SFX: bed creak, thermometer beep, baby feverish whimpering.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Mai: \"Anh ơi, con sốt rồi, đưa con đi viện đi.\" Tuấn: \"Cho nó uống thuốc là được rồi.\""
    },
    {
        "order": 15,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Bé", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Cinematic chiaroscuro close-up on Mai's face in deep midnight shadows. "
            "One side of her face is carved out by cold blue moonlight filtering through the window bars. She looks from her sleeping husband's back down to her sick infant in her arms. "
            "Her tears have stopped; her dark eyes harden with a profound, quiet moment of awakening and determination. High contrast, atmospheric shadows."
        ),
        "video_prompt": (
            "0-3s: The camera slowly dollies in on Mai's face, half-shrouded in deep blue midnight shadows. She looks at her husband's back, then down at the fragile child in her arms. "
            "3-6s: Her tears stop flowing. A cold, painful clarity settles into her eyes as she realizes she is completely alone. She whispers quietly to herself: \"Sao mình lại thành ra thế này chứ...\"\n\n"
            "Audio: Mai whispering in silent realization: \"Sao mình lại thành ra thế này chứ...\", ticking clock.\n"
            "SFX: slow steady breathing, distant night wind.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Mai: \"Sao mình lại thành ra thế này chứ...\""
    },
    {
        "order": 16,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Chị Hà", "Mai", "Bé", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Two-shot in natural morning light at the rental room doorway. "
            "Chị Hà, a 30-year-old neighbor with reddish-brown hair in a casual tank top, stands outside the door looking with deep concern and pity at the sick baby. "
            "Inside the doorway, Mai in her worn gray sweatshirt holds the baby protectively against her chest, wearing a weak strained smile with hollow eyes, trying to defend her choices."
        ),
        "video_prompt": (
            "0-3s: Morning doorway shot. Neighbor Chị Hà knocks softly and peeks inside, her brow furrowing with genuine worry as she looks at the feverish baby. She says sympathetically: \"Còn bé thế này mà...\" "
            "3-7s: Mai hugs the baby protectively, smiling weakly with hollow eyes, trying to convince herself: \"Sốt thôi mà, uống thuốc chẳng phải được rồi sao?\" Her voice trembles with denial.\n\n"
            "Audio: Chị Hà speaking gently: \"Còn bé thế này mà...\", Mai murmuring defensively: \"Sốt thôi mà, uống thuốc chẳng phải được rồi sao?\"\n"
            "SFX: wooden door creak, morning birds chirping outside.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Chị Hà: \"Còn bé thế này mà...\" Mai: \"Sốt thôi mà, uống thuốc chẳng phải được rồi sao?\""
    },
    {
        "order": 17,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Bé", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Ground-level intimate close-up of Mai as she collapses onto her knees on the bare concrete floor after the neighbor leaves. "
            "She curls her body around her newborn baby, holding the child tightly to her chest, sobbing uncontrollably with gasping breaths, tears streaming down her pale cheeks. "
            "Raw, visceral emotional breakdown, handheld camera feel."
        ),
        "video_prompt": (
            "0-2s: Tight close-up on Mai as the realization of her own empty words shatters her composure. Her defenses collapse entirely. "
            "2-5s: She sinks to her knees, clutching her baby tightly against her chest, weeping with heavy, gasping sobs. The camera shakes subtly with her trembling body in an intimate, heartbreaking moment.\n\n"
            "Audio: heavy gasping sobs, ragged breathing, deep emotional weeping.\n"
            "SFX: cloth crumpling, tears dripping.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "(Lời tự dỗ dành bỗng trở nên vô nghĩa, Mai ôm con gục xuống khóc nức nở)"
    },
    {
        "order": 18,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Bé", "Tuấn", "Phòng trọ"],
        "prompt": (
            f"{STYLE_PREFIX} Three-quarter medium shot inside the doorway looking out. "
            "Mai, holding her baby bundled tightly in her arms and pulling a small suitcase with her other hand, steps over the threshold into bright morning sunlight. "
            "She pauses for one final look back at Tuấn, who lies sleeping sprawled on the messy bed among empty cans. Resolute, determined expression on her face as she walks away."
        ),
        "video_prompt": (
            "0-4s: Medium shot inside the doorway. Mai holds her baby bundled securely against her chest with one hand, dragging her small suitcase with the other. She pauses and looks back one last time at Tuấn sprawled on the messy bed among empty cans. "
            "4-7s: From the mattress, Tuấn mumbles drowsily without turning: \"Còn mang theo cả đứa con vướng víu nữa...\" Mai turns forward, face set with quiet resolve, and steps out into the bright hallway sunlight, closing the door behind her.\n\n"
            "Audio: Tuấn mumbling sleepily: \"Còn mang theo cả đứa con vướng víu nữa...\", door latch clicking shut.\n"
            "SFX: suitcase wheels rolling over threshold, firm footsteps moving away.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Tuấn: \"Còn mang theo cả đứa con vướng víu nữa...\""
    },
    {
        "order": 19,
        "chain_type": "ROOT",
        "parent_order": None,
        "character_names": ["Mai", "Bé", "Bố (Ông Quân)", "Mẹ (Bà Hoa)", "Nhà cha mẹ"],
        "prompt": (
            f"{STYLE_PREFIX} Emotional medium shot at the open front door of the family house in bright morning sunlight. "
            "Mai stands on the porch holding her baby, her clothes worn and hair disheveled, tears spilling from red-rimmed eyes. "
            "The wooden door is wide open: Bố (Ông Quân) stands frozen in shock, hand on the door frame, while Mẹ (Bà Hoa) rushes past him with tears streaming down her face and arms outstretched to embrace them. Deeply moving family drama."
        ),
        "video_prompt": (
            "0-3s: Morning exterior doorway of the family home. Mai stands on the front step, clutching her baby, eyes red and swollen, looking up with vulnerability and guilt. "
            "3-7s: The wooden door swings open. Father stands frozen in shock, looking at his daughter and then down at his grandchild. Mother rushes past him in floods of tears, crying out: \"Mau vào đi, mau vào đi!\" as she embraces them both.\n\n"
            "Audio: Mother crying out emotionally: \"Mau vào đi, mau vào đi con!\", choked maternal weeping.\n"
            "SFX: front wooden door swinging open, rushing footsteps on tile.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "Mẹ: \"Mau vào đi, mau vào đi con.\""
    },
    {
        "order": 20,
        "chain_type": "CONTINUATION",
        "parent_order": 19,
        "character_names": ["Mẹ (Bà Hoa)", "Mai", "Bé", "Bố (Ông Quân)", "Nhà cha mẹ"],
        "prompt": (
            f"{STYLE_PREFIX} Warm golden-lit wide shot in the family living room. "
            "Mẹ (Bà Hoa) wraps her arms tightly around weeping Mai and the newborn baby on the wooden settee, holding them with unconditional love. "
            "Bố (Ông Quân) stands beside them, his stern face softened into gentle tears as he places his rough, weathered hand tenderly on the baby's head. "
            "In the soft-focus background, the framed family portrait hangs on the wall. Cathartic, heartwarming conclusion."
        ),
        "video_prompt": (
            "0-3s: Warm, golden-lit wide shot of the family living room. Mother wraps both arms around weeping Mai and the newborn baby, holding them tight with unconditional love. Father stands beside them, his stern face melting into deep compassion as he gently places his rough weathered hand on the baby's head. "
            "3-6s: The camera slowly and smoothly pans right toward the wooden cabinet, focusing on the framed family photo before gently fading out into darkness.\n\n"
            "Audio: warm cinematic string melody swelling gently, soft relieved weeping.\n"
            "SFX: gentle breathing, quiet room ambiance.\n"
            "Negative: subtitles, watermark, text overlay."
        ),
        "narrator_text": "(Nhà vẫn luôn là nơi bình yên nhất, dang rộng vòng tay đón những đứa con lầm lỡ trở về)"
    }
]

def main():
    print("=== Bắt đầu tối ưu hóa và làm mới 21 phân cảnh ===")
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    c = conn.cursor()

    # 1. Lấy danh sách scene theo thứ tự
    scenes = c.execute("SELECT id, display_order FROM scene WHERE video_id=? ORDER BY display_order", (VID,)).fetchall()
    s_map = {order: sid for sid, order in scenes}

    # 2. Cập nhật prompt, image_prompt, chain_type cho từng cảnh
    with conn:
        # Xóa các request cũ của video để batch-status sạch sẽ và chính xác 100%
        c.execute("DELETE FROM request WHERE video_id = ?", (VID,))
        for sc in SCENES_CONFIG:
            order = sc["order"]
            sid = s_map[order]
            parent_id = s_map[sc["parent_order"]] if sc["parent_order"] is not None else None
            
            c.execute("""
                UPDATE scene 
                SET prompt = ?,
                    image_prompt = ?,
                    video_prompt = ?,
                    narrator_text = ?,
                    chain_type = ?,
                    parent_scene_id = ?,
                    character_names = ?,
                    horizontal_image_status = 'PENDING',
                    horizontal_image_media_id = NULL,
                    horizontal_image_url = NULL
                WHERE id = ?
            """, (
                sc["prompt"],
                sc["prompt"],  # Đồng bộ hoàn toàn image_prompt = prompt để không bao giờ bị mất style!
                sc["video_prompt"],
                sc["narrator_text"],
                sc["chain_type"],
                parent_id,
                json.dumps(sc["character_names"], ensure_ascii=False),
                sid
            ))
            print(f"✅ Đã tối ưu Cảnh #{order + 1:02d} [{sc['chain_type']}]")

    print("\n✅ Đã cập nhật toàn bộ 21 phân cảnh vào cơ sở dữ liệu.")

    # 3. Chạy quy trình tạo ảnh theo Wave
    # Wave 1: 19 cảnh ROOT (tất cả các cảnh độc lập, đa dạng góc máy)
    # Wave 2: 2 cảnh CONTINUATION (Cảnh 2 từ Cảnh 1, Cảnh 21 từ Cảnh 20)
    print("\n=== Bắt đầu đợt tạo ảnh mới (REGENERATE) ===")
    
    # Chuẩn bị Wave 1 (ROOT)
    root_scenes = [sc for sc in SCENES_CONFIG if sc["chain_type"] == "ROOT"]
    wave1_reqs = []
    for sc in root_scenes:
        sid = s_map[sc["order"]]
        wave1_reqs.append({
            "type": "GENERATE_IMAGE",
            "scene_id": sid,
            "project_id": PID,
            "video_id": VID,
            "orientation": "HORIZONTAL"
        })

    print(f"\n[Wave 1] Gửi {len(wave1_reqs)} cảnh ROOT (GENERATE_IMAGE)...")
    payload1 = json.dumps({"requests": wave1_reqs}).encode("utf-8")
    req1 = urllib.request.Request(
        f"{BASE_URL}/api/requests/batch",
        data=payload1,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req1) as resp:
        res1 = json.loads(resp.read().decode("utf-8"))
        print(f"-> Đã gửi thành công {len(res1)} yêu cầu Wave 1")

    # Theo dõi Wave 1
    poll_wave("GENERATE_IMAGE", 1)

    # Chuẩn bị Wave 2 (CONTINUATION)
    cont_scenes = [sc for sc in SCENES_CONFIG if sc["chain_type"] == "CONTINUATION"]
    wave2_reqs = []
    for sc in cont_scenes:
        sid = s_map[sc["order"]]
        wave2_reqs.append({
            "type": "EDIT_IMAGE",
            "scene_id": sid,
            "project_id": PID,
            "video_id": VID,
            "orientation": "HORIZONTAL"
        })

    print(f"\n[Wave 2] Gửi {len(wave2_reqs)} cảnh CONTINUATION (EDIT_IMAGE)...")
    payload2 = json.dumps({"requests": wave2_reqs}).encode("utf-8")
    req2 = urllib.request.Request(
        f"{BASE_URL}/api/requests/batch",
        data=payload2,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req2) as resp:
        res2 = json.loads(resp.read().decode("utf-8"))
        print(f"-> Đã gửi thành công {len(res2)} yêu cầu Wave 2")

    # Theo dõi Wave 2
    poll_wave("EDIT_IMAGE", 2)

    print("\n" + "=" * 60)
    print("HOÀN THÀNH TOÀN BỘ 21 PHÂN CẢNH VỚI CHẤT LƯỢNG MỚI!")
    print("=" * 60)

def poll_wave(req_type: str, wave_num: int):
    start = time.time()
    url = f"{BASE_URL}/api/requests/batch-status?video_id={VID}&type={req_type}"
    while True:
        try:
            req = urllib.request.urlopen(url, timeout=10)
            data = json.loads(req.read().decode("utf-8"))
        except Exception as e:
            time.sleep(5)
            continue
            
        completed = data.get("completed", 0)
        total = data.get("total", 0)
        processing = data.get("processing", 0)
        failed = data.get("failed", 0)
        done = data.get("done", False)
        elapsed = int(time.time() - start)
        print(f"[{elapsed:03d}s] Wave {wave_num} ({req_type}): {completed}/{total} xong | Đang chạy: {processing} | Thất bại: {failed} | Done: {done}")
        
        if done:
            break
        time.sleep(12)

if __name__ == "__main__":
    main()
