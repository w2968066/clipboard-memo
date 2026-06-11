"""
全局热键管理模块
使用 Windows RegisterHotKey API + 消息窗口，比 keyboard 库更可靠
"""

import ctypes
from ctypes import wintypes
import threading

# ---- Windows API 常量 ----
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
PM_REMOVE = 0x0001
HWND_MESSAGE = -3  # 消息窗口

# ---- 虚拟键码映射 ----
VK_MAP = {
    "a": 0x41, "b": 0x42, "c": 0x43, "d": 0x44, "e": 0x45,
    "f": 0x46, "g": 0x47, "h": 0x48, "i": 0x49, "j": 0x4A,
    "k": 0x4B, "l": 0x4C, "m": 0x4D, "n": 0x4E, "o": 0x4F,
    "p": 0x50, "q": 0x51, "r": 0x52, "s": 0x53, "t": 0x54,
    "u": 0x55, "v": 0x56, "w": 0x57, "x": 0x58, "y": 0x59,
    "z": 0x5A,
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "space": 0x20, "tab": 0x09,
    "escape": 0x1B, "delete": 0x2E,
}

MOD_MAP = {
    "ctrl": MOD_CONTROL,
    "alt": MOD_ALT,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
}


# ---- WNDCLASSW 结构体 ----
class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


# ---- 窗口过程类型 ----
WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_longlong,      # LRESULT (64-bit)
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


def _parse_hotkey(hotkey_str):
    """解析热键字符串，返回 (mod_value, vk, 是否成功)"""
    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    if len(parts) < 2:
        return 0, 0, False
    key = parts[-1]
    mods = parts[:-1]
    mod_value = 0
    for m in mods:
        mod_value |= MOD_MAP.get(m, 0)
    vk = VK_MAP.get(key, 0)
    if vk == 0:
        return 0, 0, False
    return mod_value, vk, True


