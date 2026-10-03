import sqlite3
import json

con = sqlite3.connect("flow_agent.db")
con.row_factory = sqlite3.Row
cur = con.cursor()

print("--- SCENES FOR VIDEO 5dd13489-bde7-4856-a65c-ff87b0da775a ---")
cur.execute("SELECT id, video_id, vertical_image_media_id, vertical_image_url, vertical_image_status FROM scene WHERE video_id='5dd13489-bde7-4856-a65c-ff87b0da775a'")
scenes = cur.fetchall()
print(f"Count: {len(scenes)}")
for s in scenes:
    print(dict(s))

print("\n--- REQUESTS FOR VIDEO 5dd13489-bde7-4856-a65c-ff87b0da775a ---")
cur.execute("SELECT * FROM request WHERE video_id='5dd13489-bde7-4856-a65c-ff87b0da775a'")
reqs = cur.fetchall()
print(f"Count: {len(reqs)}")
for r in reqs:
    print(dict(r))

print("\n--- REQUESTS FOR PROJECT f0ee1600-5085-47c8-8226-ed62673e2363 ---")
cur.execute("SELECT * FROM request WHERE project_id='f0ee1600-5085-47c8-8226-ed62673e2363'")
reqs = cur.fetchall()
print(f"Count: {len(reqs)}")
for r in reqs:
    print(dict(r))
