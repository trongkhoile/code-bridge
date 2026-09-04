import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, time as dtime

import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

_magic_number = 20240101


def _compute_daily_pnl(mt5_mod) -> float:
    """Lãi/lỗ trong ngày = lệnh đã đóng hôm nay (lãi/lỗ + phí + swap) + lãi/lỗ nổi của lệnh đang mở."""
    now = datetime.now()
    day_start = datetime.combine(now.date(), dtime.min)
    deals = mt5_mod.history_deals_get(day_start, now)
    realized = sum(d.profit + d.swap + d.commission for d in deals) if deals else 0.0
    positions = mt5_mod.positions_get()
    floating = sum(p.profit for p in positions) if positions else 0.0
    return realized + floating


def get_daily_pnl() -> float:
    return _compute_daily_pnl(mt5)


def _check_daily_limit(mt5_mod, max_daily_loss: float, max_daily_profit: float):
    """Trả về (True, message) nếu đã chạm giới hạn lãi/lỗ ngày, ngược lại (False, None)."""
    if not max_daily_loss and not max_daily_profit:
        return False, None
    pnl = _compute_daily_pnl(mt5_mod)
    if max_daily_loss and pnl <= -abs(max_daily_loss):
        return True, f"Đã chạm giới hạn lỗ ngày ({pnl:.2f}), bỏ qua tín hiệu mới"
    if max_daily_profit and pnl >= abs(max_daily_profit):
        return True, f"Đã chạm giới hạn lãi ngày ({pnl:.2f}), bỏ qua tín hiệu mới"
    return False, None


def set_magic(magic: int):
    global _magic_number
    _magic_number = magic


# ── Single-account helpers ─────────────────────────────────────────────────

def connect(login: int = None, password: str = None, server: str = None,
            terminal_path: str = None) -> bool:
    kwargs = {}
    if terminal_path:
        kwargs["path"] = terminal_path
    if login:
        kwargs["login"] = int(login)
        kwargs["password"] = password or ""
        kwargs["server"] = server or ""
    if not mt5.initialize(**kwargs):
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
    max_daily_loss: float = 0.0,
    max_daily_profit: float = 0.0,
    close_direction: str = None,
) -> dict:
    if not _ensure_symbol(symbol):
        return {"success": False, "error": f"Không tìm thấy symbol: {symbol}"}

    action_lower = action.lower()
    if action_lower == "buy":
        order_type = mt5.ORDER_TYPE_BUY
    elif action_lower == "sell":
        order_type = mt5.ORDER_TYPE_SELL
    elif action_lower == "close":
        return close_all_positions(symbol, comment, direction=close_direction)
    else:
        return {"success": False, "error": f"Action không hợp lệ: {action}"}

    hit_limit, limit_msg = _check_daily_limit(mt5, max_daily_loss, max_daily_profit)
    if hit_limit:
        logger.warning(limit_msg)
        return {"success": True, "skipped": True, "symbol": symbol, "message": limit_msg}

    existing = mt5.positions_get(symbol=symbol)
    if existing:
        if existing[0].type == order_type:
            msg = f"Đã có lệnh {action_lower.upper()} mở cho {symbol}, bỏ qua tín hiệu trùng chiều"
            logger.info(msg)
            return {"success": True, "skipped": True, "symbol": symbol, "message": msg}
        closed, errors = _close_symbol_positions(mt5, symbol, _magic_number, comment)
        if errors:
            return {"success": False, "error": f"Không đóng được lệnh ngược chiều: {errors}"}
        logger.info(f"Đóng {closed} lệnh ngược chiều {symbol} để mở {action_lower.upper()} mới")

    price = mt5.symbol_info_tick(symbol).ask if action_lower == "buy" else mt5.symbol_info_tick(symbol).bid
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
        request["sl"] = price - sl if action_lower == "buy" else price + sl
    if tp:
        request["tp"] = price + tp if action_lower == "buy" else price - tp

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


