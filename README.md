# 鍓创鏉垮蹇樺綍 (Clipboard Memo)

<p align="center">
  <img src="assets/icon.png" width="128" alt="Clipboard Memo">
</p>

<p align="center">
  <b>鏋佺畝鏈湴鍓创鏉跨鐞嗗伐鍏凤紝涓撲负 AI 鐢ㄦ埛璁捐</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows-blue?style=flat-square">
  <img src="https://img.shields.io/badge/python-3.8+-green?style=flat-square">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square">
  <img src="https://img.shields.io/badge/dependencies-3-lightgrey?style=flat-square">
  <img src="https://img.shields.io/badge/network-zero-red?style=flat-square">
</p>

---

## Why this exists

> "璇曡繃 7 娆惧壀璐存澘宸ュ叿鍚庯紝鎴戣姳浜?3 涓櫄涓婏紝鍐欎簡鑷繁鐨勩€?

甯傞潰涓婂ぇ澶氭暟鍓创鏉垮伐鍏峰お閲嶄簡鈥斺€斿嚑鍗?MB 瀹夎鍖呫€佹敞鍐岃处鍙枫€佷簯鍚屾銆佷粯璐瑰脊绐椼€備綔涓?AI 鐢ㄦ埛锛屾垜鍙兂瀛樹釜鎻愮ず璇嶃€?
**鍓创鏉垮蹇樺綍**鏄竴涓?Python 鑴氭湰浣撻噺鐨勫伐鍏枫€? 涓緷璧栥€侀浂缃戠粶銆佺函鏈湴銆佸畬鍏ㄥ紑婧愩€?
---

## Features

| 鍔熻兘 | 璇存槑 |
|---|---|
| 馃攳 **鑷姩鎹曡幏** | 澶嶅埗鏂囨湰鎴栨埅鍥捐嚜鍔ㄤ繚瀛橈紝500ms 杞妫€娴?|
| 馃 **鏅鸿兘鍒嗙被** | 绾湰鍦板淇″彿璇勫垎寮曟搸锛岃嚜鍔ㄨ瘑鍒?Prompt/鍥剧墖/鏂囨湰 |
| 鈱笍 **鐑敭鍛煎嚭** | `Ctrl+Shift+V` 鍏ㄥ眬鐑敭锛岄紶鏍囪窡闅忓脊鍑?|
| 馃彿锔?**蹇€熷垎绫?* | 鎮仠鏉＄洰 + 鏁板瓧閿?1-4锛氭敹钘?Prompt/鍥剧墖/鍒犻櫎 |
| 馃摉 **鐘舵€佹爣璇?* | 宸插垎绫?鏈垎绫?馃摉 鏍囪瘑锛屾敹钘?猸愶笍 鏍囪瘑 |
| 馃搨 **瀛愬垎绫?* | Prompt 鍜屽浘鐗囧悇 4 绾у彲鑷畾涔夊瓙鍒嗙被 |
| 馃攧 **鍗曟潯鍒锋柊** | 鍒嗙被/鏀惰棌鎿嶄綔鍙埛鏂板崟鏉＄姸鎬侊紝涓嶅崱椤?|
| 馃捑 **杞垹闄?* | 宸插垹闄ゅ唴瀹逛繚鐣?7 澶╋紝闅忔椂鎭㈠ |
| 馃Ч **缂撳瓨绠＄悊** | 鏄剧ず鏁版嵁搴?鍥剧墖鎬诲崰鐢紝鎵归噺娓呯悊 |
| 馃寪 **鍥介檯鍖?* | 涓枃/鑻辨枃鍙岃鏀寔 |
| 馃殌 **寮€鏈鸿嚜鍚?* | 鎵樼洏鑿滃崟涓€閿垏鎹?|
| 鈿欙笍 **璁剧疆** | 鑷畾涔夌儹閿€佸瓙鍒嗙被鍚嶇О銆佽瑷€ |

---

## Quick Start

### 1. 瀹夎渚濊禆

```bash
pip install -r requirements.txt
```

3 涓緷璧栵細
- `pystray` 鈥?绯荤粺鎵樼洏
- `Pillow` 鈥?鍥剧墖缂╃暐鍥?- `pywin32` 鈥?鍓创鏉胯鍐欍€佸叏灞€鐑敭

### 2. 鍚姩

```bash
python main.py
```

### 3. 浣跨敤

| 鎿嶄綔 | 璇存槑 |
|---|---|
| `Ctrl+Shift+V` | 鍛煎嚭/闅愯棌娴獥 |
| 鐐瑰嚮鏉＄洰 | 绮樿创鍒板綋鍓嶅厜鏍囦綅缃?|
| 鐐瑰嚮 `鍒嗙被` 鎸夐挳 | 杩涘叆蹇€熷垎绫绘ā寮?|
| 鎮仠鏉＄洰 + `1/2/3/4` | 鏀惰棌 / Prompt / 鍥剧墖 / 鍒犻櫎 |
| `Backspace` / `Delete` | 鍒犻櫎褰撳墠鎮仠鏉＄洰 |
| `Esc` | 鍏抽棴娴獥 |
| `鈫戔啌` | 瀵艰埅閫夋嫨鏉＄洰 |
| `Enter` | 绮樿创閫変腑鏉＄洰 |
| 鍙抽敭鏉＄洰 | 澶嶅埗/鏀惰棌/缂栬緫鏍囬/鍒犻櫎 |

