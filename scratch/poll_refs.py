"""Poll batch status for reference image generation until done."""
import urllib.request
import json
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PID = "a0558109-06ce-4df6-837a-73cbfe4376a2"
URL = f"http://127.0.0.1:8100/api/requests/batch-status?project_id={PID}&type=GENERATE_CHARACTER_IMAGE"

def main():
    print("Bắt đầu theo dõi tiến độ tạo ảnh tham chiếu...")
    start_time = time.time()
    last_completed = -1
    
    while True:
        try:
            req = urllib.request.urlopen(URL, timeout=10)
            data = json.loads(req.read().decode("utf-8"))
        except Exception as e:
            print(f"Lỗi kết nối ({e}), thử lại...")
            time.sleep(5)
            continue
            
        total = data.get("total", 0)
        completed = data.get("completed", 0)
        processing = data.get("processing", 0)
        failed = data.get("failed", 0)
        done = data.get("done", False)
        
        elapsed = int(time.time() - start_time)
        print(f"[{elapsed:03d}s] Tiến độ: {completed}/{total} hoàn thành | Đang xử lý: {processing} | Lỗi: {failed} | Done: {done}")
        
        if done:
            print("\n" + "=" * 50)
            print("TOÀN BỘ YÊU CẦU ĐÃ XỬ LÝ XONG!")
            print(f"Thành công: {completed}/{total} | Thất bại: {failed}")
            print("=" * 50)
            break
            
        time.sleep(12)

if __name__ == "__main__":
    main()
