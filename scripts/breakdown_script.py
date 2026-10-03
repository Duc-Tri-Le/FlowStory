#!/usr/bin/env python3
"""
FlowStory — AI Script Breakdown & Consistency Engine

Chuyển đổi kịch bản thô (screenplay/story text) thành cấu trúc FlowStory Project Spec chuẩn:
1. Xác định thực thể: Nhân vật (character), Bối cảnh (location), Đồ vật/Phương tiện (visual_asset), Đám đông (creature/troop).
2. Xây dựng Visual Anchor bất biến cho nhân vật để tạo Reference Image đồng nhất.
3. Sinh Scene Prompts theo quy tắc ACTION-ONLY (không tả lại ngoại hình nhân vật).
4. Sinh Video Prompts theo cấu trúc sub-clip timing (0-3s, 3-6s, 6-8s) chuẩn Veo 3.

Sử dụng:
    # 1. Bóc tách kịch bản từ file text sử dụng AI CLI (agy, claude, codex):
    python scripts/breakdown_script.py --input kich_ban.txt --output project_spec.json

    # 2. In System Prompt mẫu để đưa vào bất kỳ Chatbot/LLM nào:
    python scripts/breakdown_script.py --print-prompt

    # 3. Tạo project trực tiếp vào hệ thống FlowStory sau khi bóc tách:
    python scripts/create_project.py --file project_spec.json
"""

