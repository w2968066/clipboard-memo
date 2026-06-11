"""
配置管理模块（带内存缓存 + 原子写入）
"""

import json
import os
import sys
import threading


def get_app_dir():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return base


APP_DIR = get_app_dir()
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
DATA_DIR = os.path.join(APP_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "clipboard.db")
IMAGES_DIR = os.path.join(APP_DIR, "assets", "images")
ICON_PATH = os.path.join(APP_DIR, "assets", "icon.png")

DEFAULT_CONFIG = {
    "hotkey": "ctrl+alt+v",
    "language": "zh",
    "popup_width": 380,
    "popup_max_height": 500,
    "max_history": 500,
    "poll_interval_ms": 500,
    "auto_start": False,
    "quick_categorize_prompt": {
        "1": "prompt_sub1", "2": "prompt_sub2",
        "3": "prompt_sub3", "4": "prompt_sub4"
    },
    "quick_categorize_image": {
        "1": "image_sub1", "2": "image_sub2",
        "3": "image_sub3", "4": "image_sub4"
    },
    "subcategory_names": {
        "prompt_sub1": "子分类1", "prompt_sub2": "子分类2",
        "prompt_sub3": "子分类3", "prompt_sub4": "子分类4",
        "image_sub1": "子分类1", "image_sub2": "子分类2",
        "image_sub3": "子分类3", "image_sub4": "子分类4"
    }
}

# ---- 内存缓存 ----
_config_cache = None
_config_mtime = 0
_config_lock = threading.Lock()


def load_config():
    """加载配置，优先使用内存缓存"""
    global _config_cache, _config_mtime

    with _config_lock:
        try:
            mtime = os.path.getmtime(CONFIG_PATH)
        except OSError:
            mtime = 0

        if _config_cache is not None and mtime == _config_mtime:
            return _config_cache.copy()

        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                # 补全缺失的默认键
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                _config_cache = config
                _config_mtime = mtime
                return config.copy()
            except (json.JSONDecodeError, IOError):
                pass

        config = DEFAULT_CONFIG.copy()
        _config_cache = config
        _config_mtime = 0
        save_config(config)
        return config.copy()


def save_config(config):
    """原子写入配置"""
    global _config_cache, _config_mtime
    with _config_lock:
        _config_cache = config.copy()
        tmp_path = CONFIG_PATH + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, CONFIG_PATH)
            try:
                _config_mtime = os.path.getmtime(CONFIG_PATH)
            except OSError:
                _config_mtime = 0
        except Exception:
            # 清理临时文件
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            raise


def get_config(key, default=None):
    """读取配置项（带缓存，无需每次都读文件）"""
    global _config_cache
    with _config_lock:
        if _config_cache is not None:
            return _config_cache.get(key, default)
    # 冷启动回退
    return load_config().get(key, default)


def set_config(key, value):
    """设置配置项"""
    config = load_config()
    config[key] = value
    save_config(config)


def get_language():
    return get_config("language", "zh")


def get_subcategory_name(sc_key):
    names = get_config("subcategory_names", {})
    return names.get(sc_key, sc_key)


def get_quick_categorize(tab="prompt"):
    """获取指定 tab 的快速分类映射"""
    config = load_config()
    key = f"quick_categorize_{tab}"
    default = DEFAULT_CONFIG.get(key, {})
    return config.get(key, default)
