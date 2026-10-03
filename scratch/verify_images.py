import urllib.request, json

VID = "13cac219-f3bc-437f-9622-5cd90fb91616"
url = f"http://127.0.0.1:8100/api/scenes?video_id={VID}"
res = urllib.request.urlopen(url)
scenes = json.loads(res.read().decode('utf-8'))

print(f"{'Scene':<7} | {'Order':<5} | {'Chain':<12} | {'Image Status':<12} | {'Media ID (UUID)':<36}")
print("-" * 80)
for s in sorted(scenes, key=lambda x: x['display_order']):
    print(f"Scene {s['display_order']:<2} | {s['display_order']:<5} | {s['chain_type']:<12} | {s['horizontal_image_status']:<12} | {s['horizontal_image_media_id']:<36}")
