cat << 'EOF' > /root/install_vwrt_bot.sh
#!/bin/sh

# ====== CẤU HÌNH ======
REPO_RAW="https://raw.githubusercontent.com/vietter99/botvwrt/main"
# ============================================================

BOT_DST="/root/bot_openwrt.py"
INIT_DST="/etc/init.d/telegram_bot"

set -e

echo "[*] Kiểm tra opkg..."
if ! command -v opkg >/dev/null 2>&1; then
    echo "[FATAL] Không tìm thấy opkg. Đây có vẻ không phải OpenWrt hoặc hệ đã bị tùy biến."
    exit 1
fi

# ---------- 1. python3 + pip qua opkg ----------

ensure_python3_and_pip() {
    HAVE_PY=0
    HAVE_PIP=0

    if command -v python3 >/dev/null 2>&1; then
        HAVE_PY=1
        echo "[*] python3 đã có."
    else
        echo "[*] Chưa có python3."
    fi

    if python3 -m pip -V >/dev/null 2>&1; then
        HAVE_PIP=1
        echo "[*] pip cho python3 đã có."
    else
        echo "[*] Chưa có pip cho python3."
    fi

    # Nếu cả hai đã có -> xong
    if [ "$HAVE_PY" -eq 1 ] && [ "$HAVE_PIP" -eq 1 ]; then
        echo "[*] python3 + pip đầy đủ, bỏ qua cài thêm."
        return 0
    fi

    echo "[*] Đang cài python3 và python3-pip bằng opkg..."
    opkg update || true
    opkg install python3 python3-pip || {
        echo "[ERROR] Không cài được python3/python3-pip, dừng."
        exit 1
    }

    # Kiểm tra lại
    if ! command -v python3 >/dev/null 2>&1; then
        echo "[FATAL] python3 vẫn không tồn tại sau khi cài."
        exit 1
    fi

    if ! python3 -m pip -V >/dev/null 2>&1; then
        echo "[FATAL] pip cho python3 vẫn không dùng được sau khi cài."
        exit 1
    fi
}

# ---------- 2. requests qua pip ----------

ensure_requests() {
    echo "[*] Kiểm tra module requests trong python3..."
    if python3 - << 'PY' >/dev/null 2>&1
try:
    import requests
except ImportError:
    raise SystemExit(1)
PY
    then
        echo "[*] Python module 'requests' đã có, bỏ qua."
        return 0
    fi

    echo "[*] Chưa có 'requests', đang cài bằng pip..."
    # --no-cache-dir + tắt check version cho nhẹ
    python3 -m pip install --no-cache-dir --disable-pip-version-check requests || {
        echo "[ERROR] Không cài được module 'requests' bằng pip."
        exit 1
    }

    echo "[*] Đã cài xong 'requests'."
}

# ---------- Hàm tải file (curl hoặc wget) ----------

download_to() {
    URL="$1"
    DST="$2"

    echo "[*] Tải $URL -> $DST"

    if command -v curl >/dev/null 2>&1; then
        curl -fL "$URL" -o "$DST"
    elif command -v wget >/dev/null 2>&1; then
        wget -O "$DST" "$URL"
    else
        echo "[FATAL] Cần curl hoặc wget (opkg install curl hoặc wget)."
        exit 1
    fi
}

# ================== BẮT ĐẦU CÀI ĐẶT ==================

echo "=== Bước 1: Đảm bảo python3 + pip ==="
ensure_python3_and_pip

echo
echo "=== Bước 2: Cài 'requests' bằng pip ==="
ensure_requests

echo
echo "=== Bước 3: Tải bot_openwrt.py từ GitHub ==="
download_to "$REPO_RAW/bot_openwrt.py" "$BOT_DST"
chmod 700 "$BOT_DST"

echo
echo "=== Bước 4: Tải init script telegram_bot từ GitHub ==="
download_to "$REPO_RAW/telegram_bot.init" "$INIT_DST"

# Loại bỏ CRLF nếu có (nếu bạn edit trên Windows)
sed -i 's/\r$//' "$INIT_DST"
chmod 755 "$INIT_DST"

echo
echo "=== Bước 5: Enable service telegram_bot ==="
/etc/init.d/telegram_bot enable || true

echo
echo "================= DONE ================="
echo "Đã tải:"
echo "  - $BOT_DST"
echo "  - $INIT_DST (service: telegram_bot)"
echo
echo "Bước tiếp theo (lần đầu cấu hình):"
echo "  python3 /root/bot_openwrt.py config"
echo
echo "Wizard cấu hình xong sẽ TỰ GỌI:"
echo "  /etc/init.d/telegram_bot restart"
echo "========================================="
EOF

chmod +x /root/install_vwrt_bot.sh
