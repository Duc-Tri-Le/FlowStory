#!/usr/bin/env python3
"""
Flow Kit — Standalone Project Creation CLI

Creates a complete Flow Kit project (Project -> Video -> Scenes -> Active Project)
via the local Flow Kit API.

Works with any environment (Antigravity, Codex, Terminal, CI).

Usage:
    # Interactive wizard:
    python scripts/create_project.py -i

    # From JSON template:
    python scripts/create_project.py --file project_spec.json

    # Quick test project:
    python scripts/create_project.py --name "Cyber City" --material cyberpunk --story "A detective investigates neon shadows."
"""

import argparse
import io
import json
import sys
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

API_BASE = "http://127.0.0.1:8100"


def http_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    url = f"{API_BASE}{endpoint}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("detail", error_body)
        except Exception:
            msg = error_body
        raise RuntimeError(f"HTTP {e.code} on {method} {endpoint}: {msg}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot connect to Flow Kit backend at {API_BASE}: {e.reason}") from e


def check_health():
    print("Checking Flow Kit backend health...")
    try:
        health = http_request("/health")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please ensure the Flow Kit server is running: python -m agent.main")
        sys.exit(1)

    if not health.get("extension_connected"):
        print("⚠️  Warning: Chrome extension is NOT connected.")
        print("   Make sure Chrome is running with the extension loaded and flow.google.com opened.")
    else:
        print("✅ Backend connected and Chrome extension ready.")


def list_materials() -> list[dict]:
    try:
        return http_request("/api/materials")
    except Exception:
        return [
            {"id": "realistic", "name": "Photorealistic"},
            {"id": "3d_pixar", "name": "3D Pixar"},
            {"id": "anime", "name": "Anime"},
            {"id": "stop_motion", "name": "Stop Motion"},
            {"id": "minecraft", "name": "Minecraft"},
            {"id": "oil_painting", "name": "Oil Painting"},
        ]


