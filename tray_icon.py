"""
绯荤粺鎵樼洏鍥炬爣妯″潡
"""

import threading
import os
import sys

from config import ICON_PATH, IMAGES_DIR, get_config, set_config


class TrayIcon:
    """绯荤粺鎵樼洏鍥炬爣绠＄悊"""

    def __init__(self, on_open=None, on_cleanup=None, on_settings=None, on_exit=None):
        self._on_open = on_open
        self._on_cleanup = on_cleanup
        self._on_settings = on_settings
        self._on_exit = on_exit
        self._tray = None
        self._icon = None
        self._running = False
        self._pystray_available = False

    def start(self):
        """鍚姩绯荤粺鎵樼洏"""
        try:
            import pystray
            from PIL import Image, ImageDraw

            self._pystray_available = True

            # 鍒涘缓鍥炬爣
            icon_path = self._get_icon_path()
            if os.path.exists(icon_path):
                self._icon = Image.open(icon_path)
            else:
                # 鐢熸垚榛樿鍥炬爣
                self._icon = self._create_default_icon()

            # 鍒涘缓鑿滃崟锛堢函鏂囧瓧锛屾棤 emoji锛?            menu = pystray.Menu(
                pystray.MenuItem("鎵撳紑鍓创鏉?, self._handle_open, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("璁剧疆", self._handle_settings),
                pystray.MenuItem("娓呯悊鍓创鏉?..", self._handle_cleanup),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "寮€鏈鸿嚜鍚?,
                    self._handle_toggle_autostart,
                    checked=lambda item: get_config("auto_start", False)
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("閫€鍑?, self._handle_exit),
            )

            self._tray = pystray.Icon(
                "clipboard_memo",
                self._icon,
                "鍓创鏉垮蹇樺綍",
                menu
            )

            self._running = True
            # 鍦ㄧ嫭绔嬬嚎绋嬩腑杩愯鎵樼洏
            tray_thread = threading.Thread(
                target=self._tray.run, daemon=True
            )
            tray_thread.start()
            print("[鎵樼洏] 绯荤粺鎵樼洏宸插惎鍔?)

            return True

        except ImportError:
            print("[鎵樼洏] pystray 鏈畨瑁咃紝鎵樼洏鍔熻兘涓嶅彲鐢?)
            self._pystray_available = False
            return False
        except Exception as e:
            print(f"[鎵樼洏] 鍚姩澶辫触: {e}")
            return False

    def stop(self):
        """鍋滄绯荤粺鎵樼洏"""
        self._running = False
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        print("[鎵樼洏] 宸插仠姝?)

    def notify(self, title, message):
        """鍙戦€侀€氱煡锛堝鏋滃彲鐢級"""
        if self._tray and hasattr(self._tray, 'notify'):
            try:
                self._tray.notify(title, message)
            except Exception:
                pass

    def _get_icon_path(self):
        """鑾峰彇鍥炬爣鏂囦欢璺緞"""
        # 灏濊瘯澶氱鍙兘鐨勫浘鏍囦綅缃?        possible_paths = [
            ICON_PATH,
            os.path.join(os.path.dirname(__file__), "assets", "icon.png"),
            os.path.join(os.path.dirname(__file__), "icon.png"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return p
        return ICON_PATH

    def _create_default_icon(self):
        """鍒涘缓榛樿鍥炬爣锛堣摑鑹插渾褰?+ 鐧藉瓧 C锛?""
        from PIL import Image, ImageDraw, ImageFont
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 钃濊壊鍦嗗舰鑳屾櫙
        draw.ellipse([4, 4, size-4, size-4], fill="#4a9eff")

        # 鐧借壊 "C" 鏂囧瓧
        try:
            font = ImageFont.truetype("segoeui.ttf", 32)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", 32)
            except Exception:
                font = ImageFont.load_default()

        # 鎵嬪姩灞呬腑鏂囧瓧
        text = "C"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((size - tw) // 2, (size - th) // 2),
                  text, fill="white", font=font)

        return img

    def _handle_open(self):
        """鎵撳紑鍓创鏉挎诞绐楋紙鍙屽嚮/榛樿锛氬睆骞曚腑澶級"""
        if self._on_open:
            self._on_open(center=True)

    def _handle_settings(self):
        """鎵撳紑璁剧疆绐楀彛"""
        if self._on_settings:
            self._on_settings()

    def _handle_cleanup(self):
        """鎵撳紑娓呯悊绐楀彛"""
        if self._on_cleanup:
            self._on_cleanup()

    def _handle_exit(self):
        """閫€鍑虹▼搴?""
        if self._on_exit:
            self._on_exit()

    def _handle_toggle_autostart(self):
        """鍒囨崲寮€鏈鸿嚜鍚?""
        current = get_config("auto_start", False)
        new_state = not current
        set_config("auto_start", new_state)

        if new_state:
            self._enable_autostart()
        else:
            self._disable_autostart()

    def _enable_autostart(self):
        """鍚敤寮€鏈鸿嚜鍚紙鍐欏叆娉ㄥ唽琛級"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            exe_path = sys.executable
            if getattr(sys, 'frozen', False):
                script_path = sys.executable
            else:
                script_path = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "main.py")
                )
            # 浣跨敤 pythonw.exe 閬垮厤鏄剧ず鎺у埗鍙?            exe_dir = os.path.dirname(sys.executable)
            pythonw = os.path.join(exe_dir, "pythonw.exe")
            if os.path.exists(pythonw):
                cmd = f'"{pythonw}" "{script_path}"'
            else:
                cmd = f'"{sys.executable}" "{script_path}"'
            winreg.SetValueEx(key, "ClipboardMemo", 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(key)
            print("[鎵樼洏] 寮€鏈鸿嚜鍚凡鍚敤")
        except Exception as e:
            print(f"[鎵樼洏] 璁剧疆寮€鏈鸿嚜鍚け璐? {e}")

    def _disable_autostart(self):
        """绂佺敤寮€鏈鸿嚜鍚?""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            try:
                winreg.DeleteValue(key, "ClipboardMemo")
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
            print("[鎵樼洏] 寮€鏈鸿嚜鍚凡绂佺敤")
        except Exception as e:
            print(f"[鎵樼洏] 鍙栨秷寮€鏈鸿嚜鍚け璐? {e}")
