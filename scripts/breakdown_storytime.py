#!/usr/bin/env python3
"""Storytime Animatic Script Breakdown Engine.

Converts raw story text (detective, thriller, mystery) into a structured JSON
tailored for Remotion 2D limited animation:
- 1 idea per scene
- 10 to 25 words per scene (~5 to 8 seconds speech)
- Explicit 'speaker', 'camera' ('close' for tension, 'zoom_in' for normal, 'pan_right', 'static')
- 'expression' for character SVG state ('serious', 'shocked', 'thinking', 'talking')
- 'background_prompt' strictly with NO people/characters
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

STORYTIME_SYSTEM_PROMPT = """Bạn là Đạo diễn kỹ thuật cho kênh Hoạt hình Kể chuyện 2D (Storytime Animation).
Nhiệm vụ của bạn là nhận một câu chuyện hoặc kịch bản thô thuộc BẤT KỲ THỂ LOẠI NÀO (Trinh thám, Khoa học viễn tưởng, Đời sống, Kinh dị, Hài hước, Tình cảm, Phiêu lưu...) và bóc tách thành kịch bản phân cảnh chuẩn cho engine đồ họa hoạt hình 2D đa nhân vật.

### QUY TẮC BẮT BUỘC (CRITICAL RULES):
1. **TRÍCH XUẤT ĐẦY ĐỦ NHÂN VẬT (CHARACTERS)**:
   - Tự động nhận diện TẤT CẢ nhân vật xuất hiện trong câu chuyện (từ 1 đến nhiều người).
   - Mỗi nhân vật có `id` (slug ngắn), `name`, `gender`, `color` (màu áo đặc trưng dạng hex như #1e293b, #0284c7, #dc2626, #16a34a, #9333ea, #f59e0b), và `description`.
   - Nếu là lời dẫn của người kể chuyện ngoài đời, gán `speaker: "narrator"`.

2. **MỖI CẢNH MỘT Ý**: Mỗi scene chỉ truyền tải duy nhất một hành động hoặc một câu thoại súc tích.

3. **ĐỘ DÀI LỜI ĐỌC (WORD COUNT)**: Lời đọc (`text`) BẮT BUỘC từ 10 đến 25 từ (tương đương 5 đến 8 giây đọc). KHÔNG viết câu quá dài. Nếu một đoạn dài, hãy chia thành 2-3 scenes liên tiếp.

4. **SÂN KHẤU ĐA NHÂN VẬT & ĐÚNG NGƯỜI NÓI (ACTORS & SPEAKER)**:
   - Trong mỗi scene, chỉ định rõ `speaker`: ID của nhân vật đang phát âm thanh câu thoại đó (chỉ người này mới nhép miệng).
   - Khai báo mảng `actors`: danh sách nhân vật có mặt trên khung hình ở cảnh đó.
     + `id`: ID nhân vật.
     + `position`: "left" (khoảng 20%), "center" (khoảng 50%), "right" (khoảng 80%).
     + `action`: "stand" (đứng), "walk" (đi bộ), "run" (chạy), "flee" (bỏ chạy), "pursue" (đuổi bắt), "shiver" (run rẩy/lo sợ).
     + `facing`: 1 (quay mặt sang phải) hoặc -1 (quay mặt sang trái).
   - `action_type`: "dialogue" (đối thoại), "chase" (rượt đuổi), "trio" (toàn cảnh 3 người trở lên), "solo" (chỉ 1 người).

5. **CAMERA DIRECTIVE**:
   - "close": Khoảnh khắc căng thẳng, cú sốc, phát hiện bất ngờ.
   - "zoom_in": Cảnh đối thoại kể chuyện bình thường, tăng dần sự chú ý.
   - "pan_right" / "pan_left": Cảnh nhân vật bước đi hoặc rượt đuổi qua lại.
   - "static": Cảnh tĩnh đối thoại hoặc toàn cảnh phòng.

6. **BỐI CẢNH (LOCATIONS)**:
   - Xác định tất cả địa điểm KHÁC NHAU xuất hiện trong truyện.
   - Mỗi bối cảnh định nghĩa một lần trong "locations" và các scene dùng chung "location_id".
   - Bối cảnh chỉ vẽ thuần phong cảnh, KHÔNG có người: kết thúc background_prompt bằng: "Pure scenery illustration, atmospheric moody background, strictly NO people, NO characters".

### ĐỊNH DẠNG JSON ĐẦU RA:
Chỉ trả về DUY NHẤT một chuỗi JSON hợp lệ (không kèm lời dẫn Markdown ngoài khối json):
{
  "title": "Tiêu đề câu chuyện",
  "genre": "the_loai (vi_du: trinh_tham, vien_tuong, doi_song, hai_huoc, kinh_di...)",
  "characters": [
    {
      "id": "nhan_vat_a",
      "name": "Tên Nhân Vật A",
      "gender": "male",
      "color": "#1e293b",
      "description": "Mô tả nhận diện ngắn"
    },
    {
      "id": "nhan_vat_b",
      "name": "Tên Nhân Vật B",
      "gender": "female",
      "color": "#9333ea",
      "description": "Mô tả nhận diện ngắn"
    }
  ],
  "locations": [
    {
      "id": "loc_1",
      "name": "Tên địa điểm",
      "background_prompt": "Mô tả bối cảnh chi tiết. Pure scenery illustration, atmospheric moody background, strictly NO people, NO characters.",
      "color": "#f59e0b"
    }
  ],
  "scenes": [
    {
      "display_order": 0,
      "speaker": "nhan_vat_a",
      "text": "10 đến 25 từ lời kể hoặc thoại tại đây...",
      "camera": "zoom_in",
      "expression": "serious",
      "action_type": "dialogue",
      "location_id": "loc_1",
      "actors": [
        { "id": "nhan_vat_a", "position": "left", "action": "stand", "facing": 1 },
        { "id": "nhan_vat_b", "position": "right", "action": "shiver", "facing": -1 }
      ]
    }
  ]
}
"""



def validate_storytime_spec(spec: dict) -> list[str]:
    """Validate word counts, camera tags, locations, and schema validity."""
    warnings = []
    scenes = spec.get("scenes", [])
    if not scenes:
        warnings.append("Lỗi: Kịch bản không có scenes nào.")
        return warnings

    allowed_cameras = {"close", "zoom_in", "zoom_out", "pan_right", "pan_left", "static"}

    # Build locations index for cross-referencing
    locations = {loc["id"]: loc for loc in spec.get("locations", [])}
    if not locations:
        warnings.append("Cảnh báo: Kịch bản không có mảng 'locations'. Các cảnh sẽ không thể dùng chung ảnh nền.")

    for idx, sc in enumerate(scenes):
        order = sc.get("display_order", idx)
        text = sc.get("text", "").strip()
        word_count = len(text.split())

        if word_count < 8:
            warnings.append(f"Cảnh #{order}: Lời thoại quá ngắn ({word_count} từ, nên từ 10-25 từ).")
        elif word_count > 30:
            warnings.append(f"Cảnh #{order}: Lời thoại quá dài ({word_count} từ, nên chia nhỏ bớt để dưới 25 từ).")

        cam = sc.get("camera", "zoom_in")
        if cam not in allowed_cameras:
            warnings.append(f"Cảnh #{order}: Camera '{cam}' không hợp lệ (nên dùng: {allowed_cameras}).")

        # Validate location reference
        loc_id = sc.get("location_id")
        if loc_id and locations and loc_id not in locations:
            warnings.append(f"Cảnh #{order}: location_id '{loc_id}' không tồn tại trong mảng locations.")

        # Validate background prompt (from location or inline)
        bg = ""
        if loc_id and loc_id in locations:
            bg = locations[loc_id].get("background_prompt", "").lower()
        else:
            bg = sc.get("background_prompt", "").lower()

        if bg and "no people" not in bg and "no character" not in bg:
            warnings.append(f"Cảnh #{order}: Background prompt chưa có câu cấm người ('strictly NO people, NO characters').")

    return warnings


def call_ai(prompt_text: str) -> str:
    """Call AI via agent CLI providers or local fallback."""
    from agent.services.cli_providers import resolve_role
    import subprocess

    full_prompt = f"{STORYTIME_SYSTEM_PROMPT}\n\n### KỊCH BẢN THÔ CẦN BÓC TÁCH:\n{prompt_text}\n\nChỉ trả về chuỗi JSON kết quả."

    # Prefer agy, fallback to claude or codex
    for bin_name in ["agy", "claude", "codex"]:
        try:
            if bin_name == "agy":
                cmd = ["agy", "--prompt", full_prompt]
            elif bin_name == "claude":
                cmd = ["claude", "-p", full_prompt]
            else:
                cmd = ["codex", "exec", full_prompt]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        except Exception:
            continue

    raise RuntimeError("Không thể gọi CLI AI (agy/claude/codex). Hãy kiểm tra môi trường.")


def extract_json(raw_text: str) -> dict:
    """Extract and parse JSON safely from model response."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
    clean = match.group(1).strip() if match else raw_text.strip()
    return json.loads(clean)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Breakdown raw story into Storytime Animatic JSON Spec")
    parser.add_argument("--input", "-i", type=str, help="Input text file containing raw story")
    parser.add_argument("--output", "-o", type=str, default="story_spec.json", help="Output JSON spec path")
    args = parser.parse_args()

    if not args.input:
        print("Vui lòng cung cấp file đầu vào: python scripts/breakdown_storytime.py --input truyen.txt")
        sys.exit(1)

    raw_story = Path(args.input).read_text(encoding="utf-8")
    print(f"[*] Đang phân tích kịch bản thô ({len(raw_story)} ký tự)...")

    ai_output = call_ai(raw_story)
    spec = extract_json(ai_output)

    warnings = validate_storytime_spec(spec)
    for w in warnings:
        print(f"  [!] {w}")

    out_file = Path(args.output)
    out_file.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] Hoàn tất! Kịch bản đã lưu tại: {out_file.resolve()}")
    print(f"    Tổng số cảnh: {len(spec.get('scenes', []))}")
