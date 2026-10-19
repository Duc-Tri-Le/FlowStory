# 🎬 FlowStory — Hệ Thống Tự Động Hóa Kể Chuyện & Video AI (Google Flow Kit)

Hệ thống kết hợp kịch bản đa nhân vật, lồng tiếng Edge-TTS/Voice Clone, làm phim hoạt hình 2D Storytime và tạo video điện ảnh bằng Google Flow (Veo 3 & Imagen 3).

---

## ⚡ Cài đặt nhanh toàn bộ (Quick Install All)

Bạn có thể chọn **Cài đặt trực tiếp (Không cần venv)** hoặc **Cài đặt với môi trường ảo (.venv)** tùy theo nhu cầu:

---

### 👉 LỰA CHỌN 1: Cài đặt trực tiếp (KHÔNG CẦN môi trường ảo / Không cần venv)

Dành cho bạn muốn cài thẳng vào Python của máy tính nhanh gọn nhất, không cần kích hoạt `.venv`:

#### 🪟 Windows (PowerShell / CMD)
```powershell
# 1. Cài đặt toàn bộ thư viện Python trực tiếp vào máy
python -m pip install --upgrade pip
pip install -r requirements.txt

# 2. Cài đặt toàn bộ thư viện Frontend Dashboard
cd dashboard
npm install
cd ..

# 3. Đồng bộ công cụ AI Skills (Antigravity / Claude / Codex)
python setup.py --tool all

Write-Host ">>> Cài đặt thành công (Không cần venv)! <<<" -ForegroundColor Green
```

#### 🍎 / 🐧 macOS & Linux / WSL (Bash)
```bash
# 1. Cài đặt thư viện Python trực tiếp
pip install --upgrade pip
pip install -r requirements.txt

# 2. Cài đặt thư viện Frontend Dashboard
cd dashboard && npm install && cd ..

# 3. Đồng bộ công cụ AI Skills
python3 setup.py --tool all

echo ">>> Cài đặt thành công (Không cần venv)! <<<"
```

---

### 👉 LỰA CHỌN 2: Cài đặt với môi trường ảo (.venv)

Dành cho bạn muốn cô lập các thư viện riêng biệt trong thư mục `.venv`:

#### 🪟 Windows (PowerShell)
```powershell
# 1. Tạo và kích hoạt môi trường ảo Python
python -m venv .venv
.\.venv\Scripts\activate

# 2. Cập nhật pip và cài đặt toàn bộ thư viện Backend
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Cài đặt toàn bộ thư viện Frontend Dashboard
cd dashboard
npm install
cd ..

# 4. Đồng bộ công cụ AI Skills (Antigravity / Claude / Codex)
python setup.py --tool all

Write-Host ">>> Cài đặt hoàn tất trong môi trường ảo .venv! <<<" -ForegroundColor Green
```

#### 🍎 / 🐧 macOS & Linux / WSL (Bash)
```bash
# 1. Tạo và kích hoạt môi trường ảo Python
python3 -m venv .venv
source .venv/bin/activate

# 2. Cập nhật pip và cài đặt toàn bộ thư viện Backend
pip install --upgrade pip
pip install -r requirements.txt

# 3. Cài đặt toàn bộ thư viện Frontend Dashboard
cd dashboard && npm install && cd ..

# 4. Đồng bộ công cụ AI Skills
python3 setup.py --tool all

echo ">>> Cài đặt hoàn tất trong môi trường ảo .venv! <<<"
```

---

## 🛠️ Yêu cầu hệ thống (Prerequisites)

