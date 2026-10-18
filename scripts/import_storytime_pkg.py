#!/usr/bin/env python3
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.stdout.reconfigure(encoding="utf-8")

from agent.db import crud
from agent.api.active_project import _write_state

async def import_pkg(pkg_dir_name: str):
    pkg_path = ROOT_DIR / "output" / "storytime" / pkg_dir_name / "package.json"
    if not pkg_path.exists():
        print(f"Error: {pkg_path} does not exist.")
        return

    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    title = "Mộc Tinh — Cây Biết Gọi Tên"
    scenes = pkg.get("scenes", [])
    full_text = "\n\n".join(s.get("text", "") for s in scenes)
    dur_min = round(pkg.get("total_duration_seconds", 0) / 60, 1)

    # 1. Create project
    proj = await crud.create_project(
        name=title,
        story=full_text[:3000],
        description=f"Kịch bản Storytime Noir ({len(scenes)} phân cảnh, ~{dur_min} phút)",
        material="realistic",
        allow_voice=True
    )
    print(f"✅ Created Project: {proj['name']} (ID: {proj['id']})")

    # 2. Create Video
    video = await crud.create_video(
        project_id=proj["id"],
        title=title,
        display_order=0,
        orientation="VERTICAL"
    )
    print(f"✅ Created Video: {video['id']}")

    # 3. Create Scenes
    for i, sc in enumerate(scenes):
        txt = sc.get("text", "")
        bg = sc.get("background_prompt", "")
        cam = sc.get("camera", "zoom_in")
        exp = sc.get("expression", "serious")
        dur = sc.get("duration_seconds", 4.0)

        s_rec = await crud.create_scene(
            video_id=video["id"],
            display_order=i,
            prompt=txt,
            image_prompt=bg,
            video_prompt=f"{txt}. Camera: {cam}. Expression: {exp}.",
            duration=dur
        )
        if txt:
            await crud.update_scene(s_rec["id"], narrator_text=txt)

    print(f"✅ Created {len(scenes)} scenes in database!")

    # 4. Set as active project
    _write_state({"project_id": proj["id"]})
    print(f"✅ Set active project to {proj['id']}")

if __name__ == "__main__":
    asyncio.run(import_pkg("pkg_c5d56649"))
