"""
工具函数模块
"""

import hashlib
import re
import os
import uuid
from datetime import datetime
from functools import lru_cache


def compute_hash(text):
    """计算文本的 MD5 哈希"""
    return hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()


def compute_image_hash(image_bytes):
    """计算图片数据的 MD5 哈希"""
    return hashlib.md5(image_bytes).hexdigest()


def generate_image_filename():
    """生成唯一的图片文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = str(uuid.uuid4())[:8]
    return f"clip_{timestamp}_{uid}.png"


@lru_cache(maxsize=512)
def _parse_time(timestamp_str):
    """缓存时间解析结果"""
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"]:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    return None


def format_time(timestamp_str):
    """格式化时间戳为简短显示格式"""
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
                return "刚刚"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60}分钟前"
            else:
                return f"{diff.seconds // 3600}小时前"
        elif diff.days == 1:
            return "昨天 " + dt.strftime("%H:%M")
        elif diff.days < 7:
            return f"{diff.days}天前"
        else:
            return dt.strftime("%m/%d %H:%M")
    except Exception:
        return timestamp_str


def truncate_text(text, max_len=50):
    """截断文本到指定长度"""
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\r", " ").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len-3] + "..."


def is_url(text):
    """判断文本是否为纯 URL"""
    text = text.strip()
    url_pattern = re.compile(
        r'^(https?://|ftp://|file://|www\.)[^\s]*$',
        re.IGNORECASE
    )
    return bool(url_pattern.match(text))


def get_display_icon(category, is_favorite=False):
    """获取分类对应的显示标记（纯文字，无 emoji）"""
    if is_favorite:
        return "[收藏]"
    icons = {
        "prompt": "[提示词]",
        "image": "[图片]",
        "other_text": "[文本]",
        "favorite": "[收藏]"
    }
    return icons.get(category, "[文本]")


def get_category_name(category):
    """获取分类的中文名称"""
    names = {
        "prompt": "提示词",
        "image": "图片",
        "other_text": "其他文本",
        "favorite": "常用"
    }
    return names.get(category, category)
