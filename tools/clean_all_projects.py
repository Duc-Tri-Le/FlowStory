#!/usr/bin/env python3
"""Clean all project data, scenes, videos, characters, requests, and generated project files."""
import os
import shutil
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "flow_agent.db"
BAK_PATH = ROOT / "flow_agent.db.bak"
OUTPUT_DIR = ROOT / "output"

def clean_database():
    if not DB_PATH.exists():
        print(f"Database {DB_PATH} does not exist.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    tables = ["request", "scene", "video", "project_character", "project", "character"]
    print("--- Trạng thái dữ liệu trước khi xóa ---")
    for t in tables:
        try:
            cnt = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t:<18}: {cnt} bản ghi")
        except Exception as e:
            print(f"  {t:<18}: lỗi ({e})")

    # Xóa toàn bộ dữ liệu dự án
    conn.execute("PRAGMA foreign_keys = OFF;")
    for t in tables:
        c.execute(f"DELETE FROM {t};")
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON;")

    # Checkpoint WAL và giải phóng bộ nhớ
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.execute("VACUUM;")
    except Exception as e:
        print(f"Warning on vacuum/checkpoint: {e}")

    print("\n--- Trạng thái sau khi xóa ---")
    for t in tables:
        cnt = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<18}: {cnt} bản ghi")

    conn.close()

def clean_files():
    print("\n--- Xóa các file dữ liệu và bộ nhớ đệm ---")

    # 1. Xóa file backup cũ nếu có
    if BAK_PATH.exists():
        BAK_PATH.unlink()
        print(f"  [x] Đã xóa {BAK_PATH.name}")

    # 2. Xóa active_project.json
    for p in [ROOT / "agent" / "active_project.json", ROOT / "active_project.json"]:
        if p.exists():
            p.unlink()
            print(f"  [x] Đã xóa {p.name}")

    # 3. Dọn dẹp thư mục output
    if OUTPUT_DIR.exists():
        # Dọn dẹp output/storytime/audio
        st_audio = OUTPUT_DIR / "storytime" / "audio"
        if st_audio.exists():
            for f in st_audio.glob("*"):
                if f.is_file():
                    f.unlink()
                    print(f"  [x] Đã xóa file âm thanh: {f.name}")

        # Dọn dẹp output/test_audio
        test_audio = OUTPUT_DIR / "test_audio"
        if test_audio.exists():
            for f in test_audio.glob("*"):
                if f.is_file():
                    f.unlink()
                    print(f"  [x] Đã xóa file test audio: {f.name}")

        # Dọn dẹp file test mp3 / json
        for test_file in [OUTPUT_DIR / "test_edge_tts.mp3", OUTPUT_DIR / "test_words.json"]:
            if test_file.exists():
                test_file.unlink()
                print(f"  [x] Đã xóa: {test_file.name}")

        # Dọn dẹp toàn bộ các thư mục pkg_* trong storytime
        st_dir = OUTPUT_DIR / "storytime"
        if st_dir.exists():
            for pkg_folder in st_dir.glob("pkg_*"):
                if pkg_folder.is_dir():
                    shutil.rmtree(pkg_folder, ignore_errors=True)
                    print(f"  [x] Đã xóa gói storytime: {pkg_folder.name}")

        # Dọn dẹp output/preview
        preview_dir = OUTPUT_DIR / "preview"
        if preview_dir.exists():
            shutil.rmtree(preview_dir, ignore_errors=True)
            print(f"  [x] Đã xóa thư mục preview video")

        # Xóa sample_remotion_dist nếu có
        sample_rem = OUTPUT_DIR / "sample_remotion_dist"
        if sample_rem.exists():
            shutil.rmtree(sample_rem, ignore_errors=True)
            print(f"  [x] Đã xóa thư mục sample_remotion_dist")

        # Xóa các thư mục project riêng biệt nếu có trong output/
        for item in OUTPUT_DIR.iterdir():
            if item.is_dir() and item.name not in ["storytime", "test_audio"]:
                shutil.rmtree(item, ignore_errors=True)
                print(f"  [x] Đã xóa thư mục output dự án: {item.name}")

if __name__ == "__main__":
    clean_database()
    clean_files()
    print("\n✅ ĐÃ XÓA TOÀN BỘ DỰ ÁN VÀ DATA LIÊN QUAN THÀNH CÔNG!")
