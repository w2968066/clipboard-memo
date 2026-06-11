"""
鍏ㄥ眬鐑敭绠＄悊妯″潡
浣跨敤 Windows RegisterHotKey API + 娑堟伅绐楀彛锛屾瘮 keyboard 搴撴洿鍙潬
"""

import ctypes
from ctypes import wintypes
import threading

# ---- Windows API 甯搁噺 ----
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
PM_REMOVE = 0x0001
HWND_MESSAGE = -3  # 娑堟伅绐楀彛

# ---- 铏氭嫙閿爜鏄犲皠 ----
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


# ---- WNDCLASSW 缁撴瀯浣?----
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


# ---- 绐楀彛杩囩▼绫诲瀷 ----
WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_longlong,      # LRESULT (64-bit)
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


def _parse_hotkey(hotkey_str):
    """瑙ｆ瀽鐑敭瀛楃涓诧紝杩斿洖 (mod_value, vk, 鏄惁鎴愬姛)"""
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
    """鍏ㄥ眬鐑敭绠＄悊鍣紙Windows 鍘熺敓瀹炵幇锛?""

    def __init__(self):
        self._user32 = ctypes.windll.user32
        self._kernel32 = ctypes.windll.kernel32
        self._hotkey_id = 1
        self._callbacks = {}
        self._registered_hids = []  # 璺熻釜宸叉敞鍐岀殑鐑敭 ID
        self._running = False
        self._thread = None
        self._hwnd = None
        self._wndproc_ref = None  # 闃叉 GC
        self._current_hotkey_str = None
        self._current_callback = None

    def register(self, hotkey_str, callback):
        """
        娉ㄥ唽鍏ㄥ眬鐑敭锛堜粎璁板綍淇℃伅锛岀湡姝ｆ敞鍐屽湪 start() 涓級

        Args:
            hotkey_str: "ctrl+alt+v"
            callback: 鍥炶皟鍑芥暟锛堝湪鍚庡彴绾跨▼涓皟鐢級
        """
        mod_value, vk, ok = _parse_hotkey(hotkey_str)
        if not ok:
            print(f"[鐑敭] 鏍煎紡閿欒鎴栨湭鐭ラ敭: {hotkey_str}")
            return False

        hid = self._hotkey_id
        self._hotkey_id += 1

        self._callbacks[hid] = callback
        self._current_hotkey_str = hotkey_str
        self._current_callback = callback

        print(f"[鐑敭] 寰呮敞鍐? {hotkey_str} (ID={hid})")
        return True

    def reregister(self, new_hotkey_str, callback=None):
        """
        鍗虫椂鏇存崲鐑敭锛屾棤闇€閲嶅惎
        鍏堟敞閿€鏃х儹閿紝鍐嶆敞鍐屾柊鐨勶紙澶嶇敤鍥哄畾 ID锛?        """
        if callback is None:
            callback = self._current_callback

        # 娉ㄩ攢鎵€鏈夋棫鐑敭
        for hid in self._registered_hids:
            self._user32.UnregisterHotKey(self._hwnd, hid)
            self._callbacks.pop(hid, None)

        self._registered_hids = []

        mod_value, vk, ok = _parse_hotkey(new_hotkey_str)
        if not ok:
            print(f"[鐑敭] 鏍煎紡閿欒鎴栨湭鐭ラ敭: {new_hotkey_str}")
            return False

        # 澶嶇敤鍥哄畾 ID=1锛岄伩鍏嶆棤闄愰€掑
        hid = 1
        self._callbacks[hid] = callback
        self._current_hotkey_str = new_hotkey_str
        self._current_callback = callback

        result = self._user32.RegisterHotKey(self._hwnd, hid, mod_value, vk)
        if result:
            self._registered_hids.append(hid)
            print(f"[鐑敭] 宸叉洿鎹负: {new_hotkey_str}")
            return True
        else:
            err = ctypes.get_last_error()
            print(f"[鐑敭] 鏇存崲澶辫触, 閿欒鐮?{err}")
            return False

    def _do_register_all(self):
        """鍚姩鏃舵敞鍐屽綋鍓嶇儹閿?""
        if not self._current_hotkey_str or not self._hwnd:
            return False

        mod_value, vk, ok = _parse_hotkey(self._current_hotkey_str)
        if not ok:
            return False

        hid = 1  # 鍥哄畾 ID
        self._callbacks[hid] = self._current_callback
        result = self._user32.RegisterHotKey(self._hwnd, hid, mod_value, vk)
        if result:
            self._registered_hids.append(hid)
            print(f"[鐑敭] 娉ㄥ唽鎴愬姛: {self._current_hotkey_str}")
            return True
        else:
            err = ctypes.get_last_error()
            print(f"[鐑敭] 娉ㄥ唽澶辫触, 閿欒鐮?{err}")
            return False

    def start(self):
        """鍚姩鐑敭娑堟伅寰幆锛堝悗鍙扮嚎绋嬶級"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()
        print("[鐑敭] 娑堟伅寰幆宸插惎鍔?)

    def stop(self):
        """鍋滄鐑敭娑堟伅寰幆"""
        self._running = False
        if self._hwnd:
            # 鍙戦€?WM_QUIT 閫€鍑烘秷鎭惊鐜?            self._user32.PostMessageW(self._hwnd, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=3)
        print("[鐑敭] 宸插仠姝?)

    def _message_loop(self):
        """Windows 娑堟伅寰幆锛堝悗鍙扮嚎绋嬶級"""
        # 璁剧疆 API 鍑芥暟鍙傛暟绫诲瀷锛?4 浣嶇郴缁熷繀闇€锛岄伩鍏?ctypes 榛樿鎸?c_int 鎴柇鎸囬拡锛?        self._user32.DefWindowProcW.argtypes = [
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

        # 淇濆瓨鍥炶皟寮曠敤闃叉琚?GC
        self._wndproc_ref = WNDPROC(self._wnd_proc)

        # 娉ㄥ唽绐楀彛绫?        class_name = "ClipboardMemoHotkeyWnd"
        wnd_class = WNDCLASSW()
        wnd_class.lpfnWndProc = ctypes.cast(self._wndproc_ref, ctypes.c_void_p)
        hinst = self._kernel32.GetModuleHandleW(None)
        wnd_class.hInstance = ctypes.c_void_p(hinst)
        wnd_class.lpszClassName = class_name

        atom = self._user32.RegisterClassW(ctypes.byref(wnd_class))
        if atom == 0:
            err = ctypes.get_last_error()
            print(f"[鐑敭] 娉ㄥ唽绐楀彛绫诲け璐? 閿欒鐮?{err}")
            return

        # 鍒涘缓娑堟伅绐楀彛
        self._hwnd = self._user32.CreateWindowExW(
            0, class_name, "", 0,
            0, 0, 0, 0,
            wintypes.HWND(HWND_MESSAGE),  # 娑堟伅涓撶敤绐楀彛
            None, ctypes.c_void_p(hinst), None
        )

        if not self._hwnd:
            err = ctypes.get_last_error()
            print(f"[鐑敭] 鍒涘缓娑堟伅绐楀彛澶辫触, 閿欒鐮?{err}")
            return

        # 娉ㄥ唽鐑敭
        self._do_register_all()

        print(f"[鐑敭] 娑堟伅绐楀彛鍒涘缓鎴愬姛 HWND={self._hwnd}")

        # 娑堟伅寰幆
        msg = wintypes.MSG()
        while self._running:
            # 浣跨敤 PeekMessage + sleep 鑰屼笉鏄樆濉炵殑 GetMessage
            # 杩欐牱 stop() 鍙互鏇村強鏃跺湴鍝嶅簲
            has_msg = self._user32.PeekMessageW(
                ctypes.byref(msg), None, 0, 0, PM_REMOVE
            )
            if has_msg:
                if msg.message == WM_QUIT:
                    break
                self._user32.TranslateMessage(ctypes.byref(msg))
                self._user32.DispatchMessageW(ctypes.byref(msg))
            else:
                # 娌℃湁娑堟伅鏃剁煭鏆備紤鐪狅紝闄嶄綆 CPU 鍗犵敤
                ctypes.windll.kernel32.Sleep(50)

        # 娓呯悊
        if self._hwnd:
            self._user32.DestroyWindow(self._hwnd)
            self._hwnd = None

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """绐楀彛娑堟伅澶勭悊锛堝湪鍚庡彴绾跨▼涓皟鐢級"""
        if msg == WM_HOTKEY:
            hid = wparam
            callback = self._callbacks.get(hid)
            if callback:
                try:
                    callback()
                except Exception as e:
                    print(f"[鐑敭] 鍥炶皟寮傚父: {e}")
            return 0
        return self._user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def parse_hotkey_string(hotkey_str):
    """鏍囧噯鍖栫儹閿瓧绗︿覆"""
    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    return "+".join(parts)


# 鍏ㄥ眬鍗曚緥
_hotkey_instance = None


def get_hotkey_manager():
    global _hotkey_instance
    if _hotkey_instance is None:
        _hotkey_instance = HotkeyManager()
    return _hotkey_instance
