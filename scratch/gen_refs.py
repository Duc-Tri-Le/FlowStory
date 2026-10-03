import json
import urllib.request
import urllib.error
import time

BASE = "http://127.0.0.1:8100"
PID = "f0ee1600-5085-47c8-8226-ed62673e2363"

def api(path, method="GET", data=None):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method=method
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8")
        return json.loads(content) if content else {}

# ─── Step 1: Get entities missing media_id ───────────────────
chars = api(f"/api/projects/{PID}/characters")

print("Entity status:")
missing = []
for c in chars:
    mid = c.get("media_id") or "NONE"
    status = "✅ has media_id" if mid != "NONE" else "❌ needs ref"
    print(f"  [{c['entity_type']:<14}] {c['name']:<22} media_id={mid[:8] if mid != 'NONE' else 'NONE':<8} {status}")
    if mid == "NONE":
        missing.append(c)

if not missing:
    print("\n✅ All entities already have reference images!")
    exit(0)

print(f"\n{len(missing)} entities need reference images.")

# ─── Step 2: Submit batch ────────────────────────────────────
requests = []
for c in missing:
    requests.append({
        "type": "GENERATE_CHARACTER_IMAGE",
        "character_id": c["id"],
        "project_id": PID
    })

print(f"\nSubmitting batch of {len(requests)} GENERATE_CHARACTER_IMAGE requests...")
batch_result = api("/api/requests/batch", method="POST", data={"requests": requests})
print(f"✅ Batch submitted: {len(batch_result)} requests queued")

# ─── Step 3: Poll until done ─────────────────────────────────
print("\nPolling batch-status every 15s...")
attempt = 0
while True:
    attempt += 1
    time.sleep(15)
    status = api(f"/api/requests/batch-status?project_id={PID}&type=GENERATE_CHARACTER_IMAGE")
    total = status.get("total", 0)
    pending = status.get("pending", 0)
    processing = status.get("processing", 0)
    completed = status.get("completed", 0)
    failed = status.get("failed", 0)
    done = status.get("done", False)
    print(f"  [{attempt:02d}] total={total} pending={pending} processing={processing} completed={completed} failed={failed} | done={done}")
    if done:
        break
    if attempt > 60:
        print("Timeout after 15 minutes. Check status manually.")
        break

# ─── Step 4: Verify ──────────────────────────────────────────
print("\nVerifying final entity status...")
chars_final = api(f"/api/projects/{PID}/characters")
failed_list = []
print("\n| Entity               | Type           | media_id             | Status |")
print("|----------------------|----------------|----------------------|--------|")
for c in chars_final:
    mid = c.get("media_id") or ""
    ok = bool(mid and len(mid) == 36 and mid.count("-") == 4)
    icon = "✅" if ok else "❌"
    print(f"| {c['name']:<20} | {c['entity_type']:<14} | {mid[:20] if mid else 'NONE':<20} | {icon}     |")
    if not ok:
        failed_list.append(c)

if failed_list:
    print(f"\n⚠️  {len(failed_list)} entities failed:")
    for c in failed_list:
        print(f"  - {c['name']} ({c['id']})")
    print("\nCheck error with: GET /api/requests?project_id=PID&status=FAILED")
    print("Then run REGENERATE_CHARACTER_IMAGE for failed ones.")
else:
    print(f"\n✅ All {len(chars_final)} reference images ready!")
    print("Next: /fk-gen-images to generate scene images.")
