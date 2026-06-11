"""
宸ュ叿鍑芥暟妯″潡
"""

import hashlib
import re
import os
import uuid
from datetime import datetime
from functools import lru_cache


def compute_hash(text):
    """璁＄畻鏂囨湰鐨?MD5 鍝堝笇"""
    return hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()


def compute_image_hash(image_bytes):
    """璁＄畻鍥剧墖鏁版嵁鐨?MD5 鍝堝笇"""
    return hashlib.md5(image_bytes).hexdigest()


def generate_image_filename():
    """鐢熸垚鍞竴鐨勫浘鐗囨枃浠跺悕"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = str(uuid.uuid4())[:8]
    return f"clip_{timestamp}_{uid}.png"


@lru_cache(maxsize=512)
def _parse_time(timestamp_str):
    """缂撳瓨鏃堕棿瑙ｆ瀽缁撴灉"""
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"]:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    return None


def format_time(timestamp_str):
    """鏍煎紡鍖栨椂闂存埑涓虹畝鐭樉绀烘牸寮?""
    if not timestamp_str:
        return ""
    try:
        dt = _parse_time(timestamp_str)
        if dt is None:
            return timestamp_str

        now = datetime.now()
        diff = now - dt

        if diff.days == 0:
            if diff.seconds < 60:
                return "鍒氬垰"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60}鍒嗛挓鍓?
            else:
                return f"{diff.seconds // 3600}灏忔椂鍓?
        elif diff.days == 1:
            return "鏄ㄥぉ " + dt.strftime("%H:%M")
        elif diff.days < 7:
            return f"{diff.days}澶╁墠"
        else:
            return dt.strftime("%m/%d %H:%M")
    except Exception:
        return timestamp_str


def truncate_text(text, max_len=50):
    """鎴柇鏂囨湰鍒版寚瀹氶暱搴?""
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\r", " ").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len-3] + "..."


def is_url(text):
    """鍒ゆ柇鏂囨湰鏄惁涓虹函 URL"""
    text = text.strip()
    url_pattern = re.compile(
        r'^(https?://|ftp://|file://|www\.)[^\s]*$',
        re.IGNORECASE
    )
    return bool(url_pattern.match(text))


def get_display_icon(category, is_favorite=False):
    """鑾峰彇鍒嗙被瀵瑰簲鐨勬樉绀烘爣璁帮紙绾枃瀛楋紝鏃?emoji锛?""
    if is_favorite:
        return "[鏀惰棌]"
    icons = {
        "prompt": "[鎻愮ず璇峕",
        "image": "[鍥剧墖]",
        "other_text": "[鏂囨湰]",
        "favorite": "[鏀惰棌]"
    }
    return icons.get(category, "[鏂囨湰]")


def get_category_name(category):
    """鑾峰彇鍒嗙被鐨勪腑鏂囧悕绉?""
    names = {
        "prompt": "鎻愮ず璇?,
        "image": "鍥剧墖",
        "other_text": "鍏朵粬鏂囨湰",
        "favorite": "甯哥敤"
    }
    return names.get(category, category)
