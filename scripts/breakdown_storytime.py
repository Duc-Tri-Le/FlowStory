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

STORYTIME_SYSTEM_PROMPT = """Bạn là Đạo diễn kỹ thuật cho kênh Hoạt hình Kể chuyện (Storytime Animation Noir/Detective).
Nhiệm vụ của bạn là nhận một câu chuyện hoặc kịch bản thô và bóc tách thành kịch bản phân cảnh chuẩn cho engine đồ họa 2D.

### QUY TẮC BẮT BUỘC (CRITICAL RULES):
1. **MỖI CẢNH MỘT Ý**: Mỗi scene chỉ truyền tải duy nhất một hành động hoặc một câu thoại súc tích.
2. **ĐỘ DÀI LỜI ĐỌC (WORD COUNT)**: Lời đọc (`text`) BẮT BUỘC từ 10 đến 25 từ (tương đương 5 đến 8 giây đọc). KHÔNG viết câu quá dài. Nếu một đoạn dài, hãy chia thành 2-3 scenes liên tiếp.
3. **CAMERA DIRECTIVE**:
   - "close": Dùng cho khoảnh khắc căng thẳng, phát hiện manh mối, cú sốc tâm lý, plot twist.
   - "zoom_in": Dùng cho cảnh kể chuyện bình thường, tăng dần sự chú ý.
   - "pan_right" / "pan_left": Dùng khi nhân vật di chuyển hoặc khảo sát hiện trường vụ án.
   - "static": Dùng cho cảnh đối thoại tĩnh giữa 2 người.
4. **EXPRESSION (BIỂU CẢM NHÂN VẬT 2D)**:
   - "serious" (nghiêm nghị, suy tư)
   - "shocked" (bàng hoàng, mắt mở to)
   - "thinking" (trầm ngâm, nghi ngờ)
   - "talking" (nói chuyện thông thường)
   - "fear" (hoảng loạn, sợ hãi)
5. **ẢNH NỀN (BACKGROUND PROMPT)**:
   - Mô tả bối cảnh noir 2D tối giản, u ám, ánh sáng kịch tính (low-key lighting).
   - BẮT BUỘC kết thúc bằng câu: "Pure scenery illustration, dark noir moody background, strictly NO people, NO characters".

### ĐỊNH DẠNG JSON ĐẦU RA:
Chỉ trả về DUY NHẤT một chuỗi JSON hợp lệ (không kèm lời dẫn Markdown ngoài khối json):
{
  "title": "Tên vụ án hoặc câu chuyện",
  "genre": "trinh_tham",
  "characters": [
    {
      "id": "thanh_tra",
      "name": "Thanh tra Minh",
      "gender": "male",
      "description": "Nhân vật người que 2D đầu tròn trắng, áo khoác măng tô xám đen, ngậm thuốc lá"
    }
  ],
  "scenes": [
    {
      "display_order": 0,
      "speaker": "thanh_tra",
      "text": "10 đến 25 từ lời kể hoặc thoại tại đây...",
      "camera": "close",
      "expression": "serious",
      "background_prompt": "Dark misty rainy street under a dim amber streetlamp. Pure scenery illustration, dark noir moody background, strictly NO people, NO characters.",
      "sound_fx": "rain_heavy"
    }
  ]
}
"""


def validate_storytime_spec(spec: dict) -> list[str]:
    """Validate word counts, camera tags, and schema validity."""
    warnings = []
    scenes = spec.get("scenes", [])
    if not scenes:
        warnings.append("Lỗi: Kịch bản không có scenes nào.")
        return warnings

    allowed_cameras = {"close", "zoom_in", "zoom_out", "pan_right", "pan_left", "static"}

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

        bg = sc.get("background_prompt", "").lower()
        if "no people" not in bg and "no character" not in bg:
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
