import json
import logging
from flask import Flask, request, jsonify
import mt5_handler

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.logger.handlers = []  # dùng logger của app thay vì Flask

settings: dict = {
    "token": "",
    "default_symbol": "XAUUSD",
    "default_lot": 0.01,
    "default_sl": 0.0,
    "default_tp": 0.0,
}


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"status": "fail", "message": "Empty JSON"}), 400

        logger.info(f"Webhook nhận: {json.dumps(data, ensure_ascii=False)}")

        token = data.get("token", "")
        if settings["token"] and token != settings["token"]:
            logger.warning("Token không hợp lệ")
            return jsonify({"status": "fail", "message": "Invalid token"}), 401

        symbol = data.get("symbol", "") or settings["default_symbol"]
        action = data.get("action", "").lower()
        lot    = float(data.get("lot", settings["default_lot"]))
        sl     = float(data.get("sl", settings["default_sl"]))
        tp     = float(data.get("tp", settings["default_tp"]))
        comment = data.get("comment", "TradingView")

        if not symbol or not action:
            return jsonify({"status": "fail", "message": "Thiếu symbol hoặc action"}), 400

        result = mt5_handler.place_order(symbol=symbol, action=action,
                                          lot=lot, sl=sl, tp=tp, comment=comment)
        if not result["success"]:
            logger.error(f"Đặt lệnh thất bại: {result}")
            return jsonify({"status": "fail", **result}), 500

        return jsonify({"status": "ok", **result})

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