class HotkeyManager:
    """全局热键管理器（Windows 原生实现）"""

    def __init__(self):
        self._user32 = ctypes.windll.user32
        self._kernel32 = ctypes.windll.kernel32
        self._hotkey_id = 1
        self._callbacks = {}
        self._registered_hids = []  # 跟踪已注册的热键 ID
        self._running = False
        self._thread = None
        self._hwnd = None
        self._wndproc_ref = None  # 防止 GC
        self._current_hotkey_str = None
        self._current_callback = None

    def register(self, hotkey_str, callback):
        """
        注册全局热键（仅记录信息，真正注册在 start() 中）

        Args:
            hotkey_str: "ctrl+alt+v"
            callback: 回调函数（在后台线程中调用）
        """
        mod_value, vk, ok = _parse_hotkey(hotkey_str)
        if not ok:
            print(f"[热键] 格式错误或未知键: {hotkey_str}")
            return False

        hid = self._hotkey_id
        self._hotkey_id += 1

        self._callbacks[hid] = callback
        self._current_hotkey_str = hotkey_str
        self._current_callback = callback

        print(f"[热键] 待注册: {hotkey_str} (ID={hid})")
        return True

    def reregister(self, new_hotkey_str, callback=None):
        """
        即时更换热键，无需重启
        先注销旧热键，再注册新的（复用固定 ID）
        """
        if callback is None:
            callback = self._current_callback

        # 注销所有旧热键
        for hid in self._registered_hids:
            self._user32.UnregisterHotKey(self._hwnd, hid)
            self._callbacks.pop(hid, None)

        self._registered_hids = []

        mod_value, vk, ok = _parse_hotkey(new_hotkey_str)
        if not ok:
            print(f"[热键] 格式错误或未知键: {new_hotkey_str}")
            return False

        # 复用固定 ID=1，避免无限递增
        hid = 1
        self._callbacks[hid] = callback
        self._current_hotkey_str = new_hotkey_str
        self._current_callback = callback

        result = self._user32.RegisterHotKey(self._hwnd, hid, mod_value, vk)
        if result:
            self._registered_hids.append(hid)
            print(f"[热键] 已更换为: {new_hotkey_str}")
            return True
        else:
            err = ctypes.get_last_error()
            print(f"[热键] 更换失败, 错误码={err}")
            return False

    def _do_register_all(self):
        """启动时注册当前热键"""
        if not self._current_hotkey_str or not self._hwnd:
            return False

        mod_value, vk, ok = _parse_hotkey(self._current_hotkey_str)
        if not ok:
            return False

        hid = 1  # 固定 ID
        self._callbacks[hid] = self._current_callback
        result = self._user32.RegisterHotKey(self._hwnd, hid, mod_value, vk)
        if result:
            self._registered_hids.append(hid)
            print(f"[热键] 注册成功: {self._current_hotkey_str}")
            return True
        else:
            err = ctypes.get_last_error()
            print(f"[热键] 注册失败, 错误码={err}")
            return False

    def start(self):
        """启动热键消息循环（后台线程）"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()
        print("[热键] 消息循环已启动")

    def stop(self):
        """停止热键消息循环"""
        self._running = False
        if self._hwnd:
            # 发送 WM_QUIT 退出消息循环
            self._user32.PostMessageW(self._hwnd, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=3)
        print("[热键] 已停止")

    def _message_loop(self):
        """Windows 消息循环（后台线程）"""
        # 设置 API 函数参数类型（64 位系统必需，避免 ctypes 默认按 c_int 截断指针）
        self._user32.DefWindowProcW.argtypes = [
            wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        ]
        self._user32.DefWindowProcW.restype = ctypes.c_longlong

        self._user32.CreateWindowExW.argtypes = [
            wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
            wintypes.DWORD, wintypes.INT, wintypes.INT,
            wintypes.INT, wintypes.INT, wintypes.HWND,
            wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
        ]
        self._user32.CreateWindowExW.restype = wintypes.HWND

        self._user32.DestroyWindow.argtypes = [wintypes.HWND]
        self._user32.DestroyWindow.restype = wintypes.BOOL

        self._user32.RegisterHotKey.argtypes = [
            wintypes.HWND, wintypes.INT, wintypes.UINT, wintypes.UINT
        ]
        self._user32.RegisterHotKey.restype = wintypes.BOOL
        self._user32.UnregisterHotKey.argtypes = [wintypes.HWND, wintypes.INT]
        self._user32.UnregisterHotKey.restype = wintypes.BOOL

        self._user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
        self._user32.RegisterClassW.restype = wintypes.ATOM

        self._kernel32.GetModuleHandleW.restype = ctypes.c_void_p

        # 保存回调引用防止被 GC
        self._wndproc_ref = WNDPROC(self._wnd_proc)

        # 注册窗口类
        class_name = "ClipboardMemoHotkeyWnd"
        wnd_class = WNDCLASSW()
        wnd_class.lpfnWndProc = ctypes.cast(self._wndproc_ref, ctypes.c_void_p)
        hinst = self._kernel32.GetModuleHandleW(None)
        wnd_class.hInstance = ctypes.c_void_p(hinst)
        wnd_class.lpszClassName = class_name

        atom = self._user32.RegisterClassW(ctypes.byref(wnd_class))
        if atom == 0:
            err = ctypes.get_last_error()
            print(f"[热键] 注册窗口类失败, 错误码={err}")
            return

        # 创建消息窗口
        self._hwnd = self._user32.CreateWindowExW(
            0, class_name, "", 0,
            0, 0, 0, 0,
            wintypes.HWND(HWND_MESSAGE),  # 消息专用窗口
            None, ctypes.c_void_p(hinst), None
        )

        if not self._hwnd:
            err = ctypes.get_last_error()
            print(f"[热键] 创建消息窗口失败, 错误码={err}")
            return

        # 注册热键
        self._do_register_all()

        print(f"[热键] 消息窗口创建成功 HWND={self._hwnd}")

        # 消息循环
        msg = wintypes.MSG()
        while self._running:
            # 使用 PeekMessage + sleep 而不是阻塞的 GetMessage
            # 这样 stop() 可以更及时地响应
            has_msg = self._user32.PeekMessageW(
                ctypes.byref(msg), None, 0, 0, PM_REMOVE
            )
            if has_msg:
                if msg.message == WM_QUIT:
                    break
                self._user32.TranslateMessage(ctypes.byref(msg))
                self._user32.DispatchMessageW(ctypes.byref(msg))
            else:
                # 没有消息时短暂休眠，降低 CPU 占用
                ctypes.windll.kernel32.Sleep(50)

        # 清理
        if self._hwnd:
            self._user32.DestroyWindow(self._hwnd)
            self._hwnd = None

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """窗口消息处理（在后台线程中调用）"""
        if msg == WM_HOTKEY:
            hid = wparam
            callback = self._callbacks.get(hid)
            if callback:
                try:
                    callback()
                except Exception as e:
                    print(f"[热键] 回调异常: {e}")
            return 0
        return self._user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def parse_hotkey_string(hotkey_str):
    """标准化热键字符串"""
    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    return "+".join(parts)


# 全局单例
_hotkey_instance = None


def get_hotkey_manager():
    global _hotkey_instance
    if _hotkey_instance is None:
        _hotkey_instance = HotkeyManager()
    return _hotkey_instance
