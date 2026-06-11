"""
閰嶇疆绠＄悊妯″潡锛堝甫鍐呭瓨缂撳瓨 + 鍘熷瓙鍐欏叆锛?"""

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
        "prompt_sub1": "瀛愬垎绫?", "prompt_sub2": "瀛愬垎绫?",
        "prompt_sub3": "瀛愬垎绫?", "prompt_sub4": "瀛愬垎绫?",
        "image_sub1": "瀛愬垎绫?", "image_sub2": "瀛愬垎绫?",
        "image_sub3": "瀛愬垎绫?", "image_sub4": "瀛愬垎绫?"
    }
}

# ---- 鍐呭瓨缂撳瓨 ----
_config_cache = None
_config_mtime = 0
_config_lock = threading.Lock()


def load_config():
    """鍔犺浇閰嶇疆锛屼紭鍏堜娇鐢ㄥ唴瀛樼紦瀛?""
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
                # 琛ュ叏缂哄け鐨勯粯璁ら敭
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
    """鍘熷瓙鍐欏叆閰嶇疆"""
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
            # 娓呯悊涓存椂鏂囦欢
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            raise


def get_config(key, default=None):
    """璇诲彇閰嶇疆椤癸紙甯︾紦瀛橈紝鏃犻渶姣忔閮借鏂囦欢锛?""
    global _config_cache
    with _config_lock:
        if _config_cache is not None:
            return _config_cache.get(key, default)
    # 鍐峰惎鍔ㄥ洖閫€
    return load_config().get(key, default)


def set_config(key, value):
    """璁剧疆閰嶇疆椤?""
    config = load_config()
    config[key] = value
    save_config(config)


def get_language():
    return get_config("language", "zh")


def get_subcategory_name(sc_key):
    names = get_config("subcategory_names", {})
    return names.get(sc_key, sc_key)


def get_quick_categorize(tab="prompt"):
    """鑾峰彇鎸囧畾 tab 鐨勫揩閫熷垎绫绘槧灏?""
    config = load_config()
    key = f"quick_categorize_{tab}"
    default = DEFAULT_CONFIG.get(key, {})
    return config.get(key, default)
