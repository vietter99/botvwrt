# 🤖 VWRT Bot – Trợ lý Telegram điều khiển OpenWrt bằng ChatGPT & Gemini

Bot Telegram chạy trực tiếp trên OpenWrt, dùng OpenAI & Gemini để:
- Chat như trợ lý AI bình thường
- Điều khiển router bằng tiếng Việt: xem client, đổi mật khẩu Wi-Fi, reboot, xem hệ thống…
- Không cần đăng nhập LuCI, mọi thao tác qua Telegram

---

## ✨ 1. Tính năng nổi bật

### 🤝 Chat AI đa nền tảng (OpenAI + Gemini)
- Hỗ trợ cả **ChatGPT (OpenAI)** và **Gemini** trong cùng một bot.
- Có thể chuyển model ngay trong Telegram:
  - `/use_chatgpt` → dùng OpenAI
  - `/use_gemini` → dùng Gemini
- Chat hỏi đáp bình thường: IT, mạng, đời sống, cấu hình OpenWrt…

### 📡 Điều khiển OpenWrt bằng ngôn ngữ tự nhiên
- Cú pháp:  
  ` /rt <câu lệnh tiếng Việt> `
- Ví dụ:
  - `/rt cho mình xem client đang kết nối Wi-Fi`
  - `/rt đổi mật khẩu wifi 5G thành 12345678`
  - `/rt xem thông tin router`
  - `/rt reboot router`
- Bot sẽ:
  1. Thu thập thông tin môi trường router (iw dev, ip link, ubus list, uci show wireless, …)
  2. Nhờ LLM sinh ra **lệnh shell tương ứng** (ưu tiên an toàn)
  3. Chạy lệnh trên router
  4. Tóm tắt kết quả gọn gàng bằng tiếng Việt gửi lại cho admin

### 🛡️ An toàn & hạn chế lệnh phá hoại
- Có danh sách chặn cứng một số lệnh nguy hiểm:
  - `rm -rf /`
  - `mkfs.*`
  - `dd if=...`
  - shell fork-bomb, v.v.
- Nếu lệnh sinh ra có chứa chuỗi nguy hiểm → bot **từ chối thực thi** và báo lại.