def create_project_pipeline(spec: dict) -> dict:
    """Execute full creation pipeline from a spec dict."""
    check_health()

    project_name = spec.get("name")
    if not project_name:
        raise ValueError("Project name is required")

    material = spec.get("material", "realistic")
    story = spec.get("story", "")
    description = spec.get("description", story)
    characters = spec.get("characters", [])
    scenes_spec = spec.get("scenes", [])
    orientation = spec.get("orientation", "VERTICAL").upper()

    print(f"\n1. Creating Project '{project_name}' (material: {material})...")
    project_payload = {
        "name": project_name,
        "description": description,
        "story": story,
        "material": material,
        "characters": characters,
    }
    if spec.get("flow_project_id"):
        project_payload["flow_project_id"] = spec["flow_project_id"]
    project = http_request("/api/projects", method="POST", data=project_payload)
    project_id = project["id"]
    print(f"   ✅ Project created: {project_name} (ID: {project_id})")

    # Fetch created entities to get IDs
    entities = http_request(f"/api/projects/{project_id}/characters")
    print(f"   Linked {len(entities)} reference entities:")
    for ent in entities:
        print(f"     - [{ent.get('entity_type', 'character')}] {ent['name']} (ID: {ent['id']})")

    # 2. Create Video
    video_title = spec.get("video_title", f"{project_name} - Main")
    print(f"\n2. Creating Video '{video_title}' ({orientation})...")
    video_payload = {
        "project_id": project_id,
        "title": video_title,
        "display_order": 0,
        "orientation": orientation,
    }
    video = http_request("/api/videos", method="POST", data=video_payload)
    video_id = video["id"]
    print(f"   ✅ Video created (ID: {video_id})")

    # 3. Create Scenes
    created_scenes = []
    if scenes_spec:
        print(f"\n3. Creating {len(scenes_spec)} Scenes...")
        scene_id_map = {}  # index or temp_id -> actual scene_id

        for idx, sc in enumerate(scenes_spec):
            chain_type = sc.get("chain_type", "ROOT")
            parent_ref = sc.get("parent_scene_id")
            # If parent_ref is an integer index, resolve it
            parent_id = None
            if isinstance(parent_ref, int) and parent_ref in scene_id_map:
                parent_id = scene_id_map[parent_ref]
            elif isinstance(parent_ref, str) and parent_ref in scene_id_map:
                parent_id = scene_id_map[parent_ref]
            elif parent_ref:
                parent_id = str(parent_ref)

            scene_payload = {
                "video_id": video_id,
                "display_order": sc.get("display_order", idx),
                "prompt": sc.get("prompt", ""),
                "video_prompt": sc.get("video_prompt", ""),
                "transition_prompt": sc.get("transition_prompt", ""),
                "character_names": sc.get("character_names", []),
                "chain_type": chain_type,
                "parent_scene_id": parent_id,
            }
            scene_res = http_request("/api/scenes", method="POST", data=scene_payload)
            sid = scene_res["id"]
            if sc.get("narrator_text"):
                try:
                    http_request(f"/api/scenes/{sid}", method="PATCH", data={"narrator_text": sc["narrator_text"]})
                except Exception as patch_err:
                    print(f"     ⚠️  Warning patching narrator_text for scene {sid[:8]}: {patch_err}")
            scene_id_map[idx] = sid
            if "id" in sc:
                scene_id_map[sc["id"]] = sid
            created_scenes.append(scene_res)
            print(f"   ✅ Scene {idx + 1} created: [{chain_type}] {scene_payload['prompt'][:60]}... (ID: {sid[:8]})")
    else:
        print("\n3. No scenes provided in spec (can be added later via /api/scenes).")

    # 4. Set Active Project
    print("\n4. Setting as Active Project...")
    try:
        http_request("/api/active-project", method="PUT", data={"project_id": project_id})
        print(f"   ✅ Active project set to {project_name} ({project_id})")
    except Exception as e:
        print(f"   ⚠️ Could not set active project: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("  PROJECT CREATION COMPLETE")
    print("=" * 60)
    print(f"  Project Name: {project_name}")
    print(f"  Project ID:   {project_id}")
    print(f"  Video ID:     {video_id}")
    print(f"  Orientation:  {orientation}")
    print(f"  Material:     {material}")
    print(f"  Entities:     {len(entities)}")
    print(f"  Scenes:       {len(created_scenes)}")
    print("\nNext steps in Flow Kit pipeline:")
    print(f"  1. Generate reference images:  POST /api/requests/batch (type=GENERATE_CHARACTER_IMAGE)")
    print(f"  2. Generate scene images:      POST /api/requests/batch (type=GENERATE_IMAGE)")
    print(f"  3. Generate videos:            POST /api/requests/batch (type=GENERATE_VIDEO)")
    print("=" * 60 + "\n")

    return {
        "project": project,
        "video": video,
        "scenes": created_scenes,
        "entities": entities,
    }


def interactive_wizard():
    print("=" * 60)
    print("  Flow Kit — Project Creation Wizard")
    print("=" * 60 + "\n")

    check_health()

    name = input("\nProject Name: ").strip()
    while not name:
        name = input("Project Name (required): ").strip()

    story = input("Story Summary / Plot: ").strip()

    materials = list_materials()
    print("\nAvailable Materials (Visual Styles):")
    for idx, m in enumerate(materials):
        print(f"  [{idx + 1}] {m['id']} ({m.get('name', '')})")
    mat_choice = input(f"Select material [1-{len(materials)}] (default: 1): ").strip()
    try:
        material_idx = int(mat_choice) - 1
        material = materials[material_idx]["id"]
    except (ValueError, IndexError):
        material = "realistic"

    orientation_choice = input("Orientation [1: VERTICAL (9:16), 2: HORIZONTAL (16:9)] (default: 1): ").strip()
    orientation = "HORIZONTAL" if orientation_choice == "2" else "VERTICAL"

    # Entities
    print("\n--- Reference Entities (Characters, Locations, Visual Assets) ---")
    characters = []
    while True:
        ent_name = input("\nEntity Name (leave empty to finish): ").strip()
        if not ent_name:
            break
        print("Entity Type: [1] character, [2] location, [3] visual_asset, [4] creature")
        t_choice = input("Select type (default: 1): ").strip()
        t_map = {"1": "character", "2": "location", "3": "visual_asset", "4": "creature"}
        ent_type = t_map.get(t_choice, "character")

        desc = input(f"Visual Description for '{ent_name}' (physical appearance only): ").strip()
        voice_desc = ""
        if ent_type == "character":
            voice_desc = input("Voice Description (optional, e.g. 'Deep gravelly calm voice'): ").strip()

        ent = {
            "name": ent_name,
            "entity_type": ent_type,
            "description": desc,
        }
        if voice_desc:
            ent["voice_description"] = voice_desc
        characters.append(ent)

    # Scenes
    print("\n--- Scenes ---")
    scene_count_str = input("Number of initial scenes to create (default: 2, 0 to skip): ").strip()
    try:
        scene_count = int(scene_count_str) if scene_count_str else 2
    except ValueError:
        scene_count = 2

    scenes = []
    for i in range(scene_count):
        print(f"\nScene #{i + 1}:")
        prompt = input("  Image prompt (action + environment only, English): ").strip()
        vid_prompt = input("  Video prompt (Veo 3 description + audio cues): ").strip()
        narr_text = input("  Narrator text (optional voiceover): ").strip()
        ref_names = input("  Entities in this scene (comma-separated names, e.g. Luna, Castle): ").strip()
        char_names = [n.strip() for n in ref_names.split(",") if n.strip()]

        chain_type = "ROOT"
        parent_idx = None
        if i > 0:
            c_input = input("  Chain type: [1] ROOT (new scene), [2] CONTINUATION (from previous): ").strip()
            if c_input == "2":
                chain_type = "CONTINUATION"
                parent_idx = i - 1

        scenes.append({
            "prompt": prompt,
            "video_prompt": vid_prompt,
            "narrator_text": narr_text,
            "character_names": char_names,
            "chain_type": chain_type,
            "parent_scene_id": parent_idx,
        })

    spec = {
        "name": name,
        "story": story,
        "material": material,
        "orientation": orientation,
        "characters": characters,
        "scenes": scenes,
    }

    create_project_pipeline(spec)


def main():
    parser = argparse.ArgumentParser(description="Create a Flow Kit Project")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run interactive wizard")
    parser.add_argument("-f", "--file", help="Path to JSON file defining project specification")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--story", help="Project story/plot")
    parser.add_argument("--material", default="realistic", help="Visual material style (default: realistic)")
    parser.add_argument("--orientation", default="VERTICAL", choices=["VERTICAL", "HORIZONTAL"])

    args = parser.parse_args()

    if args.interactive:
        interactive_wizard()
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            spec = json.load(f)
        create_project_pipeline(spec)
    elif args.name:
        spec = {
            "name": args.name,
            "story": args.story or "",
            "material": args.material,
            "orientation": args.orientation,
            "characters": [],
            "scenes": [],
        }
        create_project_pipeline(spec)
    else:
        # Default to interactive wizard if no args given
        interactive_wizard()


if __name__ == "__main__":
    main()
