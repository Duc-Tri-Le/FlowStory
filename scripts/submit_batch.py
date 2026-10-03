import json
import urllib.request

url = "http://127.0.0.1:8100/api/requests/batch"
data = {
    "requests": [
        {
            "type": "GENERATE_CHARACTER_IMAGE",
            "character_id": "char-caube-01",
            "project_id": "662aacf3-af1f-4dd1-a40f-7efff09b2211",
        },
        {
            "type": "GENERATE_CHARACTER_IMAGE",
            "character_id": "char-cobe-01",
            "project_id": "662aacf3-af1f-4dd1-a40f-7efff09b2211",
        },
        {
            "type": "GENERATE_CHARACTER_IMAGE",
            "character_id": "loc-langque-01",
            "project_id": "662aacf3-af1f-4dd1-a40f-7efff09b2211",
        },
        {
            "type": "GENERATE_CHARACTER_IMAGE",
            "character_id": "asset-quabong-01",
            "project_id": "662aacf3-af1f-4dd1-a40f-7efff09b2211",
        },
    ]
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    print("Submitted batch:", len(res), "requests queued.")
