"""Script to safely delete unfinished projects from flow_agent.db."""
import sqlite3
import json
import sys
import io
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DB_PATH = Path(__file__).parent.parent / "flow_agent.db"
ACTIVE_PROJECT_PATH = Path(__file__).parent.parent / "agent" / "active_project.json"

TARGET_PROJECT_IDS = [
    "468d1620-8c08-437a-8df8-1fbeb7a824fb",  # Linh - Hành Trình Trở Về (OverSimplified 2D)
    "d01d248b-4421-40de-9b96-54b0be4d3c76",  # Linh - Hành Trình Trở Về (draft)
    "a9957315-2929-4a39-9e77-8c127f7fbd5c",  # Khi Chúng Ta Lớn Lên
    "1a6e23b5-cf13-43c3-8b2b-5beb65028a03",  # Não tàn ngược
]

KEEP_PROJECT_ID = "8b2fdb28-a2db-44bd-a76e-7a9356970dd3"  # The DNA Test Shock

def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    c = conn.cursor()

    print("=== Bắt đầu xóa các dự án chưa hoàn thiện ===")
    
    # 1. Tìm các character chỉ thuộc về các dự án bị xóa
    placeholders = ",".join("?" * len(TARGET_PROJECT_IDS))
    chars_to_delete = [
        row[0] for row in c.execute(
            f"SELECT DISTINCT character_id FROM project_character WHERE project_id IN ({placeholders})",
            TARGET_PROJECT_IDS
        ).fetchall()
    ]
    
    # Đếm số lượng trước khi xóa
    del_projects_count = len(TARGET_PROJECT_IDS)
    del_videos_count = c.execute(
        f"SELECT COUNT(*) FROM video WHERE project_id IN ({placeholders})",
        TARGET_PROJECT_IDS
    ).fetchone()[0]
    
    del_scenes_count = c.execute(
        f"""SELECT COUNT(*) FROM scene s 
            JOIN video v ON s.video_id = v.id 
            WHERE v.project_id IN ({placeholders})""",
        TARGET_PROJECT_IDS
    ).fetchone()[0]
    
    del_requests_count = c.execute(
        f"SELECT COUNT(*) FROM request WHERE project_id IN ({placeholders})",
        TARGET_PROJECT_IDS
    ).fetchone()[0]

    # Thực hiện xóa trong transaction
    with conn:
        # Xóa các project (cascade sẽ xóa video, scene, request, project_character)
        c.execute(f"DELETE FROM project WHERE id IN ({placeholders})", TARGET_PROJECT_IDS)
        
        # Xóa các character đã được gỡ liên kết
        if chars_to_delete:
            char_placeholders = ",".join("?" * len(chars_to_delete))
            c.execute(
                f"DELETE FROM character WHERE id IN ({char_placeholders})",
                chars_to_delete
            )
            
    try:
        c.execute("PRAGMA wal_checkpoint(PASSIVE);")
    except Exception as e:
        print(f"Lưu ý checkpoint: {e}")

    print(f"Đã xóa thành công:")
    print(f"- Dự án (project): {del_projects_count}")
    print(f"- Nhân vật / Asset (character): {len(chars_to_delete)}")
    print(f"- Video: {del_videos_count}")
    print(f"- Phân cảnh (scene): {del_scenes_count}")
    print(f"- Yêu cầu tạo media (request): {del_requests_count}")

    # Cập nhật active_project.json về dự án còn lại
    if ACTIVE_PROJECT_PATH.exists():
        ACTIVE_PROJECT_PATH.write_text(
            json.dumps({"project_id": KEEP_PROJECT_ID}, indent=2),
            encoding="utf-8"
        )
        print(f"Đã cập nhật active_project.json trỏ về dự án còn lại: {KEEP_PROJECT_ID}")

    # Kiểm tra trạng thái các dự án còn lại trong DB
    remaining = c.execute("SELECT id, name, status, created_at FROM project").fetchall()
    print("\nCác dự án còn lại trong database:")
    for p in remaining:
        print(f"- ID: {p[0]} | Tên: {p[1]} | Trạng thái: {p[2]}")

if __name__ == "__main__":
    main()
