import json
import urllib.request

url = "http://127.0.0.1:8100/api/projects/662aacf3-af1f-4dd1-a40f-7efff09b2211/characters"
with urllib.request.urlopen(url) as resp:
    chars = json.loads(resp.read().decode("utf-8"))
    for c in chars:
        print(f"Name: {c['name']} | Type: {c['entity_type']} | MediaID: {c['media_id']} | Has URL: {bool(c['reference_image_url'])}")
