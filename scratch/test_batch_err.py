import urllib.request
import json
import urllib.error

PID = 'f0ee1600-5085-47c8-8226-ed62673e2363'
VID = 'c23bcadc-487b-440b-9b08-81691e7ed2e1'
sid = '9317f24f-0e31-4ca3-a092-02008cb1ff30'

payload = json.dumps({'requests': [{'type': 'REGENERATE_VIDEO', 'scene_id': sid, 'project_id': PID, 'video_id': VID, 'orientation': 'VERTICAL'}]}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8100/api/requests/batch', data=payload, headers={'Content-Type': 'application/json'})

try:
    resp = urllib.request.urlopen(req)
    print("SUCCESS:", resp.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("ERROR CODE:", e.code)
    print("BODY:", e.read().decode('utf-8'))
