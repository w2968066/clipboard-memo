"""国际化字符串模块"""
from config import get_language

STRINGS = {
    "zh": {
        "app_title": "剪贴板备忘录",
        "search_placeholder": "搜索...",
        "tab_recent": "最近", "tab_favorite": "1收藏",
        "tab_prompt": "2Prompt", "tab_image": "3图片", "tab_deleted": "4删除",
        "sub_all": "全部",
        "btn_categorize": "分类", "btn_categorizing": "分类中…",
        "btn_cleanup": "清理", "btn_settings": "设置",
        "btn_clear_deleted": "清空", "btn_restore": "恢复",
        "empty_recent": "暂无内容", "empty_hint": "复制文本或图片开始记录",
        "empty_deleted": "已删除内容为空",
        "categorize_hint": "悬停条目，1收藏 2Prompt 3图片 4删除",
        "deleted_retention": "已删除内容保留 7 天后自动清除",
        "confirm_clear": "确定要清空所有已删除内容吗？此操作不可恢复。",
        "saved": "设置已保存",
        "hotkey_switched": "快捷键已即时切换为: {}",
        "hotkey_failed": "快捷键已保存为: {}\n但更换失败，请重启应用",
        "settings": "设置",
        "settings_quickcat_title": "快速分类映射",
        "settings_quickcat_hint": "悬停在条目上，按数字键快速分类",
        "settings_hotkey_title": "快捷键",
        "settings_lang_title": "语言 / Language",
        "settings_prompt_subs": "Prompt 子分类",
        "settings_image_subs": "图片子分类",
        "settings_save": "保存", "settings_cancel": "取消",
        "cat_names": {"prompt":"提示词","image":"图片","other_text":"其他文本","favorite":"收藏"}
    },
    "en": {
        "app_title": "Clipboard Memo",
        "search_placeholder": "Search...",
        "tab_recent": "Recent", "tab_favorite": "1Saved",
        "tab_prompt": "2Prompts", "tab_image": "3Images", "tab_deleted": "4Trash",
        "sub_all": "All",
        "btn_categorize": "Categorize", "btn_categorizing": "Categorizing...",
        "btn_cleanup": "Cleanup", "btn_settings": "Settings",
        "btn_clear_deleted": "Clear All", "btn_restore": "Restore",
        "empty_recent": "No items yet", "empty_hint": "Copy text or images to start",
        "empty_deleted": "Trash is empty",
        "categorize_hint": "Hover item: 1Save 2Prompt 3Image 4Trash",
        "deleted_retention": "Items in trash are kept for 7 days",
        "confirm_clear": "Permanently clear all trashed items?",
        "saved": "Settings saved",
        "hotkey_switched": "Hotkey switched to: {}",
        "hotkey_failed": "Hotkey saved as: {}\nCould not switch, restart required",
        "settings": "Settings",
        "settings_quickcat_title": "Quick Categorize Mapping",
        "settings_quickcat_hint": "Hover over items, press number keys to categorize",
        "settings_hotkey_title": "Hotkey",
        "settings_lang_title": "Language / 语言",
        "settings_prompt_subs": "Prompt Subcategories",
        "settings_image_subs": "Image Subcategories",
        "settings_save": "Save", "settings_cancel": "Cancel",
        "cat_names": {"prompt":"Prompt","image":"Image","other_text":"Other","favorite":"Saved"}
    }
}


def t(key, lang=None):
    """获取国际化文本"""
    if lang is None:
        lang = get_language()
    return STRINGS.get(lang, STRINGS["en"]).get(key, key)


def cat_name(cat, lang=None):
    """获取分类显示名"""
    return STRINGS.get(lang or get_language(), {}).get("cat_names", {}).get(cat, cat)