| Công cụ | Phiên bản | Cách cài đặt |
|---|---|---|
| **Python** | 3.10+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js & npm** | v18+ | [nodejs.org](https://nodejs.org/) |
| **ffmpeg** | Bắt buộc (nối video/audio) | **Windows**: `winget install Gyan.FFmpeg`<br>**macOS**: `brew install ffmpeg`<br>**Ubuntu**: `sudo apt install ffmpeg` |
| **Google Chrome** | Bản mới nhất | [google.com/chrome](https://www.google.com/chrome/) |

---

## 🚀 Hướng dẫn khởi chạy hệ thống (How to Run)

---

### 👉 LỰA CHỌN 1: Khởi chạy 1-Click tự động (Khuyên dùng — Nhanh nhất)

Hệ thống đã chuẩn bị sẵn file kịch bản tự động mở cả Backend (`:8100`) và Frontend (`:5173`), đồng thời tự động kích hoạt môi trường ảo `.venv` nếu có:

#### 🪟 Trên Windows:
- **Cách đơn giản nhất:** Nhấp đúp chuột (Double-click) vào file **`start.bat`** trong thư mục dự án.
- **Hoặc chạy trong PowerShell / CMD:**
  ```powershell
  .\start.bat
  ```

#### 🍎 / 🐧 Trên macOS & Linux / WSL:
```bash
# Cấp quyền thực thi và khởi chạy
chmod +x start.sh
./start.sh
```
> Trình duyệt sẽ tự động mở giao diện tại: **`http://localhost:5173`**  
> *(Nhấn `Ctrl + C` hoặc đóng cửa sổ khi muốn dừng hệ thống)*

---

### 👉 LỰA CHỌN 2: Khởi chạy thủ công từng phần (Dành cho Developer)

Nếu bạn muốn mở các cửa sổ dòng lệnh riêng để theo dõi log chi tiết:

#### 1. Khởi chạy Backend Agent (Cổng 8100)
Mở Terminal thứ nhất:
- **Nếu không dùng venv:**
  ```bash
  python -m agent.main
  ```
- **Nếu dùng môi trường ảo `.venv`:**
  ```bash
  # Windows:
  .\.venv\Scripts\python.exe -m agent.main
  # hoặc: .\.venv\Scripts\activate rồi chạy: python -m agent.main

  # Linux/macOS:
  source .venv/bin/activate
  python -m agent.main
  ```
> Server Backend API sẽ sẵn sàng tại: **`http://127.0.0.1:8100`**

#### 2. Khởi chạy Giao diện Frontend Dashboard (Cổng 5173)
Mở Terminal thứ hai:
```bash
cd dashboard
npm run dev
```
> Truy cập giao diện quản trị tại: **`http://localhost:5173`**

---

## 🌐 Cài đặt & Kết nối Google Flow (Bắt buộc để tạo Video/Ảnh AI)

FlowStory sử dụng Chrome Extension để giao tiếp với Google Flow (Veo 3 & Imagen 3):

1. **Cài Extension vào Chrome:**
   - Mở Chrome truy cập: `chrome://extensions`
   - Bật công tắc **Developer mode** (Chế độ cho nhà phát triển) ở góc trên bên phải.
   - Bấm **Load unpacked** (Tải tiện ích đã giải nén) và chọn thư mục **`extension/`** trong dự án này.
2. **Đăng nhập Google Flow:**
   - Mở tab **[https://flow.google.com/](https://flow.google.com/)** và đăng nhập tài khoản Google Flow của bạn.
   - ⚠️ **Lưu ý quan trọng:** Luôn giữ tab này mở trong trình duyệt trong suốt quá trình tạo ảnh và video.
3. **Cấu hình Flow Project ID (Chọn 1 trong 2 cách):**
   - **Cách A (Nhập trên giao diện):** Khi tạo dự án mới trên Dashboard (`http://localhost:5173`), dán mã UUID từ thanh địa chỉ Google Flow (`https://flow.google.com/project/<UUID>`) vào ô **Flow Project ID**.
   - **Cách B (Đặt biến môi trường hệ thống):**
     ```powershell
     # Windows PowerShell:
     $env:FLOW_PROJECT_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

     # Windows CMD:
     set FLOW_PROJECT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

     # macOS / Linux / WSL:
     export FLOW_PROJECT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
     ```

---

## 🎬 Cách chạy các tính năng & Workflow tạo Video

Bạn có thể điều khiển và chạy FlowStory theo 3 cách khác nhau tùy theo sở thích:

### 🌟 Cách 1: Sử dụng Giao diện Web Dashboard (`http://localhost:5173`)

- **Nạp kịch bản & Tạo dự án:**
  - Nhấp nút **"Tạo Dự Án Mới"** trên Dashboard.
  - Hỗ trợ nạp 1 câu chuyện hoặc **nạp hàng loạt tập phim** cùng lúc bằng cách ngăn cách bởi:
    ```
    === Tập 1: Bí Ẩn Căn Phòng Kín ===
    Nội dung kịch bản tập 1...

    === Tập 2: Người Quản Gia Mất Tích ===
    Nội dung kịch bản tập 2...
    ```
  - Chọn phong cách đồ họa (Material):
    - ⭐ **Hoạt Hình 2D Người Que Tối Giản (OverSimplified & Dark Folklore)**:
      - **Nhân vật người que:** Thân elip dẹt, tay chân que đen, đầu tròn lớn tỉ lệ chibi, mảng màu phẳng viền đen dày. Biểu cảm và chuyển động sinh động bám sát kịch bản.
      - **Tương phản quái thú linh hoạt (Uncanny Contrast):** Quái thú / sinh vật ma quái (chó săn, gà cựa dao, mèo đen ma mị, lợn lòi, dê già...) vẽ theo nét bán thực tế / dark fantasy manga chi tiết ma quái, kết cấu sinh học kỳ dị và mắt phát sáng u ám bám sát mô tả của từng loài động vật (không gán ép sừng), đối lập gay gắt với nét người que tối giản.
      - **Bối cảnh sơn dầu / thủy mặc kỹ thuật số:** Làng quê, căn phòng gỗ, chuồng củi cũ kỹ với kết cấu sần sùi, nền có độ lem mờ tương phản với nhân vật phẳng cắt dán 2D.
      - **Tông màu u ám, lạnh lẽo:** Xám tro, xanh lam đêm, nâu đất xỉn; tương phản gắt với mắt đỏ hoặc ánh lửa vàng cam.
      - **Hoạt họa cắt dán 2D (Cutout Puppet Animation):** Chuyển động xoay theo khớp/trục đơ cứng có chủ ý kiểu kịch rối giấy dân gian.
    - *Photorealistic, Anime, Studio Ghibli, 3D Pixar, Comic Book, Cyberpunk...*
  - Chọn giọng đọc thuyết minh: *Nam Minh (Trầm ấm Noir / Trinh thám / Truyện ma)* hoặc *Hoài My (Cảm xúc Drama)*.
- **Quy trình Hoạt hình 2D AI Chuẩn hóa bằng Google Flow (Imagen 3 & Veo 3):**
  - **Tạo Model Sheet nhân vật 2D:** Google Imagen 3 sinh Model Sheet xoay vòng (turnaround) người que hoặc quái vật trên nền trắng để làm Reference Image bất biến.
  - **Sinh ảnh cảnh 2D:** Tạo khung hình 2D cắt dán đặt trên nền thủy mặc/sơn dầu có chiều sâu.
  - **Sinh video chuyển động 2D Veo 3:** Tạo video hoạt hình cắt dán 2D theo khớp rối giấy với nhịp điệu bám sát kịch bản.
  - **Lồng tiếng Edge-TTS & Ghép video:** Tự động cắt nối video theo giọng đọc tiếng Việt và chèn chữ phụ đề nổi bật.

---

### 🤖 Cách 2: Chạy tự động bằng Trợ lý AI (Claude Code / Antigravity Skills)

Khi bạn sử dụng Claude Code hoặc Google Antigravity trong thư mục dự án, chỉ cần gõ các lệnh Slash Commands:

| Lệnh Skill | Chức năng thực hiện |
|---|---|
| **`/fk-pipeline`** | **Chạy tự động toàn bộ quy trình từ A đến Z** (Kịch bản -> Ảnh ref -> Ảnh cảnh -> Video -> Review -> Concat) |
| **`/fk-create-project`** | Khởi tạo dự án mới với cốt truyện, thực thể nhân vật và danh sách phân cảnh |
| **`/fk-gen-refs`** | Tạo ảnh tham chiếu cho toàn bộ nhân vật và bối cảnh trong dự án |
| **`/fk-gen-images`** | Tạo ảnh nền phân cảnh (Scene Images) cho toàn bộ câu chuyện |
| **`/fk-gen-videos`** | Tạo video động AI (Veo 3) cho tất cả các cảnh |
| **`/fk-review-video`** | Dùng AI Vision tự động kiểm tra chất lượng video, phát hiện lỗi để sinh lại nếu cần |
| **`/fk-concat`** | Nối toàn bộ video phân cảnh thành một video hoàn chỉnh kèm âm thanh |
| **`/fk-concat-fit-narrator`** | Tự động căn chỉnh độ dài từng cảnh video khớp chuẩn với giọng đọc TTS và chèn phụ đề |
| **`/fk-status`** | Hiển thị bảng điều khiển trạng thái tiến độ của dự án hiện tại |
| **`/fk-doctor`** | Tự động chẩn đoán và khắc phục lỗi (lỗi extension, token, CAPTCHA, worker) |

---

### 💻 Cách 3: Chạy bằng các Script Python CLI có sẵn

Bạn có thể chạy trực tiếp các công cụ tiện ích từ dòng lệnh:

- **Khởi tạo dự án bằng Wizard tương tác:**
  ```bash
  python scripts/create_project.py -i
  ```

- **Tạo nhanh dự án từ một dòng lệnh:**
  ```bash
  python scripts/create_project.py --name "Cyber City" --material cyberpunk --story "Thanh tra Minh đuổi theo kẻ lạ mặt qua con hẻm rực ánh đèn neon."
  ```

- **Bóc tách kịch bản Storytime đa nhân vật thành file JSON:**
  ```bash
  python scripts/breakdown_storytime.py --input story.txt --genre trinh_tham --output kịch_bản_phân_cảnh.json
  ```

- **Khởi chạy Scene Review Board độc lập (Cổng 8200):**
  ```bash
  python tools/review_server.py 8200
  # Mở trình duyệt xem bảng duyệt video tại: http://localhost:8200
  ```

- **Tạo nhanh dự án Hoạt hình 2D Người que & Quái thú mẫu (Con Dê Già Trong Chuồng Củi):**
  ```bash
  python tools/create_oversimplified_story.py
  ```

- **Tạo nhanh dữ liệu dự án mẫu điện ảnh (Mộc Tinh 16:9 Noir):**
  ```bash
  python tools/create_moc_tinh_16_9.py
  ```

---

## 🩺 Kiểm tra kết nối & API Endpoints

Sau khi khởi động server, bạn có thể kiểm tra trạng thái hoạt động:

```bash
# 1. Kiểm tra Extension Chrome đã kết nối chưa (BẮT BUỘC: extension_connected: true)
curl http://127.0.0.1:8100/health

# 2. Kiểm tra trạng thái Google Flow
curl http://127.0.0.1:8100/api/flow/status

# 3. Xem danh sách dự án
curl http://127.0.0.1:8100/api/projects

# 4. Xem tài liệu API tương tác (Swagger UI & ReDoc)
# http://127.0.0.1:8100/docs
# http://127.0.0.1:8100/redoc
```

---

## 📋 Lệnh cài đặt & Kiểm thử riêng lẻ khi cần

```bash
# Chỉ cài đặt Backend Python:
pip install -r requirements.txt

# Chỉ cài đặt Frontend Dashboard:
cd dashboard && npm install && cd ..

# Đồng bộ lại toàn bộ AI Skills:
python setup.py --tool all

# Chạy kiểm thử tự động (Unit Tests):
pytest tests/unit/
```
