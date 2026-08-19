#!/usr/bin/env bash
# Automated Environment Setup and Virtual Testing for macOS (Apple Silicon M1-M4 & Intel)
# Z-Truyen X3 Backend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo "=========================================================="
echo "  Z-Truyen X3 — Thiết Lập Môi Trường Ảo / Test trên macOS"
echo "=========================================================="

# 1. Kiểm tra Python 3
echo -e "\n[1/4] Kiểm tra Python 3..."
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version)
    echo "    Đã tìm thấy: ${PY_VER}"
else
    echo "    ❌ Chưa cài đặt Python 3! Bạn có thể cài đặt bằng: brew install python@3.12"
    exit 1
fi

# 2. Tạo Môi Trường Ảo (Virtualenv)
cd "${BACKEND_DIR}"
echo -e "\n[2/4] Khởi tạo môi trường ảo Python (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "    Đã tạo thư mục .venv thành công."
else
    echo "    Môi trường .venv đã tồn tại."
fi

# 3. Kích hoạt và cài đặt gói
echo -e "\n[3/4] Cài đặt dependencies và Playwright Chromium..."
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
python3 -m playwright install chromium || true

# 4. Kiểm tra Docker trên macOS
echo -e "\n[4/4] Kiểm tra Docker Desktop / Colima / OrbStack..."
if command -v docker &>/dev/null; then
    DOCKER_VER=$(docker --version)
    echo "    Docker khả dụng: ${DOCKER_VER}"
    echo "    (Khuyên dùng chạy 24/7 trên Mac mini: cd backend && docker compose up -d)"
else
    echo "    (Docker không bắt buộc, bạn có thể chạy trực tiếp bằng Python .venv)"
fi

echo -e "\n=========================================================="
echo "  MÔI TRƯỜNG ĐÃ SẴN SÀNG! CÁC CÁCH KIỂM THỬ TRÊN MACOS:"
echo "=========================================================="
echo "1. Chạy Backend trực tiếp:"
echo "   cd backend && uvicorn app.main:app --reload --port 8080"
echo ""
echo "2. Chạy Trình Giả Lập E-Reader X3 qua Terminal:"
echo "   python3 scripts/opds_simulator.py"
echo ""
echo "3. Mở Web UI trên Trình duyệt Safari/Chrome:"
echo "   http://localhost:8080/"
echo ""
echo "4. Giả lập máy X3 trên KOReader macOS:"
echo "   Cài đặt KOReader: brew install --cask koreader"
echo "   (Hoặc tải .dmg tại: https://github.com/koreader/koreader/releases)"
echo "   Mở KOReader -> OPDS Catalog -> Thêm URL: http://localhost:8080/opds"
echo "=========================================================="
