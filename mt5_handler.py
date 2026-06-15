import MetaTrader5 as mt5
import logging

logger = logging.getLogger(__name__)

_magic_number = 20240101


def set_magic(magic: int):
    global _magic_number
    _magic_number = magic


def connect() -> bool:
    if not mt5.initialize():
        logger.error(f"MT5 initialize failed: {mt5.last_error()}")
        return False
    info = mt5.account_info()
    if info is None:
        logger.error("Chưa có tài khoản nào đăng nhập trong MT5. Vui lòng đăng nhập trước.")
        mt5.shutdown()
        return False
    logger.info(f"Kết nối MT5 thành công | Tài khoản: {info.login} | Số dư: {info.balance:.2f} {info.currency}")
    return True


def disconnect():
    mt5.shutdown()


def get_account_info() -> dict:
    info = mt5.account_info()
    if info is None:
        return {}
    return {
        "login": info.login,
        "balance": info.balance,
        "currency": info.currency,
        "server": info.server,
        "leverage": info.leverage,
    }


def _get_filling_mode(symbol: str) -> int:
    info = mt5.symbol_info(symbol)
    if info is None:
        return mt5.ORDER_FILLING_IOC
    filling = info.filling_mode
    if filling & mt5.ORDER_FILLING_IOC:
        return mt5.ORDER_FILLING_IOC
    if filling & mt5.ORDER_FILLING_FOK:
        return mt5.ORDER_FILLING_FOK
    return mt5.ORDER_FILLING_RETURN


def _ensure_symbol(symbol: str) -> bool:
    info = mt5.symbol_info(symbol)
    if info is None:
        return False
    if not info.visible:
        return mt5.symbol_select(symbol, True)
    return True


def place_order(
    symbol: str,
    action: str,
    lot: float,
    sl: float = 0.0,
    tp: float = 0.0,
    comment: str = "TradingView",
) -> dict:
    if not _ensure_symbol(symbol):
        return {"success": False, "error": f"Không tìm thấy symbol: {symbol}"}

    action_lower = action.lower()
    if action_lower == "buy":
        order_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
    elif action_lower == "sell":
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
    elif action_lower == "close":
        return close_all_positions(symbol, comment)
    else:
        return {"success": False, "error": f"Action không hợp lệ: {action}"}

    # Lấy filling mode phù hợp với broker
    filling_mode = _get_filling_mode(symbol)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": _magic_number,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling_mode,
    }
    if sl:
        request["sl"] = sl
    if tp:
        request["tp"] = tp

    result = mt5.order_send(request)
    if result is None:
        return {"success": False, "error": str(mt5.last_error())}
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return {"success": False, "error": result.comment, "retcode": result.retcode}

    logger.info(f"Lệnh thành công | {action.upper()} {lot} {symbol} @ {price} | ticket={result.order}")
    return {
        "success": True,
        "ticket": result.order,
        "symbol": symbol,
        "action": action_lower,
        "lot": lot,
        "price": price,
    }


def close_all_positions(symbol: str, comment: str = "close") -> dict:
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return {"success": True, "closed": 0, "message": "Không có lệnh đang mở"}

    closed, errors = 0, []
    for pos in positions:
        if pos.type == mt5.ORDER_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask

        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": order_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 20,
            "magic": _magic_number,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        r = mt5.order_send(req)
        if r and r.retcode == mt5.TRADE_RETCODE_DONE:
            closed += 1
            logger.info(f"Đóng lệnh ticket={pos.ticket}")
        else:
            errors.append(r.comment if r else str(mt5.last_error()))

    return {"success": len(errors) == 0, "closed": closed, "errors": errors}


def get_open_positions(symbol: str = None) -> list:
    positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
    if not positions:
        return []
    return [
        {
            "ticket": p.ticket,
            "symbol": p.symbol,
            "type": "buy" if p.type == 0 else "sell",
            "volume": p.volume,
            "open_price": p.price_open,
            "sl": p.sl,
            "tp": p.tp,
            "profit": p.profit,
        }
        for p in positions
    ]
