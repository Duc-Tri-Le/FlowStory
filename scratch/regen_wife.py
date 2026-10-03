import json, urllib.request, time

BASE = "http://127.0.0.1:8100"
PID = "f0ee1600-5085-47c8-8226-ed62673e2363"
WIFE_CID = "65531981-81c0-4a23-ad3a-e95a71b4fccf"

def api(path, method="GET", data=None):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method=method
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")

# ─── Round 2: Full back view, strip age/ethnicity, minimal description ──
BACK_VIEW_PROMPT = (
    "Single reference image of a woman seen from behind. "
    "Back view, full silhouette from head to toe, standing naturally upright. "
    "Long straight dark-brown hair falling below the shoulders. "
    "Slim build. "
    "Wearing a cream-colored knit sweater and dark-blue jeans. "
    "Standing in a neutral indoor environment with soft warm lighting. "
    "COMPOSITION: Full body back view, centered in frame, neutral simple background. "
    "ONE single image only, NOT a multi-panel grid or multiple views. "
    "Photorealistic RAW photograph, 50mm lens, natural lighting. "
    "NOT 3D render, NOT CGI, NOT illustration. "
    "Studio lighting, highly detailed."
)

print("Round 2: Updating Wife to back view prompt...")
api(f"/api/characters/{WIFE_CID}", method="PATCH", data={"image_prompt": BACK_VIEW_PROMPT})
print("  ✅ image_prompt updated (back view)")

print("Submitting REGENERATE_CHARACTER_IMAGE for Wife...")
result = api("/api/requests", method="POST", data={
    "type": "REGENERATE_CHARACTER_IMAGE",
    "character_id": WIFE_CID,
    "project_id": PID
})
print(f"  ✅ Request queued: {result.get('id')} | status: {result.get('status')}")

# Poll
print("\nPolling every 15s...")
for i in range(20):
    time.sleep(15)
    status = api(f"/api/requests/batch-status?project_id={PID}&type=REGENERATE_CHARACTER_IMAGE")
    completed = status.get("completed", 0)
    failed = status.get("failed", 0)
    done = status.get("done", False)
    print(f"  [{i+1:02d}] completed={completed} failed={failed} done={done}")
    if done:
        break

# Verify
wife = api(f"/api/characters/{WIFE_CID}")
mid = wife.get("media_id") or "NONE"
if mid != "NONE":
    print(f"\n✅ Wife ref image ready! media_id={mid}")
    print("All 6 entities complete. Next: /fk-gen-images")
else:
    # Round 3: Generic silhouette, clothing only
    print(f"\n❌ Still failed. Trying Round 3: generic silhouette, clothing only...")
    GENERIC_PROMPT = (
        "Single reference image of a woman seen from behind, full body silhouette. "
        "Wearing a light-colored knit sweater and dark jeans. "
        "Standing in front of a neutral grey background. "
        "Back view, head to toe. "
        "Photorealistic photograph. "
        "ONE single image only."
    )
    api(f"/api/characters/{WIFE_CID}", method="PATCH", data={"image_prompt": GENERIC_PROMPT})
    result = api("/api/requests", method="POST", data={
        "type": "REGENERATE_CHARACTER_IMAGE",
        "character_id": WIFE_CID,
        "project_id": PID
    })
    print(f"  ✅ Round 3 queued: {result.get('id')}")
    for i in range(10):
        time.sleep(15)
        status = api(f"/api/requests/batch-status?project_id={PID}&type=REGENERATE_CHARACTER_IMAGE")
        done = status.get("done", False)
        print(f"  [{i+1:02d}] completed={status.get('completed',0)} failed={status.get('failed',0)} done={done}")
        if done:
            break
    wife = api(f"/api/characters/{WIFE_CID}")
    mid = wife.get("media_id") or "NONE"
    if mid != "NONE":
        print(f"\n✅ Wife ref image ready! media_id={mid}")
    else:
        print(f"\n❌ Round 3 also failed. Manual intervention needed.")
