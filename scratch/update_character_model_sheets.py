import io
import json
import sys
import urllib.request

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PID = "a9957315-2929-4a39-9e77-8c127f7fbd5c"

# Cấu trúc chuẩn: 3-view character model sheet: front, back, and head profile (khung hình ngang 16:9)
CHARACTER_SHEETS = {
    "Young Boy": {
        "id": "dbd320f6-58a5-4afb-88d5-c0d5d039fb24",
        "image_prompt": (
            "STRUCTURE: 3-view character model sheet: front, back, and head profile. "
            "Side-by-side turnaround on a single wide horizontal 16:9 canvas with clean solid neutral light gray background. "
            "Left: Full body front view standing naturally. "
            "Middle: Full body back view showing the blue-and-yellow backpack clearly. "
            "Right: Close-up side head profile shot showing facial profile, neat black bangs and innocent expression. "
            "Character is a 7-year-old Asian schoolboy wearing a crisp white collared polo shirt, navy blue shorts, white socks, sneakers, and small backpack. "
            "Consistent scale, height, clothing, and photorealistic soft studio lighting across all three views. "
            "High resolution, 8k, photorealistic RAW photograph, no text, no labels, no watermark."
        )
    },
    "Adult Man": {
        "id": "0dcef9a8-4f4f-4288-ab3a-4b8f3d93af0a",
        "image_prompt": (
            "STRUCTURE: 3-view character model sheet: front, back, and head profile. "
            "Side-by-side turnaround on a single wide horizontal 16:9 canvas with clean solid neutral studio gray background. "
            "Left: Full body front view standing calmly with black messenger bag on shoulder. "
            "Middle: Full body back view showing back of gray dress shirt, charcoal trousers, and messenger bag strap. "
            "Right: Close-up side head profile shot showing side-part dark hair, tired gentle eyes and jawline. "
            "Character is a 28-year-old Asian commuter wearing a light gray collared dress shirt and charcoal trousers. "
            "Consistent scale, height, clothing, and photorealistic neutral studio lighting across all three views. "
            "High resolution, 8k, photorealistic RAW photograph, no text, no labels, no watermark."
        )
    },
    "Mother": {
        "id": "391d83c2-ba6e-4567-a13a-b54b75ce7f9d",
        "image_prompt": (
            "STRUCTURE: 3-view character model sheet: front, back, and head profile. "
            "Side-by-side turnaround on a single wide horizontal 16:9 canvas with clean solid neutral warm gray studio background. "
            "Left: Full body front view standing with hands gently folded in front, smiling warmly. "
            "Middle: Full body back view showing the texture of the cream knit cardigan and low ponytail hair. "
            "Right: Close-up side head profile shot showing gentle smile, soft jawline and hair details. "
            "Character is a 32-year-old Asian mother in a cozy cream cardigan and floral dress. "
            "Consistent scale, height, clothing, and warm photorealistic studio lighting across all three views. "
            "High resolution, 8k, photorealistic RAW photograph, no text, no labels, no watermark."
        )
    },
    "Strict Boss": {
        "id": "23d03451-2ce7-4684-a4a2-78b20638b864",
        "image_prompt": (
            "STRUCTURE: 3-view character model sheet: front, back, and head profile. "
            "Side-by-side turnaround on a single wide horizontal 16:9 canvas with clean solid neutral studio background. "
            "Left: Full body front view standing authoritatively in a tailored dark navy suit. "
            "Middle: Full body back view showing tailored suit shoulders and commanding posture. "
            "Right: Close-up side head profile shot showing furrowed brow, sharp jaw and short greying hair. "
            "Character is a 48-year-old Asian corporate executive. "
            "Consistent scale, height, clothing, and photorealistic studio lighting across all three views. "
            "High resolution, 8k, photorealistic RAW photograph, no text, no labels, no watermark."
        )
    }
}

print("1. Đang cập nhật prompt 3-view model sheet (hình ngang) cho 4 nhân vật...")
for name, data in CHARACTER_SHEETS.items():
    cid = data["id"]
    payload = {
        "image_prompt": data["image_prompt"],
        "media_id": None,
        "reference_image_url": None
    }
    req = urllib.request.Request(
        f"http://127.0.0.1:8100/api/characters/{cid}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PATCH"
    )
    resp = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    print(f"  ✅ Đã cập nhật {name} (ID: {cid})")

# 2. Gửi batch tạo lại ảnh tham chiếu với cấu trúc 3-view ngang
print("\n2. Đang gửi batch tạo lại ảnh tham chiếu (REGENERATE_CHARACTER_IMAGE)...")
batch_payload = {
    "requests": [
        {
            "type": "REGENERATE_CHARACTER_IMAGE",
            "character_id": data["id"],
            "project_id": PID
        }
        for data in CHARACTER_SHEETS.values()
    ]
}

batch_req = urllib.request.Request(
    "http://127.0.0.1:8100/api/requests/batch",
    data=json.dumps(batch_payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
batch_resp = json.loads(urllib.request.urlopen(batch_req).read().decode("utf-8"))
print(f"✅ Đã gửi thành công batch tạo lại cho {len(batch_resp)} nhân vật!")
