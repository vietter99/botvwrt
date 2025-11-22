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
Nếu đổi token/API key → chỉ cần chạy lại wizard:

python3 /root/bot_openwrt.py config

🧠 Tự tóm tắt output lệnh router

Thay vì dump cả đống log lên Telegram, bot:

Gom output lệnh

Nhờ LLM tóm tắt lại ngắn gọn

Trả về vài dòng dễ đọc: ví dụ có bao nhiêu client, thông tin hệ thống, kết quả đổi Wi-Fi…

🔁 Chạy như service trên OpenWrt

Có init script /etc/init.d/telegram_bot:

Tự start khi boot

Tự restart nếu crash

Load config từ /etc/config/telegram_bot

Log xem bằng:

logread -f
