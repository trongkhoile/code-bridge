# ALGOBOT — TradingView Automation

Phần mềm tự động đặt lệnh MT5 từ tín hiệu TradingView qua Webhook.

---

## Yêu cầu

- Windows 10 / 11
- MetaTrader 5 đã cài và **đăng nhập tài khoản**
- ngrok (nếu chạy trên máy tính cá nhân, không phải VPS)

---

## Cài đặt

### Bước 1 — Tải phần mềm

Tải file ZIP tại: [algotdv.vercel.app](https://algotdv.vercel.app)

Giải nén ra một thư mục bất kỳ.

### Bước 2 — Mở MetaTrader 5

Mở MT5 và đăng nhập tài khoản trước. Phần mềm sẽ kết nối vào MT5 đang chạy sẵn — không cần nhập thông tin tài khoản vào phần mềm.

### Bước 3 — Chạy phần mềm

Double-click vào `ALGOBOT-TradingView.exe`.

> Nếu Windows hiện cảnh báo SmartScreen → nhấn **More info** → **Run anyway**

---

## Cấu hình

Sau khi mở phần mềm, điền các thông tin sau:

| Trường | Mô tả |
|--------|-------|
| **Webhook Token** | Chuỗi bí mật để xác thực tín hiệu. Tự đặt tuỳ ý (VD: `algobot123`) |
| **Port** | Cổng server chạy. Mặc định `8000`, không cần đổi |
| **Public URL** | URL ngrok hoặc VPS (xem Bước 4 bên dưới) |
| **Symbol mặc định** | Symbol giao dịch mặc định (VD: `XAUUSD`, `EURUSD`) |
| **Lot / SL / TP** | Khối lượng, Stop Loss, Take Profit mặc định |
| **Magic Number** | Số định danh lệnh. Tự đặt tuỳ ý |

Sau khi điền xong → nhấn **Khởi động server**.

---

## Kết nối Internet (ngrok)

Nếu chạy trên máy tính cá nhân (không phải VPS), cần ngrok để TradingView gửi được tín hiệu về máy bạn.

1. Tải ngrok tại [ngrok.com](https://ngrok.com) → đăng ký tài khoản miễn phí
2. Mở terminal, chạy:
   ```
   ngrok http 8000
   ```
3. Copy URL dạng `https://xxxx.ngrok-free.app`
4. Dán vào ô **Public URL** trong phần mềm

> Nếu dùng VPS thì dán IP hoặc domain VPS vào ô Public URL, không cần ngrok.

---

## Tạo Alert trên TradingView

### Strategy (Pine Script Strategy)

1. Mở TradingView → chọn biểu đồ có Strategy
2. Nhấn biểu tượng đồng hồ (Alerts) → **Create Alert**
3. Tab **Notifications** → bật **Webhook URL** → dán URL từ phần mềm
4. Tab **Alert** → ô **Message** → dán JSON:

```json
{
  "token": "your_token",
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "lot": 0.01,
  "sl": 0,
  "tp": 0,
  "comment": "TV Signal"
}
```

### Indicator (chỉ báo thủ công)

Tạo **2 Alert riêng** — một cho BUY, một cho SELL:

**Alert BUY:**
```json
{
  "token": "your_token",
  "symbol": "XAUUSD",
  "action": "buy",
  "lot": 0.01,
  "sl": 0,
  "tp": 0,
  "comment": "TV Signal"
}
```

**Alert SELL:**
```json
{
  "token": "your_token",
  "symbol": "XAUUSD",
  "action": "sell",
  "lot": 0.01,
  "sl": 0,
  "tp": 0,
  "comment": "TV Signal"
}
```

> **Lưu ý:** Thay `your_token` bằng token bạn đã đặt trong phần mềm. Thay `XAUUSD` bằng symbol bạn muốn giao dịch.

---

## Các giá trị action hợp lệ

| Action | Mô tả |
|--------|-------|
| `buy` | Đặt lệnh Buy |
| `sell` | Đặt lệnh Sell |
| `close` | Đóng tất cả lệnh đang mở của symbol đó |

---

---

## Dành cho Developer

Nếu bạn muốn chạy trực tiếp từ source code thay vì dùng file `.exe`:

### Yêu cầu thêm

- Python 3.10+
- pip

### Cài đặt

```bash
git clone https://github.com/your-repo/algobot-tradingview
cd algobot-tradingview
pip install -r requirements.txt
```

### Chạy

```bash
python app.py
```

### Cấu trúc project

```
├── app.py            # GUI chính (customtkinter)
├── server.py         # Flask webhook server
├── mt5_handler.py    # Kết nối và đặt lệnh MT5
├── requirements.txt  # Dependencies
├── settings.json     # Cài đặt (tự sinh khi chạy lần đầu)
└── web/              # Source code website (React + TypeScript + Vite)
```

### Webhook API

**POST** `/webhook` — Nhận tín hiệu đặt lệnh

```json
{
  "token": "your_token",
  "symbol": "XAUUSD",
  "action": "buy",
  "lot": 0.01,
  "sl": 0,
  "tp": 0,
  "comment": "TV Signal"
}
```

**GET** `/positions` — Lấy danh sách lệnh đang mở

**GET** `/positions?symbol=XAUUSD` — Lọc theo symbol

**GET** `/health` — Kiểm tra server còn sống

### Test thủ công

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"your_token\",\"symbol\":\"XAUUSD\",\"action\":\"buy\",\"lot\":0.01}"
```

### Build ra file .exe

```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "ALGOBOT-TradingView" ^
  --icon "logo.ico" ^
  --add-data "logo.png;." ^
  --add-data "logo.ico;." ^
  --collect-all customtkinter ^
  --hidden-import MetaTrader5 ^
  --hidden-import flask ^
  --hidden-import werkzeug ^
  app.py
```

Kết quả nằm trong `dist\ALGOBOT-TradingView\`.

### Website

```bash
cd web
npm install
npm run dev      # Development
npm run build    # Build production
```

---

## Hỗ trợ

Liên hệ **AlgoBot VN** nếu cần hỗ trợ hoặc code bot theo yêu cầu:

- Facebook: [AlgoBot VN](https://www.facebook.com/profile.php?id=100087370578208)
- Zalo: 0856 176 102
- Website: [algobotvn.com](https://algobotvn.com)
