import json
import urllib.request

API_BASE = "http://127.0.0.1:8100/api"
VIDEO_ID = "13cac219-f3bc-437f-9622-5cd90fb91616"

# Scene timeline mappings based on user's script
durations = {
    1: {"duration": 2.0, "trim_start": 0.0, "trim_end": 2.0},   # 0-2s
    2: {"duration": 2.0, "trim_start": 0.0, "trim_end": 2.0},   # 2-4s
    3: {"duration": 2.0, "trim_start": 0.0, "trim_end": 2.0},   # 4-6s
    4: {"duration": 2.0, "trim_start": 0.0, "trim_end": 2.0},   # 6-8s
    5: {"duration": 3.0, "trim_start": 0.0, "trim_end": 3.0},   # 8-11s
    6: {"duration": 2.0, "trim_start": 0.0, "trim_end": 2.0},   # 11-13s
    7: {"duration": 3.0, "trim_start": 0.0, "trim_end": 3.0},   # 13-16s
    8: {"duration": 3.0, "trim_start": 0.0, "trim_end": 3.0},   # 16-19s
    9: {"duration": 3.0, "trim_start": 0.0, "trim_end": 3.0},   # 19-22s
    10: {"duration": 3.0, "trim_start": 0.0, "trim_end": 3.0},  # 22-25s
    11: {"duration": 1.0, "trim_start": 0.0, "trim_end": 1.0},  # 25-26s
    12: {"duration": 2.0, "trim_start": 0.0, "trim_end": 2.0},  # 26-28s
}

req = urllib.request.Request(f"{API_BASE}/scenes?video_id={VIDEO_ID}")
with urllib.request.urlopen(req) as resp:
    scenes = json.loads(resp.read().decode("utf-8"))

for s in scenes:
    order = s["display_order"]
    if order in durations:
        sid = s["id"]
        patch_payload = durations[order]
        data = json.dumps(patch_payload).encode("utf-8")
        preq = urllib.request.Request(
            f"{API_BASE}/scenes/{sid}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="PATCH"
        )
        with urllib.request.urlopen(preq) as presp:
            res = json.loads(presp.read().decode("utf-8"))
            print(f"Scene {order:02d}: duration set to {res.get('duration')}s (trim: {res.get('trim_start')}s -> {res.get('trim_end')}s)")

print("All scenes successfully updated with duration and trim settings.")
