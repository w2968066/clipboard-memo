"""
弹出浮窗 UI — 主界面 + 清理窗口
"""

import tkinter as tk
from tkinter import messagebox, ttk
import time
import os
from collections import OrderedDict
from PIL import Image as PILImage, ImageTk

from storage import get_storage
from utils import truncate_text, format_time, get_display_icon
from config import get_config, get_quick_categorize, get_subcategory_name, get_language
from i18n import t, cat_name
from settings_window import SettingsWindow


# ============================================================
# PopupWindow
# ============================================================

class PopupWindow:
    """剪贴板弹出浮窗（带增量刷新 + 缩略图 LRU）"""

    # 常量
    THUMB_SIZE = 36
    THUMB_CACHE_MAX = 100  # LRU 缓存上限

    def __init__(self):
        self.storage = get_storage()
        self.window = None
        self._current_tab = "recent"
        self._current_subcategory = None  # 子分类 key
        self._search_text = ""
        self._hovered_item_id = None
        self._selected_index = -1
        self._item_widgets = []   # [(frame, item, hoverables), ...]
        self._visible = False
        self._quick_categorize_mode = False
        self._dirty = True
        self._thumbnails = OrderedDict()  # LRU 缓存: path -> PhotoImage
        self._last_sig = None     # 数据签名，用于跳过无变化刷新
        self._force_refresh = False
        self._paste_target_hwnd = None
        self._paste_focus_hwnd = None

    def mark_dirty(self):
        """标记数据已变化"""
        self._dirty = True
        self._last_sig = None
        # 如果窗口可见且在 recent tab 且无搜索，尝试增量插入
        if self._visible and self._current_tab == "recent" and not self._search_text:
            if self.window and self.window.winfo_exists():
                try:
                    self.window.after(50, self._try_incremental_insert)
                except Exception:
                    pass

    def _try_incremental_insert(self):
        """尝试在顶部插入最新条目，避免全量重建"""
        if not self._visible or self._current_tab != "recent" or self._search_text:
            return
        try:
            items = self.storage.get_items(tab="recent", limit=1)
            if not items:
                return
            top_item = items[0]
            # 检查是否已经在列表中
            if self._item_widgets and self._item_widgets[0][1]["id"] == top_item["id"]:
                return
            # 同步更新缓存数据
            if hasattr(self, '_all_items'):
                self._all_items.insert(0, top_item)
                self._last_sig = tuple(i["id"] for i in self._all_items[:200])
            # 创建新 widget 并插入到顶部
            self._create_item_widget(top_item, insert_at_top=True)
            self._rendered_count += 1
            # 更新计数
            total = self.storage.get_item_count(tab="recent")
            self._count_label.config(text=f"{total} items")
            # 限制显示数量，超出时移除底部 widget
            limit = 200
            while len(self._item_widgets) > limit:
                self._remove_item_widget(-1)
                self._rendered_count -= 1
            self._selected_index = -1
        except Exception as e:
            print(f"[Popup] 增量插入失败，回退到全量刷新: {e}")
            self._force_refresh = True
            self._refresh_items()

    def _remove_item_widget(self, index):
        """移除指定索引的 widget"""
        if 0 <= index < len(self._item_widgets):
            frame, item, hoverables = self._item_widgets.pop(index)
            try:
                frame.destroy()
            except Exception:
                pass

    def show(self, center=False):
        if self._visible:
            self._bring_to_front()
            return

        self._visible = True
        self._quick_categorize_mode = False
        self._paste_target_hwnd = self._get_foreground_hwnd()
        self._paste_focus_hwnd = self._get_focused_hwnd()
        self._create_window()

        if center:
            self._position_at_center()
        else:
            self._position_at_cursor()

        if self._dirty or self._force_refresh:
            self._refresh_items()

        self._update_quick_categorize_ui(focus_search=False)
        self.window.update_idletasks()
        self.window.deiconify()
        self.window.update_idletasks()
        self._show_without_activation()
        self._start_outside_click_watch()

    def hide(self):
        self._visible = False
        self._outside_watch_on = False
        self._hovered_item_id = None
        self._selected_index = -1
        self._quick_categorize_mode = False
        if self.window:
            try:
                self.window.withdraw()
                self.window.update_idletasks()
            except Exception:
                pass
            try:
                import ctypes
                hwnd = self._get_toplevel_hwnd()
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 0)
            except Exception:
                pass

    def toggle(self):
        if self._visible:
            self.hide()
        else:
            self.show()

    def _bring_to_front(self):
        if self.window:
            if self._dirty or self._force_refresh:
                self._refresh_items()
            self.window.update_idletasks()
            self.window.deiconify()
            self.window.update_idletasks()
            self._show_without_activation()

    def _get_toplevel_hwnd(self):
        """取真正的顶层窗口句柄。

        Tk 在 Windows 上 winfo_id() 返回的是客户区子窗口，
        操作系统层面的顶层窗口是它的祖先（wrapper），
        WS_EX_NOACTIVATE 等样式必须设在 wrapper 上才生效。
        """
        if not self.window:
            return None
        try:
            import ctypes
            hwnd = self.window.winfo_id()
            GA_ROOT = 2
            root = ctypes.windll.user32.GetAncestor(hwnd, GA_ROOT)
            return root or hwnd
        except Exception:
            return None

    def _make_no_activate(self):
        if not self.window:
            return
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            hwnd = self._get_toplevel_hwnd()
            if not hwnd:
                return
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_TOOLWINDOW = 0x00000080
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOZORDER = 0x0004
            SWP_NOACTIVATE = 0x0010
            SWP_FRAMECHANGED = 0x0020

            get_long = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
            set_long = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
            get_long.argtypes = [wintypes.HWND, ctypes.c_int]
            get_long.restype = ctypes.c_void_p
            set_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
            set_long.restype = ctypes.c_void_p

            style = int(get_long(hwnd, GWL_EXSTYLE) or 0)
            style |= WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
            set_long(hwnd, GWL_EXSTYLE, ctypes.c_void_p(style))
            user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED
            )
        except Exception as e:
            print(f"[Popup] no-activate style failed: {e}")

    def _show_without_activation(self):
        if not self.window:
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = self._get_toplevel_hwnd()
            if not hwnd:
                return
            HWND_TOPMOST = -1
            SW_SHOWNOACTIVATE = 4
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040
            self._make_no_activate()
            user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
            user32.SetWindowPos(
                hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )
        except Exception as e:
            print(f"[Popup] show without activation failed: {e}")
            self.window.deiconify()
            self.window.lift()

    # ========== 窗口创建 ==========

    def _create_window(self):
        if self.window:
            return

        self.window = tk.Toplevel()
        self.window.title("剪贴板备忘录")
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        # taste-skill 暖暗色系
        self._bg = "#1c1c1c"
        self._fg = "#ffffff"
        self._accent = "#7eb8ff"
        self._hover_bg = "#2a2a2a"
        self._border = "#333333"
        self._sep = "#2c2c2c"
        self._search_bg = "#161616"
        self._tag_bg = "#262626"
        self._tag_active_bg = "#3a3a3a"
        self._muted = "#777777"
        self._subtle = "#555555"

        self.window.configure(bg=self._bg)

        # 外边框
        container = tk.Frame(self.window, bg=self._border, bd=0,
                             highlightthickness=1, highlightbackground=self._border)
        container.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(container, bg=self._bg, bd=0)
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # ---- 搜索栏 ----
        sf = tk.Frame(inner, bg=self._search_bg)
        sf.pack(fill=tk.X)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._on_search_change())
        self.search_entry = tk.Entry(
            sf, textvariable=self.search_var,
            bg=self._search_bg, fg=self._fg,
            insertbackground="#888888",
            font=("Microsoft YaHei UI", 11),
            relief=tk.FLAT, bd=0, highlightthickness=0
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=12, pady=8)
        self._reset_search_placeholder()

        close_btn = tk.Label(sf, text="Esc", bg=self._search_bg,
                             fg=self._subtle, font=("Segoe UI", 9), cursor="hand2")
        close_btn.pack(side=tk.RIGHT, padx=(0, 10), pady=8)
        close_btn.bind("<Button-1>", lambda e: self.hide())

        # ---- 主标签 ----
        self._tab_frame = tk.Frame(inner, bg=self._bg)
        self._tab_frame.pack(fill=tk.X, padx=8, pady=(6, 2))

        self._tabs = {}
        main_tabs = [
            ("recent", "tab_recent"),
            ("favorite", "tab_favorite"),
            ("prompt", "tab_prompt"),
            ("image", "tab_image"),
            ("deleted", "tab_deleted"),
        ]

        for cat_key, label_key in main_tabs:
            lbl = tk.Label(self._tab_frame, text=t(label_key),
                           bg=self._tag_bg, fg="#999999",
                           font=("Segoe UI", 9), padx=12, pady=4, cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=(0, 5))
            lbl.bind("<Button-1>", lambda e, k=cat_key: self._switch_tab(k))
            lbl.bind("<Enter>", lambda e, w=lbl: w.configure(fg=self._fg, bg="#303030"))
            lbl.bind("<Leave>", lambda e, w=lbl, k=cat_key:
                     w.configure(fg=self._fg if self._current_tab == k else "#999999",
                                 bg=self._tag_active_bg if self._current_tab == k else self._tag_bg))
            self._tabs[cat_key] = lbl

        # ---- 子标签容器（prompt/image 时显示） ----
        self._sub_tab_frame = tk.Frame(inner, bg=self._bg)
        self._sub_tabs = {}

        # ---- 列表区域 ----
        lc = tk.Frame(inner, bg=self._bg)
        lc.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 0))

        self._canvas = tk.Canvas(lc, bg=self._bg, highlightthickness=0)
        self._scrollbar = tk.Scrollbar(lc, orient=tk.VERTICAL)
        self._scrollbar.config(command=self._canvas.yview)
        self._canvas.config(yscrollcommand=self._scrollbar.set)

        self._items_frame = tk.Frame(self._canvas, bg=self._bg)
        self._canvas_id = self._canvas.create_window((0, 0), window=self._items_frame, anchor="nw")

        # Canvas 大小变化 → items_frame 宽度同步
        def _on_canvas_conf(event):
            self._canvas.itemconfig(self._canvas_id, width=event.width)
        self._canvas.bind("<Configure>", _on_canvas_conf)

        # items_frame 大小变化 → 更新滚动区域
        def _on_items_conf(event):
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._items_frame.bind("<Configure>", _on_items_conf)

        # 鼠标滚轮 — 统一在顶层 window 处理
        def _wheel(event):
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self.window.after(80, self._check_scroll_bottom)
        self.window.bind("<MouseWheel>", _wheel)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ---- 底部栏 ----
        bf = tk.Frame(inner, bg=self._bg)
        bf.pack(fill=tk.X, padx=8, pady=(4, 6))

        self._count_label = tk.Label(bf, text="", bg=self._bg,
                                     fg=self._subtle, font=("Segoe UI", 9))
        self._count_label.pack(side=tk.LEFT)

        # 已删除 tab 的清空按钮
        self._clear_deleted_btn = tk.Label(bf, text="", bg=self._bg, fg="#e05555",
                                           font=("Segoe UI", 9), cursor="hand2")
        self._clear_deleted_btn.bind("<Button-1>", lambda e: self._clear_deleted())
        self._clear_deleted_btn.bind("<Enter>", lambda e: self._clear_deleted_btn.configure(fg="#ff6666"))
        self._clear_deleted_btn.bind("<Leave>", lambda e: self._clear_deleted_btn.configure(fg="#e05555"))

        self._quick_cat_btn = tk.Label(bf, text=t("btn_categorize"), bg=self._bg,
                                       fg=self._muted, font=("Segoe UI", 9), cursor="hand2")
        self._quick_cat_btn.pack(side=tk.RIGHT, padx=(12, 0))
        self._quick_cat_btn.bind("<Button-1>", lambda e: self._toggle_quick_categorize())
        self._quick_cat_btn.bind("<Enter>", lambda e: self._qcb_hover(True))
        self._quick_cat_btn.bind("<Leave>", lambda e: self._qcb_hover(False))

        cleanup_btn = tk.Label(bf, text=t("btn_cleanup"), bg=self._bg,
                               fg=self._muted, font=("Segoe UI", 9), cursor="hand2")
        cleanup_btn.pack(side=tk.RIGHT, padx=(12, 0))
        cleanup_btn.bind("<Button-1>", lambda e: self._open_cleanup())
        cleanup_btn.bind("<Enter>", lambda e: cleanup_btn.configure(fg=self._fg))
        cleanup_btn.bind("<Leave>", lambda e: cleanup_btn.configure(fg=self._muted))

        settings_btn = tk.Label(bf, text=t("btn_settings"), bg=self._bg,
                                fg=self._muted, font=("Segoe UI", 9), cursor="hand2")
        settings_btn.pack(side=tk.RIGHT, padx=(12, 0))
        settings_btn.bind("<Button-1>", lambda e: self._open_settings())
        settings_btn.bind("<Enter>", lambda e: settings_btn.configure(fg=self._fg))
        settings_btn.bind("<Leave>", lambda e: settings_btn.configure(fg=self._muted))

        # ---- 右下角缩放手柄（taste-skill: subtle diagonal lines） ----
        grip_size = 14
        self._grip = tk.Canvas(inner, bg=self._bg, highlightthickness=0,
                               width=grip_size, height=grip_size, cursor="bottom_right_corner")
        self._grip.place(relx=1.0, rely=1.0, x=-grip_size-4, y=-grip_size-4, anchor="nw")
        # 画三条对角线（极 subtle）
        for i in range(3):
            x = grip_size - 3 - i * 5
            self._grip.create_line(x, grip_size-2, grip_size-2, x,
                                   fill="#444444", width=1)
        self._grip.bind("<Enter>", lambda e: self._grip.configure(bg="#2a2a2a"))
        self._grip.bind("<Leave>", lambda e: self._grip.configure(bg=self._bg))
        self._grip.bind("<Button-1>", self._resize_start)
        self._grip.bind("<B1-Motion>", self._resize_drag)

        # ---- 键盘 ----
        self.window.bind("<Escape>", lambda e: self.hide())
        self.window.bind("<Up>", lambda e: self._navigate(-1))
        self.window.bind("<Down>", lambda e: self._navigate(1))
        self.window.bind("<Return>", lambda e: self._paste_selected())
        self.window.bind("<KP_Enter>", lambda e: self._paste_selected())
        self.window.bind("<FocusOut>", self._on_focus_out)

        self._popup_width = get_config("popup_width", 380)
        self._popup_max_height = get_config("popup_max_height", 500)
        self.window.geometry(f"{self._popup_width}x{self._popup_max_height}")

        # 窗口一创建就设 NOACTIVATE，避免初次显示瞬间抢走目标窗口焦点
        self.window.update_idletasks()
        self._make_no_activate()

    def _reset_search_placeholder(self):
        lang = get_language()
        placeholder = t("search_placeholder", lang)
        self.search_var.set(placeholder)
        self.search_entry.config(fg="#666666")
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)

    # ========== 定位 ==========

    def _position_at_center(self):
        if not self.window:
            return
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        if w < 100:
            w = self._popup_width
        if h < 100:
            h = self._popup_max_height
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        self.window.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _position_at_cursor(self):
        if not self.window:
            return
        win_w = self.window.winfo_width()
        win_h = self.window.winfo_height()
        if win_w < 100:
            win_w = self._popup_width
        if win_h < 100:
            win_h = self._popup_max_height

        try:
            import ctypes
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            cx, cy = pt.x, pt.y
        except Exception:
            cx = self.window.winfo_screenwidth() // 2
            cy = self.window.winfo_screenheight() // 2

        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        margin, offset = 12, 6

        x = cx
        y = cy + offset

        if x + win_w > sw - margin:
            x = cx - win_w
        if x < margin:
            x = margin
        if y + win_h > sh - margin:
            y = cy - win_h - offset
        if y < margin:
            y = margin

        self.window.geometry(f"+{x}+{y}")

    # ========== Tab 切换 ==========

    def _switch_tab(self, tab):
        self._current_tab = tab
        self._current_subcategory = None
        self._update_tab_styles()
        self._update_sub_tabs()
        self._force_refresh = True
        self._refresh_items()

    def _switch_sub(self, sub_key):
        self._current_subcategory = sub_key
        self._update_sub_tabs()
        self._force_refresh = True
        self._refresh_items()

    def _update_tab_styles(self):
        for key, lbl in self._tabs.items():
            if key == self._current_tab:
                lbl.configure(bg=self._tag_active_bg, fg=self._fg)
            else:
                lbl.configure(bg=self._tag_bg, fg="#999999")

    def _update_sub_tabs(self):
        for w in self._sub_tab_frame.winfo_children():
            w.destroy()
        self._sub_tabs = {}

        if self._current_tab not in ("prompt", "image"):
            self._sub_tab_frame.pack_forget()
            return

        self._sub_tab_frame.pack(fill=tk.X, padx=8, pady=(2, 4), before=self._canvas.master)

        # "全部" 按钮
        all_key = None
        all_lbl = tk.Label(self._sub_tab_frame, text=t("sub_all"),
                           bg=self._tag_bg, fg="#999999",
                           font=("Segoe UI", 8), padx=10, pady=2, cursor="hand2")
        all_lbl.pack(side=tk.LEFT, padx=(0, 4))
        all_lbl.bind("<Button-1>", lambda e: self._switch_sub(None))
        all_lbl.bind("<Enter>", lambda e, w=all_lbl: w.configure(fg=self._fg, bg="#303030"))
        self._sub_tabs[None] = all_lbl

        # 子分类 1-4（前面加数字）
        for i in range(1, 5):
            sc_key = f"{self._current_tab}_sub{i}"
            name = get_subcategory_name(sc_key)
            lbl = tk.Label(self._sub_tab_frame, text=f"{i}{name}",
                           bg=self._tag_bg, fg="#999999",
                           font=("Segoe UI", 8), padx=10, pady=2, cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=(0, 4))
            lbl.bind("<Button-1>", lambda e, k=sc_key: self._switch_sub(k))
            lbl.bind("<Enter>", lambda e, w=lbl: w.configure(fg=self._fg, bg="#303030"))
            self._sub_tabs[sc_key] = lbl

        self._update_sub_tab_styles()

    def _update_sub_tab_styles(self):
        for key, lbl in self._sub_tabs.items():
            if key == self._current_subcategory:
                lbl.configure(bg=self._tag_active_bg, fg=self._fg)
            else:
                lbl.configure(bg=self._tag_bg, fg="#999999")

    # ========== 列表刷新 ==========

    def _refresh_items(self):
        self._dirty = False
        self._force_refresh = False

        # 获取数据
        tab = self._current_tab
        category = None
        subcategory = None
        if tab == "prompt":
            category = "prompt"
            subcategory = self._current_subcategory
        elif tab == "image":
            category = "image"
            subcategory = self._current_subcategory

        search = self._search_text if self._search_text else None

        items = self.storage.get_items(
            category=category, subcategory=subcategory,
            search=search, limit=200, tab=tab
        )

        # 数据签名检查：如果数据没变，跳过重建
        sig = tuple(i["id"] for i in items)
        if self._last_sig == sig and self._item_widgets:
            self._update_footer(len(items), tab)
            return
        self._last_sig = sig
        self._all_items = items
        self._rendered_count = 0

        # 清除旧 widget
        for w in self._items_frame.winfo_children():
            w.destroy()
        self._item_widgets = []

        self._update_footer(len(items), tab)

        if not items:
            empty_text = t("empty_recent") if tab != "deleted" else t("empty_deleted")
            tk.Label(self._items_frame, text=f"{empty_text}\n{t('empty_hint')}",
                     bg=self._bg, fg=self._subtle,
                     font=("Segoe UI", 10), justify=tk.CENTER).pack(pady=40)
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
            return

        self._selected_index = -1
        # 分批渲染：先渲染前 30 条，滚动时加载更多
        self._render_batch(30)
        self._canvas.yview_moveto(0)

    def _render_batch(self, count):
        """渲染下一批条目"""
        if not self._all_items:
            return
        start = self._rendered_count
        end = min(start + count, len(self._all_items))
        for i in range(start, end):
            self._create_item_widget(self._all_items[i])
        self._rendered_count = end
        self._items_frame.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _check_scroll_bottom(self):
        """检查是否滚动到底部，需要加载更多"""
        if not hasattr(self, '_all_items') or self._rendered_count >= len(self._all_items):
            return
        y1 = self._canvas.canvasy(0)
        y2 = y1 + self._canvas.winfo_height()
        bbox = self._canvas.bbox("all")
        if bbox and y2 >= bbox[3] - 120:
            self._render_batch(20)

    def _update_footer(self, filtered_count, tab):
        """更新底部计数和按钮"""
        # recent 且无搜索/子分类时才查总数
        if tab == "recent" and not self._search_text and not self._current_subcategory:
            total = self.storage.get_item_count(tab="recent")
            self._count_label.config(text=f"{total} items")
        else:
            self._count_label.config(text=f"{filtered_count} items")

    def _create_item_widget(self, item, insert_at_top=False):
        item_id = item["id"]
        content_type = item["content_type"]
        category = item["category"]
        is_favorite = bool(item["is_favorite"])
        summary = item["summary"] or ""
        text_content = item["text_content"] or ""
        image_path = item["image_path"] or ""
        created_at = item["created_at"] or ""
        deleted = bool(item["deleted"])

        preview = summary if summary else truncate_text(text_content, 40)
        time_str = format_time(created_at)

        # 主容器 frame（减少嵌套层级，提升渲染速度）
        frame = tk.Frame(self._items_frame, bg=self._bg, cursor="hand2")
        if insert_at_top and self._item_widgets:
            first_frame = self._item_widgets[0][0]
            frame.pack(fill=tk.X, padx=6, pady=(1, 0), before=first_frame)
        else:
            frame.pack(fill=tk.X, padx=6, pady=(1, 0))

        hoverables = [frame]

        # 图片缩略图（直接放在 frame 里）
        thumb_lbl = None
        if content_type == "image" and image_path and os.path.exists(image_path):
            try:
                photo = self._get_thumbnail(image_path)
                if photo:
                    thumb_lbl = tk.Label(frame, image=photo, bg=self._bg)
                    thumb_lbl.image = photo
                    thumb_lbl.pack(side=tk.LEFT, padx=(6, 6), pady=2)
                    hoverables.append(thumb_lbl)
            except Exception:
                pass

        # ---- 右侧操作按钮（先 pack 保证右对齐） ----
        right_frame = tk.Frame(frame, bg=self._bg)
        right_frame.pack(side=tk.RIGHT, padx=(0, 6), pady=8)
        hoverables.append(right_frame)

        if deleted:
            restore_btn = tk.Label(right_frame, text=t("btn_restore"), bg=self._bg,
                                   fg=self._accent, font=("Segoe UI", 8), cursor="hand2")
            restore_btn.pack(side=tk.RIGHT, padx=(6, 0))
            restore_btn.bind("<Button-1>", lambda e, iid=item_id: self._restore_item(iid))
            hoverables.append(restore_btn)
        else:
            # 📖 分类状态标识（taste-skill: 已分类或已收藏时 accent 色，未分类暗淡）
            cat_fg = self._accent if (category != "other_text" or is_favorite) else "#555555"
            cat_lbl = tk.Label(right_frame, text="📖", bg=self._bg,
                               fg=cat_fg, font=("Segoe UI", 10))
            cat_lbl.pack(side=tk.RIGHT, padx=(8, 0))
            hoverables.append(cat_lbl)
            frame._cat_lbl = cat_lbl

            # ⭐️/☆ 收藏标识
            pin_text = "⭐️" if is_favorite else "☆"
            pin_fg = "#f0c040" if is_favorite else "#555555"
            pin_lbl = tk.Label(right_frame, text=pin_text, bg=self._bg,
                               fg=pin_fg, font=("Segoe UI", 12))
            pin_lbl.pack(side=tk.RIGHT, padx=(4, 0))
            pin_lbl.bind("<Button-1>", lambda e, iid=item_id: self._toggle_favorite(iid))
            hoverables.append(pin_lbl)
            frame._pin_lbl = pin_lbl

            # [编辑] 标题按钮
            edit_lbl = tk.Label(right_frame, text="[编辑]", bg=self._bg,
                                fg="#555555", font=("Segoe UI", 8), cursor="hand2")
            edit_lbl.pack(side=tk.RIGHT, padx=(2, 0))
            edit_lbl.bind("<Button-1>", lambda e, iid=item_id, f=frame: self._inline_edit(iid, f))
            edit_lbl.bind("<Enter>", lambda e, w=edit_lbl: w.configure(fg="#aaaaaa"))
            edit_lbl.bind("<Leave>", lambda e, w=edit_lbl: w.configure(fg="#555555"))
            hoverables.append(edit_lbl)
            frame._edit_lbl = edit_lbl

        # ---- 主内容区 ----
        content_frame = tk.Frame(frame, bg=self._bg)
        content_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=7)
        hoverables.append(content_frame)

        preview_lbl = tk.Label(content_frame, text=preview, bg=self._bg,
                               fg=self._fg, font=("Microsoft YaHei UI", 10),
                               anchor="w", justify=tk.LEFT)
        preview_lbl.pack(fill=tk.X)
        hoverables.append(preview_lbl)

        time_lbl = tk.Label(content_frame, text=time_str, bg=self._bg,
                            fg="#666666", font=("Segoe UI", 8), anchor="w")
        time_lbl.pack(fill=tk.X, pady=(1, 0))
        hoverables.append(time_lbl)

        # 存引用给内联编辑用
        content_frame._data = {"preview_lbl": preview_lbl, "item": item,
                                "preview": preview, "time_str": time_str}

        # 事件绑定（frame + 内容区子组件，不包括右侧操作按钮）
        handlers = [
            ("<Enter>", lambda e, iid=item_id, hov=hoverables: self._on_item_enter(iid, hov)),
            ("<Leave>", lambda e, hov=hoverables: self._on_item_leave(hov)),
            ("<Button-1>", lambda e, iid=item_id: self._paste_item(iid)),
            ("<Button-2>", lambda e, iid=item_id: self._show_context_menu(e, iid)),
            ("<Button-3>", lambda e, iid=item_id: self._show_context_menu(e, iid)),
        ]
        for w in [frame, content_frame, preview_lbl, time_lbl]:
            for evt, handler in handlers:
                w.bind(evt, handler)
        if thumb_lbl:
            for evt, handler in handlers:
                thumb_lbl.bind(evt, handler)

        if insert_at_top:
            self._item_widgets.insert(0, (frame, item, hoverables))
        else:
            self._item_widgets.append((frame, item, hoverables))

    def _get_thumbnail(self, image_path):
        """获取缩略图（带 LRU 缓存）"""
        if image_path in self._thumbnails:
            # 移动到末尾（最近使用）
            self._thumbnails.move_to_end(image_path)
            return self._thumbnails[image_path]
        try:
            img = PILImage.open(image_path)
            img.thumbnail((self.THUMB_SIZE, self.THUMB_SIZE), PILImage.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._thumbnails[image_path] = photo
            # 淘汰旧缓存
            while len(self._thumbnails) > self.THUMB_CACHE_MAX:
                self._thumbnails.popitem(last=False)
            return photo
        except Exception:
            return None

    # ========== 交互 ==========

    def _on_item_enter(self, item_id, hoverables):
        self._hovered_item_id = item_id
        for w in hoverables:
            try:
                w.configure(bg=self._hover_bg)
            except Exception:
                pass

    def _on_item_leave(self, hoverables):
        self._hovered_item_id = None
        for w in hoverables:
            try:
                w.configure(bg=self._bg)
            except Exception:
                pass

    def _paste_item(self, item_id):
        item = self.storage.get_item_by_id(item_id)
        if not item or item.get("deleted"):
            return

        paste_text = None
        if item["content_type"] == "text" and item["text_content"]:
            paste_text = item["text_content"]
            self._copy_to_clipboard(paste_text)
        elif item["content_type"] == "image" and item["image_path"]:
            self._copy_image_to_clipboard(item["image_path"])

        self.storage.mark_used(item_id)

        target_hwnd = self._paste_target_hwnd
        focus_hwnd = self._paste_focus_hwnd
        self.hide()
        self.window.after(
            180,
            lambda hwnd=target_hwnd, focus=focus_hwnd, text=paste_text: self._simulate_paste(hwnd, focus, text)
        )

    def _paste_selected(self):
        if 0 <= self._selected_index < len(self._item_widgets):
            _, item, _ = self._item_widgets[self._selected_index]
            self._paste_item(item["id"])

    def _navigate(self, direction):
        if not self._item_widgets:
            return
        # 清除旧选中
        if 0 <= self._selected_index < len(self._item_widgets):
            _, _, hoverables = self._item_widgets[self._selected_index]
            for w in hoverables:
                try:
                    w.configure(bg=self._bg)
                except Exception:
                    pass

        self._selected_index += direction
        self._selected_index = max(0, min(self._selected_index, len(self._item_widgets) - 1))

        frame, _, hoverables = self._item_widgets[self._selected_index]
        for w in hoverables:
            try:
                w.configure(bg=self._hover_bg)
            except Exception:
                pass

        # 滚动到可见
        fy = frame.winfo_y()
        cy = self._canvas.canvasy(0)
        fh = frame.winfo_height()
        ch = self._canvas.winfo_height()
        if fy < cy:
            self._canvas.yview_moveto(fy / self._items_frame.winfo_height())
        elif fy + fh > cy + ch:
            self._canvas.yview_moveto((fy + fh - ch) / self._items_frame.winfo_height())

    def _update_item_status(self, item_id):
        """只更新指定条目的状态标识（收藏⭐️ + 分类📖），避免全量刷新"""
        for idx, (frame, item, hoverables) in enumerate(self._item_widgets):
            if item["id"] == item_id:
                new_item = self.storage.get_item_by_id(item_id)
                if not new_item:
                    return
                self._item_widgets[idx] = (frame, new_item, hoverables)

                cat_lbl = getattr(frame, '_cat_lbl', None)
                pin_lbl = getattr(frame, '_pin_lbl', None)

                category = new_item.get("category", "other_text")
                is_favorite = bool(new_item.get("is_favorite"))

                if cat_lbl:
                    cat_lbl.config(fg=self._accent if (category != "other_text" or is_favorite) else "#555555")

                if pin_lbl:
                    pin_lbl.config(text="⭐️" if is_favorite else "☆",
                                   fg="#f0c040" if is_favorite else "#555555")
                return

    def _toggle_favorite(self, item_id):
        self.storage.toggle_favorite(item_id)
        # 如果在收藏 tab 取消收藏，条目需要消失，全量刷新
        item = self.storage.get_item_by_id(item_id)
        if item and self._current_tab == "favorite" and not item.get("is_favorite"):
            self._force_refresh = True
            self._refresh_items()
        else:
            self._update_item_status(item_id)

    def _restore_item(self, item_id):
        self.storage.restore_items(item_id)
        self._force_refresh = True
        self._refresh_items()

    def _clear_deleted(self):
        if messagebox.askyesno(t("btn_clear_deleted"), t("confirm_clear")):
            n = self.storage.clear_all_deleted()
            self._dirty = True
            self._force_refresh = True
            self._refresh_items()

    # ========== 快速分类 ==========

    def _activate_popup(self):
        """显式让弹窗拿键盘焦点。

        NOACTIVATE 样式只阻止点击激活，程序主动激活仍然允许。
        分类模式需要接收数字键，必须先把焦点拿过来，
        否则按键会落进后面目标应用的输入框。
        """
        if not self.window:
            return
        try:
            import ctypes
            hwnd = self._get_toplevel_hwnd()
            if hwnd:
                self._tap_alt_for_foreground_permission()
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        try:
            self.window.focus_force()
        except Exception:
            pass

    def _toggle_quick_categorize(self):
        self._quick_categorize_mode = not self._quick_categorize_mode
        self._update_quick_categorize_ui()

    def _update_quick_categorize_ui(self, focus_search=True):
        if not self.window:
            return
        if self._quick_categorize_mode:
            self._quick_cat_btn.configure(text=t("btn_categorizing"), fg=self._accent)
            self.search_entry.configure(state="disabled")
            self.search_var.set(t("categorize_hint"))
            self.search_entry.config(fg=self._subtle)
            self._search_text = ""
            self._bind_quick_categorize_keys()
            self._hide_edit_buttons()
            self._force_refresh = True
            self._refresh_items()
            self._activate_popup()
        else:
            self._quick_cat_btn.configure(text=t("btn_categorize"), fg=self._muted)
            self.search_entry.configure(state="normal")
            self._unbind_quick_categorize_keys()
            self._show_edit_buttons()
            self._reset_search_placeholder()
            if focus_search:
                self._focus_search()

    def _hide_edit_buttons(self):
        """分类模式下隐藏所有条目的编辑按钮"""
        for frame, _, _ in self._item_widgets:
            edit_lbl = getattr(frame, '_edit_lbl', None)
            if edit_lbl:
                edit_lbl.pack_forget()

    def _show_edit_buttons(self):
        """退出分类模式后恢复编辑按钮显示"""
        for frame, _, _ in self._item_widgets:
            edit_lbl = getattr(frame, '_edit_lbl', None)
            if edit_lbl:
                edit_lbl.pack(side=tk.RIGHT, padx=(2, 0))

    def _bind_quick_categorize_keys(self):
        for i in range(1, 5):
            self.window.bind(f"<KeyPress-{i}>", lambda e, n=i: self._quick_categorize(n))
        self.window.bind("<BackSpace>", lambda e: self._quick_delete())
        self.window.bind("<Delete>", lambda e: self._quick_delete())

    def _unbind_quick_categorize_keys(self):
        for i in range(1, 5):
            self.window.unbind(f"<KeyPress-{i}>")
        self.window.unbind("<BackSpace>")
        self.window.unbind("<Delete>")

    def _quick_delete(self):
        """快速删除当前悬停的条目（分类模式下 Backspace/Delete）"""
        if not self._quick_categorize_mode or self._hovered_item_id is None:
            return
        self.storage.soft_delete(self._hovered_item_id)
        self._force_refresh = True
        self._refresh_items()

    def _quick_categorize(self, key_num):
        """快速分类模式：数字键 1-4 映射
        - prompt/image tab: 1-4 对应子分类1-4
        - 其他 tab: 1收藏 2Prompt 3图片 4删除
        操作后只刷新单条状态（软删除除外）
        """
        if not self._quick_categorize_mode or self._hovered_item_id is None:
            return

        item_id = self._hovered_item_id
        tab = self._current_tab

        if tab == "prompt":
            sub_key = f"prompt_sub{key_num}"
            self.storage.set_subcategory(item_id, sub_key)
            self.storage.set_category(item_id, "prompt")
            name = get_subcategory_name(sub_key)
            print(f"[快速分类] {item_id} -> Prompt/{name}")
            self._update_item_status(item_id)
        elif tab == "image":
            sub_key = f"image_sub{key_num}"
            self.storage.set_subcategory(item_id, sub_key)
            self.storage.set_category(item_id, "image")
            name = get_subcategory_name(sub_key)
            print(f"[快速分类] {item_id} -> Image/{name}")
            self._update_item_status(item_id)
        else:
            # 大分类映射: 1收藏 2Prompt 3图片 4删除
            if key_num == 1:
                self.storage.toggle_favorite(item_id)
                item = self.storage.get_item_by_id(item_id)
                if item and tab == "favorite" and not item.get("is_favorite"):
                    # 在收藏 tab 取消收藏，条目消失，全量刷新
                    self._force_refresh = True
                    self._refresh_items()
                    return
                self._update_item_status(item_id)
            elif key_num == 2:
                self.storage.set_category(item_id, "prompt")
                self._update_item_status(item_id)
            elif key_num == 3:
                self.storage.set_category(item_id, "image")
                self._update_item_status(item_id)
            elif key_num == 4:
                self.storage.soft_delete(item_id)
                self._force_refresh = True
                self._refresh_items()

    # ========== 搜索 ==========

    def _on_search_focus_in(self, event):
        lang = get_language()
        if self.search_var.get() == t("search_placeholder", lang):
            self.search_var.set("")
            self.search_entry.config(fg=self._fg)

    def _on_search_focus_out(self, event):
        if not self.search_var.get().strip():
            self._reset_search_placeholder()

    def _on_search_change(self):
        raw = self.search_var.get()
        lang = get_language()
        if raw == t("search_placeholder", lang):
            self._search_text = ""
        else:
            self._search_text = raw.strip()
        if hasattr(self, '_search_after_id'):
            self.window.after_cancel(self._search_after_id)
        self._search_after_id = self.window.after(150, self._do_search_refresh)

    def _do_search_refresh(self):
        self._force_refresh = True
        self._refresh_items()

    def _focus_search(self):
        if hasattr(self, 'search_entry') and self.search_entry.winfo_exists():
            self.search_entry.focus_set()
            lang = get_language()
            if self.search_var.get() == t("search_placeholder", lang):
                self.search_var.set("")
                self.search_entry.config(fg=self._fg)

    # ========== 窗口缩放 ==========

    def _resize_start(self, event):
        self._resize_x = event.x_root
        self._resize_y = event.y_root
        self._resize_w = self.window.winfo_width()
        self._resize_h = self.window.winfo_height()

    def _resize_drag(self, event):
        dx = event.x_root - self._resize_x
        dy = event.y_root - self._resize_y
        new_w = max(300, self._resize_w + dx)
        new_h = max(200, self._resize_h + dy)
        self.window.geometry(f"{new_w}x{new_h}")

    # ========== 失焦 ==========

    def _start_outside_click_watch(self):
        """NOACTIVATE 窗口收不到 FocusOut，改为轮询检测窗口外的鼠标按下来关闭弹窗"""
        self._outside_watch_on = True
        self._outside_btn_was_down = True  # 先视为按下，跳过呼出弹窗那一次点击
        self._poll_outside_click()

    def _poll_outside_click(self):
        if not getattr(self, "_outside_watch_on", False) or not self._visible or not self.window:
            return
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            down = bool(user32.GetAsyncKeyState(0x01) & 0x8000) or \
                   bool(user32.GetAsyncKeyState(0x02) & 0x8000)
            if down and not self._outside_btn_was_down:
                pt = wintypes.POINT()
                rect = wintypes.RECT()
                hwnd = self._get_toplevel_hwnd()
                if hwnd and user32.GetCursorPos(ctypes.byref(pt)) and \
                        user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    if not (rect.left <= pt.x <= rect.right and rect.top <= pt.y <= rect.bottom):
                        self.hide()
                        return
            self._outside_btn_was_down = down
        except Exception:
            pass
        self.window.after(120, self._poll_outside_click)

    def _on_focus_out(self, event):
        if self.window:
            self.window.after(100, self._check_focus)

    def _check_focus(self):
        if not self.window or not self._visible:
            return
        try:
            focused = self.window.focus_get()
            if focused is None or not str(focused).startswith(str(self.window)):
                self.hide()
        except Exception:
            pass

    # ========== 右键菜单 ==========

    def _show_context_menu(self, event, item_id):
        menu = tk.Menu(self.window, tearoff=0, bg="#333333", fg=self._fg,
                       activebackground="#444444", activeforeground="#ffffff")
        menu.add_command(label=t("btn_restore") if self._current_tab == "deleted" else "Copy only",
                         command=lambda: self._copy_only(item_id))
        menu.add_command(label="Toggle save", command=lambda: self._toggle_favorite(item_id))
        if self._current_tab != "deleted":
            menu.add_command(label="Edit title", command=lambda: self._edit_title(item_id))
        menu.add_separator()
        menu.add_command(label="Delete", command=lambda: self._delete_item(item_id))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_only(self, item_id):
        item = self.storage.get_item_by_id(item_id)
        if not item or item.get("deleted"):
            return
        if item["content_type"] == "text" and item["text_content"]:
            self._copy_to_clipboard(item["text_content"])
            self.storage.mark_used(item_id)

    def _inline_edit(self, item_id, frame):
        """内联编辑标题：点击 [编辑] 后原地变为输入框"""
        # 找到 content_frame（frame 中最后一个 Frame 子组件）
        content_frame = None
        for c in reversed(frame.winfo_children()):
            if isinstance(c, tk.Frame):
                content_frame = c
                break
        if not content_frame or not hasattr(content_frame, '_data'):
            return

        data = content_frame._data
        item = data["item"]
        current = item["summary"] or truncate_text(item["text_content"] or "", 40)

        # 清除原内容，替换为输入框
        for w in content_frame.winfo_children():
            w.destroy()

        entry = tk.Entry(content_frame, bg="#2a2a2a", fg=self._fg,
                         insertbackground=self._fg,
                         font=("Microsoft YaHei UI", 10),
                         relief=tk.FLAT, bd=0, highlightthickness=0)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.insert(0, current)
        entry.select_range(0, tk.END)
        entry.focus_set()

        # 确认/取消按钮
        btn_frame = tk.Frame(content_frame, bg=self._bg)
        btn_frame.pack(side=tk.RIGHT, padx=(4, 0))

        def _confirm():
            new_title = entry.get().strip()
            if new_title:
                self.storage.update_summary(item_id, new_title)
                item["summary"] = new_title
                self._dirty = True
            # 恢复显示
            preview = item["summary"] or truncate_text(item["text_content"] or "", 40)
            self._build_item_content(content_frame, item, preview, data["time_str"])

        def _cancel():
            self._build_item_content(content_frame, item, data["preview"], data["time_str"])

        check = tk.Label(btn_frame, text="[确认]", bg=self._bg, fg="#5f5",
                         font=("Segoe UI", 8), cursor="hand2")
        check.pack(side=tk.LEFT, padx=(0, 6))
        check.bind("<Button-1>", lambda e: _confirm())

        cross = tk.Label(btn_frame, text="[取消]", bg=self._bg, fg="#f55",
                         font=("Segoe UI", 8), cursor="hand2")
        cross.pack(side=tk.LEFT)
        cross.bind("<Button-1>", lambda e: _cancel())

        entry.bind("<Return>", lambda e: _confirm())
        entry.bind("<Escape>", lambda e: _cancel())

    def _build_item_content(self, parent, item, preview, time_str):
        """构建条目正文（可被内联编辑替换）"""
        # 清除旧内容
        for w in parent.winfo_children():
            w.destroy()

        preview_lbl = tk.Label(parent, text=preview, bg=self._bg,
                               fg=self._fg, font=("Microsoft YaHei UI", 10),
                               anchor="w", justify=tk.LEFT)
        preview_lbl.pack(fill=tk.X)

        time_lbl = tk.Label(parent, text=time_str, bg=self._bg,
                            fg="#666666", font=("Segoe UI", 8), anchor="w")
        time_lbl.pack(fill=tk.X, pady=(1, 0))

        # 存引用给内联编辑用
        parent._data = {"preview_lbl": preview_lbl, "item": item,
                        "preview": preview, "time_str": time_str}

    def _edit_title(self, item_id):
        """兼容右键菜单的编辑标题入口"""
        for f, item, _ in self._item_widgets:
            if item["id"] == item_id:
                self._inline_edit(item_id, f)
                return

    def _delete_item(self, item_id):
        self.storage.soft_delete(item_id)
        self._dirty = True
        self._force_refresh = True
        self._refresh_items()

    # ========== 剪贴板操作 ==========

    def _copy_to_clipboard(self, text):
        try:
            import html
            import time
            import win32clipboard
            import win32con

            def build_cf_html(value):
                body = html.escape(value).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
                start_marker = "<!--StartFragment-->"
                end_marker = "<!--EndFragment-->"
                fragment = f"{start_marker}{body}{end_marker}"
                document = f"<html><body>{fragment}</body></html>"
                header_template = (
                    "Version:0.9\r\n"
                    "StartHTML:{start_html:010d}\r\n"
                    "EndHTML:{end_html:010d}\r\n"
                    "StartFragment:{start_fragment:010d}\r\n"
                    "EndFragment:{end_fragment:010d}\r\n"
                )
                empty_header = header_template.format(
                    start_html=0, end_html=0, start_fragment=0, end_fragment=0
                )
                start_html = len(empty_header.encode("utf-8"))
                prefix = document[:document.index(start_marker) + len(start_marker)]
                start_fragment = start_html + len(prefix.encode("utf-8"))
                end_fragment = start_fragment + len(body.encode("utf-8"))
                end_html = start_html + len(document.encode("utf-8"))
                header = header_template.format(
                    start_html=start_html,
                    end_html=end_html,
                    start_fragment=start_fragment,
                    end_fragment=end_fragment,
                )
                return (header + document).encode("utf-8")

            for _ in range(5):
                try:
                    win32clipboard.OpenClipboard()
                    break
                except Exception:
                    time.sleep(0.03)
            else:
                print("[Clipboard] OpenClipboard failed")
                return

            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
                try:
                    win32clipboard.SetClipboardData(win32con.CF_TEXT, text.encode("mbcs", errors="replace"))
                except Exception:
                    pass
                try:
                    cf_html = win32clipboard.RegisterClipboardFormat("HTML Format")
                    win32clipboard.SetClipboardData(cf_html, build_cf_html(text))
                except Exception:
                    pass
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"[Clipboard] copy failed: {e}")

    def _copy_image_to_clipboard(self, image_path):
        try:
            from PIL import Image as PILImg
            import io
            import win32clipboard
            import win32con

            img = PILImg.open(image_path)
            if img.mode == "RGBA":
                bg = PILImg.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")

            output = io.BytesIO()
            img.save(output, format="BMP")
            dib = output.getvalue()[14:]

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_DIB, dib)
            win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"[Clipboard] image copy failed: {e}")

    def _get_foreground_hwnd(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if hwnd and (not self.window or hwnd != self.window.winfo_id()):
                return hwnd
        except Exception:
            pass
        return None

    def _get_focused_hwnd(self, hwnd=None):
        try:
            import ctypes
            from ctypes import wintypes

            class GUITHREADINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("flags", wintypes.DWORD),
                    ("hwndActive", wintypes.HWND),
                    ("hwndFocus", wintypes.HWND),
                    ("hwndCapture", wintypes.HWND),
                    ("hwndMenuOwner", wintypes.HWND),
                    ("hwndMoveSize", wintypes.HWND),
                    ("hwndCaret", wintypes.HWND),
                    ("rcCaret", wintypes.RECT),
                ]

            hwnd = hwnd or self._paste_target_hwnd or ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return None
            thread_id = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
            info = GUITHREADINFO()
            info.cbSize = ctypes.sizeof(GUITHREADINFO)
            if ctypes.windll.user32.GetGUIThreadInfo(thread_id, ctypes.byref(info)):
                return info.hwndFocus or info.hwndCaret or info.hwndActive
        except Exception:
            pass
        return None

    def _tap_alt_for_foreground_permission(self):
        try:
            import win32api
            import win32con
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        except Exception:
            pass

    def _restore_paste_target(self, hwnd, focus_hwnd=None):
        if not hwnd:
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            if not user32.IsWindow(hwnd):
                return
            attached = False
            focus_target = focus_hwnd if focus_hwnd and user32.IsWindow(focus_hwnd) else hwnd
            target_thread = user32.GetWindowThreadProcessId(focus_target, None)
            current_thread = kernel32.GetCurrentThreadId()
            try:
                if target_thread and target_thread != current_thread:
                    attached = bool(user32.AttachThreadInput(current_thread, target_thread, True))
                self._tap_alt_for_foreground_permission()
                user32.ShowWindow(hwnd, 9)
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
                user32.SetActiveWindow(hwnd)
                user32.SetFocus(focus_target)
            finally:
                if attached:
                    user32.AttachThreadInput(current_thread, target_thread, False)
        except Exception as e:
            print(f"[Paste] restore focus failed: {e}")

    def _should_type_text_directly(self, text):
        if not text:
            return False
        if not get_config("unicode_text_paste", True):
            return False
        max_chars = int(get_config("unicode_text_paste_max_chars", 2000) or 0)
        return max_chars <= 0 or len(text) <= max_chars

    def _type_text_unicode(self, text):
        try:
            import ctypes
            from ctypes import wintypes

            INPUT_KEYBOARD = 1
            KEYEVENTF_KEYUP = 0x0002
            KEYEVENTF_UNICODE = 0x0004
            ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", wintypes.WORD),
                    ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ULONG_PTR),
                ]

            class INPUT_UNION(ctypes.Union):
                _fields_ = [("ki", KEYBDINPUT)]

            class INPUT(ctypes.Structure):
                _fields_ = [("type", wintypes.DWORD), ("u", INPUT_UNION)]

            units = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r").encode("utf-16-le")
            codes = [units[i] | (units[i + 1] << 8) for i in range(0, len(units), 2)]

            for start in range(0, len(codes), 64):
                chunk = codes[start:start + 64]
                inputs = (INPUT * (len(chunk) * 2))()
                idx = 0
                for code in chunk:
                    inputs[idx].type = INPUT_KEYBOARD
                    inputs[idx].u.ki.wScan = code
                    inputs[idx].u.ki.dwFlags = KEYEVENTF_UNICODE
                    idx += 1
                    inputs[idx].type = INPUT_KEYBOARD
                    inputs[idx].u.ki.wScan = code
                    inputs[idx].u.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
                    idx += 1
                sent = ctypes.windll.user32.SendInput(len(inputs), inputs, ctypes.sizeof(INPUT))
                if sent != len(inputs):
                    print(f"[Paste] unicode typing partial: {sent}/{len(inputs)}")
                    return False
            return True
        except Exception as e:
            print(f"[Paste] unicode typing failed: {e}")
            return False

    def _simulate_paste(self, target_hwnd=None, focus_hwnd=None, direct_text=None):
        """Simulate Ctrl+V into the window that was active before the popup."""
        try:
            import time

            try:
                import ctypes
                current_hwnd = ctypes.windll.user32.GetForegroundWindow()
            except Exception:
                current_hwnd = None
            if target_hwnd and current_hwnd != target_hwnd:
                self._restore_paste_target(target_hwnd, focus_hwnd)
            time.sleep(0.12)
            if self._should_type_text_directly(direct_text):
                if self._type_text_unicode(direct_text):
                    return
            self._simulate_paste_keybd_event()
        except Exception as e:
            print(f"[Paste] failed: {e}")
            self._simulate_paste_sendinput()

    def _simulate_paste_sendinput(self):
        try:
            import ctypes
            from ctypes import wintypes
            INPUT_KEYBOARD = 1
            KEYEVENTF_KEYUP = 0x0002
            KEYEVENTF_SCANCODE = 0x0008
            ULONG_PTR = wintypes.WPARAM

            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", wintypes.WORD),
                    ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ULONG_PTR),
                ]

            class INPUT_UNION(ctypes.Union):
                _fields_ = [("ki", KEYBDINPUT)]

            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("u", INPUT_UNION),
                ]

            # Ctrl down, V down, V up, Ctrl up using scan codes.
            keys = [
                (0x1D, 0),
                (0x2F, 0),
                (0x2F, KEYEVENTF_KEYUP),
                (0x1D, KEYEVENTF_KEYUP),
            ]

            def _send(idx):
                if idx >= len(keys):
                    return
                scan, flags = keys[idx]
                inp = INPUT()
                inp.type = INPUT_KEYBOARD
                inp.u.ki.wVk = 0
                inp.u.ki.wScan = scan
                inp.u.ki.dwFlags = KEYEVENTF_SCANCODE | flags
                ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
                self.window.after(25 if flags == 0 else 20, lambda: _send(idx + 1))

            _send(0)
        except Exception as e:
            print(f"[Paste] SendInput failed: {e}")
            self._simulate_paste_keybd_event()

    def _simulate_paste_keybd_event(self):
        try:
            import time
            import win32api
            import win32con
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            time.sleep(0.02)
            win32api.keybd_event(ord('V'), 0, 0, 0)
            time.sleep(0.02)
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.02)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        except Exception as e:
            print(f"[Paste] keybd_event failed: {e}")

    # ========== 子窗口 ==========

    def _bring_window_to_front(self, win):
        """把新开的子窗口带到前台。

        弹窗本体是 NOACTIVATE 窗口，进程不持有前台权限时
        Windows 会把新建的 Toplevel 压在前台应用后面，
        必须显式置顶并激活，否则看起来像没打开。
        """
        try:
            win.update_idletasks()
            win.deiconify()
            win.attributes("-topmost", True)
            win.lift()
            import ctypes
            GA_ROOT = 2
            hwnd = ctypes.windll.user32.GetAncestor(win.winfo_id(), GA_ROOT) or win.winfo_id()
            self._tap_alt_for_foreground_permission()
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            win.focus_force()
        except Exception as e:
            print(f"[Popup] bring window to front failed: {e}")

    def _open_cleanup(self):
        w = CleanupWindow(self.window, self.storage)
        self._bring_window_to_front(w.window)

    def _open_settings(self):
        from hotkey_manager import get_hotkey_manager
        w = SettingsWindow(self.window, get_hotkey_manager())
        self._bring_window_to_front(w.window)


