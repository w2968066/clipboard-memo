"""
鍓创鏉跨洃鎺фā鍧?鍊熼壌 Ditto 鐨勬€濊矾锛岃疆璇?Windows 鍓创鏉匡紝妫€娴嬪彉鍖栧悗鍒嗙被瀛樺偍
"""

import time
import threading
import os

from config import get_config, IMAGES_DIR
from utils import compute_hash, compute_image_hash, generate_image_filename
from classifier import classify_text
from storage import get_storage


class ClipboardMonitor:
    """鍓创鏉垮彉鍖栫洃鎺у櫒"""

    def __init__(self):
        self.storage = get_storage()
        self._running = False
        self._thread = None
        self._last_hash = None
        self._poll_interval = get_config("poll_interval_ms", 500) / 1000.0
        self._callbacks = []  # 鏂版潯鐩洖璋冨垪琛?        self._win32clipboard = None
        self._win32con = None
        self._cleanup_counter = 0  # 鎺у埗娓呯悊棰戠巼

    def _init_win32(self):
        """寤惰繜瀵煎叆 win32 妯″潡"""
        if self._win32clipboard is None:
            try:
                import win32clipboard
                import win32con
                self._win32clipboard = win32clipboard
                self._win32con = win32con
                return True
            except ImportError:
                print("[璀﹀憡] pywin32 鏈畨瑁咃紝鍓创鏉跨洃鎺т笉鍙敤")
                return False
        return True

    def on_new_item(self, callback):
        """娉ㄥ唽鏂版潯鐩洖璋?""
        self._callbacks.append(callback)

    def start(self):
        """鍚姩鍓创鏉跨洃鎺?""
        if self._running:
            return

        if not self._init_win32():
            print("[閿欒] 鏃犳硶鍒濆鍖栧壀璐存澘鐩戞帶")
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print(f"[鍓创鏉跨洃鎺 宸插惎鍔?(杞闂撮殧: {self._poll_interval}s)")

    def stop(self):
        """鍋滄鍓创鏉跨洃鎺?""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("[鍓创鏉跨洃鎺 宸插仠姝?)

    def _monitor_loop(self):
        """鐩戞帶涓诲惊鐜?""
        while self._running:
            try:
                self._check_clipboard()
            except Exception as e:
                print(f"[鍓创鏉跨洃鎺 閿欒: {e}")
            time.sleep(self._poll_interval)

    def _check_clipboard(self):
        """妫€鏌ュ壀璐存澘鍐呭鏄惁鍙樺寲"""
        try:
            self._win32clipboard.OpenClipboard()
        except Exception:
            return

        try:
            # 妫€鏌ュ壀璐存澘搴忓垪鍙凤紙蹇€熷垽鏂槸鍚﹀彉鍖栵級
            if hasattr(self._win32clipboard, 'GetClipboardSequenceNumber'):
                try:
                    seq = self._win32clipboard.GetClipboardSequenceNumber()
                    if hasattr(self, '_last_seq') and seq == self._last_seq:
                        return
                    self._last_seq = seq
                except Exception:
                    pass

            # 灏濊瘯鑾峰彇鏂囨湰
            text_content = None
            image_data = None

            # 鍏堟鏌ュ彲鐢ㄦ牸寮?            formats = []
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

            # 鑾峰彇鏂囨湰
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

            # 鑾峰彇鍥剧墖锛堣褰曟槸鍚︽湁鍥剧墖鏍煎紡锛屽叧闂壀璐存澘鍚庡啀鐢?PIL 鑾峰彇锛?            has_image = cf_dib in formats or cf_bitmap in formats

        finally:
            try:
                self._win32clipboard.CloseClipboard()
            except Exception:
                pass

        # 澶勭悊鑾峰彇鍒扮殑鍐呭锛堝壀璐存澘宸插叧闂級
        if has_image:
            image_data = self._get_clipboard_image()
            if image_data:
                self._process_image(image_data)
        elif text_content and text_content.strip():
            self._process_text(text_content)

    def _process_text(self, text):
        """澶勭悊鏂囨湰鍐呭"""
        content_hash = compute_hash(text)

        # 鍘婚噸锛氫笌涓婁竴鏉＄浉鍚?        if content_hash == self._last_hash:
            return
        self._last_hash = content_hash

        # 鏌ユ壘鏄惁宸插瓨鍦?        existing = self.storage.get_item_by_hash(content_hash)
        if existing:
            self.storage.update_copy(existing["id"])
            return

        # 鍒嗙被
        category, summary, subcategory = classify_text(text)

        # 瀛樺偍
        item_id = self.storage.add_item(
            content_type="text",
            text_content=text,
            content_hash=content_hash,
            category=category,
            subcategory=subcategory,
            summary=summary
        )

        # 浣庨娓呯悊锛氭瘡 20 娆℃柊鍐呭鎵嶆墽琛屼竴娆℃竻鐞?        self._cleanup_counter += 1
        if self._cleanup_counter >= 20:
            self.storage.cleanup_old_items()
            self._cleanup_counter = 0

        # 閫氱煡鍥炶皟
        for cb in self._callbacks:
            try:
                cb(item_id, category, summary)
            except Exception as e:
                print(f"[鍓创鏉跨洃鎺 鍥炶皟閿欒: {e}")

        print(f"[鍓创鏉跨洃鎺 鏂版枃鏈?[{category}]: {summary}")

    def _process_image(self, image_bytes):
        """澶勭悊鍥剧墖鍐呭"""
        content_hash = compute_image_hash(image_bytes)

        # 鍘婚噸
        if content_hash == self._last_hash:
            return
        self._last_hash = content_hash

        # 鏌ユ壘鏄惁宸插瓨鍦?        existing = self.storage.get_item_by_hash(content_hash)
        if existing:
            self.storage.update_copy(existing["id"])
            return

        # 淇濆瓨鍥剧墖鏂囦欢
        filename = generate_image_filename()
        filepath = os.path.join(IMAGES_DIR, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(image_bytes)
        except Exception as e:
            print(f"[鍓创鏉跨洃鎺 淇濆瓨鍥剧墖澶辫触: {e}")
            return

        # 鐢熸垚鎽樿
        summary = f"鎴浘_{filename[:20]}"

        # 瀛樺偍
        item_id = self.storage.add_item(
            content_type="image",
            text_content=None,
            image_path=filepath,
            content_hash=content_hash,
            category="image",
            summary=summary
        )

        # 浣庨娓呯悊
        self._cleanup_counter += 1
        if self._cleanup_counter >= 20:
            self.storage.cleanup_old_items()
            self._cleanup_counter = 0

        # 閫氱煡鍥炶皟
        for cb in self._callbacks:
            try:
                cb(item_id, "image", summary)
            except Exception as e:
                print(f"[鍓创鏉跨洃鎺 鍥炶皟閿欒: {e}")

        print(f"[鍓创鏉跨洃鎺 鏂板浘鐗? {summary}")

    def _get_clipboard_image(self):
        """浠庡壀璐存澘鑾峰彇鍥剧墖鏁版嵁锛堝湪鍓创鏉垮叧闂悗璋冪敤锛?""
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
            print(f"[鍓创鏉跨洃鎺 鍥剧墖鑾峰彇澶辫触: {e}")
        return None

    def get_current_text(self):
        """鎵嬪姩鑾峰彇褰撳墠鍓创鏉挎枃鏈紙鐢ㄤ簬璋冭瘯/鎵嬪姩瑙﹀彂锛?""
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


# 鍏ㄥ眬鍗曚緥
_monitor_instance = None


def get_monitor():
    """鑾峰彇鍓创鏉跨洃鎺у崟渚?""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ClipboardMonitor()
    return _monitor_instance