def _close_symbol_positions(mt5_mod, symbol: str, magic: int, comment: str, direction: str = None) -> tuple:
    """
    Đóng lệnh đang mở của 1 symbol. Nếu có `direction` ("buy"/"sell"), CHỈ đóng đúng
    chiều đó — dùng để tránh tín hiệu đóng lệnh cũ đến trễ (do TradingView không đảm
    bảo thứ tự webhook) lỡ đóng nhầm lệnh mới đã được đảo chiều mở ra sau đó.
    Trả về (số lệnh đã đóng, list lỗi).
    """
    positions = mt5_mod.positions_get(symbol=symbol)
    if not positions:
        return 0, []

    if direction == "buy":
        positions = [p for p in positions if p.type == mt5_mod.ORDER_TYPE_BUY]
    elif direction == "sell":
        positions = [p for p in positions if p.type == mt5_mod.ORDER_TYPE_SELL]
    if not positions:
        return 0, []

    closed, errors = 0, []
    for pos in positions:
        if pos.type == mt5_mod.ORDER_TYPE_BUY:
            order_type = mt5_mod.ORDER_TYPE_SELL
            price = mt5_mod.symbol_info_tick(symbol).bid
        else:
            order_type = mt5_mod.ORDER_TYPE_BUY
            price = mt5_mod.symbol_info_tick(symbol).ask

        req = {
            "action": mt5_mod.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": order_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 20,
            "magic": magic,
            "comment": comment,
            "type_time": mt5_mod.ORDER_TIME_GTC,
            "type_filling": mt5_mod.ORDER_FILLING_IOC,
        }
        r = mt5_mod.order_send(req)
        if r and r.retcode == mt5_mod.TRADE_RETCODE_DONE:
            closed += 1
            logger.info(f"Đóng lệnh ticket={pos.ticket}")
        else:
            errors.append(r.comment if r else str(mt5_mod.last_error()))

    return closed, errors


def close_all_positions(symbol: str, comment: str = "close", direction: str = None) -> dict:
    closed, errors = _close_symbol_positions(mt5, symbol, _magic_number, comment, direction)
    if closed == 0 and not errors:
        return {"success": True, "closed": 0, "message": "Không có lệnh đang mở"}
    return {"success": len(errors) == 0, "closed": closed, "errors": errors}


# ── Multi-account support ──────────────────────────────────────────────────

def _order_worker(args: dict) -> dict:
    """
    Top-level function — chạy trong subprocess riêng, kết nối 1 terminal MT5,
    đặt lệnh rồi ngắt kết nối. Phải đặt ở module-level để pickle hoạt động.
    """
    import MetaTrader5 as _mt5

    login = args.get("login", 0)
    name = args.get("name", f"TK #{login}" if login else "default")

    init_kw = {}
    if args.get("terminal_path"):
        init_kw["path"] = args["terminal_path"]
    if login:
        init_kw["login"] = int(login)
        init_kw["password"] = args.get("password", "")
        init_kw["server"] = args.get("server", "")

    if not _mt5.initialize(**init_kw):
        return {
            "success": False, "name": name, "login": login,
            "error": f"Không kết nối được MT5: {_mt5.last_error()}",
        }

    try:
        # Lọc theo danh sách tài khoản nếu có
        target_accounts = args.get("target_accounts", [])
        if target_accounts:
            info = _mt5.account_info()
            actual_login = info.login if info else None
            if actual_login not in [int(a) for a in target_accounts]:
                return {"success": True, "skipped": True,
                        "name": name, "login": actual_login}
            name = f"TK #{actual_login}"

        symbol  = args["symbol"]
        action  = args["action"].lower()
        lot     = float(args["lot"])
        sl      = float(args.get("sl", 0.0))
        tp      = float(args.get("tp", 0.0))
        comment = args.get("comment", "TradingView")
        magic   = int(args.get("magic", 20240101))
        max_daily_loss   = float(args.get("max_daily_loss", 0.0))
        max_daily_profit = float(args.get("max_daily_profit", 0.0))

        sym = _mt5.symbol_info(symbol)
        if sym is None:
            return {"success": False, "name": name, "login": login,
                    "error": f"Symbol không tồn tại: {symbol}"}
        if not sym.visible:
            _mt5.symbol_select(symbol, True)
            sym = _mt5.symbol_info(symbol)

        fm = sym.filling_mode
        if fm & _mt5.ORDER_FILLING_IOC:
            fill = _mt5.ORDER_FILLING_IOC
        elif fm & _mt5.ORDER_FILLING_FOK:
            fill = _mt5.ORDER_FILLING_FOK
        else:
            fill = _mt5.ORDER_FILLING_RETURN

        if action == "close":
            close_direction = args.get("close_direction")
            closed, errors = _close_symbol_positions(_mt5, symbol, magic, comment, close_direction)
            return {"success": len(errors) == 0, "name": name, "login": login, "closed": closed}

        if action == "buy":
            otype = _mt5.ORDER_TYPE_BUY
        elif action == "sell":
            otype = _mt5.ORDER_TYPE_SELL
        else:
            return {"success": False, "name": name, "login": login,
                    "error": f"Action không hợp lệ: {action}"}

        hit_limit, limit_msg = _check_daily_limit(_mt5, max_daily_loss, max_daily_profit)
        if hit_limit:
            return {"success": True, "skipped": True, "name": name, "login": login,
                    "symbol": symbol, "message": limit_msg}

        existing = _mt5.positions_get(symbol=symbol)
        if existing:
            if existing[0].type == otype:
                return {"success": True, "skipped": True, "name": name, "login": login,
                        "symbol": symbol, "message": f"Đã có lệnh {action.upper()} mở cho {symbol}, bỏ qua tín hiệu trùng chiều"}
            closed, errors = _close_symbol_positions(_mt5, symbol, magic, comment)
            if errors:
                return {"success": False, "name": name, "login": login,
                        "error": f"Không đóng được lệnh ngược chiều: {errors}"}

        price = _mt5.symbol_info_tick(symbol).ask if action == "buy" else _mt5.symbol_info_tick(symbol).bid

        req = {
            "action": _mt5.TRADE_ACTION_DEAL, "symbol": symbol,
            "volume": lot, "type": otype, "price": price,
            "deviation": 20, "magic": magic, "comment": comment,
            "type_time": _mt5.ORDER_TIME_GTC, "type_filling": fill,
        }
        if sl:
            req["sl"] = price - sl if action == "buy" else price + sl
        if tp:
            req["tp"] = price + tp if action == "buy" else price - tp

        r = _mt5.order_send(req)
        if r is None:
            return {"success": False, "name": name, "login": login,
                    "error": str(_mt5.last_error())}
        if r.retcode != _mt5.TRADE_RETCODE_DONE:
            return {"success": False, "name": name, "login": login,
                    "error": r.comment, "retcode": r.retcode}

        return {
            "success": True, "name": name, "login": login,
            "ticket": r.order, "symbol": symbol,
            "action": action, "lot": lot, "price": price,
        }
    finally:
        _mt5.shutdown()


