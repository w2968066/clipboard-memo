"""
系统托盘图标模块
"""

import threading
import os
import sys

from config import ICON_PATH, IMAGES_DIR, get_config, set_config


class TrayIcon:
    """系统托盘图标管理"""

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
        """启动系统托盘"""
        try:
            import pystray
            from PIL import Image, ImageDraw

            self._pystray_available = True

            # 创建图标
            icon_path = self._get_icon_path()
            if os.path.exists(icon_path):
                self._icon = Image.open(icon_path)
            else:
                # 生成默认图标
                self._icon = self._create_default_icon()

            # 创建菜单（纯文字，无 emoji）
            menu = pystray.Menu(
                pystray.MenuItem("打开剪贴板", self._handle_open, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("设置", self._handle_settings),
                pystray.MenuItem("清理剪贴板...", self._handle_cleanup),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "开机自启",
                    self._handle_toggle_autostart,
                    checked=lambda item: get_config("auto_start", False)
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", self._handle_exit),
            )

            self._tray = pystray.Icon(
                "clipboard_memo",
                self._icon,
                "剪贴板备忘录",
                menu
            )

            self._running = True
            # 在独立线程中运行托盘
            tray_thread = threading.Thread(
                target=self._tray.run, daemon=True
            )
            tray_thread.start()
            print("[托盘] 系统托盘已启动")

            return True

        except ImportError:
            print("[托盘] pystray 未安装，托盘功能不可用")
            self._pystray_available = False
            return False
        except Exception as e:
            print(f"[托盘] 启动失败: {e}")
            return False

    def stop(self):
        """停止系统托盘"""
        self._running = False
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        print("[托盘] 已停止")

    def notify(self, title, message):
        """发送通知（如果可用）"""
        if self._tray and hasattr(self._tray, 'notify'):
            try:
                self._tray.notify(title, message)
            except Exception:
                pass

    def _get_icon_path(self):
        """获取图标文件路径"""
        # 尝试多种可能的图标位置
        possible_paths = [
            ICON_PATH,
            os.path.join(os.path.dirname(__file__), "assets", "icon.png"),
            os.path.join(os.path.dirname(__file__), "icon.png"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return p
        return ICON_PATH

    def _create_default_icon(self):
        """创建默认图标（蓝色圆形 + 白字 C）"""
        from PIL import Image, ImageDraw, ImageFont
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 蓝色圆形背景
        draw.ellipse([4, 4, size-4, size-4], fill="#4a9eff")

        # 白色 "C" 文字
        try:
            font = ImageFont.truetype("segoeui.ttf", 32)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", 32)
            except Exception:
                font = ImageFont.load_default()

        # 手动居中文字
        text = "C"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((size - tw) // 2, (size - th) // 2),
                  text, fill="white", font=font)

        return img

    def _handle_open(self):
        """打开剪贴板浮窗（双击/默认：屏幕中央）"""
        if self._on_open:
            self._on_open(center=True)

    def _handle_settings(self):
        """打开设置窗口"""
        if self._on_settings:
            self._on_settings()

    def _handle_cleanup(self):
        """打开清理窗口"""
        if self._on_cleanup:
            self._on_cleanup()

    def _handle_exit(self):
        """退出程序"""
        if self._on_exit:
            self._on_exit()

    def _handle_toggle_autostart(self):
        """切换开机自启"""
        current = get_config("auto_start", False)
        new_state = not current
        set_config("auto_start", new_state)

        if new_state:
            self._enable_autostart()
        else:
            self._disable_autostart()

    def _enable_autostart(self):
        """启用开机自启（写入注册表）"""
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
            # 使用 pythonw.exe 避免显示控制台
            exe_dir = os.path.dirname(sys.executable)
            pythonw = os.path.join(exe_dir, "pythonw.exe")
            if os.path.exists(pythonw):
                cmd = f'"{pythonw}" "{script_path}"'
            else:
                cmd = f'"{sys.executable}" "{script_path}"'
            winreg.SetValueEx(key, "ClipboardMemo", 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(key)
            print("[托盘] 开机自启已启用")
        except Exception as e:
            print(f"[托盘] 设置开机自启失败: {e}")

    def _disable_autostart(self):
        """禁用开机自启"""
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
            print("[托盘] 开机自启已禁用")
        except Exception as e:
            print(f"[托盘] 取消开机自启失败: {e}")
