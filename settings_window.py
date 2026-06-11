"""璁剧疆绐楀彛妯″潡"""
import tkinter as tk
from tkinter import ttk, messagebox
from config import get_config, load_config, save_config
from i18n import t


class SettingsWindow:
    def __init__(self, parent, hotkey_manager):
        self.hotkey_manager = hotkey_manager
        self.lang = get_config("language", "zh")

        self.window = tk.Toplevel(parent)
        self.window.title(t("settings", self.lang))
        self.window.attributes("-topmost", True)
        self.window.geometry("500x580")
        self.window.configure(bg="#1c1c1c")
        self.window.resizable(True, True)
        self.window.minsize(420, 400)

        # 鍙粴鍔ㄥ唴瀹瑰尯
        canvas = tk.Canvas(self.window, bg="#1c1c1c", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.window, orient=tk.VERTICAL, command=canvas.yview)
        self._content = tk.Frame(canvas, bg="#1c1c1c")
        self._content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._canvas_content_id = canvas.create_window((0, 0), window=self._content, anchor="nw")

        def _on_canvas_conf(event):
            canvas.itemconfig(self._canvas_content_id, width=event.width)
        canvas.bind("<Configure>", _on_canvas_conf)

        def _wheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.window.bind("<MouseWheel>", _wheel)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._build_ui()

    def _section(self, title):
        return tk.LabelFrame(self._content, text=f"  {title}  ", bg="#1c1c1c", fg="#ffffff",
                             font=("Microsoft YaHei UI", 10), padx=12, pady=12)

    def _build_ui(self):
        tk.Label(self._content, text=t("settings", self.lang), bg="#1c1c1c", fg="#ffffff",
                 font=("Microsoft YaHei UI", 14, "bold")).pack(pady=(16, 12))

        self._build_subcategories("prompt", t("settings_prompt_subs", self.lang))
        self._build_subcategories("image", t("settings_image_subs", self.lang))
        self._build_hotkey_section()
        self._build_language_section()
        self._build_buttons()

    def _build_subcategories(self, prefix, title):
        sec = self._section(title)
        sec.pack(fill=tk.X, padx=20, pady=(0, 12))

        names = get_config("subcategory_names", {})
        for i in range(1, 5):
            sc_key = f"{prefix}_sub{i}"
            row = tk.Frame(sec, bg="#1c1c1c")
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{i}:", bg="#1c1c1c", fg="#ffffff", width=2).pack(side=tk.LEFT)
            var = tk.StringVar(value=names.get(sc_key, f"Sub {i}"))
            setattr(self, f"_name_{sc_key}", var)
            tk.Entry(row, textvariable=var, bg="#2a2a2a", fg="#ffffff", insertbackground="#ffffff",
                     font=("Microsoft YaHei UI", 10), relief=tk.FLAT, bd=0, width=20).pack(
                side=tk.LEFT, padx=(8, 0), ipady=2)

    def _build_hotkey_section(self):
        sec = self._section(t("settings_hotkey_title", self.lang))
        sec.pack(fill=tk.X, padx=20, pady=(0, 12))

        current_hk = get_config("hotkey", "ctrl+alt+v")
        parts = [p.strip().lower() for p in current_hk.split("+")]
        self._mod_ctrl = tk.BooleanVar(value="ctrl" in parts)
        self._mod_alt = tk.BooleanVar(value="alt" in parts)
        self._mod_shift = tk.BooleanVar(value="shift" in parts)
        self._mod_win = tk.BooleanVar(value="win" in parts)
        main_key = parts[-1] if parts else "v"

        mf = tk.Frame(sec, bg="#1c1c1c")
        mf.pack(fill=tk.X)
        for text, var in [("Ctrl", self._mod_ctrl), ("Alt", self._mod_alt),
                          ("Shift", self._mod_shift), ("Win", self._mod_win)]:
            tk.Checkbutton(mf, text=text, variable=var, bg="#1c1c1c", fg="#ffffff",
                           selectcolor="#444444", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 12))

        kf = tk.Frame(sec, bg="#1c1c1c")
        kf.pack(fill=tk.X, pady=(8, 0))
        tk.Label(kf, text="+", bg="#1c1c1c", fg="#888888").pack(side=tk.LEFT, padx=(0, 6))
        self._key_var = tk.StringVar(value=main_key.upper())
        keys_list = [chr(i) for i in range(65, 91)] + [str(i) for i in range(10)] + \
                    ["F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12","Space","Tab"]
        ttk.Combobox(kf, textvariable=self._key_var, values=keys_list, state="readonly", width=6).pack(side=tk.LEFT)

        self._hk_preview = tk.Label(sec, text="", bg="#1c1c1c", fg="#7eb8ff", font=("Segoe UI", 9))
        self._hk_preview.pack(anchor="w", pady=(8, 0))
        self._update_hk_preview()
        for var in [self._mod_ctrl, self._mod_alt, self._mod_shift, self._mod_win]:
            var.trace_add("write", lambda *a: self._update_hk_preview())
        self._key_var.trace_add("write", lambda *a: self._update_hk_preview())

    def _build_language_section(self):
        sec = self._section(t("settings_lang_title", self.lang))
        sec.pack(fill=tk.X, padx=20, pady=(0, 16))

        self._lang_var = tk.StringVar(value=self.lang)
        for val, label in [("zh", "涓枃"), ("en", "English")]:
            tk.Radiobutton(sec, text=label, variable=self._lang_var, value=val,
                           bg="#1c1c1c", fg="#ffffff", selectcolor="#444444",
                           font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 24))

    def _build_buttons(self):
        bf = tk.Frame(self._content, bg="#1c1c1c")
        bf.pack(fill=tk.X, padx=20, pady=(0, 16))
        tk.Button(bf, text=t("settings_save", self.lang), bg="#7eb8ff", fg="#111111",
                  font=("Microsoft YaHei UI", 10), relief=tk.FLAT, padx=24, pady=4,
                  command=self._save).pack(side=tk.RIGHT, padx=(8, 0))
        tk.Button(bf, text=t("settings_cancel", self.lang), bg="#3a3a3a", fg="#ffffff",
                  font=("Microsoft YaHei UI", 10), relief=tk.FLAT, padx=24, pady=4,
                  command=self.window.destroy).pack(side=tk.RIGHT)

    def _update_hk_preview(self):
        parts = [m for m, v in [("Ctrl", self._mod_ctrl), ("Alt", self._mod_alt),
                 ("Shift", self._mod_shift), ("Win", self._mod_win)] if v.get()]
        parts.append(self._key_var.get().lower())
        self._hk_preview.config(text=f"Current: {'+'.join(parts)}")

    def _save(self):
        config = load_config()

        names = config.get("subcategory_names", {})
        for prefix in ["prompt", "image"]:
            for i in range(1, 5):
                key = f"{prefix}_sub{i}"
                var = getattr(self, f"_name_{key}", None)
                if var:
                    names[key] = var.get()
        config["subcategory_names"] = names

        parts = [m for m, v in [("ctrl", self._mod_ctrl), ("alt", self._mod_alt),
                 ("shift", self._mod_shift), ("win", self._mod_win)] if v.get()]
        parts.append(self._key_var.get().lower())
        new_hk = "+".join(parts)
        old_hk = config.get("hotkey", "ctrl+alt+v")
        config["hotkey"] = new_hk

        new_lang = self._lang_var.get()
        config["language"] = new_lang
        save_config(config)

        msgs = [t("saved", new_lang)]
        if new_hk != old_hk:
            msgs.append(t("hotkey_switched", new_lang).format(new_hk) if self.hotkey_manager.reregister(new_hk)
                        else t("hotkey_failed", new_lang).format(new_hk))
        if new_lang != self.lang:
            msgs.append("Restart to apply language change")

        messagebox.showinfo(t("saved", new_lang), "\n".join(msgs))
        self.window.destroy()
