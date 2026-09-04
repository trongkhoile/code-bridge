import json
import logging
import re
from flask import Flask, request, jsonify
import mt5_handler

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.logger.handlers = []

settings: dict = {
    "token": "",
    "default_symbol": "XAUUSD",
    "default_lot": 0.01,
    "default_sl": 0.0,
    "default_tp": 0.0,
    "magic_number": 20240101,
    "max_daily_loss": 0.0,
    "max_daily_profit": 0.0,
}

# Mẫu tin nhắn đóng lệnh theo tài khoản (không phải JSON), hỗ trợ 1 hoặc nhiều tài khoản
# và có chỉ định chiều lệnh (BUY/SELL) để tránh đóng nhầm lệnh mới khi bị đảo chiều:
#   ✅ TP chốt lời BUY  | {{ticker}} | {{interval}} | Giá {{close}} || Account 123456
#   ❌ SL cắt lỗ SELL   | {{ticker}} | {{interval}} | Giá {{close}} || Account 123456, 234567
_ACCOUNT_RE   = re.compile(r"Account\s*[:\-]?\s*([\d][\d,\s]*)", re.IGNORECASE)
_DIRECTION_RE = re.compile(r"\b(BUY|SELL)\b", re.IGNORECASE)


def _dispatch_order(order_params: dict) -> tuple:
    """Đẩy lệnh vào tất cả terminal MT5 tự phát hiện (hoặc 1 tài khoản nếu không có terminal nào), trả về response Flask."""
    magic = settings.get("magic_number", 20240101)
    terminal_paths = mt5_handler.find_mt5_terminals()
    if terminal_paths:
        accounts = [
            {"name": f"MT5 #{i+1}", "terminal_path": p, "enabled": True}
            for i, p in enumerate(terminal_paths)
        ]
        logger.info(f"Phát hiện {len(accounts)} terminal MT5 đang chạy")
        results = mt5_handler.place_order_parallel(accounts, order_params, magic=magic)
        ok      = sum(1 for r in results if r.get("success") and not r.get("skipped"))
        skipped = sum(1 for r in results if r.get("skipped"))
        total   = len(results) - skipped
        logger.info(f"Kết quả: {ok}/{total} tài khoản thành công"
                    + (f" ({skipped} bỏ qua)" if skipped else ""))
        return jsonify({
            "status": "ok" if ok > 0 else "fail",
            "accounts_total": total,
            "accounts_success": ok,
            "results": [r for r in results if not r.get("skipped")],
        })
    else:
        result = mt5_handler.place_order(
            symbol=order_params["symbol"], action=order_params["action"],
            lot=order_params.get("lot", 0.0), sl=order_params.get("sl", 0.0),
            tp=order_params.get("tp", 0.0), comment=order_params.get("comment", "TradingView"),
            max_daily_loss=order_params.get("max_daily_loss", 0.0),
            max_daily_profit=order_params.get("max_daily_profit", 0.0),
            close_direction=order_params.get("close_direction"),
        )
        if not result["success"]:
            logger.error(f"Đặt lệnh thất bại: {result}")
            return jsonify({"status": "fail", **result}), 500
        return jsonify({"status": "ok", **result})


def _handle_text_close_alert(text: str):
    """Nhận diện tin nhắn dạng text 'TP chốt lời / SL cắt lỗ ... || Account xxx' và đóng lệnh đúng tài khoản đó."""
    stripped = text.strip()
    if stripped.startswith("✅"):
        kind = "TP"
    elif stripped.startswith("❌"):
        kind = "SL"
    else:
        return None

    main_part, sep, acc_part = stripped.partition("||")
    if not sep:
        return None
    m_acc = _ACCOUNT_RE.search(acc_part)
    if not m_acc:
        return None
    logins = [int(n) for n in re.findall(r"\d+", m_acc.group(1))]
    if not logins:
        return None

    fields = [f.strip() for f in main_part.split("|")]
    if len(fields) < 2 or not fields[1]:
        return None
    symbol = fields[1]

    m_dir = _DIRECTION_RE.search(fields[0])
    direction = m_dir.group(1).lower() if m_dir else None

    logger.info(
        f"Webhook (text) nhận: {kind} {direction.upper() if direction else '?'} {symbol}"
        f" -> đóng lệnh Account {logins}"
    )

    order_params = {
        "symbol": symbol, "action": "close", "lot": 0.0,
        "comment": f"{kind} auto-close",
        "target_accounts": logins,
        "close_direction": direction,
    }
    return _dispatch_order(order_params)


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            text = request.get_data(as_text=True) or ""
            resp = _handle_text_close_alert(text)
            if resp is not None:
                return resp
            return jsonify({"status": "fail", "message": "Empty JSON"}), 400

        logger.info(f"Webhook nhận: {json.dumps(data, ensure_ascii=False)}")

        token = data.get("token", "")
        if settings["token"] and token != settings["token"]:
            logger.warning("Token không hợp lệ")
            return jsonify({"status": "fail", "message": "Invalid token"}), 401

        symbol  = data.get("symbol", "") or settings["default_symbol"]
        action  = data.get("action", "").lower()
        lot     = float(data.get("lot", settings["default_lot"]))
        sl      = float(data.get("sl", settings["default_sl"]))
        tp      = float(data.get("tp", settings["default_tp"]))
        comment = data.get("comment", "TradingView")
        max_daily_loss   = float(settings.get("max_daily_loss", 0.0))
        max_daily_profit = float(settings.get("max_daily_profit", 0.0))

        if not symbol or not action:
            return jsonify({"status": "fail", "message": "Thiếu symbol hoặc action"}), 400

        order_params = {
            "symbol": symbol, "action": action, "lot": lot,
            "sl": sl, "tp": tp, "comment": comment,
            "max_daily_loss": max_daily_loss, "max_daily_profit": max_daily_profit,
        }

        # Lọc tài khoản nếu webhook chỉ định
        target_accounts = data.get("accounts", [])
        if target_accounts:
            order_params["target_accounts"] = [int(a) for a in target_accounts]
            logger.info(f"Chỉ đẩy vào tài khoản: {target_accounts}")

        return _dispatch_order(order_params)

    except Exception as e:
        logger.error(f"Lỗi webhook: {e}")
        return jsonify({"status": "fail", "message": str(e)}), 500


@app.route("/positions", methods=["GET"])
def positions():
    symbol = request.args.get("symbol")
    return jsonify(mt5_handler.get_open_positions(symbol))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})
