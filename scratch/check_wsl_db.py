import sqlite3
import json

db_path = "/home/ductri/flowkit/flow_agent.db"
con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row
cur = con.cursor()

print("=== PROJECTS in WSL DB ===")
for r in cur.execute("SELECT id, name, created_at FROM project").fetchall():
    print(dict(r))

print("\n=== REQUESTS in WSL DB (last 20) ===")
for r in cur.execute("SELECT id, type, project_id, scene_id, status, error_message, media_id, created_at FROM request ORDER BY created_at DESC LIMIT 20").fetchall():
    print(dict(r))

print("\n=== SCENES in WSL DB for video 5dd13489-bde7-4856-a65c-ff87b0da775a ===")
for r in cur.execute("SELECT id, scene_index, vertical_image_media_id, vertical_video_media_id FROM scene WHERE video_id='5dd13489-bde7-4856-a65c-ff87b0da775a'").fetchall():
    print(dict(r))
