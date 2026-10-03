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

# Check failed request error
print("=== Failed requests ===")
reqs = api(f"/api/requests?project_id={PID}&status=FAILED")
for r in reqs:
    print(f"type: {r.get('type')} | char_id: {r.get('character_id')} | error: {r.get('error_message')}")

# Check Wife current image_prompt
print("\n=== Wife current image_prompt ===")
wife = api(f"/api/characters/{WIFE_CID}")
print(f"name: {wife.get('name')}")
print(f"media_id: {wife.get('media_id')}")
print(f"image_prompt:\n{wife.get('image_prompt')}")
