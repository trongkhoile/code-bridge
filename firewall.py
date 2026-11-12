"""Tự động thêm rule Windows Firewall (inbound TCP) cho port webhook nếu chưa có."""
import ctypes
import logging
import subprocess
import sys
from ctypes import wintypes

RULE_PREFIX = "ALGOBOT Webhook TCP"

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_ERROR_CANCELLED = 1223  # người dùng bấm No ở UAC


def rule_name(port: int) -> str:
    return f"{RULE_PREFIX} {port}"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=_NO_WINDOW,
    )


def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def rule_exists(port: int) -> bool:
    # netsh trả exit code 0 nếu tìm thấy rule, khác 0 nếu không có
    r = _run(["netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name(port)}"])
    return r.returncode == 0


def _add_params(port: int) -> str:
    # Chuỗi tham số cho netsh; tên rule có dấu cách nên phải bọc ngoặc kép
    return (
        f'advfirewall firewall add rule name="{rule_name(port)}" '
        f"dir=in action=allow protocol=TCP localport={port} profile=any"
    )


# ── Chạy chương trình bằng quyền Admin (UAC) qua ShellExecuteExW ──────────────

class _SHELLEXECUTEINFOW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("fMask", ctypes.c_ulong),
        ("hwnd", wintypes.HWND),
        ("lpVerb", wintypes.LPCWSTR),
        ("lpFile", wintypes.LPCWSTR),
        ("lpParameters", wintypes.LPCWSTR),
        ("lpDirectory", wintypes.LPCWSTR),
        ("nShow", ctypes.c_int),
        ("hInstApp", wintypes.HINSTANCE),
        ("lpIDList", ctypes.c_void_p),
        ("lpClass", wintypes.LPCWSTR),
        ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD),
        ("hIconOrMonitor", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE),
    ]


_SEE_MASK_NOCLOSEPROCESS = 0x00000040
_SEE_MASK_NOASYNC = 0x00000100
_SW_HIDE = 0
_INFINITE = 0xFFFFFFFF


def _shell_execute(verb: str, file: str, params: str) -> tuple[bool, int]:
    """Chạy file với verb ('runas' = xin quyền Admin), chờ xong.
    Trả về (đã_chạy_được, exit_code_hoặc_mã_lỗi_Windows)."""
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    info = _SHELLEXECUTEINFOW()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = _SEE_MASK_NOCLOSEPROCESS | _SEE_MASK_NOASYNC
    info.lpVerb = verb
    info.lpFile = file
    info.lpParameters = params
    info.nShow = _SW_HIDE

    if not shell32.ShellExecuteExW(ctypes.byref(info)):
        return False, ctypes.get_last_error()
    if not info.hProcess:
        return True, 0
    try:
        kernel32.WaitForSingleObject(info.hProcess, _INFINITE)
        code = wintypes.DWORD()
        kernel32.GetExitCodeProcess(info.hProcess, ctypes.byref(code))
        return True, code.value
    finally:
        kernel32.CloseHandle(info.hProcess)


def _add_rule(port: int) -> tuple[bool, str]:
    """Thêm rule. Trả về (thành_công, lý_do_nếu_lỗi)."""
    if _is_admin():
        # subprocess tự bọc ngoặc kép cho tham số có dấu cách
        r = _run(["netsh", "advfirewall", "firewall", "add", "rule",
                  f"name={rule_name(port)}", "dir=in", "action=allow", "protocol=TCP",
                  f"localport={port}", "profile=any"])
        if r.returncode == 0:
            return True, ""
        out = (r.stdout or b"").decode("utf-8", "replace").strip()
        return False, f"netsh error (code {r.returncode}): {out}"

    # Không có quyền Admin → xin quyền qua hộp thoại UAC
    launched, code = _shell_execute("runas", "netsh.exe", _add_params(port))
    if not launched:
        if code == _ERROR_CANCELLED:
            return False, "UAC prompt was declined (No)"
        return False, f"could not run netsh as Admin (Windows error {code})"
    if code != 0:
        return False, f"netsh error (code {code})"
    if not rule_exists(port):
        return False, "netsh finished but the rule was not found"
    return True, ""


def ensure_inbound_rule(port: int) -> None:
    """Kiểm tra rule cho port; nếu chưa có thì thêm. Chạy được trong thread nền."""
    if sys.platform != "win32":
        logging.info("Firewall: not Windows — skipping check")
        return
    logging.info(f"Firewall: checking inbound TCP {port} rule...")
    try:
        if rule_exists(port):
            logging.info(f"Firewall: inbound TCP {port} rule already exists — skipping")
            return
        logging.info(f"Firewall: no inbound TCP {port} rule — adding it (Admin required, click Yes on the UAC prompt)...")
        ok, reason = _add_rule(port)
        if ok:
            logging.info(f"Firewall: added rule '{rule_name(port)}'")
        else:
            logging.warning(
                f"Firewall: FAILED to add rule for port {port} — {reason}. "
                f"External webhooks may be blocked."
            )
    except Exception as exc:
        logging.error(f"Firewall: error while checking/adding rule: {exc}")
