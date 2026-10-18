"""Submit batch GENERATE_CHARACTER_IMAGE for active project."""
import urllib.request
import json
import sys
import io

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PID = "a0558109-06ce-4df6-837a-73cbfe4376a2"
BASE_URL = "http://127.0.0.1:8100"

def main():
    # 1. Fetch characters
    req = urllib.request.urlopen(f"{BASE_URL}/api/projects/{PID}/characters")
    chars = json.loads(req.read().decode("utf-8"))
    
    missing = [c for c in chars if not c.get("media_id")]
    print(f"Tổng số thực thể: {len(chars)} | Cần tạo ref image: {len(missing)}")
    
    if not missing:
        print("Tất cả thực thể đã có media_id!")
        return

    requests = []
    for c in missing:
        requests.append({
            "type": "GENERATE_CHARACTER_IMAGE",
            "character_id": c["id"],
            "project_id": PID
        })
        print(f"  + Chuẩn bị: [{c.get('entity_type', 'character')}] {c['name']} (ID: {c['id'][:8]}...)")

    payload = json.dumps({"requests": requests}).encode("utf-8")
    post_req = urllib.request.Request(
        f"{BASE_URL}/api/requests/batch",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(post_req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("\n✅ Đã gửi batch request thành công:")
        print(json.dumps(res, indent=2, ensure_ascii=False))

    # Kiểm tra trạng thái tức thì
    status_req = urllib.request.urlopen(f"{BASE_URL}/api/requests/batch-status?project_id={PID}&type=GENERATE_CHARACTER_IMAGE")
    status_data = json.loads(status_req.read().decode("utf-8"))
    print("\nTrạng thái hàng đợi hiện tại:")
    print(json.dumps(status_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