### 🔐 Bảo mật API key & token
- Không hardcode token/API key trong code Python.
- Token & key được lưu trong **`/etc/config/telegram_bot`**, bot đọc qua biến môi trường.
- File cấu hình được khuyến nghị:
  ```bash
  chmod 600 /etc/config/telegram_bot
  chown root:root /etc/config/telegram_bot
  
* Nếu đổi token/API key → chỉ cần chạy lại wizard:

  ```bash
  python3 /root/bot_openwrt.py config
  ```

### 🧠 Tự tóm tắt output lệnh router

* Thay vì dump cả đống log lên Telegram, bot:

  * Gom output lệnh
  * Nhờ LLM tóm tắt lại ngắn gọn
  * Trả về vài dòng dễ đọc: ví dụ có bao nhiêu client, thông tin hệ thống, kết quả đổi Wi-Fi…

### 🔁 Chạy như service trên OpenWrt

* Có init script `/etc/init.d/telegram_bot`:

  * Tự start khi boot
  * Tự restart nếu crash
  * Load config từ `/etc/config/telegram_bot`
* Log xem bằng:

  ```bash
  logread -f
  ```
---

## ⚠️ 2. Nhắc nhở & yêu cầu hệ thống

### 🧩 Yêu cầu tối thiểu

* Thiết bị: Router chạy **OpenWrt** (khuyến nghị 19.07+ / 21.02+ / 22.03+)
* RAM: tối thiểu **64 MB**, nên có **128 MB** trở lên cho chạy LLM + Python ổn định.
* Flash:

  * Cài được:

    * `python3`
    * `python3-pip`
    * module Python `requests`
* Kết nối Internet ổn định (để gọi API Telegram, OpenAI, Gemini).

### 🐍 Yêu cầu về Python trên OpenWrt

Bot cần:

```bash
opkg update
opkg install python3 python3-pip
pip3 install requests
```

Nếu firmware bạn đang dùng:

* Đã **lược bỏ python3** / **không có pip** / quá ít flash:

  * Khuyến nghị dùng **ROM gốc** hoặc bản build có đầy đủ `python3`, `python3-pip`.
  * Hoặc tự build lại OpenWrt có thêm gói Python.

### 🔑 Yêu cầu tài khoản & API

Bạn cần chuẩn bị:

1. **Telegram Bot Token** từ BotFather
2. **Telegram ADMIN_ID**: ID Telegram của bạn (dùng bot @userinfobot hoặc tương tự để lấy).
3. **OpenAI API key** (nếu muốn dùng ChatGPT).
4. **Gemini API key** (nếu muốn dùng Gemini).

---

## ⚡ 3. Cài đặt nhanh (Một dòng lệnh)

### 🧷 Bước 1 – Cài bot bằng 1 lệnh

Chạy trên router (SSH vào xong paste nguyên dòng):

```bash
wget --no-check-certificate "https://raw.githubusercontent.com/vietter99/botvwrt/main/install_vwrt_bot.sh" -O /tmp/install_vwrt_bot.sh && chmod +x /tmp/install_vwrt_bot.sh && sed -i 's/\r$//' /tmp/install_vwrt_bot.sh && /tmp/install_vwrt_bot.sh
```

Script này sẽ:

* Cài `python3` + `python3-pip` nếu chưa có.
* `pip3 install requests` nếu thiếu.
* Tải:

  * `bot_openwrt.py` → `/root/bot_openwrt.py`
  * init script → `/etc/init.d/telegram_bot`
* Cấp quyền thực thi, enable service.

### 🧷 Bước 2 – Chạy wizard cấu hình lần đầu

Sau khi cài xong:

```bash
python3 /root/bot_openwrt.py config
```

Wizard sẽ hỏi:

* `TELEGRAM_TOKEN`
* `OPENAI_API_KEY`
* `GEMINI_API_KEY`
* `ADMIN_ID`

Và sẽ lưu vào:

```text
/etc/config/telegram_bot
```

Sau khi lưu cấu hình:

* Bot tự restart (nếu script cài đặt cấu hình sẵn),
* Gửi **lời chào & hướng dẫn** tới Telegram của ADMINID, không cần gõ `/start` thủ công.

Nếu chưa tự restart, bạn có thể:

```bash
/etc/init.d/telegram_bot restart
```

---

## 💬 Cách sử dụng cơ bản

Trong Telegram, chat với bot:

### 1) Xem hướng dẫn

```text
/start
```

(Trong thiết kế của bạn, sau khi lưu config bot có thể gửi lời chào tự động. `/start` dùng lại để xem help.)

### 2) Chọn model AI

```text
/use_chatgpt   → dùng ChatGPT (OpenAI)
/use_gemini    → dùng Gemini
```

### 3) Chat bình thường

Gõ câu hỏi bất kỳ:

```text
giá vàng 9999 hôm nay
hướng dẫn cấu hình port forwarding trên OpenWrt
cách tối ưu sóng wifi trong nhà 3 tầng
```

Bot sẽ trả lời bằng model hiện tại (ChatGPT hoặc Gemini).

### 4) Điều khiển router

Dùng prefix `/rt` + tiếng Việt tự nhiên:

```text
/rt cho mình xem client đang kết nối Wi-Fi
/rt đổi mật khẩu wifi 2.4G thành 12345678
/rt cho mình xem thông tin router
/rt reboot router
/rt tắt wifi 5G trong 30 phút
```

Bot:

* Sinh lệnh shell,
* Chạy trên router,
* Tóm tắt kết quả lại bằng tiếng Việt.

---

## 🧹 Gỡ cài đặt (tùy chọn)

Nếu muốn gỡ:

```bash
/etc/init.d/telegram_bot stop
/etc/init.d/telegram_bot disable
rm -f /etc/init.d/telegram_bot
rm -f /etc/config/telegram_bot
rm -f /root/bot_openwrt.py
```

(Nếu không chắc, chỉ cần disable service thôi, không cần xoá file.)

---

## 📝 Gợi ý phát triển thêm

* Giao diện web nhỏ trên LuCI để xem log bot và restart service.
* Mapping thủ công một số lệnh “nhạy cảm” (reboot, reset Wi-Fi…) thành action riêng, không để LLM tự suy đoán.
* Thêm chế độ “read-only” cho một số user khác ngoài ADMIN, chỉ xem thông tin, không thay đổi cấu hình.

---

