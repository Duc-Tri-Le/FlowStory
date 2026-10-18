import urllib.request
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PID = "468d1620-8c08-437a-8df8-1fbeb7a824fb"
url = f"http://127.0.0.1:8100/api/projects/{PID}/characters"

with urllib.request.urlopen(url) as resp:
    chars = json.loads(resp.read().decode("utf-8"))

print("| Entity | Type | media_id | Status |")
print("|--------|------|----------|--------|")
for c in chars:
    mid = c.get("media_id")
    status = "OK" if mid else "MISSING"
    print(f"| {c['name']} | {c['entity_type']} | `{mid}` | {status} |")
