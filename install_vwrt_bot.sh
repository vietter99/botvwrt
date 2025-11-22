cat << 'EOF' > /root/install_vwrt_bot.sh
#!/bin/sh

# ====== CẤU HÌNH ======
REPO_RAW="https://raw.githubusercontent.com/vietter99/botvwrt/main"
# ============================================================

BOT_DST="/root/bot_openwrt.py"
INIT_DST="/etc/init.d/telegram_bot"

set -e

echo "=== VWRT BOT INSTALLER (rút gọn) ==="
echo
echo "Lưu ý:"
echo "  - YÊU CẦU đã có sẵn: python3, python3-pip, và module python 'requests'."
echo "  - Nếu chưa có, tự cài thủ công trước khi chạy bot."
echo

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

echo "=== Bước 1: Tải bot_openwrt.py từ GitHub ==="
download_to "$REPO_RAW/bot_openwrt.py" "$BOT_DST"
chmod 700 "$BOT_DST"

echo
echo "=== Bước 2: Tạo init script /etc/init.d/telegram_bot ==="

cat << 'EOF_INIT' > "$INIT_DST"
#!/bin/sh /etc/rc.common

START=99
STOP=10
USE_PROCD=1

SCRIPT="/root/bot_openwrt.py"
PYTHON_BIN="/usr/bin/python3"

. /lib/functions.sh

load_bot_config() {
    config_load telegram_bot
    config_get TELEGRAM_TOKEN main telegram_token
    config_get OPENAI_API_KEY main openai_key
    config_get GEMINI_API_KEY main gemini_key
    config_get ADMIN_ID       main admin_id
}

start_service() {
    load_bot_config

    if [ -z "$TELEGRAM_TOKEN" ]; then
        logger -t telegram_bot "TELEGRAM_TOKEN chưa cấu hình, không start bot"
        return 1
    fi

    procd_open_instance

    procd_set_param env \
        TELEGRAM_TOKEN="$TELEGRAM_TOKEN" \
        OPENAI_API_KEY="$OPENAI_API_KEY" \
        GEMINI_API_KEY="$GEMINI_API_KEY" \
        ADMIN_ID="$ADMIN_ID"

    procd_set_param command "$PYTHON_BIN" -u "$SCRIPT"
    procd_set_param stdout 1
    procd_set_param stderr 1

    procd_close_instance
}

stop_service() {
    :
}
EOF_INIT

# Loại bỏ CRLF nếu lỡ bị dính
sed -i 's/\r$//' "$INIT_DST"
chmod 755 "$INIT_DST"

echo
echo "=== Bước 3: Enable service telegram_bot ==="
/etc/init.d/telegram_bot enable || true

echo
echo "=== Bước 4: Chạy wizard cấu hình lần đầu ==="
if command -v python3 >/dev/null 2>&1; then
    python3 /root/bot_openwrt.py config
    echo
    echo "=== Bước 5: Restart service telegram_bot ==="
    /etc/init.d/telegram_bot restart || true
else
    echo "[CẢNH BÁO] Không tìm thấy python3, không chạy được wizard."
    echo "Bạn cần tự chạy sau khi cài python3:"
    echo "  python3 /root/bot_openwrt.py config"
    echo "  /etc/init.d/telegram_bot restart"
fi

echo
echo "================= DONE ================="
echo "Đã tạo:"
echo "  - $BOT_DST"
echo "  - $INIT_DST (service: telegram_bot)"
echo "Bot đã được cấu hình (nếu python3 có sẵn) và service đã restart."
echo "========================================="
EOF

chmod +x /root/install_vwrt_bot.sh
