"""
剪贴板监控模块
借鉴 Ditto 的思路，轮询 Windows 剪贴板，检测变化后分类存储
"""

import time
import threading
import os

from config import get_config, IMAGES_DIR
from utils import compute_hash, compute_image_hash, generate_image_filename
from classifier import classify_text
from storage import get_storage


class ClipboardMonitor:
    """剪贴板变化监控器"""

    def __init__(self):
        self.storage = get_storage()
        self._running = False
        self._thread = None
        self._last_hash = None
        self._poll_interval = get_config("poll_interval_ms", 500) / 1000.0
        self._callbacks = []  # 新条目回调列表
        self._win32clipboard = None
        self._win32con = None
        self._cleanup_counter = 0  # 控制清理频率

    def _init_win32(self):
        """延迟导入 win32 模块"""
        if self._win32clipboard is None:
            try:
                import win32clipboard
                import win32con
                self._win32clipboard = win32clipboard
                self._win32con = win32con
                return True
            except ImportError:
                print("[警告] pywin32 未安装，剪贴板监控不可用")
                return False
        return True

    def on_new_item(self, callback):
        """注册新条目回调"""
        self._callbacks.append(callback)

    def start(self):
        """启动剪贴板监控"""
        if self._running:
            return

        if not self._init_win32():
            print("[错误] 无法初始化剪贴板监控")
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print(f"[剪贴板监控] 已启动 (轮询间隔: {self._poll_interval}s)")

    def stop(self):
        """停止剪贴板监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("[剪贴板监控] 已停止")

    def _monitor_loop(self):
        """监控主循环"""
        while self._running:
            try:
                self._check_clipboard()
            except Exception as e:
                print(f"[剪贴板监控] 错误: {e}")
            time.sleep(self._poll_interval)

    def _check_clipboard(self):
        """检查剪贴板内容是否变化"""
        try:
            self._win32clipboard.OpenClipboard()
        except Exception:
            return

        try:
            # 检查剪贴板序列号（快速判断是否变化）
            if hasattr(self._win32clipboard, 'GetClipboardSequenceNumber'):
                try:
                    seq = self._win32clipboard.GetClipboardSequenceNumber()
                    if hasattr(self, '_last_seq') and seq == self._last_seq:
                        return
                    self._last_seq = seq
                except Exception:
                    pass

            # 尝试获取文本
            text_content = None
            image_data = None

            # 先检查可用格式
            formats = []
            fmt = 0
            try:
                while True:
                    fmt = self._win32clipboard.EnumClipboardFormats(fmt)
                    if fmt == 0:
                        break
                    formats.append(fmt)
            except Exception:
                pass

            cf_text = getattr(self._win32con, 'CF_UNICODETEXT', 13)
            cf_text_ansi = getattr(self._win32con, 'CF_TEXT', 1)
            cf_bitmap = getattr(self._win32con, 'CF_BITMAP', 2)
            cf_dib = getattr(self._win32con, 'CF_DIB', 8)

            # 获取文本
            if cf_text in formats:
                try:
                    text_content = self._win32clipboard.GetClipboardData(cf_text)
                except Exception:
                    pass

            if text_content is None and cf_text_ansi in formats:
                try:
                    raw = self._win32clipboard.GetClipboardData(cf_text_ansi)
                    if isinstance(raw, bytes):
                        text_content = raw.decode("gbk", errors="ignore")
                    else:
                        text_content = raw
                except Exception:
                    pass

            # 获取图片（记录是否有图片格式，关闭剪贴板后再用 PIL 获取）
            has_image = cf_dib in formats or cf_bitmap in formats

        finally:
            try:
                self._win32clipboard.CloseClipboard()
            except Exception:
                pass

        # 处理获取到的内容（剪贴板已关闭）
        if has_image:
            image_data = self._get_clipboard_image()
            if image_data:
                self._process_image(image_data)
        elif text_content and text_content.strip():
            self._process_text(text_content)

    def _process_text(self, text):
        """处理文本内容"""
        content_hash = compute_hash(text)

        # 去重：与上一条相同
        if content_hash == self._last_hash:
            return
        self._last_hash = content_hash

        # 查找是否已存在
        existing = self.storage.get_item_by_hash(content_hash)
        if existing:
            self.storage.update_copy(existing["id"])
            return

        # 分类
        category, summary, subcategory = classify_text(text)

        # 存储
        item_id = self.storage.add_item(
            content_type="text",
            text_content=text,
            content_hash=content_hash,
            category=category,
            subcategory=subcategory,
            summary=summary
        )

        # 低频清理：每 20 次新内容才执行一次清理
        self._cleanup_counter += 1
        if self._cleanup_counter >= 20:
            self.storage.cleanup_old_items()
            self._cleanup_counter = 0

        # 通知回调
        for cb in self._callbacks:
            try:
                cb(item_id, category, summary)
            except Exception as e:
                print(f"[剪贴板监控] 回调错误: {e}")

        print(f"[剪贴板监控] 新文本 [{category}]: {summary}")

    def _process_image(self, image_bytes):
        """处理图片内容"""
        content_hash = compute_image_hash(image_bytes)

        # 去重
        if content_hash == self._last_hash:
            return
        self._last_hash = content_hash

        # 查找是否已存在
        existing = self.storage.get_item_by_hash(content_hash)
        if existing:
            self.storage.update_copy(existing["id"])
            return

        # 保存图片文件
        filename = generate_image_filename()
        filepath = os.path.join(IMAGES_DIR, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(image_bytes)
        except Exception as e:
            print(f"[剪贴板监控] 保存图片失败: {e}")
            return

        # 生成摘要
        summary = f"截图_{filename[:20]}"

        # 存储
        item_id = self.storage.add_item(
            content_type="image",
            text_content=None,
            image_path=filepath,
            content_hash=content_hash,
            category="image",
            summary=summary
        )

        # 低频清理
        self._cleanup_counter += 1
        if self._cleanup_counter >= 20:
            self.storage.cleanup_old_items()
            self._cleanup_counter = 0

        # 通知回调
        for cb in self._callbacks:
            try:
                cb(item_id, "image", summary)
            except Exception as e:
                print(f"[剪贴板监控] 回调错误: {e}")

        print(f"[剪贴板监控] 新图片: {summary}")

    def _get_clipboard_image(self):
        """从剪贴板获取图片数据（在剪贴板关闭后调用）"""
        try:
            from PIL import ImageGrab, Image
            import io

            img = ImageGrab.grabclipboard()
            if img and isinstance(img, Image.Image):
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return buf.getvalue()
        except ImportError:
            pass
        except Exception as e:
            print(f"[剪贴板监控] 图片获取失败: {e}")
        return None

    def get_current_text(self):
        """手动获取当前剪贴板文本（用于调试/手动触发）"""
        if not self._init_win32():
            return None
        try:
            self._win32clipboard.OpenClipboard()
            cf_text = getattr(self._win32con, 'CF_UNICODETEXT', 13)
            try:
                text = self._win32clipboard.GetClipboardData(cf_text)
                return text
            except Exception:
                return None
            finally:
                self._win32clipboard.CloseClipboard()
        except Exception:
            return None


# 全局单例
_monitor_instance = None


def get_monitor():
    """获取剪贴板监控单例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ClipboardMonitor()
    return _monitor_instance
