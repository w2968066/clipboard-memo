"""
剪贴板备忘录 — 入口模块
极简 AI 剪贴板管理工具，完全本地运行
"""

import sys
import os
import ctypes
import threading
import tkinter as tk

# ---- DPI 感知（必须在 tkinter 初始化之前设置）----
# 否则高 DPI 屏幕上 GetCursorPos 和 tkinter 坐标不一致，导致窗口位置偏移
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

# 将项目目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import load_config, get_config, set_config
from storage import get_storage
from classifier import classify_text
from clipboard_monitor import get_monitor
from popup_window import get_popup, CleanupWindow
from settings_window import SettingsWindow
from hotkey_manager import get_hotkey_manager, parse_hotkey_string
from tray_icon import TrayIcon


class Application:
    """应用程序主控制器"""

    def __init__(self):
        self.config = load_config()
        self.storage = get_storage()
        self.monitor = get_monitor()
        self.popup = get_popup()
        self.hotkey_manager = get_hotkey_manager()
        self.tray = None

        # 创建隐藏的 tkinter 根窗口
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏根窗口
        self.root.title("剪贴板备忘录")

        self._exiting = False

    def start(self):
        """启动应用程序"""
        print("=" * 50)
        print("  剪贴板备忘录 v1.0")
        print("  完全本地运行，保护您的隐私")
        print("=" * 50)

        # 1. 启动剪贴板监控，通知弹窗有新内容
        self.monitor.start()
        self.monitor.on_new_item(lambda *a: self.popup.mark_dirty())

        # 2. 注册全局热键（先 register 再 start，确保消息循环启动时热键信息已就绪）
        hotkey_str = self.config.get("hotkey", "ctrl+alt+v")
        hotkey_str = parse_hotkey_string(hotkey_str)

        self.hotkey_manager.register(
            hotkey_str,
            lambda: self._on_hotkey()
        )
        self.hotkey_manager.start()

        # 3. 启动系统托盘
        self.tray = TrayIcon(
            on_open=lambda center=False: self._safe_call(lambda: self.popup.show(center=center)),
            on_settings=lambda: self._safe_call(self._open_settings),
            on_cleanup=lambda: self._safe_call(self._open_cleanup),
            on_exit=lambda: self._safe_call(self.exit_app),
        )
        self.tray.start()

        # 4. 处理退出时的清理
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        # 5. 启动时清理过期（已删除超过7天的）和超量条目
        n = self.storage.purge_expired_deleted(7)
        if n > 0:
            print(f"[系统] 清理了 {n} 条过期已删除内容")
        self._schedule_cleanup()

        print("[系统] 应用已启动，按 {} 打开剪贴板".format(hotkey_str))
        print("[系统] 右键托盘图标查看更多选项")

        # 启动 tkinter 主循环（在主线程）
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.exit_app()

    def _on_hotkey(self):
        """热键触发：显示弹出窗口"""
        self._safe_call(self.popup.toggle)

    def _open_settings(self):
        """打开设置窗口（直接打开，置顶）"""
        SettingsWindow(self.root, self.hotkey_manager)

    def _open_cleanup(self):
        """打开清理窗口"""
        # 使用 tkinter 根窗口作为父窗口
        CleanupWindow(self.root, self.storage)

    def _safe_call(self, func):
        """线程安全地调用 tkinter 函数（仅在未退出时）"""
        if self._exiting:
            return
        try:
            self.root.after(0, func)
        except Exception:
            pass

    def _schedule_cleanup(self):
        """定期自动清理（每小时执行一次）"""
        try:
            self.storage.cleanup_old_items()
            self.storage.purge_expired_deleted(7)
        except Exception:
            pass
        if not self._exiting:
            self.root.after(3600000, self._schedule_cleanup)

    def exit_app(self):
        """退出应用程序"""
        if self._exiting:
            return
        self._exiting = True

        print("[系统] 正在退出...")

        # 停止各模块
        for mod_name, mod in [("monitor", self.monitor), ("hotkey", self.hotkey_manager),
                               ("tray", self.tray)]:
            try:
                if mod:
                    mod.stop()
            except Exception as e:
                print(f"[系统] 停止 {mod_name} 时出错: {e}")

        # 关闭数据库连接
        try:
            self.storage.close()
        except Exception as e:
            print(f"[系统] 关闭数据库出错: {e}")

        # 关闭所有 tkinter 窗口
        try:
            self.popup.hide()
        except Exception:
            pass

        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

        print("[系统] 已退出")
        sys.exit(0)


def main():
    """入口函数"""
    app = Application()
    app.start()


if __name__ == "__main__":
    main()
