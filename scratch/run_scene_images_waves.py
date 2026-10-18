"""Run wave-by-wave scene image generation for active video."""
import urllib.request
import json
import time
import sys
import io

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PID = "a0558109-06ce-4df6-837a-73cbfe4376a2"
VID = "caf885ed-d8cc-41e6-9cdc-b3e38d387842"
ORI = "HORIZONTAL"
ori = "horizontal"
BASE_URL = "http://127.0.0.1:8100"

def get_scenes():
    url = f"{BASE_URL}/api/scenes?video_id={VID}"
    req = urllib.request.urlopen(url)
    scenes = json.loads(req.read().decode("utf-8"))
    scenes.sort(key=lambda s: s["display_order"])
    return scenes

def poll_batch(req_type: str, wave_num: int):
    print(f"\n[Wave {wave_num}] Bắt đầu theo dõi tiến độ ({req_type})...")
    start_time = time.time()
    url = f"{BASE_URL}/api/requests/batch-status?video_id={VID}&type={req_type}"
    
    while True:
        try:
            req = urllib.request.urlopen(url, timeout=10)
            data = json.loads(req.read().decode("utf-8"))
        except Exception as e:
            print(f"Lỗi kết nối ({e}), thử lại...")
            time.sleep(5)
            continue
            
        total = data.get("total", 0)
        completed = data.get("completed", 0)
        processing = data.get("processing", 0)
        pending = data.get("pending", 0)
        failed = data.get("failed", 0)
        done = data.get("done", False)
        
        elapsed = int(time.time() - start_time)
        print(f"[{elapsed:03d}s] Wave {wave_num} ({req_type}): {completed}/{total} xong | Đang chạy: {processing} | Chờ: {pending} | Lỗi: {failed} | Done: {done}")
        
        if done:
            print(f"✅ Wave {wave_num} ({req_type}) đã hoàn thành!")
            break
            
        time.sleep(12)

def submit_batch(requests: list):
    payload = json.dumps({"requests": requests}).encode("utf-8")
    post_req = urllib.request.Request(
        f"{BASE_URL}/api/requests/batch",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(post_req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    scenes = get_scenes()
    scene_by_id = {s["id"]: s for s in scenes}

    def get_depth(s):
        if s.get("chain_type") == "ROOT" or not s.get("parent_scene_id"):
            return 1
        p = scene_by_id.get(s["parent_scene_id"])
        if not p:
            return 1
        return 1 + get_depth(p)

    waves = {}
    for s in scenes:
        d = get_depth(s)
        waves.setdefault(d, []).append(s)

    max_wave = max(waves.keys())
    print(f"=== Bắt đầu quy trình tạo ảnh phân cảnh ({max_wave} Waves) ===")
    print(f"Project ID: {PID}")
    print(f"Video ID:   {VID}")
    print(f"Định dạng:  {ORI}")

    for w in sorted(waves.keys()):
        wave_scenes = waves[w]
        req_type = "GENERATE_IMAGE" if w == 1 else "EDIT_IMAGE"
        
        # Lấy lại trạng thái scene mới nhất
        curr_scenes = {s["id"]: s for s in get_scenes()}
        
        needed = []
        for s in wave_scenes:
            curr = curr_scenes.get(s["id"], s)
            st = curr.get(f"{ori}_image_status")
            mid = curr.get(f"{ori}_image_media_id")
            if st != "COMPLETED" or not mid:
                needed.append(curr)

        print(f"\n" + "-" * 50)
        print(f"WAVE {w} / {max_wave} ({req_type}): {len(needed)} phân cảnh cần tạo ảnh")
        print("-" * 50)

        if not needed:
            print(f"Tất cả phân cảnh trong Wave {w} đã hoàn thành trước đó!")
            continue

        req_list = []
        for s in needed:
            req_list.append({
                "type": req_type,
                "scene_id": s["id"],
                "project_id": PID,
                "video_id": VID,
                "orientation": ORI
            })
            p_desc = f"(parent: {s['parent_scene_id'][:8]})" if s.get("parent_scene_id") else "(ROOT)"
            print(f"  + Cảnh #{s['display_order'] + 1:02d} {p_desc} | ID: {s['id'][:8]}")

        # Gửi batch
        res = submit_batch(req_list)
        print(f"-> Đã gửi thành công {len(res)} yêu cầu cho Wave {w}")

        # Poll cho đến khi wave hoàn thành
        poll_batch(req_type, w)

    # Tổng kết
    print("\n" + "=" * 60)
    print("HOÀN THÀNH TẤT CẢ CÁC WAVES TẠO ẢNH!")
    print("=" * 60)
    final_scenes = get_scenes()
    print("| Cảnh | Chain | Status | Media ID (UUID) |")
    print("| :--- | :--- | :--- | :--- |")
    for s in final_scenes:
        order = s["display_order"] + 1
        st = s.get(f"{ori}_image_status", "UNKNOWN")
        mid = s.get(f"{ori}_image_media_id") or "None"
        icon = "✅" if st == "COMPLETED" else "❌"
        print(f"| Cảnh #{order:02d} | `{s['chain_type']}` | {icon} {st} | `{mid[:18]}...` |")

if __name__ == "__main__":
    main()
