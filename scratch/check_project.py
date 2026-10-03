import urllib.request
import json
import sys
sys.stdout.reconfigure(encoding="utf-8")

PID = "f0ee1600-5085-47c8-8226-ed62673e2363"
VID = "5dd13489-bde7-4856-a65c-ff87b0da775a"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "test"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("=== PROJECT ===")
proj = get(f"http://127.0.0.1:8100/api/projects/{PID}")
print(f"ID: {proj['id']}")
print(f"Name: {proj['name']}")

print("\n=== CHARACTERS ===")
chars = get(f"http://127.0.0.1:8100/api/projects/{PID}/characters")
for c in chars:
    mid = c.get("media_id") or "NONE"
    url = c.get("image_url") or "NONE"
    print(f"  {c['name']:<20} | Type: {c.get('entity_type'):<12} | media_id: {mid[:15]}... | url: {url[:60]}...")

print("\n=== SCENES ===")
scenes = get(f"http://127.0.0.1:8100/api/scenes?video_id={VID}")
print(f"Total scenes: {len(scenes)}")
for s in scenes:
    idx = s.get("scene_index")
    sid = s.get("id")
    img_mid = s.get("vertical_image_media_id") or "NONE"
    img_status = s.get("vertical_image_status") or "NONE"
    img_url = s.get("vertical_image_url") or "NONE"
    vid_mid = s.get("vertical_video_media_id") or "NONE"
    vid_status = s.get("vertical_video_status") or "NONE"
    print(f"Scene {idx} ({sid[:8]}): img_status={img_status} img_mid={img_mid[:15]} vid_status={vid_status} vid_mid={vid_mid[:15]}")
    print(f"   image_url: {img_url[:80]}...")
