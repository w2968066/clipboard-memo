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
    ('甯垜鍐欎竴涓狿ython鑴氭湰锛屽疄鐜拌嚜鍔ㄥ浠藉姛鑳?, 'prompt'),
    ('https://www.example.com/path/to/page', 'other_text'),
    ('hello world', 'other_text'),
    ('浣犳槸涓€涓祫娣辩殑Python寮€鍙戣€咃紝璇峰府鎴戝垎鏋愯繖娈典唬鐮佺殑鎬ц兘闂', 'prompt'),
    ('translate the following text to Chinese: Hello, how are you?', 'prompt'),
    ('act as a senior engineer and review this code', 'prompt'),
    ('浠婂ぉ澶╂皵涓嶉敊', 'other_text'),
    ('甯垜', 'other_text'),  # too short, score reduced by 0.5
    ('璇风敤markdown鏍煎紡鍐欎竴浠介」鐩鍒掍功锛屽寘鍚互涓嬪唴瀹癸細1. 椤圭洰鑳屾櫙 2. 鎶€鏈柟妗?3. 瀹炴柦姝ラ', 'prompt'),
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
