import json
import urllib.request

API_BASE = "http://127.0.0.1:8100/api"
PROJECT_ID = "8b2fdb28-a2db-44bd-a76e-7a9356970dd3"
VIDEO_ID = "13cac219-f3bc-437f-9622-5cd90fb91616"

def http_patch(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def http_get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

# 1. Update project material
http_patch(f"{API_BASE}/projects/{PROJECT_ID}", {"material": "anime"})
print("Updated project material to anime")

# 2. Update characters
chars = http_get(f"{API_BASE}/projects/{PROJECT_ID}/characters")
char_prompts = {
    "Wife": (
        "Single reference image of A 28-year-old Asian woman with shoulder-length soft brown hair, gentle facial features, wearing comfortable casual home attire including a cream knit sweater and dark trousers. Expressive hazel-brown eyes, natural makeup.. "
        "Japanese anime style, cel-shaded rendering, vibrant saturated colors, clean sharp linework, large expressive eyes, stylized anatomy. High-quality anime production, studio Ghibli meets modern anime aesthetic. "
        "NOT photorealistic, NOT 3D render, NOT oil painting, NOT sketch, NOT watercolor, NOT Western cartoon. "
        "COMPOSITION: Full body shot from head to toe, standing upright and straight (not tilted or leaning). Centered in frame with balanced composition. Front-facing view, looking directly at camera. Neutral simple background that doesn't distract from the subject. Proper proportions and anatomy. Character perfectly vertical, not skewed or rotated. "
        "ONE single image only, NOT a multi-panel grid or multiple views. Anime-style dramatic lighting, highly detailed"
    ),
    "Husband": (
        "Single reference image of A 32-year-old Asian man with short neat black hair, clean-shaven, sharp jawline, wearing a casual navy blue button-down shirt with rolled-up sleeves and grey trousers. Stern demeanor.. "
        "Japanese anime style, cel-shaded rendering, vibrant saturated colors, clean sharp linework, large expressive eyes, stylized anatomy. High-quality anime production, studio Ghibli meets modern anime aesthetic. "
        "NOT photorealistic, NOT 3D render, NOT oil painting, NOT sketch, NOT watercolor, NOT Western cartoon. "
        "COMPOSITION: Full body shot from head to toe, standing upright and straight (not tilted or leaning). Centered in frame with balanced composition. Front-facing view, looking directly at camera. Neutral simple background that doesn't distract from the subject. Proper proportions and anatomy. Character perfectly vertical, not skewed or rotated. "
        "ONE single image only, NOT a multi-panel grid or multiple views. Anime-style dramatic lighting, highly detailed"
    ),
    "Living Room": (
        "Single reference image of Modern family living room in the evening, with a large neutral grey fabric sofa, wooden coffee table, warm ambient lamp light casting cozy yet tense shadows, clean contemporary shelves in the soft-focus background.. "
        "Japanese anime style, cel-shaded rendering, vibrant saturated colors, clean sharp linework, large expressive eyes, stylized anatomy. High-quality anime production, studio Ghibli meets modern anime aesthetic. "
        "NOT photorealistic, NOT 3D render, NOT oil painting, NOT sketch, NOT watercolor, NOT Western cartoon. "
        "COMPOSITION: Establishing shot showing the full environment. Balanced level composition with straight horizon. Clear focal point. Atmospheric and richly detailed. Show depth and spatial layout. "
        "ONE single image only, NOT a multi-panel grid or multiple views. Anime-style dramatic lighting, highly detailed"
    ),
    "DNA Test Document": (
        "Single reference image of An official printed medical test report paper with crisp black text, laboratory header logo, and clear printed checkmarks and tables.. "
        "Japanese anime style, cel-shaded rendering, vibrant saturated colors, clean sharp linework, large expressive eyes, stylized anatomy. High-quality anime production, studio Ghibli meets modern anime aesthetic. "
        "NOT photorealistic, NOT 3D render, NOT oil painting, NOT sketch, NOT watercolor, NOT Western cartoon. "
        "COMPOSITION: Clear detailed view showing the asset's complete form. Appropriate angle to showcase distinctive features and functional elements. Centered with proper scale reference. Neutral background. Show key details, materials, and surface textures. "
        "ONE single image only, NOT a multi-panel grid or multiple views. Anime-style dramatic lighting, highly detailed"
    )
}

for c in chars:
    cname = c["name"]
    if cname in char_prompts:
        http_patch(f"{API_BASE}/characters/{c['id']}", {"image_prompt": char_prompts[cname]})
        print(f"Updated entity '{cname}' image_prompt")

# 3. Update scenes
scenes = http_get(f"{API_BASE}/scenes?video_id={VIDEO_ID}")
old_prefix = "Real RAW photograph, shot on Canon EOS R5, 35mm lens, natural available light."
new_prefix = "Anime style, cel-shaded, vibrant colors, clean linework, dramatic anime lighting."

for s in scenes:
    prompt = s["prompt"]
    if old_prefix in prompt:
        new_prompt = prompt.replace(old_prefix, new_prefix).strip()
    elif not prompt.startswith(new_prefix):
        new_prompt = f"{new_prefix} {prompt}"
    else:
        new_prompt = prompt
        
    http_patch(f"{API_BASE}/scenes/{s['id']}", {"prompt": new_prompt})
    print(f"Updated Scene {s['display_order']} prompt to 2D anime style")

print("Switch to 2D Anime style completed successfully.")
