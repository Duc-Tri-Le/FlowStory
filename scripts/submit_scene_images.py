import io
import json
import sys
import urllib.request

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 1. Lấy Active Project
active_resp = json.loads(urllib.request.urlopen("http://127.0.0.1:8100/api/active-project").read().decode("utf-8"))
project_id = active_resp["project_id"]
video_id = active_resp["video_id"]
orientation = active_resp.get("orientation", "VERTICAL")

print(f"Active Project: {active_resp.get('project_name')} (ID: {project_id})")
print(f"Video ID: {video_id} ({orientation})")

# 2. Lấy danh sách scenes
scenes_resp = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8100/api/scenes?video_id={video_id}").read().decode("utf-8"))
print(f"Tìm thấy {len(scenes_resp)} scenes.")

# 3. Tạo batch requests
batch = {
    "requests": [
        {
            "type": "GENERATE_IMAGE",
            "project_id": project_id,
            "scene_id": sc["id"],
            "video_id": video_id,
            "orientation": orientation,
        }
        for sc in scenes_resp
    ]
}

# 4. Gửi batch lên server
url = "http://127.0.0.1:8100/api/requests/batch"
req = urllib.request.Request(
    url,
    data=json.dumps(batch).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    print(f"✅ Đã gửi thành công batch tạo ảnh cho {len(res)} scenes!")
