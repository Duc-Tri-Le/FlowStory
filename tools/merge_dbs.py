import shutil
import sqlite3
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

src_bak = ROOT / "flow_agent.db.bak"
dst_db = ROOT / "flow_agent.db"
wsl_db = ROOT / "wsl_flow_agent.db"

# 1. Ensure flow_agent.db exists from bak
if not dst_db.exists() or dst_db.stat().st_size == 0:
    shutil.copyfile(src_bak, dst_db)
    print("Created flow_agent.db from flow_agent.db.bak")

conn = sqlite3.connect(str(dst_db))
conn.execute(f"ATTACH DATABASE '{wsl_db.as_posix()}' AS wsl")

tables = ["material", "project", "character", "project_character", "video", "scene", "request"]

for t in tables:
    before = conn.execute(f"SELECT COUNT(*) FROM main.{t}").fetchone()[0]
    conn.execute(f"INSERT OR IGNORE INTO main.{t} SELECT * FROM wsl.{t}")
    after = conn.execute(f"SELECT COUNT(*) FROM main.{t}").fetchone()[0]
    added = after - before
    print(f"Table {t:<18}: {before} -> {after} (+{added})")

conn.commit()
conn.close()

# Cleanup temporary wsl_flow_agent.db
if wsl_db.exists():
    wsl_db.unlink()
    print("Removed temporary wsl_flow_agent.db")

print("\nAll projects merged into flow_agent.db successfully!")
