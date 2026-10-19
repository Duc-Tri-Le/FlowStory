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

## 🚀 Hướng dẫn khởi chạy (How to Run)

### Bước 1: Cài đặt Chrome Extension
1. Mở Chrome truy cập: `chrome://extensions`
2. Bật công tắc **Developer mode** (Chế độ dành cho nhà phát triển) ở góc trên bên phải.
3. Bấm **Load unpacked** (Tải tiện ích đã giải nén) và chọn thư mục `extension/` trong dự án này.
4. Mở tab [https://flow.google.com/](https://flow.google.com/) và đăng nhập tài khoản Google Flow của bạn (giữ nguyên tab này mở).

---

### Bước 2: Khởi chạy Backend Agent (Cổng 8100)

Mở cửa sổ dòng lệnh (Terminal/PowerShell):

- **Nếu không dùng môi trường ảo:**
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

> Server API backend sẽ chạy tại: **`http://127.0.0.1:8100`**

---

### Bước 3: Khởi chạy Giao diện Dashboard (Cổng 5173)

Mở một cửa sổ dòng lệnh thứ hai:

```bash
cd dashboard
npm run dev
```
> Truy cập giao diện quản trị tại: **`http://localhost:5173`**

---

## 🩺 Kiểm tra kết nối & API Endpoints

Sau khi khởi động server, bạn có thể kiểm tra trạng thái bằng các lệnh sau:

```bash
# 1. Kiểm tra Extension Chrome đã kết nối chưa (BẮT BUỘC: extension_connected: true)
curl http://127.0.0.1:8100/health

# 2. Kiểm tra trạng thái Google Flow
curl http://127.0.0.1:8100/api/flow/status

# 3. Xem danh sách dự án
curl http://127.0.0.1:8100/api/projects

# 4. Xem tài liệu API Swagger / OpenAPI
# http://127.0.0.1:8100/docs
# http://127.0.0.1:8100/redoc
```

---

## 📋 Lệnh cài đặt riêng lẻ khi cần

Nếu bạn muốn cài đặt riêng từng phần:

### Chỉ cài đặt Backend Python:
```bash
pip install -r requirements.txt
```

### Chỉ cài đặt Frontend Dashboard:
```bash
cd dashboard
npm install
```

### Chạy kiểm thử tự động (Unit Tests):
```bash
pytest tests/unit/
```
