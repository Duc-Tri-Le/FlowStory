#!/usr/bin/env bash
# FlowStory Launcher — Starts Backend & Frontend

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "========================================================"
echo "  🎬 FlowStory — Khởi chạy Hệ thống (Backend + Frontend)"
echo "========================================================"
echo ""

# 1. Kiểm tra môi trường Python
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
    echo "[*] Sử dụng môi trường ảo: .venv"
elif [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
    echo "[*] Sử dụng môi trường ảo: venv"
else
    PYTHON_CMD="python3"
    echo "[*] Sử dụng Python hệ thống"
fi

# 2. Khởi động Backend
echo "[*] Đang khởi động Backend Server (cổng 8100)..."
$PYTHON_CMD -m agent.main &
BACKEND_PID=$!

sleep 2

# 3. Khởi động Frontend Dashboard
echo "[*] Đang khởi động Frontend Dashboard (cổng 5173)..."
cd dashboard
npm run dev &
FRONTEND_PID=$!
cd "$ROOT_DIR"

# Xử lý tắt sạch sẽ khi bấm Ctrl+C
cleanup() {
    echo ""
    echo "========================================================"
    echo "  Đang tắt FlowStory..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "  Đã dừng toàn bộ dịch vụ. Tạm biệt!"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo ""
echo "========================================================"
echo "  🚀 Hệ thống đã sẵn sàng!"
echo "  - Web Dashboard: http://localhost:5173"
echo "  - Backend API:   http://127.0.0.1:8100"
echo "  - API Swagger:   http://127.0.0.1:8100/docs"
echo "========================================================"
echo "Nhấn Ctrl+C để dừng toàn bộ hệ thống."
echo ""

wait