# ============================================================
# CleanupWindow
# ============================================================

class CleanupWindow:
    def __init__(self, parent, storage):
        self.storage = storage
        self._sort_by = "use_count"
        self._filter_category = "all"
        self._check_vars = {}
        self._thumbs = {}  # PhotoImage 必须持有引用，否则被 GC 后不显示

        self.window = tk.Toplevel(parent)
        self.window.title("Cleanup")
        self.window.geometry("500x550")
        self.window.configure(bg="#1c1c1c")
        self.window.resizable(True, True)
        self.window.minsize(400, 400)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        bg, fg = "#1c1c1c", "#ffffff"
        tk.Label(self.window, text="Cleanup", bg=bg, fg=fg,
                 font=("Microsoft YaHei UI", 14, "bold")).pack(pady=(16, 8))

        # 缓存大小显示（taste-skill: accent 色）
        self._size_label = tk.Label(self.window, text="", bg=bg, fg="#7eb8ff",
                                    font=("Segoe UI", 9))
        self._size_label.pack(anchor="w", padx=16, pady=(0, 4))

        controls = tk.Frame(self.window, bg=bg)
        controls.pack(fill=tk.X, padx=16, pady=(0, 8))
        tk.Label(controls, text="Sort:", bg=bg, fg="#888888", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self._sort_var = tk.StringVar(value="use_count")
        cb = ttk.Combobox(controls, textvariable=self._sort_var,
                          values=["use_count", "created_at_asc", "copy_count"], state="readonly", width=14)
        cb.pack(side=tk.LEFT, padx=(4, 16))
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_sort_change())

        tk.Label(controls, text="Filter:", bg=bg, fg="#888888", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self._filter_var = tk.StringVar(value="all")
        fb = ttk.Combobox(controls, textvariable=self._filter_var,
                          values=["all", "prompt", "image", "other_text", "favorite"], state="readonly", width=12)
        fb.pack(side=tk.LEFT, padx=(4, 0))
        fb.bind("<<ComboboxSelected>>", lambda e: self._on_filter_change())

        lf = tk.Frame(self.window, bg=bg)
        lf.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)

        self._cc = tk.Canvas(lf, bg=bg, highlightthickness=0)
        sb = tk.Scrollbar(lf, orient=tk.VERTICAL, command=self._cc.yview)
        self._cc.configure(yscrollcommand=sb.set)
        self._cif = tk.Frame(self._cc, bg=bg)
        self._cif.bind("<Configure>", lambda e: self._cc.configure(scrollregion=self._cc.bbox("all")))
        self._cc.create_window((0, 0), window=self._cif, anchor="nw")
        self._cc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        def _mw(event):
            self._cc.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # 绑在窗口上，光标悬停在列表条目等子组件上时滚轮也能生效
        self.window.bind("<MouseWheel>", _mw)

        bf = tk.Frame(self.window, bg=bg)
        bf.pack(fill=tk.X, padx=16, pady=(8, 12))
        self._select_all_var = tk.BooleanVar(value=False)
        tk.Checkbutton(bf, text="Select all", variable=self._select_all_var, bg=bg, fg=fg,
                       selectcolor="#444444", activebackground=bg, activeforeground=fg,
                       command=lambda: self._toggle_all(self._select_all_var.get())).pack(side=tk.LEFT)
        tk.Button(bf, text="Delete selected", bg="#c0392b", fg="white",
                  font=("Microsoft YaHei UI", 10), relief=tk.FLAT, padx=16, pady=4,
                  cursor="hand2", activebackground="#e74c3c", command=self._delete_selected).pack(side=tk.RIGHT)
        tk.Button(bf, text="Cancel", bg="#3a3a3a", fg=fg, font=("Microsoft YaHei UI", 10),
                  relief=tk.FLAT, padx=16, pady=4, cursor="hand2", activebackground="#555555",
                  command=self.window.destroy).pack(side=tk.RIGHT, padx=(0, 8))

    def _format_size(self, size_bytes):
        """字节转人类可读格式"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.1f} GB"

    def _refresh(self):
        for w in self._cif.winfo_children():
            w.destroy()
        self._check_vars = {}

        # 更新缓存大小
        try:
            size = self.storage.get_storage_size()
            self._size_label.config(text=f"缓存占用: {self._format_size(size)}")
        except Exception:
            self._size_label.config(text="缓存占用: --")

        cat = None if self._filter_category == "all" else self._filter_category
        items = self.storage.get_items_sorted(sort_by=self._sort_by, category=cat)
        for item in items:
            fid = item["id"]
            is_fav = bool(item["is_favorite"])
            frame = tk.Frame(self._cif, bg="#1c1c1c")
            frame.pack(fill=tk.X, pady=2)
            var = tk.BooleanVar(value=not is_fav)
            self._check_vars[fid] = var
            tk.Checkbutton(frame, variable=var, bg="#1c1c1c", fg="#ffffff",
                           selectcolor="#444444").pack(side=tk.LEFT)
            if item["content_type"] == "image" and item["image_path"]:
                photo = self._get_thumb(item["image_path"])
                if photo:
                    tk.Label(frame, image=photo, bg="#1c1c1c").pack(side=tk.LEFT, padx=(4, 0))
            summary = item["summary"] or truncate_text(item["text_content"] or "", 35)
            icon = get_display_icon(item["category"], is_fav)
            tk.Label(frame, text=f"{icon} {summary}", bg="#1c1c1c", fg="#ffffff",
                     font=("Microsoft YaHei UI", 10), anchor="w").pack(side=tk.LEFT, padx=(4, 10), fill=tk.X, expand=True)
            tk.Label(frame, text=f"Used: {item['use_count']}x", bg="#1c1c1c", fg="#888888",
                     font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=(0, 8))
            if is_fav:
                tk.Label(frame, text="[已收藏]", bg="#1c1c1c", fg="#f0c040", font=("Segoe UI", 9)).pack(side=tk.RIGHT)

    def _get_thumb(self, image_path):
        """获取缩略图（带缓存）"""
        if image_path in self._thumbs:
            return self._thumbs[image_path]
        try:
            img = PILImage.open(image_path)
            img.thumbnail((36, 36), PILImage.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._thumbs[image_path] = photo
            return photo
        except Exception:
            return None

    def _toggle_all(self, state):
        for var in self._check_vars.values():
            var.set(state)

    def _delete_selected(self):
        selected = [iid for iid, var in self._check_vars.items() if var.get()]
        if not selected:
            messagebox.showinfo("Info", "Select items first")
            return
        if messagebox.askyesno("Confirm", f"Delete {len(selected)} items?"):
            self.storage.soft_delete(selected)
            self._refresh()

    def _on_sort_change(self):
        self._sort_by = self._sort_var.get()
        self._refresh()

    def _on_filter_change(self):
        self._filter_category = self._filter_var.get()
        self._refresh()


# ============================================================
# 单例
# ============================================================

_popup_instance = None


def get_popup():
    global _popup_instance
    if _popup_instance is None:
        _popup_instance = PopupWindow()
    return _popup_instance
