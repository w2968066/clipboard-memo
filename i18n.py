"""鍥介檯鍖栧瓧绗︿覆妯″潡"""
from config import get_language

STRINGS = {
    "zh": {
        "app_title": "鍓创鏉垮蹇樺綍",
        "search_placeholder": "鎼滅储...",
        "tab_recent": "鏈€杩?, "tab_favorite": "1鏀惰棌",
        "tab_prompt": "2Prompt", "tab_image": "3鍥剧墖", "tab_deleted": "4鍒犻櫎",
        "sub_all": "鍏ㄩ儴",
        "btn_categorize": "鍒嗙被", "btn_categorizing": "鍒嗙被涓€?,
        "btn_cleanup": "娓呯悊", "btn_settings": "璁剧疆",
        "btn_clear_deleted": "娓呯┖", "btn_restore": "鎭㈠",
        "empty_recent": "鏆傛棤鍐呭", "empty_hint": "澶嶅埗鏂囨湰鎴栧浘鐗囧紑濮嬭褰?,
        "empty_deleted": "宸插垹闄ゅ唴瀹逛负绌?,
        "categorize_hint": "鎮仠鏉＄洰锛?鏀惰棌 2Prompt 3鍥剧墖 4鍒犻櫎",
        "deleted_retention": "宸插垹闄ゅ唴瀹逛繚鐣?7 澶╁悗鑷姩娓呴櫎",
        "confirm_clear": "纭畾瑕佹竻绌烘墍鏈夊凡鍒犻櫎鍐呭鍚楋紵姝ゆ搷浣滀笉鍙仮澶嶃€?,
        "saved": "璁剧疆宸蹭繚瀛?,
        "hotkey_switched": "蹇嵎閿凡鍗虫椂鍒囨崲涓? {}",
        "hotkey_failed": "蹇嵎閿凡淇濆瓨涓? {}\n浣嗘洿鎹㈠け璐ワ紝璇烽噸鍚簲鐢?,
        "settings": "璁剧疆",
        "settings_quickcat_title": "蹇€熷垎绫绘槧灏?,
        "settings_quickcat_hint": "鎮仠鍦ㄦ潯鐩笂锛屾寜鏁板瓧閿揩閫熷垎绫?,
        "settings_hotkey_title": "蹇嵎閿?,
        "settings_lang_title": "璇█ / Language",
        "settings_prompt_subs": "Prompt 瀛愬垎绫?,
        "settings_image_subs": "鍥剧墖瀛愬垎绫?,
        "settings_save": "淇濆瓨", "settings_cancel": "鍙栨秷",
        "cat_names": {"prompt":"鎻愮ず璇?,"image":"鍥剧墖","other_text":"鍏朵粬鏂囨湰","favorite":"鏀惰棌"}
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
        "settings_lang_title": "Language / 璇█",
        "settings_prompt_subs": "Prompt Subcategories",
        "settings_image_subs": "Image Subcategories",
        "settings_save": "Save", "settings_cancel": "Cancel",
        "cat_names": {"prompt":"Prompt","image":"Image","other_text":"Other","favorite":"Saved"}
    }
}


def t(key, lang=None):
    """鑾峰彇鍥介檯鍖栨枃鏈?""
    if lang is None:
        lang = get_language()
    return STRINGS.get(lang, STRINGS["en"]).get(key, key)


def cat_name(cat, lang=None):
    """鑾峰彇鍒嗙被鏄剧ず鍚?""
    return STRINGS.get(lang or get_language(), {}).get("cat_names", {}).get(cat, cat)
