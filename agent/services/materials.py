"""Material registry — built-in and custom visual styles for image generation."""

_BUILTIN_IDS: frozenset[str] = frozenset({
    "realistic", "3d_pixar", "anime", "anime_comedy", "ghibli", "stop_motion", "minecraft",
    "oil_painting", "watercolor", "comic_book", "cyberpunk", "claymation",
    "lego", "retro_vhs", "oversimplified_2d", "cinematic_drama",
})

MATERIALS: dict[str, dict] = {
    "realistic": {
        "id": "realistic",
        "name": "Photorealistic",
        "style_instruction": (
            "Photorealistic RAW photograph, shot on Canon EOS R5, 35mm lens, "
            "natural available light, real footage."
        ),
        "negative_prompt": (
            "NOT 3D render, NOT CGI, NOT digital art, NOT illustration, "
            "NOT anime, NOT painting, NOT cartoon."
        ),
        "scene_prefix": (
            "Real RAW photograph, shot on Canon EOS R5, 35mm lens, "
            "natural available light."
        ),
        "video_prefix": (
            "Real live-action cinema footage, shot on Canon EOS R5 35mm lens, "
            "natural lighting, real authentic footage, fine details."
        ),
        "lighting": "Studio lighting, highly detailed",
    },
    "3d_pixar": {
        "id": "3d_pixar",
        "name": "3D Pixar",
        "style_instruction": (
            "3D animated style, Pixar-quality rendering, Disney-Pixar aesthetic. "
            "Smooth subsurface scattering skin, expressive cartoon eyes, "
            "stylized proportions, vibrant saturated colors."
        ),
        "negative_prompt": (
            "NOT photorealistic, NOT photograph, NOT live action, NOT anime, "
            "NOT flat 2D."
        ),
        "scene_prefix": (
            "3D animated Pixar-quality rendering, vibrant colors, "
            "cinematic lighting."
        ),
        "video_prefix": (
            "3D animated film footage, Pixar-quality animation, smooth subsurface scattering skin, "
            "stylized cartoon anatomy, Disney-Pixar movie rendering, vibrant colors, cinematic lighting."
        ),
        "lighting": "Studio lighting, global illumination, highly detailed",
    },
    "anime": {
        "id": "anime",
        "name": "Anime",
        "style_instruction": (
            "Japanese anime style, cel-shaded rendering, vibrant saturated colors, "
            "clean sharp linework, large expressive eyes, stylized anatomy. "
            "High-quality anime production, studio Ghibli meets modern anime aesthetic."
        ),
        "negative_prompt": (
            "NOT photorealistic, NOT 3D render, NOT oil painting, "
            "NOT sketch, NOT watercolor, NOT Western cartoon."
        ),
        "scene_prefix": (
            "Anime style, cel-shaded, vibrant colors, clean linework, "
            "dramatic anime lighting."
        ),
        "video_prefix": (
            "Japanese anime animation, smooth cel-shaded motion, sharp linework, "
            "vibrant colors, expressive anime character animation, studio quality anime production."
        ),
        "lighting": "Anime-style dramatic lighting, highly detailed",
    },
    "anime_comedy": {
        "id": "anime_comedy",
        "name": "Anime Comedy",
        "style_instruction": (
            "Anime comedy cartoon style, expressive humorous facial expressions, "
            "exaggerated chibi reactions, bright vibrant pastel colors, clean cel-shaded anime lineart, "
            "energetic comedy manga aesthetic."
        ),
        "negative_prompt": (
            "NOT photorealistic, NOT dark gritty, NOT 3D render, NOT realistic."
        ),
        "scene_prefix": (
            "Anime comedy style, hilarious expressive cartoon faces, vibrant colors, "
            "clean cel-shaded lines, comedy anime aesthetic."
        ),
        "video_prefix": (
            "Funny anime comedy animation, exaggerated hilarious cartoon expressions, "
            "energetic character motion, chibi anime comedy style."
        ),
        "lighting": "Bright cheerful anime lighting, colorful and clean",
    },
    "stop_motion": {
        "id": "stop_motion",
        "name": "Felt & Wood Stop Motion",
        "style_instruction": (
            "Stop-motion animation style with handcrafted felt and wood puppets. "
            "Visible felt fabric texture, wooden joints and dowels, "
            "miniature handmade set pieces, warm craft workshop lighting. "
            "Laika Studios / Wes Anderson stop-motion aesthetic."
        ),
        "negative_prompt": (
            "NOT photorealistic, NOT 3D render, NOT digital, NOT anime, "
            "NOT smooth surfaces, NOT plastic."
        ),
        "scene_prefix": (
            "Stop-motion style, handcrafted felt and wood puppets, "
            "miniature set, warm workshop lighting."
        ),
        "video_prefix": (
            "Felt and wood stop-motion animation, handcrafted puppet motion, "
            "Wes Anderson and Laika style stop-motion frame rate, miniature tactile lighting."
        ),
        "lighting": "Warm practical miniature lighting, macro photography detail",
    },
    "minecraft": {
        "id": "minecraft",
        "name": "Minecraft",
        "style_instruction": (
            "Minecraft voxel art style, blocky cubic geometry, pixel textures, "
            "16x16 texture resolution aesthetic, square heads and bodies. "
            "Everything made of cubes and rectangular prisms. "
            "Minecraft game screenshot aesthetic."
        ),
        "negative_prompt": (
            "NOT smooth, NOT round, NOT photorealistic, NOT anime, "
            "NOT organic curves, NOT high-poly."
        ),
        "scene_prefix": (
            "Minecraft style, blocky voxel world, pixel textures, "
            "cubic geometry, game screenshot aesthetic."
        ),
        "video_prefix": (
            "Minecraft voxel animation, blocky cubic character motion, "
            "16x16 pixel textures, rigid game aesthetic, cubic geometry."
        ),
        "lighting": "Minecraft-style ambient lighting, block shadows",
    },
    "oil_painting": {
        "id": "oil_painting",
        "name": "Oil Painting",
        "style_instruction": (
            "Classical oil painting on canvas, visible thick brushstrokes, "
            "rich impasto texture, warm color palette, chiaroscuro lighting. "
            "Renaissance masters meets impressionist technique. "
            "Museum-quality fine art painting."
        ),
        "negative_prompt": (
            "NOT photorealistic, NOT digital art, NOT 3D render, NOT anime, "
            "NOT flat colors, NOT cartoon."
        ),
        "scene_prefix": (
            "Oil painting style, visible brushstrokes, rich impasto texture, "
            "warm palette, dramatic chiaroscuro lighting."
        ),
        "video_prefix": (
            "Living oil painting animation, animated canvas with visible brushstrokes, "
            "impasto texture in motion, rich chiaroscuro lighting, fine art masterpiece."
        ),
        "lighting": "Dramatic chiaroscuro lighting, rich tonal depth",
    },
    "ghibli": {
        "id": "ghibli",
        "name": "Studio Ghibli",
        "style_instruction": (
            "Studio Ghibli anime style, hand-painted watercolor backgrounds, "
            "soft pastel colors, gentle rounded character designs, whimsical atmosphere. "
            "Hayao Miyazaki aesthetic, detailed natural environments, magical realism."
        ),
        "negative_prompt": (
            "NOT photorealistic, NOT 3D render, NOT dark, NOT gritty, "
            "NOT sharp edges, NOT Western cartoon."
        ),
        "scene_prefix": (
            "Studio Ghibli anime style, hand-painted watercolor backgrounds, "
            "soft pastel colors, gentle whimsical atmosphere."
        ),
        "video_prefix": (
            "Studio Ghibli style anime animation, hand-drawn watercolor aesthetic, "
            "gentle whimsical motion, Hayao Miyazaki anime movie quality, soft pastel lighting."
        ),
        "lighting": "Soft natural Ghibli lighting, golden hour warmth, dappled sunlight",
    },
    "watercolor": {
        "id": "watercolor",
        "name": "Watercolor",
        "style_instruction": (
            "Soft watercolor painting on cold-press paper, loose wet brushwork, "
            "translucent color washes bleeding into each other, white paper showing through. "
            "Delicate ink outlines, impressionistic and dreamy."
        ),
        "negative_prompt": (
            "NOT photorealistic, NOT 3D render, NOT digital art, NOT anime, "
            "NOT sharp edges, NOT bold outlines."
        ),
        "scene_prefix": (
            "Watercolor painting style, soft wet brushwork, "
            "translucent color washes, delicate ink outlines."
        ),
        "video_prefix": (
            "Animated watercolor painting, flowing color washes, delicate ink linework, "
            "soft impressionistic motion on paper texture, dreamy artistic animation."
        ),
        "lighting": "Soft diffused natural light, watercolor wash",
    },
    "comic_book": {
        "id": "comic_book",
        "name": "Comic Book",
        "style_instruction": (
            "American comic book art style, bold black ink outlines, flat vibrant colors "
            "with halftone dot shading, dynamic action poses, dramatic foreshortening. "
            "Marvel/DC superhero comic aesthetic, Ben-Day dots, speech bubble ready."
        ),
        "negative_prompt": (
            "NOT photorealistic, NOT 3D render, NOT anime, NOT watercolor, "
            "NOT soft edges, NOT muted colors."
        ),
        "scene_prefix": (
            "Comic book style, bold ink outlines, vibrant flat colors, "
            "halftone shading, dynamic composition."
        ),
        "video_prefix": (
            "Comic book animation, bold graphic novel ink outlines, "
            "halftone dot textures in motion, dynamic comic action, vivid pop colors."
        ),
        "lighting": "High contrast comic lighting, dramatic shadows, rim light",
    },
    "cyberpunk": {
        "id": "cyberpunk",
        "name": "Cyberpunk",
        "style_instruction": (
            "Cyberpunk sci-fi aesthetic, neon-lit dark urban environment, "
            "holographic displays, rain-slicked streets reflecting neon signs. "
            "Blade Runner meets Ghost in the Shell, high-tech low-life, "
            "chrome and glass, purple and cyan color palette."
        ),
        "negative_prompt": (
            "NOT natural environment, NOT bright daylight, NOT historical, "
            "NOT cartoon, NOT fantasy medieval."
        ),
        "scene_prefix": (
            "Cyberpunk aesthetic, neon-lit dark urban, holographic displays, "
            "rain-slicked streets, purple and cyan neon."
        ),
        "video_prefix": (
            "Cyberpunk cinematic footage, neon-drenched dark sci-fi aesthetic, "
            "holographic reflections in rain, volumetric neon lighting, Blade Runner movie feel."
        ),
        "lighting": "Neon rim lighting, volumetric fog, cyan and magenta",
    },
    "claymation": {
        "id": "claymation",
        "name": "Claymation",
        "style_instruction": (
            "Clay animation style, characters made of modeling clay with visible "
            "fingerprint textures, slightly imperfect sculpted features. "
            "Wallace & Gromit / Aardman aesthetic, miniature handmade sets, "
            "warm practical lighting on tiny clay world."
        ),
        "negative_prompt": (
            "NOT photorealistic, NOT digital, NOT anime, NOT smooth skin, "
            "NOT 3D render, NOT glass or metal surfaces."
        ),
        "scene_prefix": (
            "Claymation style, clay puppet characters with fingerprint textures, "
            "miniature handmade sets, warm practical lighting."
        ),
        "video_prefix": (
            "Claymation stop-motion animation, malleable clay figures with visible fingerprint textures, "
            "Aardman Studios style tactile motion, warm miniature set lighting."
        ),
        "lighting": "Warm miniature set lighting, soft shadows, macro detail",
    },
    "lego": {
        "id": "lego",
        "name": "LEGO",
        "style_instruction": (
            "LEGO brick style, characters are LEGO minifigures with yellow skin "
            "and claw hands, environments built entirely from LEGO bricks and plates. "
            "Visible brick studs, ABS plastic texture, The LEGO Movie aesthetic."
        ),
        "negative_prompt": (
            "NOT photorealistic, NOT organic, NOT smooth, NOT anime, "
            "NOT round shapes, NOT natural materials."
        ),
        "scene_prefix": (
            "LEGO style, minifigure characters, brick-built environments, "
            "visible studs, plastic ABS texture."
        ),
        "video_prefix": (
            "LEGO animated film footage, plastic brick minifigure stop-motion, "
            "The LEGO Movie aesthetic, ABS plastic reflections, clicky brick animation."
        ),
        "lighting": "Bright toy photography lighting, sharp focus, product shot quality",
    },
    "retro_vhs": {
        "id": "retro_vhs",
        "name": "Retro VHS",
        "style_instruction": (
            "1980s VHS tape aesthetic, analog video noise and scan lines, "
            "slightly washed-out warm colors, CRT TV curvature, tracking artifacts. "
            "Retro camcorder footage feel, date stamp overlay, nostalgic grain."
        ),
        "negative_prompt": (
            "NOT modern, NOT 4K, NOT clean, NOT digital, NOT anime, "
            "NOT sharp, NOT high-definition."
        ),
        "scene_prefix": (
            "Retro VHS style, analog scan lines, warm washed-out colors, "
            "CRT curvature, nostalgic 80s grain."
        ),
        "video_prefix": (
            "1980s retro VHS camcorder footage, authentic analog tape scan lines, "
            "chromatic aberration, tracking noise, nostalgic CRT color bleed."
        ),
        "lighting": "Warm tungsten lighting, CRT glow, analog video bloom",
    },
    "oversimplified_2d": {
        "id": "oversimplified_2d",
        "name": "OverSimplified 2D Cartoon",
        "style_instruction": (
            "OverSimplified 2D minimalist animated cartoon aesthetic. "
            "Thick, bold, uniform pitch-black contour lines enclosing every shape. "
            "Strictly flat solid 2D colors, completely zero shading, no gradients, no shadows. "
            "Simple bean-shaped torso with no visible neck, thick straight black stick-figure limbs, "
            "simple oval head with tiny solid black dot eyes and simple line mouth. "
            "Clean flat vector illustration, pure solid white background."
        ),
        "negative_prompt": (
            "NOT 3D render, NOT CGI, NOT realistic, NOT photorealistic, "
            "NO shading, NO gradients, NO shadows, NO 3D depth, NO realistic anatomy, "
            "NO fingers, NO detailed hands, NO complex muscles, NO textures, "
            "NO text, NO labels, NO watermark."
        ),
        "scene_prefix": (
            "OverSimplified 2D animated cartoon style, thick bold black outlines, "
            "flat solid 2D vector colors, zero shading, minimalist stick-figure limbs."
        ),
        "video_prefix": (
            "Keep exact 2D flat animated style, 2D vector animation, rigid stick-figure motion, strictly flat colors, no 3D depth, no shadows."
        ),
        "lighting": "Flat uniform ambient lighting, completely shadowless",
    },
    "cinematic_drama": {
        "id": "cinematic_drama",
        "name": "Cinematic Drama (Desaturated 35mm)",
        "style_instruction": (
            "Photorealistic cinematic live-action drama, shot on 35mm lens, shallow depth of field, "
            "handheld camera with subtle shake, natural practical lighting, muted desaturated warm-gray color grade, "
            "fine film grain, realistic skin texture and natural imperfections, authentic Vietnamese urban setting. "
            "Real live-action cinema aesthetic."
        ),
        "negative_prompt": (
            "NOT 3D render, NOT CGI, NOT digital art, NOT illustration, NOT anime, NOT cartoon, "
            "NOT painting, NOT oversaturated, NOT high-gloss commercial, "
            "NO text, NO subtitles, NO logo, NO watermark."
        ),
        "scene_prefix": (
            "Photorealistic cinematic live-action drama, shot on 35mm lens, shallow depth of field, "
            "handheld camera with subtle shake, natural practical lighting, muted desaturated color grade, "
            "fine film grain."
        ),
        "video_prefix": (
            "Cinematic live-action film footage, 35mm lens, handheld camera with subtle natural shake, "
            "natural practical lighting, muted warm-gray desaturated tones, fine film grain, raw human emotion."
        ),
        "lighting": "Natural practical lighting, available interior and street light, muted warm-gray tones",
    },
}


def get_material(material_id: str) -> dict | None:
    """Get built-in or custom material by ID."""
    return MATERIALS.get(material_id)


def list_materials() -> list[dict]:
    """List all available materials (built-in + custom)."""
    return list(MATERIALS.values())


def register_material(material: dict) -> None:
    """Register a custom material at runtime."""
    if material["id"] in _BUILTIN_IDS:
        raise ValueError(f"Cannot override built-in material '{material['id']}'")
    MATERIALS[material["id"]] = material
