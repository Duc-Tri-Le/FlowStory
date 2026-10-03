import asyncio
import json
from agent.sdk.persistence.sqlite_repository import SQLiteRepository
from agent.api.projects import _build_character_profile
from agent.materials import get_material

PROJECT_ID = "8b2fdb28-a2db-44bd-a76e-7a9356970dd3"
VIDEO_ID = "13cac219-f3bc-437f-9622-5cd90fb91616"
NEW_MATERIAL = "anime"

async def main():
    repo = SQLiteRepository()
    
    # 1. Update project material
    await repo.update("project", PROJECT_ID, material=NEW_MATERIAL)
    print(f"Project {PROJECT_ID} updated to material: {NEW_MATERIAL}")
    
    # 2. Update characters / entities image prompts
    characters = await repo.get_project_characters(PROJECT_ID)
    project_row = await repo.get_project(PROJECT_ID)
    story = project_row.story if hasattr(project_row, "story") else project_row.get("story")
    
    # Extract base descriptions
    base_descriptions = {
        "Wife": "A 28-year-old Asian woman with shoulder-length soft brown hair, gentle facial features, wearing comfortable casual home attire including a cream knit sweater and dark trousers. Expressive hazel-brown eyes, natural makeup.",
        "Husband": "A 32-year-old Asian man with short neat black hair, clean-shaven, sharp jawline, wearing a casual navy blue button-down shirt with rolled-up sleeves and grey trousers. Stern demeanor.",
        "Living Room": "Modern family living room in the evening, with a large neutral grey fabric sofa, wooden coffee table, warm ambient lamp light casting cozy yet tense shadows, clean contemporary shelves in the soft-focus background.",
        "DNA Test Document": "An official printed medical test report paper with crisp black text, laboratory header logo, and clear printed checkmarks and tables."
    }
    
    for c in characters:
        base_desc = base_descriptions.get(c.name, c.description.split(". Story context:")[0] if c.description else c.name)
        profile = _build_character_profile(
            char_name=c.name,
            char_desc=base_desc,
            story=story,
            entity_type=c.entity_type,
            material_id=NEW_MATERIAL
        )
        await repo.update("character", c.id, image_prompt=profile["image_prompt"], description=profile["description"])
        print(f"Updated entity '{c.name}' image_prompt with {NEW_MATERIAL} style.")
        
    # 3. Update scene prompts prefix
    old_prefix = "Real RAW photograph, shot on Canon EOS R5, 35mm lens, natural available light."
    new_mat = get_material(NEW_MATERIAL)
    new_prefix = new_mat["scene_prefix"]
    
    scenes = await repo.list_scenes(VIDEO_ID)
    for s in scenes:
        prompt = s.prompt
        if prompt.startswith(old_prefix):
            clean_body = prompt[len(old_prefix):].strip()
            prompt = f"{new_prefix} {clean_body}"
        elif not prompt.startswith(new_prefix):
            prompt = f"{new_prefix} {prompt}"
            
        await repo.update("scene", s.id, prompt=prompt)
        print(f"Scene {s.display_order} prompt updated.")
        
    print("All entities and scenes successfully updated to 2D Anime style!")

if __name__ == "__main__":
    asyncio.run(main())
