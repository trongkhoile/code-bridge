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

## Kết nối Internet (ngrok / VPS)

Nếu chạy trên máy tính cá nhân (không phải VPS), cần ngrok để TradingView gửi được tín hiệu về máy bạn.

1. Tải ngrok tại [ngrok.com](https://ngrok.com) → đăng ký tài khoản miễn phí
2. Mở terminal, chạy:
   ```
   ngrok http 8000
   ```
3. Copy URL dạng `https://xxxx.ngrok-free.app`
4. Dán vào ô **Public URL** trong phần mềm

Nếu dùng VPS (khuyến nghị cho chạy 24/7):

- Cài app này **trực tiếp trên VPS** (MT5 phải chạy cùng máy với app).
- Mở port app đang dùng (mặc định `8000`) ở **2 lớp tường lửa**: Windows Firewall trên VPS, và tường lửa mạng của nhà cung cấp VPS (Security Group / NSG).
- Điền ô **Public URL** dạng `http://<IP-VPS-của-bạn>:8000` (nếu để mặc định port `8000` thì bắt buộc phải ghi `:8000` trong URL — bỏ port đi thì trình duyệt/TradingView sẽ mặc định gọi vào port `80`).
- Không cần ngrok trong trường hợp này.

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

### Đóng lệnh theo tài khoản (TP/SL — alert dạng text)

Dùng cho Alert báo "đã chạm TP/SL" — app sẽ tự đóng toàn bộ lệnh đang mở của symbol đó, chỉ trên (các) tài khoản MT5 (login) bạn chỉ định. Message **không phải JSON**, dán nguyên văn (TradingView tự điền `{{ticker}}` / `{{interval}}` / `{{close}}` khi kích hoạt):

```
✅ TP chốt lời | {{ticker}} | {{interval}} | Giá {{close}} || Account 123456
❌ SL cắt lỗ   | {{ticker}} | {{interval}} | Giá {{close}} || Account 123456
```

Muốn đóng cùng lúc nhiều tài khoản bằng 1 alert, liệt kê login cách nhau bằng dấu phẩy:

```
✅ TP chốt lời | {{ticker}} | {{interval}} | Giá {{close}} || Account 123456, 234567
```

---

## Các giá trị action hợp lệ

| Action | Mô tả |
|--------|-------|
| `buy` | Đặt lệnh Buy. Nếu đang có lệnh Sell mở cho symbol đó, app tự đóng Sell trước rồi mở Buy mới (đảo chiều) |
| `sell` | Đặt lệnh Sell. Nếu đang có lệnh Buy mở cho symbol đó, app tự đóng Buy trước rồi mở Sell mới (đảo chiều) |
| `close` | Đóng tất cả lệnh đang mở của symbol đó |

Nếu tín hiệu mới **cùng chiều** với lệnh đang mở (VD: đang Buy, tín hiệu Buy tiếp) → app bỏ qua, không mở thêm lệnh.

---

## Dành cho Developer

Nếu bạn muốn chạy trực tiếp từ source code thay vì dùng file `.exe`:

### Yêu cầu thêm

- Python 3.10+ (bản dùng để build hiện tại là 3.12)
- pip

### Cài đặt

```bash
git clone https://github.com/trongkhoile/code-bridge.git
cd code-bridge
pip install -r requirements.txt pillow
```

> Lưu ý: `pillow` không nằm trong `requirements.txt` nhưng bắt buộc phải có — `app.py` dùng nó để hiển thị logo, và bước build cũng dùng nó để tạo file icon (`logo.ico`).

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
├── build.bat         # Script build ra file .exe (xem mục bên dưới)
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

### Build ra file .exe + đóng gói .zip

Dự án đã có sẵn `build.bat` để tự động hoá toàn bộ bước build bằng PyInstaller — không cần tự gõ lệnh `pyinstaller` thủ công.

**Yêu cầu trước khi build:**
```bash
pip install -r requirements.txt pillow pyinstaller
```
(`pyinstaller` nếu chưa cài thì `build.bat` sẽ tự cài giúp bạn ở bước [1/3])

Cần còn đủ dung lượng ổ đĩa trống — nên có tối thiểu **300–500 MB trống**. Quá trình build tạo ra thư mục `build\` (file tạm, ~25–70 MB), thư mục `dist\ALGOBOT-TradingView\` (app đã đóng gói, ~70 MB), và file zip cuối cùng (~30 MB). Nếu ổ đĩa gần đầy, build có thể báo lỗi giữa chừng hoặc file zip bị lỗi/thiếu.

**Chạy build** (double-click `build.bat`, hoặc chạy qua terminal):

PowerShell:
```powershell
.\build.bat
```

Git Bash:
```bash
./build.bat
```

Build mất khoảng 1–2 phút. Thấy dòng `Build xong! Thu muc: dist\ALGOBOT-TradingView` là thành công. Kết quả nằm ở `dist\ALGOBOT-TradingView\ALGOBOT-TradingView.exe`, chạy được ngay không cần cài Python.

**Nén thành .zip để gửi khách:**

Cách nhanh nhất: click phải thư mục `dist\ALGOBOT-TradingView` → **Send to** → **Compressed (zipped) folder**.

Hoặc bằng lệnh (đảm bảo ghi đè bản cũ):

PowerShell:
```powershell
if (Test-Path "dist\ALGOBOT-TradingView.zip") { Remove-Item "dist\ALGOBOT-TradingView.zip" -Force }
Compress-Archive -Path "dist\ALGOBOT-TradingView" -DestinationPath "dist\ALGOBOT-TradingView.zip" -Force
```

Git Bash (không có sẵn lệnh `zip` nên gọi PowerShell ngay trong dòng lệnh):
```bash
rm -f "dist/ALGOBOT-TradingView.zip"
powershell -NoProfile -Command "Compress-Archive -Path 'dist/ALGOBOT-TradingView' -DestinationPath 'dist/ALGOBOT-TradingView.zip' -Force"
```

**Lưu ý quan trọng:** mỗi khi sửa `app.py`, `server.py`, hoặc `mt5_handler.py`, file `.exe` cũ **không tự cập nhật** — phải build lại và nén lại zip mới trước khi gửi khách.

**Sự cố thường gặp:**

| Hiện tượng | Nguyên nhân / cách xử lý |
|---|---|
| Build báo lỗi thiếu module (`ModuleNotFoundError`) | Chạy lại `pip install -r requirements.txt pillow pyinstaller` |
| Build dừng giữa chừng, không rõ lỗi | Kiểm tra dung lượng ổ đĩa còn trống, dọn bớt nếu gần đầy |
| File zip bị thiếu / lỗi khi nén | Xóa file zip cũ trước khi nén, đảm bảo `dist\ALGOBOT-TradingView` đã build xong hoàn chỉnh |
| Khách chạy `.exe` bị chặn | Do Windows SmartScreen/antivirus chặn file chưa có chữ ký số — hướng dẫn khách chọn "More info" → "Run anyway" |
| Sửa code xong mà khách vẫn thấy bản cũ | Quên build lại và/hoặc quên xóa zip cũ trước khi nén |

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
