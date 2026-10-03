import json
import urllib.request

API_BASE = "http://127.0.0.1:8100/api"
VIDEO_ID = "13cac219-f3bc-437f-9622-5cd90fb91616"

narrations = {
    1: "Người phụ nữ ngồi trên sofa trong phòng khách vào buổi tối, cầm tờ giấy xét nghiệm với vẻ bối rối.",
    2: "Người đàn ông bước vào với vẻ mặt nghiêm nghị, lạnh lùng thông báo kết quả.",
    3: "Anh ta nhìn thẳng với ánh mắt tức giận và tuyên bố cả hai đứa trẻ không phải con mình.",
    4: "Người phụ nữ chết lặng vì sốc, không thể tin vào những gì vừa nghe thấy.",
    5: "Anh ta giận dữ yêu cầu ly hôn ngay ngày mai và bắt cô dẫn con rời đi.",
    6: "Toàn bộ căn phòng chìm trong bầu không khí ngột ngạt và hoang mang tột độ.",
    7: "Người phụ nữ bật dậy phản bác trong sự khó hiểu và tức giận.",
    8: "Người đàn ông nghiến răng tiếp tục buộc tội vì nghĩ rằng mình bị phản bội.",
    9: "Cô nhìn anh ta vài giây rồi nhận ra sự vô lý đến mức nực cười.",
    10: "Cú lật bất ngờ: Những đứa trẻ thực chất là con của người vợ cũ của anh ta.",
    11: "Tờ giấy xét nghiệm tuột khỏi tay và rơi xuống sàn trong sự ngỡ ngàng tột độ.",
    12: "Cái kết kết thúc bằng cái nhìn hình viên đạn và câu hỏi chốt hạ."
}

req = urllib.request.Request(f"{API_BASE}/scenes?video_id={VIDEO_ID}")
with urllib.request.urlopen(req) as resp:
    scenes = json.loads(resp.read().decode("utf-8"))

for s in scenes:
    order = s["display_order"]
    if order in narrations:
        sid = s["id"]
        patch_data = json.dumps({"narrator_text": narrations[order]}).encode("utf-8")
        preq = urllib.request.Request(
            f"{API_BASE}/scenes/{sid}",
            data=patch_data,
            headers={"Content-Type": "application/json"},
            method="PATCH"
        )
        with urllib.request.urlopen(preq) as presp:
            pass
        print(f"Patched scene {order} with narrator text")

print("All narrator texts patched successfully.")
