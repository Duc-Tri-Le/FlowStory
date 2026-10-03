import urllib.request, json

VID = "13cac219-f3bc-437f-9622-5cd90fb91616"
url = f"http://127.0.0.1:8100/api/scenes?video_id={VID}"
res = urllib.request.urlopen(url)
scenes = json.loads(res.read().decode('utf-8'))

print(f"{'Scene':<7} | {'Order':<5} | {'Video Status':<12} | {'Video Media ID':<36} | {'Video URL'}")
print("-" * 120)
for s in sorted(scenes, key=lambda x: x['display_order']):
    vurl = s['horizontal_video_url'] or ''
    # Shorten vurl for display if too long
    vurl_short = (vurl[:50] + '...') if len(vurl) > 50 else vurl
    print(f"Scene {s['display_order']:<2} | {s['display_order']:<5} | {s['horizontal_video_status']:<12} | {s['horizontal_video_media_id']:<36} | {vurl_short}")
