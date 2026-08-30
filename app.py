import json
import logging
import os
import queue
import sys
import threading


def resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def data_path(rel: str) -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)


import customtkinter as ctk
from PIL import Image
from werkzeug.serving import make_server

# ── Brand colors ──────────────────────────────────────────────────────────────
C_BG     = "#0d1b2e"
C_DARK   = "#071629"
C_CARD   = "#0f2137"
C_BORDER = "#1a3a5c"
C_ACCENT = "#00c896"
C_HOVER  = "#00a87e"
C_BTN2   = "#1a3a5c"
C_BTN2H  = "#243e5e"
C_RED    = "#e53935"
C_RED_H  = "#c62828"
C_TEXT   = "#ffffff"
C_MUTED  = "#7fb5d5"
C_HINT   = "#4a7a9b"

import mt5_handler
import server as srv

SETTINGS_FILE = data_path("settings.json")

DEFAULT_SETTINGS = {
    "token": "my_secret_token",
    "port": 8000,
    "public_url": "",
    "default_symbol": "XAUUSD",
    "default_lot": 0.01,
    "default_sl": 0.0,
    "default_tp": 0.0,
    "magic_number": 20240101,
    "max_daily_loss": 0.0,
    "max_daily_profit": 0.0,
}


class QueueLogHandler(logging.Handler):
    def __init__(self, q: queue.Queue):
        super().__init__()
        self.q = q
        self.setFormatter(logging.Formatter("%(asctime)s  [%(levelname)s]  %(message)s", "%H:%M:%S"))

    def emit(self, record):
        self.q.put(self.format(record))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("ALGOBOT - TradingView Automation")
        self.geometry("900x680")
        self.resizable(True, True)
        self.minsize(720, 580)
        self.configure(fg_color=C_BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._settings = self._load_settings()
        self._log_queue: queue.Queue = queue.Queue()
        self._flask_server = None
        self._server_thread = None

        self._setup_logging()
        self._build_ui()
        self._connect_mt5()
        self.after(150, self._poll_logs)

    # ── Settings ──────────────────────────────────────────────────────────────

    def _load_settings(self) -> dict:
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, encoding="utf-8") as f:
                    return {**DEFAULT_SETTINGS, **json.load(f)}
            except Exception:
                pass
        return DEFAULT_SETTINGS.copy()

    def _save_settings(self) -> dict:
        s = {
            "token": self._token_var.get().strip(),
            "port": int(self._port_var.get() or 8000),
            "public_url": self._public_url_var.get().strip().rstrip("/"),
            "default_symbol": self._symbol_var.get().strip().upper(),
            "default_lot": float(self._lot_var.get() or 0.01),
            "default_sl": float(self._sl_var.get() or 0.0),
            "default_tp": float(self._tp_var.get() or 0.0),
            "magic_number": int(self._magic_var.get() or 20240101),
            "max_daily_loss": float(self._max_loss_var.get() or 0.0),
            "max_daily_profit": float(self._max_profit_var.get() or 0.0),
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2, ensure_ascii=False)
        self._settings = s
        return s

    # ── Logging ───────────────────────────────────────────────────────────────

    def _setup_logging(self):
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(QueueLogHandler(self._log_queue))
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    def _poll_logs(self):
        try:
            while True:
                msg = self._log_queue.get_nowait()
                self._log_box.configure(state="normal")
                self._log_box.insert("end", msg + "\n")
                self._log_box.see("end")
                self._log_box.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(150, self._poll_logs)

    # ── MT5 ───────────────────────────────────────────────────────────────────

    def _connect_mt5(self):
        ok = mt5_handler.connect()
        if ok:
            info = mt5_handler.get_account_info()
            self._mt5_label.configure(
                text=(
                    f"MT5 ●  #{info['login']}  |  "
                    f"{info['balance']:,.2f} {info['currency']}  |  {info['server']}"
                ),
                text_color=C_ACCENT,
            )
        else:
            self._mt5_label.configure(
                text="MT5 ✕  Không kết nối được — hãy mở và đăng nhập MT5 trước",
                text_color=C_RED,
            )

        # Kiểm tra bao nhiêu terminal đang chạy
        def check_multi():
            paths = mt5_handler.find_mt5_terminals()
            if len(paths) > 1:
                self.after(0, lambda: self._mt5_label.configure(
                    text=f"MT5  ●  {len(paths)} terminal đang mở",
                    text_color=C_ACCENT,
                ))
        threading.Thread(target=check_multi, daemon=True).start()

    # ── Accounts tab ──────────────────────────────────────────────────────────

    def _build_accounts_tab(self, tab):
        ctk.CTkLabel(tab,
                     text="App tự động tìm tất cả MT5 terminal đang mở và đẩy lệnh vào từng cái.",
                     font=("Segoe UI", 11), text_color=C_MUTED,
                     wraplength=500, justify="left").pack(anchor="w", pady=(0, 16))

        scan_card = ctk.CTkFrame(tab, corner_radius=10, fg_color=C_DARK,
                                  border_color=C_BORDER, border_width=1)
        scan_card.pack(fill="x")

        hdr = ctk.CTkFrame(scan_card, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(hdr, text="MT5 terminal đang mở",
                     font=("Segoe UI", 11, "bold"), text_color=C_ACCENT).pack(side="left")
        ctk.CTkButton(hdr, text="Scan", width=70, height=28,
                      fg_color=C_BTN2, hover_color=C_BTN2H,
                      font=("Segoe UI", 10), text_color=C_MUTED,
                      corner_radius=6, command=self._scan_terminals).pack(side="right")

        self._scan_result = ctk.CTkLabel(scan_card,
                                          text="Nhấn Scan để kiểm tra",
                                          font=("Segoe UI", 10), text_color=C_HINT,
                                          anchor="w", justify="left", wraplength=480)
        self._scan_result.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkLabel(tab,
                     text=(
                         "Cách dùng:\n"
                         "1.  Mở tất cả MT5, đăng nhập mỗi cái 1 tài khoản\n"
                         "2.  Nhấn Scan để kiểm tra app đã nhìn thấy chưa\n"
                         "3.  Khởi động server — tín hiệu từ TradingView sẽ tự đẩy vào TẤT CẢ"
                     ),
                     font=("Segoe UI", 11), text_color=C_MUTED,
                     anchor="w", justify="left").pack(anchor="w", pady=(20, 0))

    def _scan_terminals(self):
        self._scan_result.configure(text="Đang scan...", text_color=C_HINT)

        def run():
            paths = mt5_handler.find_mt5_terminals()
            if paths:
                lines = "\n".join(f"  ✓  {p}" for p in paths)
                msg = f"Tìm thấy {len(paths)} terminal:\n{lines}"
                color = C_ACCENT
                self.after(0, lambda: self._mt5_label.configure(
                    text=f"MT5  ●  {len(paths)} terminal đang mở",
                    text_color=C_ACCENT,
                ))
            else:
                msg = "Không tìm thấy terminal MT5 nào đang chạy."
                color = C_RED
            self.after(0, lambda: self._scan_result.configure(text=msg, text_color=color))

        threading.Thread(target=run, daemon=True).start()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        s = self._settings
        LOGO_PATH = resource_path("logo.png")

        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, height=58, corner_radius=0, fg_color=C_DARK)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        try:
            pil_logo = Image.open(LOGO_PATH)
            logo_img = ctk.CTkImage(pil_logo, size=(40, 40))
            ctk.CTkLabel(hdr, image=logo_img, text="").pack(side="left", padx=(14, 6), pady=9)
            ico_path = data_path("logo.ico")
            if not os.path.exists(ico_path):
                pil_logo.resize((32, 32), Image.LANCZOS).save(ico_path, format="ICO")
            self.iconbitmap(ico_path)
        except Exception:
            ctk.CTkLabel(hdr, text="ALGOBOT", font=("Segoe UI", 15, "bold"),
                         text_color=C_ACCENT).pack(side="left", padx=16)

        ctk.CTkFrame(hdr, width=1, fg_color=C_BORDER).pack(side="left", fill="y", pady=12)
        ctk.CTkLabel(hdr, text="  TradingView Automation",
                     font=("Segoe UI", 11), text_color=C_MUTED).pack(side="left")

        self._mt5_label = ctk.CTkLabel(hdr, text="Đang kết nối MT5...",
                                        font=("Segoe UI", 12), text_color=C_HINT)
        self._mt5_label.pack(side="right", padx=16)

        # ── Body ──────────────────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=10)

        # ── Left panel ────────────────────────────────────────────────────────
        left = ctk.CTkFrame(body, width=276, corner_radius=12, fg_color=C_CARD)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Cài đặt", font=("Segoe UI", 12, "bold"),
                     text_color=C_ACCENT).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkFrame(left, height=1, fg_color=C_BORDER).pack(fill="x", padx=16, pady=(0, 4))

        # Buttons (packed bottom-first so the scrollable settings area above
        # only claims the remaining space instead of pushing these off-screen)
        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=14, pady=(0, 14))
        ctk.CTkFrame(btn_frame, height=1, fg_color=C_BORDER).pack(fill="x", pady=(0, 10))

        self._status_label = ctk.CTkLabel(btn_frame, text="●  Chưa chạy",
                                           text_color=C_HINT, font=("Segoe UI", 11))
        self._status_label.pack(anchor="w", pady=(0, 6))

        self._start_btn = ctk.CTkButton(
            btn_frame, text="▶   Khởi động server",
            fg_color=C_ACCENT, hover_color=C_HOVER, text_color="#071629",
            font=("Segoe UI", 12, "bold"), height=40, corner_radius=8,
            command=self._start_server)
        self._start_btn.pack(fill="x", pady=(0, 6))

        self._stop_btn = ctk.CTkButton(
            btn_frame, text="■   Dừng server",
            fg_color=C_RED, hover_color=C_RED_H, text_color=C_TEXT,
            font=("Segoe UI", 12, "bold"), height=40, corner_radius=8,
            state="disabled", command=self._stop_server)
        self._stop_btn.pack(fill="x")

        left = ctk.CTkScrollableFrame(left, fg_color="transparent")
        left.pack(fill="both", expand=True)

        def field(parent, label, var):
            ctk.CTkLabel(parent, text=label, anchor="w",
                         font=("Segoe UI", 10), text_color=C_MUTED).pack(
                fill="x", padx=16, pady=(6, 1))
            return ctk.CTkEntry(parent, textvariable=var, height=33,
                                fg_color=C_DARK, border_color=C_BORDER,
                                text_color=C_TEXT, font=("Segoe UI", 11))

        self._token_var = ctk.StringVar(value=s["token"])
        e_tok = field(left, "Webhook Token", self._token_var)
        e_tok.configure(show="*")
        e_tok.pack(fill="x", padx=16)
        self._show_token = False

        def toggle_token():
            self._show_token = not self._show_token
            e_tok.configure(show="" if self._show_token else "*")
            btn_show.configure(text="Ẩn" if self._show_token else "Hiện")

        btn_show = ctk.CTkButton(left, text="Hiện", width=55, height=20,
                                  fg_color=C_BTN2, hover_color=C_BTN2H,
                                  font=("Segoe UI", 9), text_color=C_MUTED,
                                  corner_radius=6, command=toggle_token)
        btn_show.pack(anchor="e", padx=16, pady=(2, 0))

        self._port_var = ctk.StringVar(value=str(s["port"]))
        field(left, "Port", self._port_var).pack(fill="x", padx=16)

        self._public_url_var = ctk.StringVar(value=s["public_url"])
        field(left, "Public URL  (ngrok / VPS)", self._public_url_var).pack(fill="x", padx=16)
        ctk.CTkLabel(left, text="VD: https://xxxx.ngrok-free.app",
                     font=("Segoe UI", 9), text_color=C_HINT, anchor="w").pack(
            fill="x", padx=16, pady=(2, 0))

        self._symbol_var = ctk.StringVar(value=s["default_symbol"])
        field(left, "Symbol mặc định", self._symbol_var).pack(fill="x", padx=16)

        ctk.CTkLabel(left, text="Lot / SL / TP", anchor="w",
                     font=("Segoe UI", 10), text_color=C_MUTED).pack(
            fill="x", padx=16, pady=(6, 1))
        trade_frame = ctk.CTkFrame(left, fg_color="transparent")
        trade_frame.pack(fill="x", padx=16)
        trade_frame.columnconfigure((0, 1, 2), weight=1, uniform="col")
        self._lot_var = ctk.StringVar(value=str(s["default_lot"]))
        self._sl_var  = ctk.StringVar(value=str(s["default_sl"]))
        self._tp_var  = ctk.StringVar(value=str(s["default_tp"]))
        for col, (var, ph) in enumerate([(self._lot_var, "Lot"),
                                          (self._sl_var, "SL"),
                                          (self._tp_var, "TP")]):
            ctk.CTkEntry(trade_frame, textvariable=var, height=33,
                         placeholder_text=ph, font=("Segoe UI", 11),
                         fg_color=C_DARK, border_color=C_BORDER,
                         text_color=C_TEXT).grid(
                row=0, column=col, sticky="ew",
                padx=(0 if col == 0 else 4, 0))

        self._magic_var = ctk.StringVar(value=str(s["magic_number"]))
        field(left, "Magic Number", self._magic_var).pack(fill="x", padx=16)

        ctk.CTkLabel(left, text="Giới hạn lỗ / lãi ngày (USD, 0 = không giới hạn)", anchor="w",
                     font=("Segoe UI", 10), text_color=C_MUTED, wraplength=240).pack(
            fill="x", padx=16, pady=(6, 1))
        limit_frame = ctk.CTkFrame(left, fg_color="transparent")
        limit_frame.pack(fill="x", padx=16)
        limit_frame.columnconfigure((0, 1), weight=1, uniform="col")
        self._max_loss_var   = ctk.StringVar(value=str(s["max_daily_loss"]))
        self._max_profit_var = ctk.StringVar(value=str(s["max_daily_profit"]))
        for col, (var, ph) in enumerate([(self._max_loss_var, "Lỗ tối đa"),
                                          (self._max_profit_var, "Lãi tối đa")]):
            ctk.CTkEntry(limit_frame, textvariable=var, height=33,
                         placeholder_text=ph, font=("Segoe UI", 11),
                         fg_color=C_DARK, border_color=C_BORDER,
                         text_color=C_TEXT).grid(
                row=0, column=col, sticky="ew",
                padx=(0 if col == 0 else 4, 0))

        # ── Right panel — tabs ────────────────────────────────────────────────
        tabs = ctk.CTkTabview(body, corner_radius=12, fg_color=C_CARD,
                               segmented_button_fg_color=C_DARK,
                               segmented_button_selected_color=C_ACCENT,
                               segmented_button_selected_hover_color=C_HOVER,
                               segmented_button_unselected_color=C_DARK,
                               segmented_button_unselected_hover_color=C_BTN2)
        tabs.pack(side="left", fill="both", expand=True)
        tabs.add("Log hoạt động")
        tabs.add("Tài khoản")
        tabs.add("TradingView Alert")

        # ── Tab 1: Log ────────────────────────────────────────────────────────
        log_tab = tabs.tab("Log hoạt động")
        log_hdr = ctk.CTkFrame(log_tab, height=30, corner_radius=6, fg_color=C_DARK)
        log_hdr.pack(fill="x", pady=(0, 6))
        log_hdr.pack_propagate(False)
        ctk.CTkLabel(log_hdr, text="Hoạt động realtime",
                     font=("Segoe UI", 10), text_color=C_HINT).pack(side="left", padx=10, pady=5)
        ctk.CTkButton(log_hdr, text="Xóa", width=55, height=20,
                       fg_color=C_BTN2, hover_color=C_BTN2H,
                       font=("Segoe UI", 9), text_color=C_MUTED,
                       command=self._clear_log).pack(side="right", padx=8, pady=5)
        self._log_box = ctk.CTkTextbox(log_tab, font=("Consolas", 11),
                                        state="disabled", wrap="word",
                                        fg_color=C_DARK, text_color="#a0c8e8")
        self._log_box.pack(fill="both", expand=True)

        # ── Tab 2: Tài khoản ──────────────────────────────────────────────────
        self._build_accounts_tab(tabs.tab("Tài khoản"))

        # ── Tab 3: TradingView Alert ──────────────────────────────────────────
        tv_tab_outer = tabs.tab("TradingView Alert")
        tv_tab = ctk.CTkScrollableFrame(tv_tab_outer, fg_color="transparent")
        tv_tab.pack(fill="both", expand=True)

        def section_label(parent, text):
            ctk.CTkLabel(parent, text=text, font=("Segoe UI", 12, "bold"),
                         text_color=C_ACCENT, anchor="w").pack(fill="x", pady=(16, 5))

        def copy_btn(parent, get_fn):
            def do():
                self.clipboard_clear()
                self.clipboard_append(get_fn())
                btn.configure(text="✓ Đã copy")
                self.after(1500, lambda: btn.configure(text="Copy"))
            btn = ctk.CTkButton(parent, text="Copy", width=70, height=26,
                                fg_color=C_BTN2, hover_color=C_BTN2H,
                                font=("Segoe UI", 10), text_color=C_MUTED,
                                corner_radius=6, command=do)
            return btn

        section_label(tv_tab, "① Webhook URL")
        url_row = ctk.CTkFrame(tv_tab, fg_color="transparent")
        url_row.pack(fill="x")
        self._tv_url_var = ctk.StringVar(value=self._build_webhook_url(s))
        ctk.CTkEntry(url_row, textvariable=self._tv_url_var,
                     font=("Consolas", 11), state="readonly",
                     fg_color=C_DARK, border_color=C_BORDER,
                     text_color=C_ACCENT).pack(side="left", fill="x", expand=True, padx=(0, 8))
        copy_btn(url_row, self._tv_url_var.get).pack(side="left")
        ctk.CTkLabel(tv_tab, text="Dán URL vào TradingView Alert → Notifications → Webhook URL",
                     font=("Segoe UI", 10), text_color=C_HINT, anchor="w",
                     wraplength=500).pack(fill="x", pady=(4, 0))

        section_label(tv_tab, "② Message (JSON)")
        mode_btn = ctk.CTkSegmentedButton(
            tv_tab, values=["Strategy", "Indicator"],
            command=self._on_json_mode_change,
            font=("Segoe UI", 11), fg_color=C_DARK,
            selected_color=C_ACCENT, selected_hover_color=C_HOVER,
            unselected_color=C_BTN2, unselected_hover_color=C_BTN2H,
            text_color="#071629")
        mode_btn.set("Strategy")
        mode_btn.pack(fill="x", pady=(0, 8))

        json_container = ctk.CTkFrame(tv_tab, fg_color="transparent")
        json_container.pack(fill="x")

        self._frame_strategy = ctk.CTkFrame(json_container, fg_color="transparent")
        self._frame_strategy.pack(fill="x")
        self._json_box = ctk.CTkTextbox(self._frame_strategy, font=("Consolas", 11),
                                         height=150, fg_color=C_DARK, text_color="#a0c8e8")
        self._json_box.pack(fill="x", pady=(0, 4))
        strat_row = ctk.CTkFrame(self._frame_strategy, fg_color="transparent")
        strat_row.pack(fill="x")
        copy_btn(strat_row, lambda: self._json_box.get("1.0", "end").strip()).pack(side="left")
        ctk.CTkLabel(strat_row, text="  action tự động từ {{strategy.order.action}}",
                     font=("Segoe UI", 10), text_color=C_HINT).pack(side="left")

        self._frame_indicator = ctk.CTkFrame(json_container, fg_color="transparent")
        ind_cols = ctk.CTkFrame(self._frame_indicator, fg_color="transparent")
        ind_cols.pack(fill="x")
        ind_cols.columnconfigure((0, 1), weight=1, uniform="ind")

        def ind_box(parent, label, color, col):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 5, 0))
            ctk.CTkLabel(f, text=label, font=("Segoe UI", 12, "bold"),
                         text_color=color).pack(anchor="w", pady=(0, 3))
            box = ctk.CTkTextbox(f, font=("Consolas", 11), height=200,
                                  fg_color=C_DARK, text_color="#a0c8e8")
            box.pack(fill="x", pady=(0, 4))
            copy_btn(f, lambda b=box: b.get("1.0", "end").strip()).pack(anchor="w")
            return box

        self._json_buy_box  = ind_box(ind_cols, "BUY",  C_ACCENT, 0)
        self._json_sell_box = ind_box(ind_cols, "SELL", C_RED,    1)
        ctk.CTkLabel(self._frame_indicator,
                     text="Tạo 2 Alert riêng trên TradingView, mỗi Alert paste 1 JSON",
                     font=("Segoe UI", 10), text_color=C_HINT).pack(anchor="w", pady=(8, 0))

        for var in (self._token_var, self._lot_var, self._sl_var, self._tp_var):
            var.trace_add("write", self._refresh_json_template)
        for var in (self._token_var, self._symbol_var, self._lot_var, self._sl_var, self._tp_var):
            var.trace_add("write", self._refresh_indicator_json)
        for var in (self._public_url_var, self._port_var):
            var.trace_add("write", self._refresh_webhook_url)
        self._refresh_json_template()
        self._refresh_indicator_json()

        # ── Lọc tài khoản ────────────────────────────────────────────────
        section_label(tv_tab, "③ Lọc tài khoản  (tùy chọn)")

        acc_note = (
            'Thêm "accounts" vào JSON để chỉ đẩy vào một số tài khoản cụ thể.\n'
            'Không có trường này → đẩy vào TẤT CẢ MT5 đang mở.'
        )
        ctk.CTkLabel(tv_tab, text=acc_note, font=("Segoe UI", 10),
                     text_color=C_HINT, anchor="w", justify="left").pack(fill="x", pady=(0, 6))

        acc_json = '{\n  ...\n  "accounts": [123456, 234567]\n}'
        acc_json_frame = ctk.CTkFrame(tv_tab, fg_color="transparent")
        acc_json_frame.pack(fill="x", pady=(0, 4))
        acc_box = ctk.CTkTextbox(acc_json_frame, font=("Consolas", 11), height=80,
                                  fg_color=C_DARK, text_color="#a0c8e8")
        acc_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        acc_box.insert("1.0", acc_json)
        acc_box.configure(state="disabled")
        copy_btn(acc_json_frame,
                 lambda: '{\n  "token": "' + self._token_var.get() + '",\n'
                         '  "symbol": "' + (self._symbol_var.get() or "XAUUSD") + '",\n'
                         '  "action": "buy",\n'
                         '  "lot": ' + (self._lot_var.get() or "0.01") + ',\n'
                         '  "accounts": [123456, 234567]\n}'
                 ).pack(side="left", anchor="n")

        # ── Đóng lệnh theo tài khoản (alert dạng text) ──────────────────────
        section_label(tv_tab, "④ Đóng lệnh theo tài khoản  (TP/SL — không phải JSON)")

        close_note = (
            'Dùng cho Alert báo "đã chạm TP/SL" — app sẽ tự đóng TOÀN BỘ lệnh đang mở\n'
            'của symbol đó, CHỈ trên (các) tài khoản MT5 (login) bạn nhập bên dưới.\n'
            'Nhập nhiều tài khoản thì cách nhau bằng dấu phẩy — 1 alert đóng được nhiều account,\n'
            'y như lúc mở lệnh.'
        )
        ctk.CTkLabel(tv_tab, text=close_note, font=("Segoe UI", 10),
                     text_color=C_HINT, anchor="w", justify="left").pack(fill="x", pady=(0, 6))

        close_acc_row = ctk.CTkFrame(tv_tab, fg_color="transparent")
        close_acc_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(close_acc_row, text="Số tài khoản MT5 (login), cách nhau bằng dấu phẩy:",
                     font=("Segoe UI", 10), text_color=C_MUTED).pack(side="left", padx=(0, 8))
        self._close_account_var = ctk.StringVar(value="123456, 234567")
        ctk.CTkEntry(close_acc_row, textvariable=self._close_account_var, height=30, width=220,
                     font=("Consolas", 11), fg_color=C_DARK, border_color=C_BORDER,
                     text_color=C_TEXT).pack(side="left")

        close_cols = ctk.CTkFrame(tv_tab, fg_color="transparent")
        close_cols.pack(fill="x")
        close_cols.columnconfigure((0, 1), weight=1, uniform="close")

        def close_box(parent, label, color, col):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 5, 0))
            ctk.CTkLabel(f, text=label, font=("Segoe UI", 12, "bold"),
                         text_color=color).pack(anchor="w", pady=(0, 3))
            box = ctk.CTkTextbox(f, font=("Consolas", 10), height=60,
                                  fg_color=C_DARK, text_color="#a0c8e8", wrap="word")
            box.pack(fill="x", pady=(0, 4))
            copy_btn(f, lambda b=box: b.get("1.0", "end").strip()).pack(anchor="w")
            return box

        self._close_tp_box = close_box(close_cols, "TP chốt lời", C_ACCENT, 0)
        self._close_sl_box = close_box(close_cols, "SL cắt lỗ",   C_RED,    1)

        self._close_account_var.trace_add("write", self._refresh_close_templates)
        self._refresh_close_templates()

        ctk.CTkLabel(tv_tab,
                     text=(
                         "Cách dùng: tạo 2 Alert riêng trên TradingView cho điều kiện chạm TP và chạm SL,\n"
                         "webhook URL dùng đúng URL ở mục ①, Message dán đúng nội dung ở trên (giữ nguyên,\n"
                         "không sửa {{ticker}}/{{interval}}/{{close}} — TradingView tự điền khi kích hoạt)."
                     ),
                     font=("Segoe UI", 10), text_color=C_HINT,
                     anchor="w", justify="left", wraplength=500).pack(fill="x", pady=(0, 4))

        section_label(tv_tab, "⑤ Các bước tạo Alert")
        ctk.CTkLabel(tv_tab,
                     text=(
                         "1.  Mở TradingView → chọn biểu đồ → nhấn nút đồng hồ (Alerts)\n"
                         "2.  Tạo Alert mới → chọn điều kiện tín hiệu\n"
                         "3.  Tab Notifications → bật Webhook URL → dán URL ở trên\n"
                         "4.  Tab Alert actions → Message → dán JSON ở trên\n"
                         "5.  Lưu Alert — lệnh sẽ tự đặt trên MT5 mỗi khi tín hiệu kích hoạt"
                     ),
                     font=("Segoe UI", 11), text_color=C_MUTED,
                     anchor="w", justify="left", wraplength=500).pack(fill="x")

        # ── Footer ────────────────────────────────────────────────────────────
        ftr = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color=C_DARK)
        ftr.pack(fill="x")
        ftr.pack_propagate(False)
        ctk.CTkLabel(ftr,
                     text="Liên hệ AlgoBot VN nếu bạn cần code bot MT5, MT4, chỉ báo TradingView theo yêu cầu",
                     font=("Segoe UI", 11), text_color=C_MUTED).pack(side="left", padx=12)

    def _on_json_mode_change(self, mode: str):
        if mode == "Strategy":
            self._frame_indicator.pack_forget()
            self._frame_strategy.pack(fill="x")
        else:
            self._frame_strategy.pack_forget()
            self._frame_indicator.pack(fill="x")

    def _refresh_indicator_json(self, *_):
        token  = self._token_var.get()
        symbol = self._symbol_var.get().strip().upper() or "XAUUSD"
        lot    = self._lot_var.get() or "0.01"
        sl     = self._sl_var.get() or "0.0"
        tp     = self._tp_var.get() or "0.0"

        def make_json(action):
            return (
                '{\n'
                f'  "token": "{token}",\n'
                f'  "symbol": "{symbol}",\n'
                f'  "action": "{action}",\n'
                f'  "lot": {lot},\n'
                f'  "sl": {sl},\n'
                f'  "tp": {tp},\n'
                '  "comment": "TV Signal"\n'
                '}'
            )

        for box, action in ((self._json_buy_box, "buy"), (self._json_sell_box, "sell")):
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.insert("1.0", make_json(action))
            box.configure(state="disabled")

    def _refresh_close_templates(self, *_):
        acc = self._close_account_var.get().strip() or "123456"
        tp_text = f"✅ TP chốt lời | {{{{ticker}}}} | {{{{interval}}}} | Giá {{{{close}}}} || Account {acc}"
        sl_text = f"❌ SL cắt lỗ | {{{{ticker}}}} | {{{{interval}}}} | Giá {{{{close}}}} || Account {acc}"
        for box, text in ((self._close_tp_box, tp_text), (self._close_sl_box, sl_text)):
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.insert("1.0", text)
            box.configure(state="disabled")

    def _refresh_webhook_url(self, *_):
        pub  = self._public_url_var.get().strip().rstrip("/")
        port = self._port_var.get().strip() or "8000"
        url  = f"{pub}/webhook" if pub else f"http://localhost:{port}/webhook"
        self._tv_url_var.set(url)

    def _refresh_json_template(self, *_):
        token = self._token_var.get()
        lot   = self._lot_var.get() or "0.01"
        sl    = self._sl_var.get()  or "0.0"
        tp    = self._tp_var.get()  or "0.0"
        text = (
            '{\n'
            f'  "token": "{token}",\n'
            '  "symbol": "{{ticker}}",\n'
            '  "action": "{{strategy.order.action}}",\n'
            f'  "lot": {lot},\n'
            f'  "sl": {sl},\n'
            f'  "tp": {tp},\n'
            '  "comment": "TV Signal"\n'
            '}'
        )
        self._json_box.configure(state="normal")
        self._json_box.delete("1.0", "end")
        self._json_box.insert("1.0", text)
        self._json_box.configure(state="disabled")

    # ── Server control ────────────────────────────────────────────────────────

    def _build_webhook_url(self, s: dict) -> str:
        pub = s.get("public_url", "").strip().rstrip("/")
        if pub:
            return f"{pub}/webhook"
        return f"http://localhost:{s['port']}/webhook"

    def _start_server(self):
        try:
            s = self._save_settings()
        except (ValueError, TypeError) as exc:
            logging.error(f"Cài đặt không hợp lệ: {exc}")
            return

        srv.settings["token"]          = s["token"]
        srv.settings["default_symbol"] = s["default_symbol"]
        srv.settings["default_lot"]    = s["default_lot"]
        srv.settings["default_sl"]     = s["default_sl"]
        srv.settings["default_tp"]     = s["default_tp"]
        srv.settings["magic_number"]   = s["magic_number"]
        srv.settings["max_daily_loss"]   = s["max_daily_loss"]
        srv.settings["max_daily_profit"] = s["max_daily_profit"]
        mt5_handler.set_magic(s["magic_number"])

        port = s["port"]
        self._flask_server = make_server("0.0.0.0", port, srv.app)
        self._server_thread = threading.Thread(target=self._flask_server.serve_forever, daemon=True)
        self._server_thread.start()

        webhook_url = self._build_webhook_url(s)
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._status_label.configure(text=f"●  Đang chạy  —  port {port}", text_color=C_ACCENT)
        self._tv_url_var.set(webhook_url)
        logging.info(f"Server khởi động tại port {port} | Webhook: {webhook_url}")

    def _stop_server(self):
        if self._flask_server:
            self._flask_server.shutdown()
            self._flask_server = None
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._status_label.configure(text="●  Đã dừng", text_color=C_RED)
        logging.info("Server đã dừng")

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _on_close(self):
        self._stop_server()
        mt5_handler.disconnect()
        self.destroy()


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    App().mainloop()