import argparse
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Đảm bảo UTF-8 cho stdout/stderr trên Windows PowerShell
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# System prompt master tối ưu cho FlowStory / Google Flow / Veo 3
BREAKDOWN_SYSTEM_PROMPT = """Bạn là Chuyên gia Đạo diễn & Biên kịch AI của hệ thống FlowStory (Google Flow & Veo 3 Engine).
Nhiệm vụ của bạn là nhận một kịch bản thô (screenplay/story) và bóc tách thành một cấu trúc JSON kỹ thuật chính xác 100% để đưa vào pipeline sản xuất video AI.

### QUY TẮC BẮT BUỘC ĐỂ ĐỒNG NHẤT NHÂN VẬT & THẾ GIỚI (CRITICAL CONSISTENCY RULES):

1. **QUY TẮC ĐỒNG NHẤT NHÂN VẬT (VISUAL ANCHORS)**:
   - Trong AI video, khuôn mặt và trang phục sẽ bị thay đổi nếu không có "Neo thị giác" (Visual Anchors).
   - Với mỗi nhân vật (entity_type: "character"), bạn phải xác định một bộ trang phục MẶC ĐỊNH BẤT BIẾN (signature attire) xuyên suốt câu chuyện: kiểu dáng, màu sắc cụ thể, chất liệu, phụ kiện đặc trưng (áo khoác, đồng hồ, ba lô...).
   - Trường `description` của nhân vật phải mô tả chi tiết: Độ tuổi, giới tính, nét mặt, kiểu tóc, vóc dáng và trang phục cố định.
   - Trường `image_prompt`: Prompt chụp ảnh chân dung (portrait, 9:16) dùng để tạo Reference Image. Chụp toàn thân/bán thân, nền đơn giản, nhìn thẳng vào ống kính.

2. **QUY TẮC BỐI CẢNH (LOCATIONS) & ĐỒ VẬT (VISUAL ASSETS)**:
   - Bối cảnh (entity_type: "location"): Mô tả kiến trúc, ánh sáng, thời tiết, môi trường. BẮT BUỘC có dòng: "PURE SCENERY, EMPTY ENVIRONMENT, ABSOLUTELY NO PEOPLE, NO CHARACTERS".
   - Đồ vật/Phương tiện quan trọng (entity_type: "visual_asset"): Những vật phẩm đóng vai trò then chốt trong kịch bản (ví dụ: Nút đỏ khẩn cấp, Xe SUV hỏng, Thùng nước, Cuộn dây...). Chụp cận cảnh chi tiết, không có người.

3. **QUY TẮC SCENE PROMPT (ACTION ONLY - CỰC KỲ QUAN TRỌNG)**:
   - Trong `prompt` của từng cảnh: TUYỆT ĐỐI KHÔNG mô tả lại màu tóc, màu áo, khuôn mặt của nhân vật! Google Flow sẽ tự truyền ảnh tham chiếu (Reference Image) vào.
   - Scene prompt CHỈ TẢ: Góc máy (Wide shot, Close-up, Low angle...), hành động của nhân vật, tương tác vật lý, bố cục khung hình và ánh sáng môi trường.
   - Luôn gọi nhân vật bằng TÊN CHÍNH XÁC đã khai báo trong mảng `characters`.
   - `character_names`: Liệt kê chính xác tên của tất cả nhân vật, bối cảnh, và vật phẩm xuất hiện trong cảnh đó.

4. **QUY TẮC VIDEO PROMPT (VEO 3 SUB-CLIP TIMING)**:
   - Video có độ dài 4-8 giây, chia thành các phân đoạn thời gian rõ ràng:
     "0-3s: [Hành động mở đầu].
      3-6s: [Hành động tiếp theo/cao trào]. [Tên nhân vật] says \"[Lời thoại trong ngoặc kép]\".
      6-8s: [Hành động kết thúc cảnh].
      
      Audio: [Mô tả âm thanh môi trường].
      SFX: [Hiệu ứng âm thanh cụ thể].
      Negative: subtitles, watermark, text overlay."

### ĐỊNH DẠNG JSON ĐẦU RA (JSON OUTPUT SCHEMA):
Chỉ trả về DUY NHẤT một chuỗi JSON hợp lệ (không kèm markdown ```json bọc ngoài nếu có thể, hoặc bọc trong ```json):
{
  "name": "Tên dự án ngắn gọn hấp dẫn",
  "description": "Tóm tắt ngắn kịch bản",
  "material": "realistic",  // hoặc: 3d_pixar, anime, comic, cyberpunk...
  "orientation": "VERTICAL", // hoặc: HORIZONTAL
  "story": "Cốt truyện tổng quan của toàn bộ video",
  "characters": [
    {
      "name": "Tên nhân vật hoặc Bối cảnh hoặc Đồ vật",
      "entity_type": "character", // "character" | "location" | "visual_asset" | "generic_troop" | "creature"
      "description": "Mô tả visual anchor chi tiết",
      "image_prompt": "Prompt tạo ảnh tham chiếu (portrait cho character, landscape cho location/asset)"
    }
  ],
  "scenes": [
    {
      "display_order": 1,
      "character_names": ["Tên Nhân Vật A", "Tên Nhân Vật B", "Tên Bối Cảnh"],
      "chain_type": "ROOT",
      "prompt": "Góc máy + Hành động cụ thể của nhân vật (ACTION ONLY, không tả trang phục)",
      "video_prompt": "0-3s: ... 3-6s: ... 6-8s: ...\n\nAudio: ...\nSFX: ...\nNegative: subtitles, watermark, text overlay.",
      "narrator_text": "Lời dẫn thuyết minh (nếu có)",
      "duration": 5.0
    }
  ]
}
"""


def validate_spec(spec: dict) -> list[str]:
    """Kiểm tra tính nhất quán (Consistency Validation) của dự án."""
    warnings = []
    
    entities = {c["name"]: c for c in spec.get("characters", [])}
    if not entities:
        warnings.append("Cảnh báo: Không có nhân vật/bối cảnh nào trong danh sách 'characters'.")

    # Kiểm tra scenes
    scenes = spec.get("scenes", [])
    if not scenes:
        warnings.append("Lỗi: Không có cảnh nào trong mảng 'scenes'.")

    for idx, sc in enumerate(scenes):
        sc_num = sc.get("display_order", idx + 1)
        c_names = sc.get("character_names", [])
        
        # 1. Kiểm tra character_names có được định nghĩa trong entities không
        for name in c_names:
            if name not in entities:
                warnings.append(f"Cảnh #{sc_num}: Thực thể '{name}' xuất hiện trong cảnh nhưng chưa được khai báo trong 'characters'.")
                
        # 2. Kiểm tra rule Action Only (cảnh báo nếu scene prompt chứa từ khóa tả trang phục nhân vật)
        prompt = sc.get("prompt", "").lower()
        forbidden_words = ["wearing a", "wears a", "dressed in", "has blonde hair", "with brown hair"]
        for fw in forbidden_words:
            if fw in prompt:
                warnings.append(f"Cảnh #{sc_num}: Scene prompt vi phạm quy tắc Action-Only (chứa '{fw}'). Hãy để Reference Image quản lý ngoại hình!")
                
        # 3. Kiểm tra video_prompt có sub-clip timing không
        v_prompt = sc.get("video_prompt", "")
        if "0-3s:" not in v_prompt and "0-2s:" not in v_prompt:
            warnings.append(f"Cảnh #{sc_num}: Video prompt thiếu cấu trúc sub-clip timing (ví dụ: '0-3s: ...').")
            
    return warnings


