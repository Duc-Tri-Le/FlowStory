import json
import urllib.request

req = urllib.request.Request(
    "http://127.0.0.1:8100/api/models",
    data=json.dumps({"default_video_model_family": "omni_flash"}).encode(),
    headers={"Content-Type": "application/json"},
    method="PATCH"
)
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    print("Updated default_video_model_family:", res["models"].get("default_video_model_family"))