def _test_account_worker(args: dict) -> dict:
    """Subprocess worker để test kết nối một tài khoản."""
    import MetaTrader5 as _mt5

    login = args.get("login", 0)
    init_kw = {}
    if args.get("terminal_path"):
        init_kw["path"] = args["terminal_path"]
    if login:
        init_kw["login"] = int(login)
        init_kw["password"] = args.get("password", "")
        init_kw["server"] = args.get("server", "")

    if not _mt5.initialize(**init_kw):
        return {"success": False, "error": str(_mt5.last_error())}

    info = _mt5.account_info()
    _mt5.shutdown()

    if info is None:
        return {"success": False, "error": "Không lấy được thông tin tài khoản"}

    return {
        "success": True,
        "login": info.login,
        "balance": info.balance,
        "currency": info.currency,
        "server": info.server,
    }


def find_mt5_terminals() -> list:
    """Tìm tất cả terminal64.exe đang chạy, trả về list đường dẫn."""
    import subprocess
    try:
        cmd = (
            "Get-Process -Name terminal64 -ErrorAction SilentlyContinue"
            " | Select-Object -ExpandProperty Path"
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=5,
        )
        return list({p.strip() for p in r.stdout.splitlines() if p.strip()})
    except Exception:
        return []


def test_account(account: dict) -> dict:
    """Test kết nối cho một tài khoản (chạy trong subprocess)."""
    with ProcessPoolExecutor(max_workers=1) as ex:
        f = ex.submit(_test_account_worker, account)
        try:
            return f.result(timeout=20)
        except Exception as e:
            return {"success": False, "error": str(e)}


def place_order_parallel(accounts: list, order_params: dict, magic: int = 20240101) -> list:
    """Đặt lệnh song song trên tất cả tài khoản đang bật."""
    enabled = [a for a in accounts if a.get("enabled", True) and (a.get("login") or a.get("terminal_path"))]
    if not enabled:
        logger.warning("Không có tài khoản nào được bật / được cấu hình")
        return []

    worker_args = [{**order_params, **a, "magic": magic} for a in enabled]
    results = []

    with ProcessPoolExecutor(max_workers=min(len(enabled), 8)) as ex:
        fs = {
            ex.submit(_order_worker, wa): wa.get("name", f"TK #{wa.get('login', '?')}")
            for wa in worker_args
        }
        for f in as_completed(fs):
            try:
                results.append(f.result(timeout=30))
            except Exception as e:
                results.append({"success": False, "name": fs[f], "error": str(e)})

    for r in results:
        n = r.get("name", f"TK #{r.get('login', '?')}")
        if r.get("skipped") and r.get("message"):
            logger.info(f"[{n}]  {r['message']}")
        elif r.get("success"):
            if "ticket" in r:
                logger.info(
                    f"[{n}]  {r['action'].upper()} {r['lot']} {r['symbol']}"
                    f" @ {r['price']} | ticket={r['ticket']}"
                )
            else:
                logger.info(f"[{n}]  Đóng {r.get('closed', 0)} lệnh")
        else:
            logger.error(f"[{n}]  Thất bại: {r.get('error', '?')}")

    return results
