import json
import urllib.request

req = urllib.request.Request(
    "http://127.0.0.1:8100/api/models",
    data=json.dumps({"default_video_model_family": "veo"}).encode(),
    headers={"Content-Type": "application/json"},
    method="PATCH"
)

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    print("Response status:", res.get("status"))
    print("Models default_video_model_family:", res.get("models", {}).get("default_video_model_family"))
