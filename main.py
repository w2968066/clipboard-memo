"""
鍓创鏉垮蹇樺綍 鈥?鍏ュ彛妯″潡
鏋佺畝 AI 鍓创鏉跨鐞嗗伐鍏凤紝瀹屽叏鏈湴杩愯
"""

import sys
import os
import ctypes
import threading
import tkinter as tk

# ---- DPI 鎰熺煡锛堝繀椤诲湪 tkinter 鍒濆鍖栦箣鍓嶈缃級----
# 鍚﹀垯楂?DPI 灞忓箷涓?GetCursorPos 鍜?tkinter 鍧愭爣涓嶄竴鑷达紝瀵艰嚧绐楀彛浣嶇疆鍋忕Щ
try:
    # Windows 10 1703+ PerMonitorV2
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        # Windows 8.1+
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            # Windows Vista+
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# 灏嗛」鐩洰褰曞姞鍏ヨ矾寰?sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import load_config, get_config, set_config
from storage import get_storage
from classifier import classify_text
from clipboard_monitor import get_monitor
from popup_window import get_popup, CleanupWindow
from settings_window import SettingsWindow
from hotkey_manager import get_hotkey_manager, parse_hotkey_string
from tray_icon import TrayIcon


class Application:
    """搴旂敤绋嬪簭涓绘帶鍒跺櫒"""

    def __init__(self):
        self.config = load_config()
        self.storage = get_storage()
        self.monitor = get_monitor()
        self.popup = get_popup()
        self.hotkey_manager = get_hotkey_manager()
        self.tray = None

        # 鍒涘缓闅愯棌鐨?tkinter 鏍圭獥鍙?        self.root = tk.Tk()
        self.root.withdraw()  # 闅愯棌鏍圭獥鍙?        self.root.title("鍓创鏉垮蹇樺綍")

        self._exiting = False

    def start(self):
        """鍚姩搴旂敤绋嬪簭"""
        print("=" * 50)
        print("  鍓创鏉垮蹇樺綍 v1.0")
        print("  瀹屽叏鏈湴杩愯锛屼繚鎶ゆ偍鐨勯殣绉?)
        print("=" * 50)

        # 1. 鍚姩鍓创鏉跨洃鎺э紝閫氱煡寮圭獥鏈夋柊鍐呭
        self.monitor.start()
        self.monitor.on_new_item(lambda *a: self.popup.mark_dirty())

        # 2. 娉ㄥ唽鍏ㄥ眬鐑敭锛堝厛 register 鍐?start锛岀‘淇濇秷鎭惊鐜惎鍔ㄦ椂鐑敭淇℃伅宸插氨缁級
        hotkey_str = self.config.get("hotkey", "ctrl+alt+v")
        hotkey_str = parse_hotkey_string(hotkey_str)

        self.hotkey_manager.register(
            hotkey_str,
            lambda: self._on_hotkey()
        )
        self.hotkey_manager.start()

        # 3. 鍚姩绯荤粺鎵樼洏
        self.tray = TrayIcon(
            on_open=lambda center=False: self._safe_call(lambda: self.popup.show(center=center)),
            on_settings=lambda: self._safe_call(self._open_settings),
            on_cleanup=lambda: self._safe_call(self._open_cleanup),
            on_exit=lambda: self._safe_call(self.exit_app),
        )
        self.tray.start()

        # 4. 澶勭悊閫€鍑烘椂鐨勬竻鐞?        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        # 5. 鍚姩鏃舵竻鐞嗚繃鏈燂紙宸插垹闄よ秴杩?澶╃殑锛夊拰瓒呴噺鏉＄洰
        n = self.storage.purge_expired_deleted(7)
        if n > 0:
            print(f"[绯荤粺] 娓呯悊浜?{n} 鏉¤繃鏈熷凡鍒犻櫎鍐呭")
        self._schedule_cleanup()

        print("[绯荤粺] 搴旂敤宸插惎鍔紝鎸?{} 鎵撳紑鍓创鏉?.format(hotkey_str))
        print("[绯荤粺] 鍙抽敭鎵樼洏鍥炬爣鏌ョ湅鏇村閫夐」")

        # 鍚姩 tkinter 涓诲惊鐜紙鍦ㄤ富绾跨▼锛?        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.exit_app()

    def _on_hotkey(self):
        """鐑敭瑙﹀彂锛氭樉绀哄脊鍑虹獥鍙?""
        self._safe_call(self.popup.toggle)

    def _open_settings(self):
        """鎵撳紑璁剧疆绐楀彛锛堢洿鎺ユ墦寮€锛岀疆椤讹級"""
        SettingsWindow(self.root, self.hotkey_manager)

    def _open_cleanup(self):
        """鎵撳紑娓呯悊绐楀彛"""
        # 浣跨敤 tkinter 鏍圭獥鍙ｄ綔涓虹埗绐楀彛
        CleanupWindow(self.root, self.storage)

    def _safe_call(self, func):
        """绾跨▼瀹夊叏鍦拌皟鐢?tkinter 鍑芥暟锛堜粎鍦ㄦ湭閫€鍑烘椂锛?""
        if self._exiting:
            return
        try:
            self.root.after(0, func)
        except Exception:
            pass

    def _schedule_cleanup(self):
        """瀹氭湡鑷姩娓呯悊锛堟瘡灏忔椂鎵ц涓€娆★級"""
        try:
            self.storage.cleanup_old_items()
            self.storage.purge_expired_deleted(7)
        except Exception:
            pass
        if not self._exiting:
            self.root.after(3600000, self._schedule_cleanup)

    def exit_app(self):
        """閫€鍑哄簲鐢ㄧ▼搴?""
        if self._exiting:
            return
        self._exiting = True

        print("[绯荤粺] 姝ｅ湪閫€鍑?..")

        # 鍋滄鍚勬ā鍧?        for mod_name, mod in [("monitor", self.monitor), ("hotkey", self.hotkey_manager),
                               ("tray", self.tray)]:
            try:
                if mod:
                    mod.stop()
            except Exception as e:
                print(f"[绯荤粺] 鍋滄 {mod_name} 鏃跺嚭閿? {e}")

        # 鍏抽棴鏁版嵁搴撹繛鎺?        try:
            self.storage.close()
        except Exception as e:
            print(f"[绯荤粺] 鍏抽棴鏁版嵁搴撳嚭閿? {e}")

        # 鍏抽棴鎵€鏈?tkinter 绐楀彛
        try:
            self.popup.hide()
        except Exception:
            pass

        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

        print("[绯荤粺] 宸查€€鍑?)
        sys.exit(0)


def main():
    """鍏ュ彛鍑芥暟"""
    app = Application()
    app.start()


if __name__ == "__main__":
    main()