### 4. 涓€閿墦鍖咃紙鍙€夛級

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ClipboardMemo main.py
```

---

## Architecture

```
clipboard-memo/
鈹溾攢鈹€ main.py              # 搴旂敤鍏ュ彛锛屽惎鍔ㄦ祦绋嬬紪鎺?鈹溾攢鈹€ popup_window.py       # 寮圭獥 UI锛堟诞绐?+ 娓呯悊绐楀彛锛?鈹溾攢鈹€ clipboard_monitor.py  # 鍓创鏉胯疆璇㈢洃鎺?鈹溾攢鈹€ classifier.py         # 鏂囨湰鍒嗙被寮曟搸锛堝淇″彿璇勫垎锛?鈹溾攢鈹€ storage.py            # SQLite 鏁版嵁灞傦紙WAL 妯″紡锛?鈹溾攢鈹€ hotkey_manager.py     # Windows 鍏ㄥ眬鐑敭锛圧egisterHotKey锛?鈹溾攢鈹€ tray_icon.py          # 绯荤粺鎵樼洏锛坧ystray锛?鈹溾攢鈹€ settings_window.py    # 璁剧疆绐楀彛
鈹溾攢鈹€ config.py             # 閰嶇疆绠＄悊锛堝唴瀛樼紦瀛橈級
鈹溾攢鈹€ utils.py              # 宸ュ叿鍑芥暟
鈹溾攢鈹€ i18n.py               # 鍥介檯鍖栵紙zh/en锛?鈹溾攢鈹€ config.json           # 杩愯鏃堕厤缃?鈹溾攢鈹€ data/clipboard.db     # SQLite 鏁版嵁搴擄紙鑷姩鍒涘缓锛?鈹溾攢鈹€ assets/images/        # 鍥剧墖瀛樺偍
鈹斺攢鈹€ requirements.txt      # 3 涓緷璧?```

### Classification Engine

```
classify_text(text) 鈫?(category, summary, subcategory)

澶氫俊鍙疯瘎鍒嗘潈閲嶏細
  鎸囦护鎬у姩璇?   鏉冮噸 4  (涓婇檺 12)
  瑙掕壊瀹氫箟妯″紡  鏉冮噸 5  (鍛戒腑鍗虫弧鍒?
  缁撴瀯鍖栫壒寰?   鏉冮噸 2-3 (涓婇檺 6)
  鎻愰棶妯″紡      鏉冮噸 2  (涓婇檺 4)
  浠ｇ爜鐩稿叧      鏉冮噸 2  (涓婇檺 4)
  闀垮害绯绘暟      脳0.5 ~ 脳1.0
  鈫?鎬诲垎 鈮?5 鈫?"prompt" | 鍚﹀垯 "other_text"
```

### Hotkey System

```
Windows RegisterHotKey + HWND_MESSAGE 娑堟伅绐楀彛
鈫?PeekMessageW 闈為樆濉炴秷鎭惊鐜?鈫?鏀寔鐑垏鎹紙reregister 鏃犻渶閲嶅惎锛?鈫?64-bit 鍘熺敓鏀寔锛堟樉寮忓０鏄?ctypes argtypes锛?```

---

## Tech Stack

| 灞?| 鎶€鏈?|
|---|---|
| UI | tkinter (overrideredirect 鏃犺竟妗嗙獥鍙? |
| 鏁版嵁 | SQLite (WAL, threading.local 杩炴帴姹? |
| 鍒嗙被 | 绾湰鍦版鍒欒鍒欏紩鎿?|
| 鐑敭 | Windows RegisterHotKey API (ctypes) |
| 鎵樼洏 | pystray + PIL 鍥炬爣缁樺埗 |
| 閰嶇疆 | JSON 鏂囦欢 + 鍐呭瓨缂撳瓨 |
| 闊虫晥 | (鏃?鈥?瀹屽叏闈欓粯杩愯) |

---

## FAQ

**Q: 涓轰粈涔堝彧鏈?Windows 鐗堬紵**
A: 鐩墠浣跨敤浜?Windows 鍘熺敓 API锛圧egisterHotKey銆佸壀璐存澘璇诲啓锛夈€俶acOS/Linux 鏀寔璁″垝涓€?
**Q: 鏁版嵁瀹夊叏鍚楋紵**
A: 瀹屽叏鏈湴杩愯锛岄浂缃戠粶璇锋眰銆係QLite 鏂囦欢鍦?`data/clipboard.db`锛屽浘鐗囧湪 `assets/images/`銆?
**Q: 鎬庝箞鍗歌浇锛?*
A: 鍒犻櫎鏂囦欢澶瑰嵆鍙€傚鏋滃惎鐢ㄤ簡寮€鏈鸿嚜鍚紝鍏堝湪鎵樼洏鑿滃崟涓叧闂€?
---

## License

MIT 漏 2026

---

<p align="center">
  <sub>Built with 鉂わ笍 for the vibecoding community. #vibecoding澶ц祻</sub>
</p>
