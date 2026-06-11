"""Quick test of all modules"""
import sys
sys.path.insert(0, '.')

print('Testing imports...')

from config import load_config, DEFAULT_CONFIG
print('  config.py OK')

from utils import compute_hash, format_time, truncate_text, get_display_icon
print('  utils.py OK')

from storage import Storage
print('  storage.py OK')
s = Storage()
row = s._get_conn().execute("PRAGMA database_list").fetchone()
print(f'  DB created at: {row[2]}')

from classifier import classify_text
print('  classifier.py OK')

# Test classifier
tests = [
    ('帮我写一个Python脚本，实现自动备份功能', 'prompt'),
    ('https://www.example.com/path/to/page', 'other_text'),
    ('hello world', 'other_text'),
    ('你是一个资深的Python开发者，请帮我分析这段代码的性能问题', 'prompt'),
    ('translate the following text to Chinese: Hello, how are you?', 'prompt'),
    ('act as a senior engineer and review this code', 'prompt'),
    ('今天天气不错', 'other_text'),
    ('帮我', 'other_text'),  # too short, score reduced by 0.5
    ('请用markdown格式写一份项目计划书，包含以下内容：1. 项目背景 2. 技术方案 3. 实施步骤', 'prompt'),
]

print('\nClassifier tests:')
all_pass = True
for text, expected in tests:
    cat, summary, subcat = classify_text(text)
    status = 'OK' if cat == expected else 'FAIL'
    if cat != expected:
        all_pass = False
    print(f'  [{status}] "{text[:40]}..." -> {cat}/{subcat} | {summary}')

print(f'\nAll imports successful! Classifier tests: {"ALL PASSED" if all_pass else "SOME FAILED"}')
if not all_pass:
    print('  (Some classifier tests failed - check the scoring algorithm)')

# Test popup window creation (won't display, just verify code loads)
print('\nTesting popup_window imports...')
from popup_window import PopupWindow, CleanupWindow, get_popup
print('  popup_window.py OK')

print('\nTesting hotkey_manager imports...')
from hotkey_manager import HotkeyManager, parse_hotkey_string
hotkey = parse_hotkey_string("ctrl+alt+v")
print(f'  hotkey_manager.py OK (parsed: {hotkey})')

print('\nTesting tray_icon imports...')
from tray_icon import TrayIcon
print('  tray_icon.py OK')

print('\n[SUCCESS] All modules loaded successfully!')