def call_ai_cli(prompt_text: str, provider: str = "agy") -> str:
    """Gọi AI CLI (agy, claude, codex) để phân tích kịch bản."""
    print(f"[*] Đang gọi AI provider '{provider}' để phân tích kịch bản...")
    
    full_prompt = f"{BREAKDOWN_SYSTEM_PROMPT}\n\n### KỊCH BẢN ĐẦU VÀO:\n{prompt_text}\n\nChỉ trả về chuỗi JSON kết quả."
    
    if provider == "agy":
        cmd = ["agy", "--prompt", full_prompt]
    elif provider == "claude":
        cmd = ["claude", "-p", full_prompt]
    elif provider == "codex":
        cmd = ["codex", "exec", full_prompt]
    else:
        raise ValueError(f"Provider không hợp lệ: {provider}")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout
    except FileNotFoundError:
        raise RuntimeError(f"Không tìm thấy lệnh '{provider}' trên máy. Vui lòng cài đặt CLI hoặc sử dụng API.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Lỗi khi thực thi {provider}: {e.stderr}")


def extract_json(raw_text: str) -> dict:
    """Bóc tách JSON từ phản hồi của LLM."""
    raw_text = raw_text.strip()
    
    # Bóc từ code block ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
    if match:
        json_str = match.group(1).strip()
    else:
        json_str = raw_text

    return json.loads(json_str)


def main():
    parser = argparse.ArgumentParser(description="FlowStory AI Script Breakdown & Consistency Engine")
    parser.add_argument("--input", "-i", type=str, help="Đường dẫn file kịch bản (.txt / .md)")
    parser.add_argument("--output", "-o", type=str, default="project_spec.json", help="File JSON kết quả")
    parser.add_argument("--provider", "-p", type=str, default="agy", choices=["agy", "claude", "codex"], help="AI CLI provider")
    parser.add_argument("--print-prompt", action="store_true", help="In ra System Prompt mẫu để dùng thủ công")
    
    args = parser.parse_args()

    if args.print_prompt:
        print(BREAKDOWN_SYSTEM_PROMPT)
        return

    if not args.input:
        print("Vui lòng cung cấp file kịch bản qua tham số --input <file_path> hoặc xem prompt qua --print-prompt")
        sys.exit(1)

    script_path = Path(args.input)
    if not script_path.exists():
        print(f"Lỗi: Không tìm thấy file '{args.input}'")
        sys.exit(1)

    content = script_path.read_text(encoding="utf-8")
    
    try:
        raw_output = call_ai_cli(content, provider=args.provider)
        spec = extract_json(raw_output)
    except Exception as e:
        print(f"❌ Xảy ra lỗi khi chạy AI Breakdown: {e}")
        print("\n💡 Bạn có thể dùng cờ --print-prompt để lấy System Prompt và chạy trực tiếp trên ChatGPT/Claude/Gemini Web, sau đó lưu kết quả vào file JSON.")
        sys.exit(1)

    # Kiểm tra tính nhất quán
    warnings = validate_spec(spec)
    if warnings:
        print("\n⚠️  Cảnh báo kiểm tra tính nhất quán:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("✅ Kiểm tra tính nhất quán: ĐẠT 100% tiêu chuẩn FlowStory!")

    out_path = Path(args.output)
    out_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n🎉 Đã xuất thành công cấu trúc dự án: {out_path.resolve()}")
    print(f"Để tạo dự án vào FlowStory, chạy:")
    print(f"    python scripts/create_project.py --file {out_path.name}")


if __name__ == "__main__":
    main()
